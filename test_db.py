"""CRUD round-trip against the relational store.

Follows test_retrieval.py / test_gatekeeper_adversarial.py's main() +
__main__ guard shape rather than test_checker.py's run-at-import shape, so
importing this module (for a REPL poke, say) does not hit the database.

Needs a reachable Postgres:
    docker compose up -d postgres
    .venv/Scripts/python.exe test_db.py

It writes and then deletes its own rows, keyed by a per-run UUID in
google_sub, so a leftover row from an interrupted run never collides with
the next one.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from db import session_scope
from models import ChatMessage, ChatSession, User

failures = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global failures
    if not condition:
        failures += 1
    print(f"[{'PASS' if condition else 'FAIL'}] {label}" + (f" {detail}" if detail else ""))


def main() -> None:
    run_id = uuid.uuid4().hex[:12]
    google_sub = f"test-sub-{run_id}"

    warnings = ["rule 1: uses min() which is absent from the context"]
    grounding = {
        "pinned": [{"id": "df41", "label": "Opérateurs arithmétiques et relationnels"}],
        "retrieved": [{"id": "a85c", "section": "V. Les opérations", "score": 0.3157}],
    }

    # --- create -------------------------------------------------------------
    with session_scope() as s:
        user = User(
            google_sub=google_sub,
            email=f"{run_id}@example.test",
            display_name="Test Élève",
            last_login_at=datetime.now(timezone.utc),
        )
        chat = ChatSession(
            user=user, niveau="2eme", chapitre="1", title="Ecrire un programme qui…"
        )
        chat.messages.append(
            ChatMessage(role="user", content="Ecrire un programme qui affiche le carré.")
        )
        chat.messages.append(
            ChatMessage(
                role="assistant",
                content="**1. Résumé du problème**\n…",
                checker_status="warned",
                checker_warnings=warnings,
                grounding_excerpts=grounding,
            )
        )
        s.add(user)
        s.flush()
        user_id, session_id = user.id, chat.id

    check("user/session/messages created", True, f"user={user_id}")
    check("PK is a real UUID, not a serial int", isinstance(user_id, uuid.UUID))

    # --- read back ----------------------------------------------------------
    with session_scope() as s:
        got = s.scalar(select(User).where(User.google_sub == google_sub))
        check("user round-trips by google_sub", got is not None)
        check("email round-trips", got.email == f"{run_id}@example.test")
        check("display_name keeps accents", got.display_name == "Test Élève", repr(got.display_name))
        check("created_at is timezone-aware", got.created_at.tzinfo is not None, str(got.created_at))

        check("exactly one session", len(got.sessions) == 1)
        sess = got.sessions[0]
        check("session scope round-trips", (sess.niveau, sess.chapitre) == ("2eme", "1"))
        check("session title round-trips", sess.title == "Ecrire un programme qui…")

        msgs = sess.messages
        check("two messages, ordered by created_at", len(msgs) == 2, f"got {len(msgs)}")
        check("first is the student's", msgs[0].role == "user")
        check("second is the tutor's", msgs[1].role == "assistant")

        a = msgs[1]
        check("checker_status persisted", a.checker_status == "warned", repr(a.checker_status))
        check("checker_warnings round-trips as a list", a.checker_warnings == warnings, repr(a.checker_warnings))
        check("grounding_excerpts round-trips as nested json", a.grounding_excerpts == grounding)
        check(
            "grounding score survives as a float, not a string",
            isinstance(a.grounding_excerpts["retrieved"][0]["score"], float),
        )
        check("user message has no checker verdict", msgs[0].checker_status is None)

    # --- role CHECK constraint ---------------------------------------------
    from sqlalchemy.exc import IntegrityError

    rejected = False
    try:
        with session_scope() as s:
            s.add(ChatMessage(session_id=session_id, role="system", content="nope"))
    except IntegrityError:
        rejected = True
    check("CHECK constraint rejects an unknown role", rejected)

    # --- cascade delete -----------------------------------------------------
    with session_scope() as s:
        s.delete(s.get(User, user_id))

    with session_scope() as s:
        check("user deleted", s.get(User, user_id) is None)
        check("session cascade-deleted", s.get(ChatSession, session_id) is None)
        remaining = s.scalars(
            select(ChatMessage).where(ChatMessage.session_id == session_id)
        ).all()
        check("messages cascade-deleted", len(remaining) == 0, f"{len(remaining)} left")

    print()
    print("ALL PASSED" if failures == 0 else f"{failures} CHECK(S) FAILED")


if __name__ == "__main__":
    main()
