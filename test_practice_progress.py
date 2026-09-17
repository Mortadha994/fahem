"""Tests for Exercice similaire and the progress page: routing, prompt, the
daily limit, the admin switch, and progress derived from discussions. Real app
through TestClient, real Postgres and Redis; Groq, the classifier and retrieval
are fakes, so no token is spent.

    docker compose exec -T backend python test_practice_progress.py
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import delete

import api
import auth
import chapters
import gatekeeper
import llm_queue
import llm_usage
import runtime_settings
from db import session_scope
from models import User

results: list[bool] = []


def check(name: str, ok: bool, detail: object = "") -> None:
    results.append(bool(ok))
    print(
        ("[PASS] " if ok else "[FAIL] ")
        + name
        + (f"  -> {str(detail)[:400]!r}" if not ok and detail != "" else "")
    )


def frames(text: str) -> list[tuple[str, dict]]:
    out = []
    for block in text.strip().split("\n\n"):
        event = data = None
        for line in block.split("\n"):
            if line.startswith("event: "):
                event = line[7:]
            elif line.startswith("data: "):
                data = json.loads(line[6:])
        if event:
            out.append((event, data))
    return out


PRACTICE_ANSWER = (
    "### Exercice similaire (plus difficile)\n\nÉcrire un algorithme qui lit le prix "
    "d'un livre et le nombre de livres, puis affiche le total.\n\n**Exemple :** pour 12.5 "
    "et 4 le programme affiche 50."
)
TABLE = (
    "| Objet | Nature/type |\n|---|---|\n| a | entier |\n\n"
    "| Algorithme | Python |\n|---|---|\n| Lire (a) | a = int(input()) |\n"
)


def main() -> None:
    run = uuid.uuid4().hex[:8]
    with session_scope() as s:
        me = User(email=f"practice-{run}@example.com", display_name="Élève", password_hash="x")
        other = User(email=f"practice-o-{run}@example.com", display_name="Autre", password_hash="x")
        s.add_all([me, other])
        s.flush()
        me_id, other_id = me.id, other.id

    client = TestClient(api.app)

    def as_user(uid):
        client.cookies.clear()
        client.cookies.set(auth.SESSION_COOKIE_NAME, auth.create_session_token(uid))

    state = {"classified": 0, "stream": [], "answer": PRACTICE_ANSWER}

    def fake_classify_steps(message, priority=None, budget=None, previous=None):
        state["classified"] += 1
        if False:
            yield
        return "PROBLEM"

    def fake_build_context(query, niveau, chapitre, k=5):
        pin = SimpleNamespace(chunk_id="p1", label="Opérateurs", section="II", content="div mod")
        return SimpleNamespace(pinned=[pin], retrieved=[], render=lambda: "CONTEXTE")

    def fake_stream_groq(messages, priority=None, budget=None, route=None, memory_chars=0):
        state["stream"].append({"messages": messages, "route": route})
        yield state["answer"]

    overrides: dict[str, object] = {"solve_rate_limit": "1000/minute"}
    real_get = runtime_settings.get

    def fake_get(key):
        return overrides[key] if key in overrides else real_get(key)

    saved = (gatekeeper.classify_steps, api.build_context, api.stream_groq, runtime_settings.get)
    gatekeeper.classify_steps = fake_classify_steps
    api.build_context = fake_build_context
    api.stream_groq = fake_stream_groq
    runtime_settings.get = fake_get
    llm_usage.LLM_USAGE_RECORDING = False
    limit_key = f"fahem:practice:{me_id}:{time.strftime('%Y-%m-%d', time.gmtime())}"

    exercises = chapters.load_exercises("1")
    first, second = exercises[0], exercises[1]
    sid = str(uuid.uuid4())
    n = {"i": 0}

    def solve(problem, **extra):
        n["i"] += 1
        state["classified"] = 0
        before = len(state["stream"])
        r = client.post(
            "/solve/stream",
            json={
                "problem": problem,
                "niveau": "2eme",
                "chapitre": "1",
                "session_id": sid,
                "user_message_id": f"u_{n['i']}",
                "assistant_message_id": f"a_{n['i']}",
                **extra,
            },
        )
        done = next((d for e, d in frames(r.text) if e == "done"), {})
        text = "".join(d["t"] for e, d in frames(r.text) if e == "delta")
        called = len(state["stream"]) > before
        return done, text, (state["stream"][-1] if called else None)

    try:
        as_user(me_id)
        f = client.get("/chat/features").json()
        check("features: Exercice similaire is offered", f.get("practice") is True, f)

        # --- practice ---------------------------------------------------------------------------
        done, _, call = solve(
            "Exercice similaire (plus difficile)",
            mode="practice",
            difficulty="harder",
            exercise=first.question,
        )
        prompt = call["messages"][1]["content"] if call else ""
        check(
            "practice: a new statement from the exercise, harder, without the classifier",
            done.get("route") == "PRACTICE"
            and done.get("practice") == {"difficulty": "harder"}
            and state["classified"] == 0
            and call["route"] == "PRACTICE"
            and first.question in prompt
            and "PLUS DIFFICILE" in prompt
            and "### Exercice similaire (plus difficile)" in prompt,
            (done, prompt[-400:]),
        )
        full = client.get(f"/chat/sessions/{sid}").json()
        check(
            "practice: saved with its difficulty, not vouched for as a solution",
            full["messages"][-1].get("practice") == {"difficulty": "harder"}
            and full["messages"][-1]["status"] == "none"
            and full["messages"][-2].get("mode") == "practice",
            full["messages"][-2:],
        )

        llm_queue._sync_client().delete(limit_key)
        overrides["practice_daily_limit"] = 2
        solve("Exercice similaire", mode="practice", exercise=first.question)
        solve("Exercice similaire", mode="practice", exercise=first.question)
        done, text, call = solve("Exercice similaire", mode="practice", exercise=first.question)
        check(
            "practice: past the daily limit, a clear message and no model call",
            done.get("route") == "PRACTICE_LIMIT" and call is None and "2 exercices" in text,
            (done, text),
        )
        overrides.pop("practice_daily_limit")
        llm_queue._sync_client().delete(limit_key)

        overrides["practice_enabled"] = False
        state["answer"] = "Résumé.\n\n" + TABLE
        done, _, call = solve("Exercice similaire", mode="practice", exercise=first.question)
        check(
            "practice: switched off by the admin, the request is answered the normal way",
            done.get("route") != "PRACTICE"
            and client.get("/chat/features").json()["practice"] is False,
            done,
        )
        overrides.pop("practice_enabled")

        # --- progress ---------------------------------------------------------------------------
        as_user(other_id)
        p = client.get("/progress").json()
        ch1 = next(c for c in p["chapters"] if c["id"] == "1")
        check(
            "progress: a new student has nothing started, the next exercise is the first",
            ch1["started"] == 0
            and ch1["done"] == 0
            and ch1["total"] == len(exercises)
            and ch1["next_exercise"]["id"] == first.id
            and p["recent_checks"] == []
            and p["mistakes"] == [],
            ch1 | {"exercises": len(ch1["exercises"])},
        )

        def save(user_msgs_and_answers, title="t"):
            session_id = str(uuid.uuid4())
            messages = []
            for i, (u, a) in enumerate(user_msgs_and_answers):
                messages.append({"id": f"u{i}", "role": "user", "content": u})
                messages.append({"id": f"a{i}", "role": "assistant", "content": "x", **a})
            r = client.put(
                f"/chat/sessions/{session_id}",
                json={"title": title, "niveau": "2eme", "chapitre": "1", "messages": messages},
            )
            assert r.status_code == 200, r.text
            return session_id

        # first exercise: guided hint only -> started; second: full solution then a correct check
        save([(first.question, {"status": "none", "guided": {"step": 2, "exerciseId": "u0"}})])
        p = client.get("/progress").json()
        ch1 = next(c for c in p["chapters"] if c["id"] == "1")
        st = {e["id"]: e["status"] for e in ch1["exercises"]}
        check(
            "progress: a guided hint counts as started, and the next exercise moves on",
            st[first.id] == "started" and ch1["next_exercise"]["id"] == second.id,
            (st.get(first.id), ch1["next_exercise"]),
        )

        s2 = save(
            [
                (second.question, {"status": "clean"}),
                (
                    "Voici ma solution : Lire (a)",
                    {
                        "status": "clean",
                        "route": "CHECK",
                        "check": {"verdict": "presque", "findings": ["operator", "declaration"]},
                    },
                ),
                (
                    "Voici ma solution corrigée",
                    {
                        "status": "clean",
                        "route": "CHECK",
                        "check": {"verdict": "correct", "findings": ["operator"]},
                    },
                ),
            ],
            title="Deuxième",
        )
        p = client.get("/progress").json()
        ch1 = next(c for c in p["chapters"] if c["id"] == "1")
        st = {e["id"]: e for e in ch1["exercises"]}
        check(
            "progress: a correct check makes the exercise done, linked to its discussion",
            st[second.id]["status"] == "done"
            and st[second.id]["session_id"] == s2
            and ch1["done"] == 1
            and ch1["started"] == 2,
            (st[second.id], ch1["done"], ch1["started"]),
        )
        check(
            "progress: the latest checks and the recurring mistakes are listed",
            p["recent_checks"][0]["session_id"] == s2
            and p["recent_checks"][0]["verdict"] == "correct"
            and p["recent_checks"][0]["checks"] == 2
            and p["mistakes"][0] == {"kind": "operator", "count": 2},
            (p["recent_checks"][:1], p["mistakes"]),
        )

        save([(first.question, {"status": "clean"})])
        p = client.get("/progress").json()
        ch1 = next(c for c in p["chapters"] if c["id"] == "1")
        st = {e["id"]: e["status"] for e in ch1["exercises"]}
        check(
            "progress: a full solution shown makes it « solution vue », never above done",
            st[first.id] == "solution_seen" and st[second.id] == "done",
            st,
        )

        as_user(me_id)
        mine = client.get("/progress").json()
        ch1 = next(c for c in mine["chapters"] if c["id"] == "1")
        check(
            "progress: one student's work never shows in another's",
            ch1["done"] == 0 and mine["recent_checks"] == [],
            (ch1["done"], mine["recent_checks"][:1]),
        )
        client.cookies.clear()
        check("progress: signed in only", client.get("/progress").status_code == 401)
    finally:
        gatekeeper.classify_steps, api.build_context, api.stream_groq, runtime_settings.get = saved
        llm_queue._sync_client().delete(limit_key)
        with session_scope() as s:
            s.execute(delete(User).where(User.id.in_([me_id, other_id])))

    print("\nALL PASSED" if all(results) else f"\n{results.count(False)} FAILED")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
