"""Manual-inspection harness for the retrieval step. No LLM involved.

Runs each sample problem through retrieve() and prints the chunks that come
back, with their metadata, so the scoping and the chunk quality can be eyeballed
before we wire up generation.

    python test_retrieval.py
    python test_retrieval.py --problems sample_problems.json -k 5
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from rag_store import DEFAULT_DB_DIR, get_collection
from retrieval import format_hit, retrieve

DEFAULT_PROBLEMS = Path("sample_problems.json")


def load_problems(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"{path} not found - add your problems there (see the file in the repo).")
    problems = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(problems, list) or not problems:
        raise SystemExit(f"{path}: expected a non-empty list of problems.")
    return problems


def known_scopes(db_dir: Path) -> set[tuple[str, str]]:
    """Every (niveau, chapitre) pair actually present in the store."""
    collection = get_collection(db_dir)
    if collection.count() == 0:
        return set()
    metas = collection.get(include=["metadatas"])["metadatas"]
    return {(str(m.get("niveau")), str(m.get("chapitre"))) for m in metas}


def run_problem(problem: dict[str, Any], k: int, db_dir: Path, max_chars: int) -> int:
    """Print retrieval results for one problem. Returns the number of hits."""
    pid = problem.get("id", "?")
    question = problem.get("question") or problem.get("enonce") or ""
    niveau = str(problem.get("niveau", "")).strip().lower()
    chapitre = str(problem.get("chapitre", "")).strip().lower()

    print("=" * 78)
    print(f"[{pid}] niveau={niveau} chapitre={chapitre}")
    print(f"Q: {question}")
    print("-" * 78)

    if not question or not niveau or not chapitre:
        print("  SKIPPED - problem needs question + niveau + chapitre")
        print()
        return 0

    hits = retrieve(question, niveau=niveau, chapitre=chapitre, k=k, db_dir=db_dir)
    if not hits:
        print("  no chunks retrieved in this scope")
    for i, hit in enumerate(hits, 1):
        print(format_hit(hit, i, max_chars=max_chars))
        print()
    if hits:
        types = {}
        for hit in hits:
            types[hit.type] = types.get(hit.type, 0) + 1
        breakdown = ", ".join(f"{t}={n}" for t, n in sorted(types.items()))
        print(f"  {len(hits)} hit(s) | types: {breakdown} | "
              f"score range {hits[-1].score:.3f}-{hits[0].score:.3f}")
    print()
    return len(hits)


def scope_leak_check(problems: list[dict[str, Any]], db_dir: Path, k: int) -> None:
    """Sanity check that the where clause really is a hard filter.

    Re-runs the first problem against every *other* scope in the store: anything
    that comes back must carry that other scope's metadata, never the original's.
    """
    print("=" * 78)
    print("SCOPE FILTER CHECK")
    print("-" * 78)

    scopes = known_scopes(db_dir)
    if len(scopes) < 2:
        print(f"  only {len(scopes)} scope(s) ingested - "
              "ingest a second niveau/chapitre to make this check meaningful")
        print()
        return

    probe = problems[0]
    question = probe.get("question") or probe.get("enonce") or ""
    own = (str(probe.get("niveau", "")).strip().lower(),
           str(probe.get("chapitre", "")).strip().lower())

    leaks = 0
    for niveau, chapitre in sorted(scopes):
        hits = retrieve(question, niveau=niveau, chapitre=chapitre, k=k, db_dir=db_dir)
        bad = [h for h in hits if (h.niveau, h.chapitre) != (niveau, chapitre)]
        leaks += len(bad)
        marker = "OK " if not bad else "LEAK"
        tag = " (problem's own scope)" if (niveau, chapitre) == own else ""
        print(f"  {marker} niveau={niveau} chapitre={chapitre}: {len(hits)} hit(s){tag}")
    print()
    print("  result: " + ("no cross-scope leakage" if leaks == 0
                          else f"{leaks} LEAKED hit(s) - investigate before generation"))
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect retrieval output. No LLM.")
    parser.add_argument("--problems", type=Path, default=DEFAULT_PROBLEMS)
    parser.add_argument("-k", type=int, default=5)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_DIR)
    parser.add_argument("--max-chars", type=int, default=700,
                        help="truncate each printed chunk (use a big number to see tables whole)")
    parser.add_argument("--no-leak-check", action="store_true")
    args = parser.parse_args()

    collection = get_collection(args.db)
    if collection.count() == 0:
        raise SystemExit(
            f"Chroma collection at {args.db}/ is empty. Ingest first:\n"
            "  python rag_store.py --chunks chunks.json"
        )
    print(f"Store: {collection.count()} chunk(s) in {args.db}/")
    scopes = sorted(known_scopes(args.db))
    print("Scopes present: " + ", ".join(f"{n}/ch{c}" for n, c in scopes))
    print()

    problems = load_problems(args.problems)
    total = 0
    for problem in problems:
        total += run_problem(problem, args.k, args.db, args.max_chars)

    if not args.no_leak_check:
        scope_leak_check(problems, args.db, args.k)

    print("=" * 78)
    print(f"{len(problems)} problem(s), {total} chunk(s) retrieved in total.")


if __name__ == "__main__":
    main()
