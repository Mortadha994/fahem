"""Tests for Mode guidé and Vérifier ma réponse: routing, prompts, the
notation pre-check, what is saved and what the console counts. The real app
through TestClient, real Postgres and Redis; Groq, the classifier and the
course retrieval are fakes, so no token is spent.

    docker compose exec -T backend python test_guided_check.py
"""

from __future__ import annotations

import json
import sys
import uuid
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import delete

import admin_monitoring
import ai_control
import answer_check
import api
import auth
import gatekeeper
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


TABLE = (
    "| Objet | Nature/type |\n|---|---|\n| N | entier |\n| c | entier |\n\n"
    "| Algorithme | Python |\n|---|---|\n| c ← N div 100 | c = N // 100 |\n"
)
HINT = "Pense à `div` pour la centaine. Quelle variable te faut-il ?"
CHECK_ANSWER = (
    "**Verdict : Presque**\n\nCe qui est juste : la lecture.\n\n"
    "| Ligne | Ce que tu as écrit | Problème | Correction |\n|---|---|---|---|\n"
    "| 3 | c ← N // 100 | `//` n'existe pas en algorithme | c ← N div 100 |\n\n"
    "### Correction complète\n\n" + TABLE
)
STATEMENT = "Ecrire un algorithme qui lit un entier N de trois chiffres et affiche sa centaine."
STUDENT = "Début\nLire (N)\nc ← N // 100\nEcrire (c)\nFin"


def main() -> None:
    run = uuid.uuid4().hex[:8]
    with session_scope() as s:
        me = User(email=f"guided-{run}@example.com", display_name="Élève", password_hash="x")
        s.add(me)
        s.flush()
        me_id = me.id

    client = TestClient(api.app)
    # The AI's live availability (pause, daily budget guard) is an admin
    # setting, not what these tests are about: a real instance whose budget
    # guard is on would otherwise refuse every solve below.
    api.app.dependency_overrides[ai_control.require_ai_available] = lambda: None
    client.cookies.set(auth.SESSION_COOKIE_NAME, auth.create_session_token(me_id))

    state = {"route": "PROBLEM", "classified": 0, "answer": HINT, "stream": []}

    def fake_classify_steps(message, priority=None, budget=None, previous=None):
        state["classified"] += 1
        if False:
            yield
        return state["route"]

    def fake_build_context(query, niveau, chapitre, k=5):
        state["retrieval_query"] = query
        pin = SimpleNamespace(chunk_id="p1", label="Opérateurs", section="II", content="div mod")
        return SimpleNamespace(pinned=[pin], retrieved=[], render=lambda: "CONTEXTE div mod ←")

    def fake_stream_groq(
        messages, priority=None, budget=None, route=None, memory_chars=0, user_id=None
    ):
        state["stream"].append({"messages": messages, "route": route})
        yield state["answer"]

    # This file sends more solves than a student may in a minute.
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

    sid = str(uuid.uuid4())
    counter = {"n": 0}

    def solve(problem, answer=HINT, route="PROBLEM", history=None, **extra):
        counter["n"] += 1
        n = counter["n"]
        state.update(route=route, answer=answer, classified=0)
        body = {
            "problem": problem,
            "niveau": "2eme",
            "chapitre": "1",
            "session_id": sid,
            "user_message_id": f"u_{n}",
            "assistant_message_id": f"a_{n}",
            "history": history or [],
            **extra,
        }
        r = client.post("/solve/stream", json=body)
        events = frames(r.text)
        done = next((d for e, d in events if e == "done"), None)
        if done is None:
            print("   (no done frame:", r.status_code, r.text[:300], ")")
            done = {}
        last = state["stream"][-1] if state["stream"] else {}
        return done, last, f"a_{n}"

    try:
        # --- features ---------------------------------------------------------------------
        f = client.get("/chat/features").json()
        check(
            "features: guided and check are on, new discussions start guided",
            f["guided"] is True and f["check"] is True and f["defaultMode"] == "guided",
            f,
        )

        # --- guided: a new exercise starts at step 1 ------------------------------------------
        done, last, a1 = solve(STATEMENT, mode="guided")
        prompt = last["messages"][1]["content"]
        check(
            "guided: a new statement starts the exercise at step 1",
            done["route"] == "GUIDED"
            and done["guided"] == {"step": 1, "exerciseId": "u_1"}
            and last["route"] == "GUIDED"
            and "ÉTAPE 1 / 4" in prompt
            and STATEMENT in prompt
            and "MODE GUIDÉ" in last["messages"][0]["content"],
            (done, prompt[-300:]),
        )
        history = [
            {"role": "user", "content": STATEMENT},
            {"role": "assistant", "content": HINT},
        ]

        # --- the buttons: no classifier, the step moves on ------------------------------------
        done, last, _ = solve(
            "Indice suivant",
            mode="guided",
            step=1,
            action="next_step",
            exercise=STATEMENT,
            exercise_id="u_1",
            history=history,
        )
        check(
            "guided: « Indice suivant » goes to step 2 without asking the classifier",
            done["guided"] == {"step": 2, "exerciseId": "u_1"}
            and state["classified"] == 0
            and "ÉTAPE 2 / 4" in last["messages"][1]["content"]
            and state["retrieval_query"].startswith(STATEMENT),
            (done, state["classified"], state["retrieval_query"][:80]),
        )
        check(
            "guided: a hint is not vouched for as a verified solution",
            done["warnings"] == [] and "leak" not in done["guided"],
            done,
        )

        done, last, _ = solve(
            "deux variables entières ?",
            mode="guided",
            step=2,
            exercise=STATEMENT,
            exercise_id="u_1",
            history=history,
        )
        check(
            "guided: a short reply mid-exercise stays at its step, no classifier",
            done["guided"]["step"] == 2 and state["classified"] == 0,
            (done, state["classified"]),
        )
        check(
            "guided: the reply is answered as a reply (checked, not the step repeated)",
            "RÉPONSE de l'élève" in last["messages"][1]["content"],
        )

        done, last, leaked = solve(
            "Indice suivant",
            answer="Voici tout :\n\n" + TABLE,
            mode="guided",
            step=2,
            action="next_step",
            exercise=STATEMENT,
            exercise_id="u_1",
            history=history,
        )
        full = client.get(f"/chat/sessions/{sid}").json()
        saved_msg = next(m for m in full["messages"] if m["id"] == leaked)
        check(
            "guided: a step 1-3 answer that gives the whole solution is flagged as a leak",
            done["guided"].get("leak") is True
            and saved_msg.get("guided", {}).get("leak") is True
            and saved_msg["status"] == "none",
            (done, saved_msg.get("guided"), saved_msg.get("status")),
        )

        done, last, sol = solve(
            "Voir la solution",
            answer="Résumé.\n\n" + TABLE,
            mode="guided",
            step=3,
            action="show_solution",
            exercise=STATEMENT,
            exercise_id="u_1",
            history=history,
        )
        full = client.get(f"/chat/sessions/{sid}").json()
        saved_msg = next(m for m in full["messages"] if m["id"] == sol)
        user_msg = full["messages"][full["messages"].index(saved_msg) - 1]
        check(
            "guided: « Voir la solution » gives step 4, saved with its step and a verified status",
            done["guided"]["step"] == 4
            and "ÉTAPE 4 / 4" in last["messages"][1]["content"]
            and saved_msg.get("guided") == {"step": 4, "exerciseId": "u_1"}
            and saved_msg["status"] == "clean"
            and user_msg.get("mode") == "guided",
            (done, saved_msg.get("guided"), saved_msg.get("status"), user_msg),
        )

        done, _, _ = solve(
            STATEMENT + " Et la dizaine aussi.",
            mode="guided",
            step=4,
            exercise=STATEMENT,
            exercise_id="u_1",
            history=history,
        )
        check(
            "guided: a new statement mid-exercise starts a new one at step 1",
            done["guided"]["step"] == 1 and done["guided"]["exerciseId"] == f"u_{counter['n']}",
            done,
        )

        state["route"] = "QUESTION"
        done, _, _ = solve("c'est quoi div ?", route="QUESTION", mode="guided")
        check(
            "guided: a course question outside an exercise keeps its own prompt",
            done["route"] == "QUESTION" and "guided" not in done,
            done,
        )

        # --- check -------------------------------------------------------------------------------
        done, last, checked_id = solve(STUDENT, answer=CHECK_ANSWER, route="PROBLEM", mode="check")
        prompt = last["messages"][1]["content"]
        full = client.get(f"/chat/sessions/{sid}").json()
        saved_msg = next(m for m in full["messages"] if m["id"] == checked_id)
        check(
            "check: the button uses the CHECK prompt without the classifier",
            done["route"] == "CHECK" and last["route"] == "CHECK" and state["classified"] == 0,
            (done, state["classified"]),
        )
        check(
            "check: the notation pre-check reaches the prompt as facts",
            "`//` doit s'écrire `div`" in prompt
            and "tableau de déclaration" in prompt
            and "### Correction complète" in prompt,
            prompt[-600:],
        )
        check(
            "check: verdict and mistake kinds are read and saved",
            done.get("check") == {"verdict": "presque", "findings": ["declaration", "operator"]}
            and saved_msg.get("check") == done.get("check"),
            (done.get("check"), saved_msg.get("check")),
        )
        check(
            "check: the student's quoted `//` is not reported, the correction is checked",
            done["warnings"] == [] and saved_msg["status"] == "clean",
            (done.get("warnings"), saved_msg.get("status")),
        )

        done, _, _ = solve(
            "voici ma solution, est-ce que c'est juste ?\n" + STUDENT,
            answer=CHECK_ANSWER,
            route="CODE",
        )
        check(
            "check: asking in words, without the button, is checked too",
            done["route"] == "CHECK" and state["classified"] == 1,
            done,
        )

        # --- admin switches ---------------------------------------------------------------------
        overrides.update(guided_mode_enabled=False, check_answer_enabled=False)
        f = client.get("/chat/features").json()
        done_g, _, _ = solve(STATEMENT, answer="Résumé.\n\n" + TABLE, mode="guided")
        done_c, _, _ = solve(STUDENT, answer="ok", route="CODE", mode="check")
        check(
            "admin: with both modes off, requests are answered the normal way",
            f["guided"] is False
            and f["check"] is False
            and f["defaultMode"] == "full"
            and done_g.get("route") == "PROBLEM"
            and "guided" not in done_g
            and done_c.get("route") == "CODE"
            and state["classified"] == 1,
            (f, done_g.get("route"), done_c.get("route")),
        )
        overrides.pop("guided_mode_enabled")
        overrides.pop("check_answer_enabled")
        overrides["default_chat_mode"] = "guided"
        check(
            "admin: the default mode reaches the chat",
            client.get("/chat/features").json()["defaultMode"] == "guided",
        )
        overrides.pop("default_chat_mode")
        try:
            runtime_settings.SPECS["default_chat_mode"].validate("bientôt")
            check("admin: an unknown default mode is refused", False)
        except runtime_settings.InvalidSetting:
            check("admin: an unknown default mode is refused", True)

        # --- the pre-check itself -----------------------------------------------------------------
        found = {
            (f.kind, f.found)
            for f in answer_check.precheck('Début\nLire (N)\nc = N // 100\nEcrire ("5 %", c)\nFin')
        }
        check(
            "precheck: `=` and `//` in an algorithm are found, a % inside a message is not",
            ("assignment", "=") in found
            and ("operator", "//") in found
            and ("operator", "%") not in found,
            found,
        )
        check(
            "precheck: plain Python is not judged as algorithm",
            answer_check.precheck("n = int(input())\nprint(n % 2)") == [],
        )

        # --- console -------------------------------------------------------------------------------
        data = admin_monitoring.monitoring()
        learning = data.learning
        check(
            "monitoring: guided steps, leaks, verdicts and mistakes are counted",
            learning is not None
            and learning.guided_answers >= 5
            and learning.guided_leaks >= 1
            and learning.checks >= 2
            and learning.verdicts["presque"] >= 2
            and any(x["kind"] == "operator" for x in learning.top_findings),
            learning,
        )
    finally:
        gatekeeper.classify_steps, api.build_context, api.stream_groq, runtime_settings.get = saved
        api.app.dependency_overrides.clear()
        with session_scope() as s:
            s.execute(delete(User).where(User.id == me_id))

    print("\nALL PASSED" if all(results) else f"\n{results.count(False)} FAILED")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
