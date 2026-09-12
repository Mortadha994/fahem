"""Admin-only routes (Phase 7).

This phase ships the gate, not a feature: one route whose only job is to prove
that get_current_admin admits admins and turns everyone else away, end to end
and through the real session cookie. The admin panel's actual features (user
management, content, usage and cost, security) are later phases and will be
added to this router.

Every route on this router MUST depend on auth.get_current_admin. It is set
once, on the router itself, rather than repeated per route: a route added
later cannot forget it, the same structural guarantee App.jsx gives the
frontend by not mounting authenticated routes at all for a signed-out visitor.

There is deliberately no route here - or anywhere - that grants the admin
role. The only way to create an admin is promote_admin.py, run by an operator
with shell access to the backend. See that script's docstring.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

import auth
from models import User

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_current_admin)],
)


class AdminWhoAmI(BaseModel):
    """The smallest honest answer the gate can give: you got in, as this."""

    email: str
    role: str


@router.get("/whoami", response_model=AdminWhoAmI)
def whoami(user: User = Depends(auth.get_current_admin)) -> AdminWhoAmI:
    """Confirm the caller is an admin.

    The dependency is repeated here on top of the router-level one for the
    value, not the check: FastAPI caches a dependency within one request, so
    this does not run the role check (or the user lookup) twice.
    """
    return AdminWhoAmI(email=user.email, role=user.role)
