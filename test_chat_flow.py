"""End-to-end tests for the chat's backend: history, saves, the stream with
memory, feedback. The real app through TestClient, real Postgres and Redis;
Groq, the classifier and the course retrieval are replaced by fakes, so no
token is spent.

    docker compose exec -T backend python test_chat_flow.py
"""

from __future__ import annotations

import json
import uuid
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

import admin_monitoring
import ai_control
import api
import auth
import chat_history
import gatekeeper
import llm_usage
from db import session_scope
from models import ChatMessage, LlmCall, User

results: list[bool] = []


def check(name: str, ok: bool, detail: object = "") -> None:
    results.append(bool(ok))
    print(
        ("[PASS] " if ok else "[FAIL] ")
        + name
        + (f"  -> {str(detail)[:300]!r}" if not ok and detail != "" else "")
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


ANSWER = (
    "Voici la solution.\n\n| Algorithme | Python |\n|---|---|\n"
    "| reste ← N mod 2 | reste = N % 2 |\n"
)


def main() -> None:
    run = uuid.uuid4().hex[:8]
    with session_scope() as s:
        me = User(email=f"chat-{run}@example.com", display_name="Élève", password_hash="x")
        other = User(email=f"chat-other-{run}@example.com", display_name="Autre", password_hash="x")
        s.add_all([me, other])
        s.flush()
        me_id, other_id = me.id, other.id

    client = TestClient(api.app)
    # The AI's live availability (pause, daily budget guard) is an admin
    # setting, not what these tests are about: a real instance whose budget
    # guard is on would otherwise refuse every solve below.
    api.app.dependency_overrides[ai_control.require_ai_available] = lambda: None

    def as_user(uid):
        client.cookies.clear()
        client.cookies.set(auth.SESSION_COOKIE_NAME, auth.create_session_token(uid))

    # --- fakes: classifier, retrieval, Groq ------------------------------------------
    calls = {"route": "PROBLEM", "stream": []}

    def fake_classify_steps(message, priority=None, budget=None, previous=None):
        calls["previous"] = previous
        if False:
            yield
        return calls["route"]

    def fake_build_context(query, niveau, chapitre, k=5):
        calls["retrieval_query"] = query
        pin = SimpleNamespace(chunk_id="p1", label="Opérateurs", section="II", content="div mod")
        return SimpleNamespace(pinned=[pin], retrieved=[], render=lambda: "CONTEXTE")

    def fake_stream_groq(
        messages, priority=None, budget=None, route=None, memory_chars=0, user_id=None
    ):
        calls["stream"].append({"messages": messages, "route": route, "memory_chars": memory_chars})
        yield from (ANSWER[:20], ANSWER[20:])

    saved = (gatekeeper.classify_steps, api.build_context, api.stream_groq)
    gatekeeper.classify_steps = fake_classify_steps
    api.build_context = fake_build_context
    api.stream_groq = fake_stream_groq
    llm_usage.LLM_USAGE_RECORDING = False

    sid = str(uuid.uuid4())
    try:
        as_user(me_id)

        # --- save, list, read -----------------------------------------------------------
        body = {
            "title": "Parité",
            "niveau": "2eme",
            "chapitre": "1",
            "messages": [
                {"id": "u_1", "role": "user", "content": "Exercice parité"},
                {
                    "id": "a_1",
                    "role": "assistant",
                    "content": ANSWER,
                    "status": "clean",
                    "pinned": [{"id": "p1", "content": "long " * 200}],
                },
            ],
        }
        r = client.put(f"/chat/sessions/{sid}", json=body)
        v1 = r.json().get("version")
        check(
            "save: a new discussion is created at version 1",
            r.status_code == 200 and v1 == 1,
            r.text,
        )

        listed = next(x for x in client.get("/chat/sessions").json() if x["id"] == sid)
        check(
            "list: light - no answer text, no excerpts, but the skeleton",
            listed["loaded"] is False
            and listed["messages"][1]["content"] == ""
            and listed["messages"][1]["status"] == "clean"
            and "pinned" not in listed["messages"][1]
            and listed["messages"][0]["content"] == "Exercice parité",
            listed,
        )
        full = client.get(f"/chat/sessions/{sid}").json()
        check(
            "read: the full discussion when opened",
            full["loaded"]
            and full["messages"][1]["content"] == ANSWER
            and full["messages"][1]["pinned"],
        )

        # --- versions and incremental saves -----------------------------------------------
        r = client.put(f"/chat/sessions/{sid}", json={**body, "baseVersion": v1})
        check("save: nothing changed, the version stays", r.json()["version"] == v1, r.text)
        with session_scope() as s:
            ids_before = dict(
                s.execute(
                    select(ChatMessage.client_id, ChatMessage.id).where(
                        ChatMessage.session_id == uuid.UUID(sid)
                    )
                ).all()
            )
        body2 = {**body, "baseVersion": v1, "title": "Parité (suite)"}
        r = client.put(f"/chat/sessions/{sid}", json=body2)
        v2 = r.json()["version"]
        with session_scope() as s:
            ids_after = dict(
                s.execute(
                    select(ChatMessage.client_id, ChatMessage.id).where(
                        ChatMessage.session_id == uuid.UUID(sid)
                    )
                ).all()
            )
        check(
            "save: a change bumps the version and keeps the message rows (no delete/re-insert)",
            v2 == v1 + 1 and ids_before == ids_after,
            (v2, ids_before, ids_after),
        )
        r = client.put(f"/chat/sessions/{sid}", json={**body, "baseVersion": v1})
        check(
            "save: a stale copy is refused with 409 and the current version",
            r.status_code == 409 and r.json()["detail"] == {"code": "stale", "version": v2},
            r.text,
        )
        skeleton = {
            **body2,
            "baseVersion": v2,
            "messages": [
                {"id": "u_1", "role": "user", "content": "Exercice parité"},
                {"id": "a_1", "role": "assistant", "content": "", "status": "clean"},
            ],
        }
        client.put(f"/chat/sessions/{sid}", json=skeleton)
        full = client.get(f"/chat/sessions/{sid}").json()
        check(
            "save: an empty answer never erases a written one (nor its excerpts)",
            full["messages"][1]["content"] == ANSWER and full["messages"][1]["pinned"],
        )
        version = full["version"]

        # --- the stream: follow-up, memory, server-side save -------------------------------
        history = [m for m in body["messages"]]
        r = client.post(
            "/solve/stream",
            json={
                "problem": "et si N est négatif ?",
                "niveau": "2eme",
                "chapitre": "1",
                "history": [{"role": m["role"], "content": m["content"]} for m in history],
                "session_id": sid,
                "user_message_id": "u_2",
                "assistant_message_id": "a_2",
                "title": "Parité",
            },
        )
        events = frames(r.text)
        done = next(d for e, d in events if e == "done")
        meta = next(d for e, d in events if e == "meta")
        last = calls["stream"][-1]
        check(
            "stream: a short follow-up with memory uses the FOLLOW_UP prompt",
            done["route"] == "FOLLOW_UP"
            and meta["route"] == "FOLLOW_UP"
            and last["route"] == "FOLLOW_UP"
            and "POURSUIT" in last["messages"][0]["content"],
            (done, last["route"]),
        )
        check(
            "stream: the memory went with it (prompt, gatekeeper, retrieval, monitoring)",
            "<memoire>" in last["messages"][1]["content"]
            and last["memory_chars"] > 0
            and calls["previous"]
            and calls["retrieval_query"].startswith("Exercice parité"),
        )
        check(
            "stream: done says how many exchanges were remembered", done["memory_turns"] == 1, done
        )
        full = client.get(f"/chat/sessions/{sid}").json()
        ids = [m["id"] for m in full["messages"]]
        check(
            "stream: the exchange is saved server-side, at the end, with the new version",
            ids == ["u_1", "a_1", "u_2", "a_2"]
            and full["messages"][3]["content"] == ANSWER
            and full["messages"][3]["route"] == "FOLLOW_UP"
            and done["session_version"] == full["version"] == version + 1,
            (ids, done.get("session_version"), full["version"]),
        )

        calls["route"] = "PROBLEM"
        long_problem = "Ecrire un algorithme qui lit trois entiers et affiche le plus grand. " * 5
        r = client.post(
            "/solve/stream",
            json={
                "problem": long_problem,
                "niveau": "2eme",
                "chapitre": "1",
                "history": [
                    {"role": "user", "content": "x"},
                    {"role": "assistant", "content": "y"},
                ],
            },
        )
        done = next(d for e, d in frames(r.text) if e == "done")
        check(
            "stream: a full new statement keeps the classifier's route",
            done["route"] == "PROBLEM" and calls["stream"][-1]["route"] == "PROBLEM",
            done,
        )
        r = client.post(
            "/solve/stream", json={"problem": "a" * 2100, "niveau": "2eme", "chapitre": "1"}
        )
        events = frames(r.text)
        text = "".join(d["t"] for e, d in events if e == "delta")
        check(
            "stream: too long gets a clear message, not the refusal",
            text == gatekeeper.TOO_LONG_MESSAGE and "trop long" in text,
            text,
        )

        # --- server-side save rules ----------------------------------------------------------
        foreign = chat_history.record_exchange(
            other_id,
            uuid.UUID(sid),
            niveau="2eme",
            chapitre="1",
            title=None,
            user_message={"id": "u_x", "role": "user", "content": "intrus"},
            assistant_message={"id": "a_x", "role": "assistant", "content": "intrus"},
        )
        check("record: another account cannot write into this discussion", foreign is None)
        stopped = chat_history.record_exchange(
            me_id,
            uuid.UUID(sid),
            niveau="2eme",
            chapitre="1",
            title=None,
            user_message={"id": "u_3", "role": "user", "content": "et en Python ?"},
            assistant_message={
                "id": "a_3",
                "role": "assistant",
                "content": "Début de répo",
                "status": "streaming",
            },
        )
        full = client.get(f"/chat/sessions/{sid}").json()
        check(
            "record: an answer cut short is kept, as stopped",
            stopped == full["version"] and full["messages"][-1]["status"] == "stopped",
            full["messages"][-1],
        )

        # --- feedback -----------------------------------------------------------------------------
        r = client.post(
            "/chat/feedback",
            json={"session_id": sid, "message_id": "a_2", "rating": -1, "comment": "faux"},
        )
        full = client.get(f"/chat/sessions/{sid}").json()
        check(
            "feedback: a 👎 is stored and comes back with the discussion",
            r.status_code == 204 and full["messages"][3].get("feedback") == -1,
            r.text,
        )
        client.post("/chat/feedback", json={"session_id": sid, "message_id": "a_2", "rating": 1})
        full = client.get(f"/chat/sessions/{sid}").json()
        check("feedback: changing it replaces it", full["messages"][3].get("feedback") == 1)
        client.post("/chat/feedback", json={"session_id": sid, "message_id": "a_2", "rating": 0})
        full = client.get(f"/chat/sessions/{sid}").json()
        check("feedback: 0 takes it back", "feedback" not in full["messages"][3])
        check(
            "feedback: only on an answer that exists",
            client.post(
                "/chat/feedback", json={"session_id": sid, "message_id": "u_1", "rating": 1}
            ).status_code
            == 404,
        )
        # A row written without client_id (older backend): its id lives in extra.
        with session_scope() as s:
            legacy = s.scalar(
                select(ChatMessage).where(
                    ChatMessage.session_id == uuid.UUID(sid), ChatMessage.client_id == "a_1"
                )
            )
            legacy.client_id = None
            legacy.extra = {**(legacy.extra or {}), "id": "a_1"}
        r = client.post(
            "/chat/feedback", json={"session_id": sid, "message_id": "a_1", "rating": 1}
        )
        full = client.get(f"/chat/sessions/{sid}").json()
        with session_scope() as s:
            fixed = s.scalar(
                select(ChatMessage.client_id).where(
                    ChatMessage.session_id == uuid.UUID(sid), ChatMessage.position == 1
                )
            )
        check(
            "feedback: an answer saved without client_id can still be rated (and gets one)",
            r.status_code == 204 and full["messages"][1].get("feedback") == 1 and fixed == "a_1",
            (r.status_code, r.text, fixed),
        )
        as_user(other_id)
        check(
            "ownership: another account cannot read, rate or save this discussion",
            client.get(f"/chat/sessions/{sid}").status_code == 404
            and client.post(
                "/chat/feedback", json={"session_id": sid, "message_id": "a_2", "rating": 1}
            ).status_code
            == 404
            and client.put(f"/chat/sessions/{sid}", json=body).status_code == 404,
        )

        # --- monitoring ---------------------------------------------------------------------------
        data = admin_monitoring.monitoring()
        check(
            "monitoring: answers by prompt and feedback are reported",
            isinstance(data.routes, list) and data.feedback is not None,
        )
    finally:
        gatekeeper.classify_steps, api.build_context, api.stream_groq = saved
        api.app.dependency_overrides.clear()
        with session_scope() as s:
            s.execute(delete(User).where(User.id.in_([me_id, other_id])))
            s.execute(delete(LlmCall).where(LlmCall.route == "__never__"))

    print("\nALL PASSED" if all(results) else f"\n{results.count(False)} FAILED")


if __name__ == "__main__":
    main()
