"""Phase 2 solve path: context -> prompt -> model -> constraint check.

Backends
--------
groq   : the target backend, gpt-oss-120b by default (override with the
         GROQ_MODEL env var). The ProManager reuse is the call shape, not
         the model name - Llama is not enabled on this key. Needs
         GROQ_API_KEY. Selected automatically when that variable is set.
ollama : local fallback, for verifying the plumbing only. The installed
         models are 3-4B; a small model breaking rule 2 says nothing about
         whether Llama-70B would, so treat local runs as a smoke test of the
         wiring and never as evidence about constraint adherence.

The constraint checker used to live here too; it now has its own module,
checker.py, imported below for main()'s end-to-end run. Nothing about its
rules changed in that move.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from checker import check_constraints

# Config moved to config.py; re-exported here so existing imports keep
# working unchanged - llm_stream.py does `from generate import GROQ_MODEL,
# GROQ_URL`, and load_env is imported from here by gatekeeper.py.
from config import (  # noqa: F401  (re-exported for backwards compatibility)
    GROQ_MODEL,
    GROQ_URL,
    OLLAMA_MODEL,
    OLLAMA_URL,
    load_env,
)
from context import build_context
from prompts import build_messages


def call_groq(messages: list[dict], temperature: float = 0.2) -> str:
    key = os.environ["GROQ_API_KEY"]
    payload = json.dumps(
        {"model": GROQ_MODEL, "messages": messages, "temperature": temperature}
    ).encode("utf-8")
    request = urllib.request.Request(
        GROQ_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            # Groq's edge rejects the default "Python-urllib/x.y" agent with a
            # 403 that looks like an auth failure. Send an explicit one.
            "User-Agent": "algo-rag/0.1",
        },
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        body = json.loads(response.read().decode("utf-8"))
    message = body["choices"][0]["message"]
    # Reasoning models (gpt-oss) put the chain of thought in `reasoning` and the
    # answer in `content`; fall back to reasoning only if content came back empty.
    return message.get("content") or message.get("reasoning") or ""


def call_ollama(messages: list[dict], temperature: float = 0.2) -> str:
    payload = json.dumps(
        {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=600) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body["message"]["content"]


def pick_backend(requested: str | None) -> str:
    if requested:
        return requested
    return "groq" if os.environ.get("GROQ_API_KEY") else "ollama"


def generate(messages: list[dict], backend: str, temperature: float = 0.2) -> str:
    if backend == "groq":
        return call_groq(messages, temperature)
    if backend == "ollama":
        return call_ollama(messages, temperature)
    raise SystemExit(f"unknown backend: {backend}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the solve path end to end.")
    parser.add_argument("--problems", type=Path, default=Path("sample_problems.json"))
    parser.add_argument("--only", help="comma-separated problem ids")
    parser.add_argument("--backend", choices=["groq", "ollama"], default=None)
    parser.add_argument("-k", type=int, default=5)
    parser.add_argument("--niveau-label", default="2ème")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--tag", default="", help="label for this run in the output")
    parser.add_argument("--out", type=Path, default=None, help="write answers to a file")
    args = parser.parse_args()

    backend = pick_backend(args.backend)
    model = GROQ_MODEL if backend == "groq" else OLLAMA_MODEL
    print(f"backend={backend} model={model}\n")
    if backend == "ollama":
        print(
            "NOTE: local model is small - this verifies the wiring only.\n"
            "      Constraint adherence must be re-tested on the target model.\n"
        )

    problems = json.loads(args.problems.read_text(encoding="utf-8"))
    if args.only:
        wanted = {p.strip() for p in args.only.split(",")}
        problems = [p for p in problems if p.get("id") in wanted]

    transcript = []
    for problem in problems:
        pid = problem.get("id", "?")
        context = build_context(
            problem["question"],
            niveau=str(problem["niveau"]),
            chapitre=str(problem["chapitre"]),
            k=args.k,
        ).render()

        messages = build_messages(
            context=context,
            query=problem["question"],
            niveau=args.niveau_label,
            chapitre=str(problem["chapitre"]),
        )

        print("=" * 78)
        print(f"[{pid}] {problem['question'][:70]}...")
        print(
            f"  context {len(context)} chars | prompt {sum(len(m['content']) for m in messages)} chars"
        )
        try:
            answer = generate(messages, backend, args.temperature)
        except urllib.error.URLError as exc:
            print(f"  BACKEND ERROR: {exc}")
            continue
        except KeyError:
            print("  GROQ_API_KEY not set")
            return

        violations, notes = check_constraints(answer, context)
        print(f"  answer {len(answer)} chars")
        for note in notes:
            print(f"    - {note}")
        if violations:
            print("  CONSTRAINT VIOLATIONS:")
            for violation in violations:
                print(f"    ! {violation}")
        else:
            print("  constraint check: clean")
        print("-" * 78)
        print(answer)
        print()
        transcript.append({"id": pid, "answer": answer, "violations": violations, "notes": notes})

    if args.out:
        args.out.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
