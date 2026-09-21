"""Regression tests for two gatekeeper bugs found in real chat transcripts.

1. The meta-responder showed the model's raw reasoning. _call_groq_cheap fell
   back to the `reasoning` field when `content` came back empty; harmless for
   the classifier, but respond_meta put it in front of a student ("The user
   asks... Let me think... So answer: ...").
2. Identity and own-level questions were declined: "vous ete qui" and
   "je suis au quelle niveua" got the refusal instead of an answer.

Two parts, like the other gatekeeper script:
  offline (always) - Groq's HTTP boundary is mocked and the queue bypassed, so
                     these checks are deterministic and cost nothing;
  --live           - the four real messages from the transcript, in order,
                     through the real classifier and meta-responder (spends
                     Groq quota, same as tests/test_gatekeeper_adversarial.py).

Run inside the backend container:
    docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec -T backend python -m tests.test_gatekeeper_meta [--live]
"""

from __future__ import annotations

import json
import sys
import time
from types import SimpleNamespace

from app.llm import gatekeeper, llm_queue

results: list[bool] = []

# Phrases of a chain of thought that must never reach a student.
REASONING_ARTIFACTS = ("the user asks", "let me think", "so answer", "provide")

# The student's class as api.meta_niveau formats it.
NIVEAU = "2ème année, section Informatique"


def check(name: str, ok: bool, detail: object = "") -> None:
    results.append(bool(ok))
    print(
        ("[PASS] " if ok else "[FAIL] ")
        + name
        + (f"  -> {detail!r}" if not ok and detail != "" else "")
    )


def has_artifact(text: str) -> list[str]:
    lowered = text.lower()
    return [p for p in REASONING_ARTIFACTS if p in lowered]


# --- offline --------------------------------------------------------------------


class FakeGroq:
    """Stands in for Groq's HTTP endpoint, and for the queue in front of it."""

    def __init__(self):
        self.reply = {"content": "", "reasoning": ""}
        self.requests: list[dict] = []

    def urlopen(self, request, timeout=None):
        self.requests.append(json.loads(request.data.decode("utf-8")))
        body = json.dumps({"choices": [{"message": dict(self.reply)}]}).encode("utf-8")

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self):
                return body

        return Response()

    @staticmethod
    def groq_call_steps(model, priority, send, **_options):
        if False:  # a generator, like the real one, that never waits
            yield
        return send()


def offline() -> None:
    fake = FakeGroq()
    saved = (
        gatekeeper.urllib.request.urlopen,
        llm_queue.groq_call_steps,
        gatekeeper.GATEKEEPER_REASONING_EFFORT,
    )
    gatekeeper.urllib.request.urlopen = fake.urlopen
    llm_queue.groq_call_steps = fake.groq_call_steps
    try:
        chain = (
            'The user asks "c\'est quoi fahem". Let me think about whether this is allowed... '
            "So answer: ... That matches greeting? Not"
        )

        # Bug 1: empty content + a reasoning chain.
        fake.reply = {"content": "", "reasoning": chain}
        answer = gatekeeper.respond_meta("c'est quoi fahem", niveau=NIVEAU)
        check(
            "meta: empty content is refused, the reasoning is never shown",
            answer == gatekeeper.DECLINE_MESSAGE and not has_artifact(answer),
            answer,
        )
        fake.reply = {"content": "   \n ", "reasoning": chain}
        answer = gatekeeper.respond_meta("vous ete qui", niveau=NIVEAU)
        check(
            "meta: whitespace-only content is refused too",
            answer == gatekeeper.DECLINE_MESSAGE,
            answer,
        )
        check("safety net: empty text is unsafe", gatekeeper.is_safe_meta_output("") is False)
        check(
            "safety net: whitespace-only text is unsafe",
            gatekeeper.is_safe_meta_output("  \n ") is False,
        )

        # The classifier keeps the fallback: a one-word route may sit in `reasoning`.
        fake.reply = {"content": "", "reasoning": "META"}
        check(
            "classify: still reads a route from `reasoning` when content is empty",
            gatekeeper.classify("hi") == "META",
        )
        fake.reply = {"content": "", "reasoning": chain}
        check(
            "classify: a reasoning chain in the fallback resolves to OFF_TOPIC, never leaks",
            gatekeeper.classify("c'est quoi fahem") == "OFF_TOPIC",
        )

        # A normal answer still comes through.
        fake.reply = {"content": "Je suis Fahem, ton tuteur d'algorithmique.", "reasoning": chain}
        answer = gatekeeper.respond_meta("vous ete qui", niveau=NIVEAU)
        check(
            "meta: a real answer in content is returned", answer.startswith("Je suis Fahem"), answer
        )

        # Bug 2: the niveau reaches the meta prompt; the router knows the phrasings.
        fake.requests.clear()
        gatekeeper.respond_meta("je suis au quelle niveua", niveau=NIVEAU)
        system = fake.requests[-1]["messages"][0]["content"]
        check(
            "meta prompt: carries the student's niveau", f"NIVEAU DE L'ÉLÈVE : {NIVEAU}" in system
        )
        gatekeeper.respond_meta("je suis au quelle niveua")
        system = fake.requests[-1]["messages"][0]["content"]
        check(
            "meta prompt: an unknown niveau says so", "NIVEAU DE L'ÉLÈVE : non renseigné" in system
        )
        router = gatekeeper.ROUTER_SYSTEM_PROMPT
        check(
            "router prompt: META covers formal identity questions and the student's own level",
            all(
                p in router
                for p in (
                    "vous êtes qui",
                    "c'est quoi Fahem",
                    "quel est mon niveau",
                    "je suis en quelle classe",
                )
            ),
        )

        # reasoning_effort is sent exactly when configured.
        gatekeeper.GATEKEEPER_REASONING_EFFORT = "low"
        fake.requests.clear()
        fake.reply = {"content": "META", "reasoning": ""}
        gatekeeper.classify("hi")
        check(
            "request: reasoning_effort sent when configured",
            fake.requests[-1].get("reasoning_effort") == "low",
        )
        gatekeeper.GATEKEEPER_REASONING_EFFORT = ""
        gatekeeper.classify("hi")
        check(
            "request: reasoning_effort omitted when not configured",
            "reasoning_effort" not in fake.requests[-1],
        )
    finally:
        (
            gatekeeper.urllib.request.urlopen,
            llm_queue.groq_call_steps,
            gatekeeper.GATEKEEPER_REASONING_EFFORT,
        ) = saved

    # The niveau app/main.py passes: the student's own class when they have set it.
    from app import main as api

    student = SimpleNamespace(niveau="bac", section="math")
    blank = SimpleNamespace(niveau=None, section=None)
    payload = SimpleNamespace(niveau="2eme")
    check(
        "api.meta_niveau: the student's profile when set",
        api.meta_niveau(student, payload) == "Bac, section Mathématiques",
        api.meta_niveau(student, payload),
    )
    check(
        "api.meta_niveau: the discussion's niveau otherwise",
        api.meta_niveau(blank, payload) == "2ème",
        api.meta_niveau(blank, payload),
    )


# --- live -----------------------------------------------------------------------


def with_busy_retry(call):
    """Groq saturated (gatekeeper.Busy) is not a result: wait for the minute's
    token budget to refill and try once more, then say plainly it was busy."""
    try:
        return call()
    except gatekeeper.Busy:
        print("    (Groq busy - waiting 30s for the per-minute budget, then retrying once)")
        time.sleep(30)
        try:
            return call()
        except gatekeeper.Busy:
            return "<GROQ BUSY>"


def live() -> None:
    """The transcript, in order: each message is classified, and META ones are
    answered, exactly as /solve/stream does."""
    transcript = [
        ("hi", ("fahem", "exercice", "algorithm")),
        ("je suis au quelle niveua", ("2ème",)),
        ("vous ete qui", ("fahem", "tuteur")),
        ("c'est quoi fahem", ("fahem", "tuteur", "algorithm")),
    ]
    for message, expect_any in transcript:
        route = with_busy_retry(lambda: gatekeeper.classify(message))
        print(f"\n>>> {message!r} -> route {route}")
        check(f"live {message!r}: classified META", route == "META", route)
        if route != "META":
            continue
        answer = with_busy_retry(lambda: gatekeeper.respond_meta(message, niveau=NIVEAU))
        print(f"    answer: {answer!r}")
        check(
            f"live {message!r}: a real answer, not the refusal",
            answer != gatekeeper.DECLINE_MESSAGE,
            answer,
        )
        check(
            f"live {message!r}: no reasoning artifacts",
            not has_artifact(answer),
            has_artifact(answer),
        )
        check(
            f"live {message!r}: on topic (mentions one of {expect_any})",
            any(word in answer.lower() for word in (w.lower() for w in expect_any)),
            answer,
        )


if __name__ == "__main__":
    offline()
    if "--live" in sys.argv:
        live()
    print("\nALL PASSED" if all(results) else f"\n{results.count(False)} FAILED")
