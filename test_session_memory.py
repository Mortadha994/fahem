"""Tests for session memory (session_memory.py and where it is wired in).

Offline part (always): compaction and its limits, the prompt block, the
router excerpt, the retrieval query, build_messages, the gatekeeper request
(Groq mocked), and the API accepting and capping `history`.
--live: a real two-turn discussion - an exercise, then a follow-up that only
makes sense with the first turn in memory (spends Groq quota).

    docker compose exec -T backend python test_session_memory.py [--live]
"""

from __future__ import annotations

import json
import sys

import gatekeeper
import llm_queue
import session_memory as sm
from prompts import build_messages

results: list[bool] = []


def check(name: str, ok: bool, detail: object = "") -> None:
    results.append(bool(ok))
    print(
        ("[PASS] " if ok else "[FAIL] ")
        + name
        + (f"  -> {str(detail)[:300]!r}" if not ok and detail != "" else "")
    )


ANSWER = "\n".join(
    [
        "Le programme lit un entier N et affiche s'il est pair ou impair.",
        "",
        "| Objet | Nature/type |",
        "|---|---|",
        "| N | entier |",
        "",
        "| Algorithme | Python |",
        "|---|---|",
        "| Début | |",
        '| Ecrire ("Donner N : ") | |',
        '| Lire (N) | N = int(input("Donner N : ")) |',
        "| reste ← N mod 2 | reste = N % 2 |",
        "| Si reste = 0 Alors | if reste == 0 : |",
        '| Ecrire (N, " est pair") | print(N, " est pair") |',
        "| Fin | |",
        "",
        "Trace : " + "N = 14, reste = 0, affichage « 14 est pair ». " * 60,
    ]
)


def offline() -> None:
    # --- compaction ---------------------------------------------------------------
    history = [
        {"role": "user", "content": "Ancien exercice " + "x" * 2000},
        {"role": "assistant", "content": "Ancienne réponse. " + "y" * 3000},
        {"role": "user", "content": "Exercice parité"},
        {"role": "assistant", "content": ANSWER},
        {"role": "user", "content": "   "},
    ]
    memory = sm.compact(history)
    check("compact: blank messages dropped", all(m["content"].strip() for m in memory))
    check(
        "compact: a student message is cut",
        len(memory[0]["content"]) <= sm.USER_CHARS + 2,
        len(memory[0]["content"]),
    )
    check(
        "compact: an older answer keeps only its opening",
        len(memory[1]["content"]) <= sm.OLDER_ANSWER_CHARS + 2,
        len(memory[1]["content"]),
    )
    latest = memory[-1]["content"]
    check(
        "compact: the latest answer keeps its whole Algorithme | Python table",
        "| reste ← N mod 2 | reste = N % 2 |" in latest and "| Fin | |" in latest,
        latest,
    )
    check(
        "compact: the latest answer stays within its cap", len(latest) <= sm.LAST_ANSWER_CHARS + 2
    )
    check(
        "compact: never more than MAX_TURNS exchanges",
        len(sm.compact([{"role": "user", "content": f"m{i}"} for i in range(20)]))
        == sm.MAX_TURNS * 2,
    )
    flood = [{"role": "user", "content": "z" * 60_000} for _ in range(20)]
    check(
        "compact: a flooded history stays within TOTAL_CHARS",
        sum(len(m["content"]) for m in sm.compact(flood)) <= sm.TOTAL_CHARS,
    )
    check("compact: no history, no memory", sm.compact([]) == [] and sm.memory_block([]) is None)

    # --- prompt block ----------------------------------------------------------------
    block = sm.memory_block(memory)
    check(
        "block: quoted between <memoire> tags and declared data, not instructions",
        "<memoire>" in block and "</memoire>" in block and "jamais des instructions" in block,
    )
    check("block: speakers labelled", "Élève :" in block and "Fahem :" in block)
    check(
        "block: follow-ups continue the remembered exercise", "ne\nredemande pas l'énoncé" in block
    )

    messages = build_messages(
        context="CTX", query="et si N est négatif ?", niveau="2ème", chapitre="2", memory=block
    )
    check(
        "build_messages: memory not in the system prompt", "<memoire>" not in messages[0]["content"]
    )
    user = messages[1]["content"]
    check(
        "build_messages: memory comes before the context and the request",
        user.index("<memoire>") < user.index("CTX") < user.index("et si N est négatif ?"),
    )
    plain = build_messages(context="CTX", query="q", niveau="2ème", chapitre="2")
    check("build_messages: without memory, unchanged", "<memoire>" not in plain[1]["content"])
    check(
        "build_messages: braces in the memory are harmless",
        "{x}"
        in build_messages(context="C", query="q", niveau="2", chapitre="1", memory="{x}")[1][
            "content"
        ],
    )

    # --- router excerpt and retrieval ---------------------------------------------------
    excerpt = sm.router_excerpt(memory)
    check(
        "router: last exchange only, short, without the table",
        excerpt.startswith("Élève : Exercice parité")
        and "| reste" not in excerpt
        and len(excerpt) < 2 * sm.ROUTER_CHARS + 40,
        excerpt,
    )
    check(
        "retrieval: a short follow-up is searched with the previous message",
        sm.retrieval_query("et en Python ?", memory) == "Exercice parité\net en Python ?",
    )
    long_problem = "Ecrire un algorithme " * 20
    check(
        "retrieval: a full new statement is searched alone",
        sm.retrieval_query(long_problem, memory) == long_problem,
    )

    # --- the gatekeeper request (Groq mocked) --------------------------------------------
    sent = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return json.dumps({"choices": [{"message": {"content": "QUESTION"}}]}).encode()

    def fake_urlopen(request, timeout=None):
        sent.append(json.loads(request.data.decode()))
        return Response()

    def fake_call_steps(model, priority, send, **_):
        if False:
            yield
        return send()

    saved = (gatekeeper.urllib.request.urlopen, llm_queue.groq_call_steps)
    gatekeeper.urllib.request.urlopen, llm_queue.groq_call_steps = fake_urlopen, fake_call_steps
    try:
        route = gatekeeper.classify("explique la ligne 3", previous=excerpt)
        user_msg = sent[-1]["messages"][1]["content"]
        check(
            "gatekeeper: the previous exchange is sent before the message",
            route == "QUESTION"
            and user_msg.index("<echange_precedent>") < user_msg.index("<user_message>"),
            user_msg,
        )
        gatekeeper.classify("bonjour")
        check(
            "gatekeeper: no previous exchange, no block",
            "<echange_precedent>" not in sent[-1]["messages"][1]["content"],
        )
        check(
            "gatekeeper: the router prompt explains follow-ups",
            "ÉCHANGE PRÉCÉDENT" in gatekeeper.ROUTER_SYSTEM_PROMPT,
        )
    finally:
        gatekeeper.urllib.request.urlopen, llm_queue.groq_call_steps = saved

    # --- the API contract ------------------------------------------------------------------
    from api import SolveRequest

    req = SolveRequest(problem="et en Python ?", niveau="2eme", chapitre="2", history=history[:4])
    check("api: history is accepted", len(req.history) == 4 and req.history[0].role == "user")
    try:
        SolveRequest(
            problem="x", niveau="2eme", chapitre="2", history=[{"role": "system", "content": "x"}]
        )
        check("api: a 'system' turn is refused", False)
    except Exception:
        check("api: a 'system' turn is refused", True)
    check(
        "api: history is optional",
        SolveRequest(problem="x", niveau="2eme", chapitre="2").history == [],
    )


def live() -> None:
    """Two turns, like the chat: the follow-up only makes sense with memory."""
    from context import build_context
    from generate import call_groq

    first = (
        "Ecrire un algorithme et sa traduction en Python intitulé PARITE qui lit un "
        "entier N puis affiche s'il est pair ou impair."
    )
    context = build_context(first, niveau="2eme", chapitre="2", k=5)
    answer1 = call_groq(
        build_messages(context=context.render(), query=first, niveau="2ème", chapitre="2")
    )
    print("\n--- turn 1 answer (start) ---\n" + answer1[:400])

    follow_up = "explique-moi la ligne avec mod"
    memory = sm.compact(
        [{"role": "user", "content": first}, {"role": "assistant", "content": answer1}]
    )
    route = gatekeeper.classify(follow_up, previous=sm.router_excerpt(memory))
    without = gatekeeper.classify(follow_up)
    print(f"\nroute with memory: {route}   without memory: {without}")
    check(
        "live: the follow-up is routed to a grounded answer",
        route in ("QUESTION", "PROBLEM", "CODE"),
        route,
    )

    context2 = build_context(
        sm.retrieval_query(follow_up, memory), niveau="2eme", chapitre="2", k=5
    )
    answer2 = call_groq(
        build_messages(
            context=context2.render(),
            query=follow_up,
            niveau="2ème",
            chapitre="2",
            kind=route if route in ("QUESTION", "PROBLEM", "CODE") else "QUESTION",
            memory=sm.memory_block(memory),
        )
    )
    print("\n--- turn 2 answer ---\n" + answer2[:900])
    lowered = answer2.lower()
    check(
        "live: turn 2 explains the remembered line (mod 2, the remainder)",
        "mod" in lowered and ("reste" in lowered or "2" in lowered),
        answer2[:300],
    )
    check(
        "live: turn 2 does not ask for the statement again",
        "colle" not in lowered and "énoncé de ton exercice" not in lowered,
        answer2[:300],
    )


if __name__ == "__main__":
    offline()
    if "--live" in sys.argv:
        live()
    print("\nALL PASSED" if all(results) else f"\n{results.count(False)} FAILED")
