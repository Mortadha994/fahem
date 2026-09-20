"""Admin-only routes: the gate (Phase 7) and user management (Phase 8).

Every route on this router depends on auth.get_current_admin, declared once on
the router itself rather than per route: a route added later cannot forget it.
tests/test_admin.py asserts that every route here inherits it.

What an admin can do to an account, and - as deliberately - what they cannot:

  can     list and search accounts, read one, create a password account,
          edit the display name and the verified flag, end every session
          (force sign-out), delete a student account.
  cannot  change anyone's role. scripts/promote_admin.py stays the only way in or out
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

from app.auth import auth, password_auth
from app.core import runtime_settings
from app.core.db import session_scope
from app.core.models import NIVEAUX, PLANS, ROLE_ADMIN, ROLES, SECTIONS_BY_NIVEAU, User
from app.llm import ai_control

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
    plan: str = "free"
    suspended_at: datetime | None = None
    suspended_reason: str | None = None
    solve_rate_limit: str | None = None

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
            plan=user.plan,
            suspended_at=user.suspended_at,
            suspended_reason=user.suspended_reason,
            solve_rate_limit=user.solve_rate_limit,
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
    suspended: int = 0


class Suspend(BaseModel):
    reason: str = Field(default="", max_length=300)


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
    # niveau and section are set together, validated as a pair like the
    # student's own profile. solve_rate_limit: a limit string sets a personal
    # limit; an explicit null or "" goes back to the global one; absent
    # leaves it unchanged.
    niveau: str | None = None
    section: str | None = None
    plan: str | None = None
    solve_rate_limit: str | None = None

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
                func.count().filter(User.suspended_at.is_not(None)),
            ).select_from(User)
        ).one()
    total, admins, password, verified, new, active, suspended = row
    return AdminStats(
        users=total,
        admins=admins,
        students=total - admins,
        password_accounts=password,
        google_accounts=total - password,
        verified=verified,
        new_last_7_days=new,
        active_last_7_days=active,
        suspended=suspended,
    )


@router.get("/users", response_model=UserPage)
def list_users(
    q: str = Query("", max_length=200, description="matches email or display name"),
    role: str | None = Query(None),
    method: Literal["google", "password"] | None = Query(None),
    state: Literal["active", "suspended"] | None = Query(None),
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
    if state == "suspended":
        stmt = stmt.where(User.suspended_at.is_not(None))
    elif state == "active":
        stmt = stmt.where(User.suspended_at.is_(None))

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
def update_user(
    user_id: uuid.UUID, payload: UpdateUser, me: User = Depends(auth.get_current_admin)
) -> AdminUser:
    sent = payload.model_fields_set
    if ("niveau" in sent) != ("section" in sent):
        raise HTTPException(
            status_code=422, detail="Le niveau et la section se modifient ensemble."
        )
    if "niveau" in sent and (payload.niveau is not None or payload.section is not None):
        if payload.niveau not in NIVEAUX:
            raise HTTPException(status_code=422, detail="Niveau inconnu.")
        if payload.section not in SECTIONS_BY_NIVEAU[payload.niveau]:
            raise HTTPException(
                status_code=422, detail="Cette section n'existe pas pour ce niveau."
            )
    if "plan" in sent and payload.plan not in PLANS:
        raise HTTPException(status_code=422, detail=f"Offre inconnue ({', '.join(PLANS)}).")
    personal_limit = None
    if "solve_rate_limit" in sent and (payload.solve_rate_limit or "").strip():
        try:
            personal_limit = runtime_settings.rate_limit(payload.solve_rate_limit)
        except runtime_settings.InvalidSetting as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    with session_scope() as s:
        user = _get_or_404(s, user_id)
        before = AdminUser.of(user).model_dump(mode="json")
        if payload.display_name is not None:
            user.display_name = payload.display_name
        if payload.email_verified is not None:
            user.email_verified = payload.email_verified
        if "niveau" in sent:
            user.niveau = payload.niveau
            user.section = payload.section
        if "plan" in sent:
            user.plan = payload.plan
        if "solve_rate_limit" in sent:
            user.solve_rate_limit = personal_limit
        s.flush()
        after = AdminUser.of(user)
        email = user.email

    changes = {
        k: {"old": before[k], "new": v}
        for k, v in after.model_dump(mode="json").items()
        if before.get(k) != v
    }
    if changes:
        runtime_settings.audit(me.email, "user.update", email, changes, target_id=str(user_id))
    if "solve_rate_limit" in changes:
        ai_control.forget_user_limit(user_id)
    return after


@router.post("/users/{user_id}/suspend", response_model=AdminUser)
def suspend_user(
    user_id: uuid.UUID, payload: Suspend, me: User = Depends(auth.get_current_admin)
) -> AdminUser:
    """Suspend an account: every session ends now, and signing in again is
    refused (auth.refuse_if_suspended) until it is reactivated. Nothing is
    deleted. Refused for admins, yourself included, for the same reason they
    cannot be deleted here."""
    if user_id == me.id:
        raise HTTPException(status_code=400, detail="Tu ne peux pas suspendre ton propre compte.")
    now = datetime.now(timezone.utc)
    with session_scope() as s:
        user = _get_or_404(s, user_id)
        if user.role == ROLE_ADMIN:
            raise HTTPException(
                status_code=409, detail="Un compte admin ne peut pas être suspendu ici."
            )
        user.suspended_at = user.suspended_at or now
        user.suspended_reason = payload.reason.strip() or None
        user.sessions_valid_after = now
        s.flush()
        out, email = AdminUser.of(user), user.email
    runtime_settings.audit(
        me.email,
        "user.suspend",
        email,
        {"reason": out.suspended_reason},
        target_id=str(user_id),
    )
    return out


@router.post("/users/{user_id}/reactivate", response_model=AdminUser)
def reactivate_user(user_id: uuid.UUID, me: User = Depends(auth.get_current_admin)) -> AdminUser:
    """Lift a suspension. The student signs in again normally."""
    with session_scope() as s:
        user = _get_or_404(s, user_id)
        was_suspended = user.suspended_at is not None
        user.suspended_at = None
        user.suspended_reason = None
        s.flush()
        out, email = AdminUser.of(user), user.email
    if was_suspended:
        runtime_settings.audit(me.email, "user.reactivate", email, target_id=str(user_id))
    return out


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
                detail="admin accounts cannot be deleted here; demote with scripts/promote_admin.py first",
            )
        s.delete(user)
