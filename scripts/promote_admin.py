"""Grant or revoke the admin role. The ONLY way to do either (Phase 7).

    docker compose exec backend python -m scripts.promote_admin student@example.com
    docker compose exec backend python -m scripts.promote_admin student@example.com --demote
    docker compose exec backend python -m scripts.promote_admin --list

Why a script and not an endpoint: the first admin cannot be created through
the app, because no admin exists yet to authorise it - and any HTTP route that
could grant the role would have to be reachable by a non-admin to solve that,
which is a privilege-escalation hole by construction. Requiring shell access to
the backend container means the authority to create an admin is the authority
to run the server, which the operator already has and a student never does.

Two things it is careful about:

1. An email can match more than one account. users.email is unique only among
   password accounts (app/core/models.py): a Google account and a password account are
   separate identities and may share an address. Promoting "the" account for
   an address would then be a guess, and promoting the wrong identity is
   granting admin to whoever controls it. So on more than one match the script
   lists them and changes nothing; pass --id to pick one.

2. It never leaves zero admins. --demote refuses when the target is the last
   admin. The count and the update run in one transaction with the admin rows
   locked (FOR UPDATE), so two operators demoting two admins at once cannot
   each see "one other admin remains" and both succeed. This is the same guard
   a later admin user-management phase must apply - see
   auth.get_current_admin's docstring for where.

Exit codes: 0 changed or already in the requested state, 1 refused or not
found, 2 usage error.
"""

from __future__ import annotations

import argparse
import sys
import uuid

from sqlalchemy import func, select

from app.core.db import session_scope
from app.core.models import ROLE_ADMIN, ROLE_STUDENT, User


def _describe(user: User) -> str:
    method = "password" if user.password_hash else "google"
    return f"{user.id}  {user.email}  ({method}, role={user.role})"


def _find(session, email: str | None, user_id: uuid.UUID | None) -> User | None:
    """The single account to act on, or None after explaining why not."""
    if user_id is not None:
        user = session.get(User, user_id)
        if user is None:
            print(f"No account with id {user_id}.", file=sys.stderr)
        elif email and user.email.lower() != email.lower():
            # --id and an email that disagree is almost certainly a pasted
            # id from the wrong row; refuse rather than pick one of the two.
            print(
                f"Account {user_id} has email {user.email!r}, not {email!r}. Nothing changed.",
                file=sys.stderr,
            )
            return None
        return user

    matches = session.scalars(
        select(User).where(func.lower(User.email) == email.lower()).order_by(User.created_at)
    ).all()
    if not matches:
        print(f"No account with email {email!r}.", file=sys.stderr)
        return None
    if len(matches) > 1:
        print(
            f"{len(matches)} accounts use {email!r} - a Google account and a password "
            "account are separate identities. Nothing changed. Re-run with --id:",
            file=sys.stderr,
        )
        for user in matches:
            print(f"  {_describe(user)}", file=sys.stderr)
        return None
    return matches[0]


def promote(email: str | None, user_id: uuid.UUID | None) -> int:
    with session_scope() as session:
        user = _find(session, email, user_id)
        if user is None:
            return 1
        if user.role == ROLE_ADMIN:
            print(f"Already an admin: {_describe(user)}")
            return 0
        user.role = ROLE_ADMIN
        print(f"Promoted to admin: {_describe(user)}")
    return 0


def demote(email: str | None, user_id: uuid.UUID | None) -> int:
    with session_scope() as session:
        # Lock every admin row before counting. A plain count(*) cannot take
        # FOR UPDATE in Postgres, so the rows are selected and counted here.
        admins = session.scalars(select(User).where(User.role == ROLE_ADMIN).with_for_update()).all()

        user = _find(session, email, user_id)
        if user is None:
            return 1
        if user.role != ROLE_ADMIN:
            print(f"Not an admin, nothing to do: {_describe(user)}")
            return 0
        if len(admins) <= 1:
            print(
                f"Refused: {user.email} is the last admin. Promote another account first, "
                "so the system is never left with no admin.",
                file=sys.stderr,
            )
            return 1
        user.role = ROLE_STUDENT
        print(f"Demoted to student: {_describe(user)}")
    return 0


def list_admins() -> int:
    with session_scope() as session:
        admins = session.scalars(
            select(User).where(User.role == ROLE_ADMIN).order_by(User.created_at)
        ).all()
    if not admins:
        print("No admins.")
    for user in admins:
        print(_describe(user))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Grant or revoke Fahem's admin role. Operator-only; there is no API for this."
    )
    parser.add_argument("email", nargs="?", help="the account's email address")
    parser.add_argument("--id", type=uuid.UUID, help="the account's id, when an email is ambiguous")
    parser.add_argument("--demote", action="store_true", help="revoke admin instead of granting it")
    parser.add_argument("--list", action="store_true", help="list current admins and exit")
    args = parser.parse_args(argv)

    if args.list:
        return list_admins()
    if not args.email and args.id is None:
        parser.print_usage(sys.stderr)
        print("error: give an email, --id, or --list", file=sys.stderr)
        return 2
    return (demote if args.demote else promote)(args.email, args.id)


if __name__ == "__main__":
    sys.exit(main())
