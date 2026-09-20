"""Seed one demonstration account with twelve weeks of chat activity, so the
console's Activité charts have a shape to show before real students have made
one.

    docker compose exec -T backend python seed_demo_activity.py
    docker compose exec -T backend python seed_demo_activity.py --remove
    docker compose exec -T backend python seed_demo_activity.py --tokens

Everything lands on its own account - demo-activite@fahem.invalid, "Élève de
démonstration (test)" - and never on a real student's history. Re-running
replaces that account's seeded rows rather than adding a second copy, and
--remove deletes the account, which takes its sessions and messages with it
(ON DELETE CASCADE).

The password hash is deliberately not a valid hash, so the account cannot be
signed into. `.invalid` is the reserved TLD (RFC 2606): the address can never
belong to anybody.

--tokens additionally writes llm_calls rows so the "Jetons consommés" line has
something in it. It is off by default on purpose: llm_calls is what the
monitoring pages and the daily budget guard read, and seeded tokens would
show up in those totals as if they had really been spent. Use it only if you
want the token line populated and accept that the console's global usage
numbers will count this fake spend until the rows are removed (--remove takes
them out again).

The shape is written to be worth looking at rather than to be realistic: a
slow start, a gap, a climb, a dip, and a recovery, with the mode mix drifting
from "just give me the solution" towards the guided mode over the term - so
the weekly bars, the sparkline, the delta and every branch of the written
reading all have something to say.
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from db import session_scope
from models import ChatMessage, ChatSession, LlmCall, User

EMAIL = "demo-activite@fahem.invalid"
NAME = "Élève de démonstration (test)"

# [guided, full, check, practice] per week, oldest first (12 weeks).
SHAPE = [
    [0, 3, 0, 0],
    [1, 5, 1, 0],
    [0, 0, 0, 0],  # a quiet week early on
    [2, 6, 1, 0],
    [3, 7, 2, 1],
    [5, 6, 2, 0],
    [8, 5, 3, 1],
    [11, 4, 4, 2],  # the climb
    [4, 2, 1, 0],  # a dip - holidays, say
    [9, 3, 3, 1],
    [13, 3, 5, 2],
    [15, 2, 6, 2],  # ends strong and mostly guided
]

QUESTIONS = [
    "Écrire un algorithme qui lit deux entiers et affiche leur somme.",
    "Comment on écrit une affectation en algorithme ?",
    "Écrire un algorithme qui lit un entier et affiche son carré.",
    "C'est quoi la différence entre div et mod ?",
    "Écrire un algorithme qui lit trois notes et calcule la moyenne.",
    "Pourquoi on écrit ← et pas = ?",
    "Écrire un algorithme qui affiche les chiffres d'un nombre à deux chiffres.",
    "Je ne comprends pas le tableau de déclaration.",
]

ANSWER = (
    "**Ce que demande l'exercice** : lire les valeurs, calculer, afficher.\n\n"
    "### Tableau de déclaration\n\n"
    "| Objet | Nature/type |\n| --- | --- |\n| A | entier |\n| B | entier |\n\n"
    "### Solution\n\n"
    "| Algorithme | Python |\n| --- | --- |\n| Début |  |\n"
    "| Lire (A) | A = int(input()) |\n| Fin |  |\n"
)

MODES = ("guided", "full", "check", "practice")


def monday_of_this_week() -> datetime:
    now = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return now - timedelta(days=now.weekday())


def find(s) -> User | None:
    return s.execute(select(User).where(User.email == EMAIL)).scalar_one_or_none()


def remove() -> None:
    with session_scope() as s:
        user = find(s)
        if user is None:
            print("nothing to remove: the demonstration account does not exist")
            return
        # Any seeded llm_calls first: the FK is ON DELETE SET NULL, so deleting
        # the account would otherwise leave the fake spend behind, counted in
        # the monitoring totals with nobody attached to it.
        calls = s.execute(delete(LlmCall).where(LlmCall.user_id == user.id)).rowcount
        s.delete(user)  # sessions and messages cascade
        print(f"removed the demonstration account and {calls} seeded llm_calls row(s)")


def seed(with_tokens: bool) -> None:
    first_monday = monday_of_this_week() - timedelta(weeks=len(SHAPE) - 1)

    with session_scope() as s:
        user = find(s)
        if user is None:
            user = User(
                email=EMAIL,
                display_name=NAME,
                # Not a valid hash, so the account cannot be signed into.
                password_hash="seeded-not-a-real-hash",
                niveau="2eme",
                section="informatique",
            )
            s.add(user)
            s.flush()
            print(f"created {EMAIL}")
        else:
            # Replace rather than pile a second term on top of the first.
            old = s.execute(
                select(ChatSession.id).where(ChatSession.user_id == user.id)
            ).scalars().all()
            if old:
                s.execute(delete(ChatSession).where(ChatSession.id.in_(old)))
            s.execute(delete(LlmCall).where(LlmCall.user_id == user.id))
            print(f"cleared {len(old)} previous session(s) on {EMAIL}")

        sessions = messages = calls = 0
        for week, counts in enumerate(SHAPE):
            monday = first_monday + timedelta(weeks=week)
            n = 0
            for mode, count in zip(MODES, counts):
                for i in range(count):
                    # Spread across the working week, at plausible hours.
                    when = monday + timedelta(
                        days=(n % 5), hours=17 + (n % 4), minutes=(n * 7) % 60
                    )
                    question = QUESTIONS[(week + n) % len(QUESTIONS)]
                    session = ChatSession(
                        user_id=user.id,
                        niveau="2eme",
                        chapitre="1",
                        title=question[:60],
                        created_at=when,
                        updated_at=when,
                    )
                    s.add(session)
                    s.flush()
                    sessions += 1

                    extra = {"mode": mode} if mode != "full" else None
                    s.add(
                        ChatMessage(
                            session_id=session.id,
                            role="user",
                            content=question,
                            position=0,
                            created_at=when,
                            client_id=f"u_seed_{week}_{n}",
                            extra=extra,
                        )
                    )
                    # One correct check per handful, so "Exercices réussis" is
                    # not stuck at zero.
                    reply_extra = {"check": {"verdict": "correct"}} if (
                        mode == "check" and i % 2 == 0
                    ) else None
                    s.add(
                        ChatMessage(
                            session_id=session.id,
                            role="assistant",
                            content=ANSWER,
                            position=1,
                            created_at=when + timedelta(seconds=20),
                            client_id=f"a_seed_{week}_{n}",
                            checker_status="clean",
                            extra=reply_extra,
                        )
                    )
                    messages += 2

                    if with_tokens:
                        s.add(
                            LlmCall(
                                created_at=when + timedelta(seconds=20),
                                model="openai/gpt-oss-120b",
                                kind="solve",
                                status="ok",
                                prompt_tokens=900 + (n * 13) % 400,
                                completion_tokens=500 + (n * 7) % 300,
                                total_tokens=1400 + (n * 20) % 700,
                                latency_ms=1800,
                                route="PROBLEM",
                                user_id=user.id,
                            )
                        )
                        calls += 1
                    n += 1

        print(
            f"seeded {sessions} discussions, {messages} messages"
            + (f", {calls} llm_calls rows" if with_tokens else "")
            + f"\naccount id: {user.id}"
            + f"\nopen: /admin/utilisateurs/{user.id}?onglet=activite"
        )


if __name__ == "__main__":
    if "--remove" in sys.argv:
        remove()
    else:
        seed("--tokens" in sys.argv)
