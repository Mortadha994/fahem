"""Admin-only routes: the gate (Phase 7) and user management (Phase 8).

Every route on this router depends on auth.get_current_admin, declared once on
the router itself rather than per route: a route added later cannot forget it.
test_admin.py asserts that every route here inherits it.

What an admin can do to an account, and - as deliberately - what they cannot:

  can     list and search accounts, read one, create a password account,
          edit the display name and the verified flag, end every session
          (force sign-out), delete a student account.
  cannot  change anyone's role. promote_admin.py stays the only way in or out
          of the admin role (Phase 7's rule), so a stolen admin session cannot
          mint more admins.
  cannot  delete an admin account, including their own. Demote it with the
          script first. This is what makes "never zero admins" hold for the
          API: the only paths that reduce the admin count are the script's
          --demote (which refuses the last admin under a row lock) and nothing
          else. If a later phase adds role changes here, the lockout guard
          described in auth.get_current_admin has to come with it.
  cannot  change an email address. For a password account the email is the
          login identity, and silently re-pointing it is an account takeover
          tool; that needs its own design (confirmation to both addresses).

Chat sessions and exercise content are not here: chat history still lives in
the browser (models.ChatSession is unused), and chapters/exercises are code
and a JSON file, not rows. Admin CRUD for them needs those moved into the
database first.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError

import auth
import password_auth
from db import session_scope
from models import ROLE_ADMIN, ROLES, User

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_current_admin)],
)


# --- schemas -------------------------------------------------------------------


class AdminWhoAmI(BaseModel):
    """The smallest honest answer the gate can give: you got in, as this."""

    email: str
    role: str


class AdminUser(BaseModel):
    """What the console shows about an account. Still not the ORM object:
    password_hash and google_sub never leave the backend, even for admins."""

    id: uuid.UUID
    email: str
    display_name: str | None
    role: str
    auth_method: Literal["google", "password"]
    email_verified: bool
    created_at: datetime
    last_login_at: datetime | None
    sessions_valid_after: datetime | None
    niveau: str | None = None
    section: str | None = None

    @classmethod
    def of(cls, user: User) -> "AdminUser":
        return cls(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            role=user.role,
            auth_method="password" if user.password_hash else "google",
            email_verified=user.email_verified,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
            sessions_valid_after=user.sessions_valid_after,
            niveau=user.niveau,
            section=user.section,
        )


class UserPage(BaseModel):
    items: list[AdminUser]
    total: int
    limit: int
    offset: int


class AdminStats(BaseModel):
    users: int
    admins: int
    students: int
    password_accounts: int
    google_accounts: int
    verified: int
    new_last_7_days: int
    active_last_7_days: int


class CreateUser(BaseModel):
    """A password account created by an admin. Always a student (see module
    docstring); the same password and name rules as self-service signup."""

    email: EmailStr
    display_name: str = Field(min_length=1, max_length=80)
    password: str
    email_verified: bool = False

    @field_validator("password")
    @classmethod
    def _password_rules(cls, v: str) -> str:
        return password_auth._check_password_rules(v)

    @field_validator("display_name")
    @classmethod
    def _name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Le nom ne peut pas être vide.")
        return v


class UpdateUser(BaseModel):
    """Only the fields an admin may change. Anything else in the body - role,
    email - is ignored by pydantic, not applied."""

    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    email_verified: bool | None = None

    @field_validator("display_name")
    @classmethod
    def _name_not_blank(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Le nom ne peut pas être vide.")
        return v


# --- helpers -------------------------------------------------------------------


def _get_or_404(session, user_id: uuid.UUID) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return user


# --- routes --------------------------------------------------------------------


@router.get("/whoami", response_model=AdminWhoAmI)
def whoami(user: User = Depends(auth.get_current_admin)) -> AdminWhoAmI:
    """Confirm the caller is an admin. The console calls this before drawing
    anything. The dependency is cached per request, so repeating it here for
    the value does not run the check twice."""
    return AdminWhoAmI(email=user.email, role=user.role)


@router.get("/stats", response_model=AdminStats)
def stats() -> AdminStats:
    """Counts for the dashboard, in one round trip."""
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    with session_scope() as s:
        row = s.execute(
            select(
                func.count(),
                func.count().filter(User.role == ROLE_ADMIN),
                func.count().filter(User.password_hash.is_not(None)),
                func.count().filter(User.email_verified.is_(True)),
                func.count().filter(User.created_at >= week_ago),
                func.count().filter(User.last_login_at >= week_ago),
            ).select_from(User)
        ).one()
    total, admins, password, verified, new, active = row
    return AdminStats(
        users=total,
        admins=admins,
        students=total - admins,
        password_accounts=password,
        google_accounts=total - password,
        verified=verified,
        new_last_7_days=new,
        active_last_7_days=active,
    )


@router.get("/users", response_model=UserPage)
def list_users(
    q: str = Query("", max_length=200, description="matches email or display name"),
    role: str | None = Query(None),
    method: Literal["google", "password"] | None = Query(None),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> UserPage:
    if role is not None and role not in ROLES:
        raise HTTPException(status_code=422, detail=f"role must be one of {list(ROLES)}")

    stmt = select(User)
    if q.strip():
        # LIKE metacharacters in the search box are literal text, not patterns.
        term = q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"%{term}%"
        stmt = stmt.where(
            or_(User.email.ilike(like, escape="\\"), User.display_name.ilike(like, escape="\\"))
        )
    if role:
        stmt = stmt.where(User.role == role)
    if method == "password":
        stmt = stmt.where(User.password_hash.is_not(None))
    elif method == "google":
        stmt = stmt.where(User.password_hash.is_(None))

    with session_scope() as s:
        total = s.scalar(select(func.count()).select_from(stmt.subquery()))
        rows = s.scalars(
            stmt.order_by(User.created_at.desc(), User.id).limit(limit).offset(offset)
        ).all()
    return UserPage(items=[AdminUser.of(u) for u in rows], total=total, limit=limit, offset=offset)


@router.get("/users/{user_id}", response_model=AdminUser)
def read_user(user_id: uuid.UUID) -> AdminUser:
    with session_scope() as s:
        return AdminUser.of(_get_or_404(s, user_id))


@router.post("/users", response_model=AdminUser, status_code=status.HTTP_201_CREATED)
def create_user(payload: CreateUser) -> AdminUser:
    """Create a password account on someone's behalf.

    No session is issued (the admin stays signed in as themselves) and no
    verification email is sent: the admin chooses the verified flag, and the
    student can use "mot de passe oublié" to set their own password.
    """
    email = password_auth.normalize_email(payload.email)
    try:
        with session_scope() as s:
            user = User(
                email=email,
                display_name=payload.display_name,
                password_hash=password_auth.hash_password(payload.password),
                email_verified=payload.email_verified,
            )
            s.add(user)
            s.flush()
            return AdminUser.of(user)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=password_auth.EMAIL_TAKEN)


@router.patch("/users/{user_id}", response_model=AdminUser)
def update_user(user_id: uuid.UUID, payload: UpdateUser) -> AdminUser:
    with session_scope() as s:
        user = _get_or_404(s, user_id)
        if payload.display_name is not None:
            user.display_name = payload.display_name
        if payload.email_verified is not None:
            user.email_verified = payload.email_verified
        s.flush()
        return AdminUser.of(user)


@router.post("/users/{user_id}/revoke-sessions", response_model=AdminUser)
def revoke_sessions(user_id: uuid.UUID) -> AdminUser:
    """End every session the account has, on every device.

    Same mechanism as a password reset: get_current_user rejects any token
    issued before sessions_valid_after. The account itself is untouched; they
    can sign in again. Allowed on your own account - it signs you out too.
    """
    with session_scope() as s:
        user = _get_or_404(s, user_id)
        user.sessions_valid_after = datetime.now(timezone.utc)
        s.flush()
        return AdminUser.of(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: uuid.UUID, me: User = Depends(auth.get_current_admin)) -> None:
    """Delete a student account and everything that cascades from it.

    Refuses admins (including yourself) - see the module docstring: this is
    what keeps the API from ever reducing the number of admins.
    """
    if user_id == me.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="you cannot delete your own account",
        )
    with session_scope() as s:
        user = _get_or_404(s, user_id)
        if user.role == ROLE_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="admin accounts cannot be deleted here; demote with promote_admin.py first",
            )
        s.delete(user)
