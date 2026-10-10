"""Who may open which niveau.

A student works inside the niveau on their profile: 2ème sees the 2ème
chapters, 3ème the 3ème ones, Bac the Bac ones. Two kinds of account are not
limited that way:

- an admin (by role), who has no niveau of their own;
- a test account, marked with users.full_access in the admin console.

A student whose profile is not filled in yet has no niveau and so sees nothing
until it is: the profile screen is how they get their chapters.

The rule lives here and nowhere else, so the chapter list, the course
endpoints and the assistant cannot disagree about it.
"""

from __future__ import annotations

from fastapi import HTTPException, status

from app.core.models import ROLE_ADMIN, User

DENIED = "Ce contenu n'est pas dans ton niveau."


def has_full_access(user: User) -> bool:
    return user.role == ROLE_ADMIN or bool(getattr(user, "full_access", False))


def can_open(user: User, niveau: str | None) -> bool:
    """May this user open content of `niveau`?"""
    if has_full_access(user):
        return True
    return bool(user.niveau) and (niveau or "").strip().lower() == user.niveau


def require_niveau(user: User, niveau: str | None) -> None:
    if not can_open(user, niveau):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=DENIED)


def listing_niveau(user: User) -> str | None:
    """The niveau a chapter list is filtered by, or None for every niveau.

    A student without a profile gets a filter that matches nothing rather than
    None, which would mean everything.
    """
    if has_full_access(user):
        return None
    return user.niveau or "-"
