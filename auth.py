"""Google sign-in and session issuance.

Added in Phase 0c; the gate it exists for was flipped in Phase 1, so
/solve and /solve/stream now require get_current_user() and anonymous use is
no longer possible. /auth/google carries a per-IP rate limit (Phase 2) since
it is the one route here reachable before a session exists.

Three ideas worth reading before the code:

1. The session is an httpOnly cookie, not a token handed to JavaScript.
   Frontend JS cannot read it, so an XSS bug cannot exfiltrate it the way it
   could a token in localStorage. The cost is that the browser only attaches
   it when CORS is configured with credentials on both ends - see
   config.SESSION_COOKIE_SAMESITE for the same-site trap this creates in the
   current local setup.

2. The Google ID token is verified, never trusted. verify_google_id_token()
   checks the signature against Google's published keys AND checks that the
   audience is our own client id. Skipping the audience check is the classic
   mistake: a validly-signed token issued for a *different* application would
   otherwise be accepted, letting anyone with any Google app sign in as
   anyone.

3. The user upsert is one statement, not select-then-branch. Two concurrent
   first-time sign-ins for the same account would both see "no row" and both
   insert, and one would die on the unique index. ON CONFLICT DO UPDATE makes
   that case impossible rather than rare.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from pydantic import BaseModel, Field
from sqlalchemy.dialects.postgresql import insert as pg_insert

import ratelimit as _ratelimit
from config import (
    GOOGLE_CLIENT_ID,
    RATE_LIMIT_AUTH,
    SESSION_COOKIE_NAME,
    SESSION_COOKIE_SAMESITE,
    SESSION_COOKIE_SECURE,
    SESSION_SECRET_KEY,
    SESSION_TTL_SECONDS,
)
from db import session_scope
from models import User

# HS256, not RS256: the only party that signs these tokens is also the only
# party that verifies them, so an asymmetric key pair would add key management
# for no gain. Revisit if a second service ever needs to verify sessions
# without being able to mint them.
JWT_ALGORITHM = "HS256"

# Google's issuer values. verify_oauth2_token checks these itself; the tuple
# is here so the check is visible rather than implied.
GOOGLE_ISSUERS = ("accounts.google.com", "https://accounts.google.com")


class AuthConfigurationError(RuntimeError):
    """Raised when sign-in is attempted with no GOOGLE_CLIENT_ID configured."""


class GoogleSignInRequest(BaseModel):
    id_token: str = Field(min_length=1, description="ID token from Google Sign-In")


class UserOut(BaseModel):
    """What the API says about a user. Deliberately not the ORM object:
    google_sub is an internal join key and never leaves the backend."""

    id: uuid.UUID
    email: str | None
    display_name: str | None
    # Phase 5. email_verified alone cannot drive a "confirm your address"
    # reminder: Google accounts are always false (Fahem never mails them a
    # link), so the client also needs to know which kind of account this is.
    # The method, not google_sub - that stays an internal join key.
    email_verified: bool
    auth_method: Literal["google", "password"]

    @classmethod
    def of(cls, user: User) -> "UserOut":
        return cls(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            email_verified=user.email_verified,
            auth_method="password" if user.password_hash else "google",
        )


# --- Google ID token verification -------------------------------------------


def verify_google_id_token(token: str) -> dict:
    """Verify a Google ID token and return its claims.

    Raises ValueError if the token is malformed, expired, signed by the wrong
    key, or issued for a different audience. google-auth fetches and caches
    Google's public keys itself, so there is no key material to manage here.
    """
    if not GOOGLE_CLIENT_ID:
        # Refuse rather than verify with audience=None. Passing None disables
        # the audience check, which would accept a token minted for any other
        # Google application - a misconfiguration that silently becomes an
        # authentication bypass is worse than a loud failure.
        raise AuthConfigurationError(
            "GOOGLE_CLIENT_ID is not set; refusing to verify an ID token with an unchecked audience"
        )

    claims = google_id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)

    if claims.get("iss") not in GOOGLE_ISSUERS:
        raise ValueError(f"unexpected issuer: {claims.get('iss')!r}")
    if not claims.get("sub"):
        raise ValueError("token carries no `sub` claim")
    return claims


# --- user upsert -------------------------------------------------------------


def upsert_user(claims: dict) -> User:
    """Create or refresh the user behind a set of verified Google claims.

    Keyed on `sub`, never on email: a Google account's email can change, and
    keying on it would orphan the user's history after a rename (models.py
    makes the same point at the column).

    Only email/display_name/last_login_at are updated - `id` and `created_at`
    stay put, so a returning user keeps the identity every chat_session row
    references.
    """
    now = datetime.now(timezone.utc)
    values = {
        "google_sub": claims["sub"],
        "email": claims.get("email"),
        "display_name": claims.get("name"),
        "last_login_at": now,
    }

    stmt = (
        pg_insert(User)
        .values(id=uuid.uuid4(), **values)
        .on_conflict_do_update(
            index_elements=[User.google_sub],
            set_={
                "email": values["email"],
                "display_name": values["display_name"],
                "last_login_at": now,
            },
        )
        .returning(User)
    )

    with session_scope() as session:
        return session.scalars(stmt).one()


# --- session tokens ----------------------------------------------------------


def create_session_token(user_id: uuid.UUID, ttl_seconds: int = SESSION_TTL_SECONDS) -> str:
    """Sign a session JWT carrying the user id and an expiry."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(seconds=ttl_seconds),
    }
    return jwt.encode(payload, SESSION_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_session_token(token: str) -> uuid.UUID:
    """Return the user id in a session token, or raise.

    algorithms is pinned to a single value on purpose: accepting a list the
    attacker can steer (notably "none") is the standard JWT forgery route.
    """
    payload = jwt.decode(token, SESSION_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    return uuid.UUID(payload["sub"])


# --- cookie handling ---------------------------------------------------------


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite=SESSION_COOKIE_SAMESITE,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    """Delete the cookie.

    The attributes must match what set_session_cookie() used - a browser
    treats a cookie with a different path or samesite as a different cookie
    and would leave the original in place.
    """
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite=SESSION_COOKIE_SAMESITE,
        path="/",
    )


# --- FastAPI dependency ------------------------------------------------------


def get_current_user(session_cookie: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)) -> User:
    """Resolve the signed-in user, or raise 401.

    Built now, applied to nothing yet - /solve and /solve/stream stay open to
    anonymous requests until the frontend can sign in (Phase 0c non-goal).

    Every failure returns the same 401 with the same body. Distinguishing
    "no cookie" from "bad signature" from "expired" from "user deleted" would
    tell an attacker which half of a forgery attempt worked.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated"
    )
    if not session_cookie:
        raise unauthorized

    try:
        claims = jwt.decode(session_cookie, SESSION_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = uuid.UUID(claims["sub"])
        issued_at = int(claims["iat"])
    except (jwt.InvalidTokenError, ValueError, KeyError, TypeError):
        raise unauthorized

    with session_scope() as session:
        user = session.get(User, user_id)

    if user is None:
        # Valid signature, but the row is gone - a deleted account whose
        # cookie has not expired yet.
        raise unauthorized

    # Phase 4: a password reset sets sessions_valid_after, which ends every
    # session issued before it. Null (every Google account, and any password
    # account that has never reset) means no cut-off, so this changes nothing
    # for them. Compared in whole seconds because `iat` is an integer.
    cutoff = user.sessions_valid_after
    if cutoff is not None and issued_at < int(cutoff.timestamp()):
        raise unauthorized
    return user


def bind_user(
    request: Request,
    user: User = Depends(get_current_user),
) -> User:
    """get_current_user, plus publishing the id for the rate limiter's key.

    Lives here rather than in ratelimit.py because ratelimit.py must not
    import this module - auth.py imports it for the /auth/google decorator,
    and the reverse import would be a cycle.

    The ordering this relies on: FastAPI resolves dependencies before the
    endpoint function runs, and slowapi's decorator wraps that function, so
    the id is already on request.state when the limiter evaluates its key.
    That is what lets the limit key off the DB-verified identity rather than a
    separately re-parsed token, which can disagree - a deleted account still
    presents a well-formed unexpired token.
    """
    setattr(request.state, _ratelimit.STATE_USER_ID, user.id)
    return user


# --- routes ------------------------------------------------------------------

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google", response_model=UserOut)
@_ratelimit.limiter.limit(RATE_LIMIT_AUTH, key_func=_ratelimit.ip_key)
def google_sign_in(request: Request, payload: GoogleSignInRequest, response: Response) -> UserOut:
    """Exchange a Google ID token for a session cookie.

    Rate-limited per client IP, not per user: there is no user yet at this
    point. See config.RATE_LIMIT_AUTH for why the limit is deliberately loose
    (a school behind one NAT shares it) and what it does and does not protect.

    `request` is the Starlette Request, required by slowapi under that exact
    name; the body model is `payload`.
    """
    try:
        claims = verify_google_id_token(payload.id_token)
    except AuthConfigurationError as exc:
        # A server misconfiguration, not a bad request from the client.
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=f"invalid Google ID token: {exc}")

    user = upsert_user(claims)
    set_session_cookie(response, create_session_token(user.id))
    return UserOut.of(user)


@router.get("/me", response_model=UserOut)
def read_current_user(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.of(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> Response:
    """Clear the session cookie.

    No get_current_user dependency: logging out with an already-invalid
    cookie should succeed quietly, not 401. The action is idempotent.
    """
    clear_session_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
