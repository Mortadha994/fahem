"""Email + password accounts: signup, login, verification, password reset.

Phase 4. A second, fully independent way to establish identity, next to the
Google flow in auth.py. Four things to know before the code:

1. Identity is the only thing that differs. Once a password is verified, the
   session is issued by exactly the functions the Google flow uses -
   create_session_token() and set_session_cookie(), imported from auth.py
   below - and validated afterwards by the same get_current_user(). There is
   no second session format, cookie or validator to drift out of step.

2. Google and password accounts are never linked. The same address may exist
   as a Google account and as a separate password account; nothing here looks
   up a Google account by email except forgot-password, and that only to
   choose which email to send. Auto-linking by email would let someone who
   pre-registers a victim's address with a password they control inherit the
   victim's later Google sign-in. (If linking is ever wanted, the safe shape is
   an explicit action taken while signed in to BOTH accounts - proving control
   of each - never a match on the address.)

3. Nothing reveals whether an address has an account where it can be avoided.
   Login fails with one message and one timing whether the address is unknown,
   belongs to a Google account, or the password is wrong. Forgot-password
   answers identically in every case and sends mail after the response.
   Signup is the one unavoidable exception: it must say "that address is
   taken" - see signup().

4. Emailed tokens are single-use, time-limited, and stored only as a hash.
   Consuming one is a single UPDATE ... WHERE used_at IS NULL, so two
   simultaneous uses cannot both succeed.
"""

from __future__ import annotations

import functools
import hashlib
import logging
import re
import secrets
import unicodedata
import uuid
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

import emails
import ratelimit as _ratelimit
from auth import (  # the shared mechanism
    UserOut,
    bind_user,
    create_session_token,
    set_session_cookie,
)
from config import (
    APP_BASE_URL,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    PUBLIC_API_URL,
    RATE_LIMIT_FORGOT,
    RATE_LIMIT_FORGOT_EMAIL,
    RATE_LIMIT_LOGIN,
    RATE_LIMIT_LOGIN_EMAIL,
    RATE_LIMIT_RESEND_VERIFY,
    RATE_LIMIT_SIGNUP,
    RATE_LIMIT_TOKEN,
    RESET_TOKEN_TTL_SECONDS,
    VERIFY_TOKEN_TTL_SECONDS,
)
from db import session_scope
from models import AuthToken, User

log = logging.getLogger("fahem.auth")

PURPOSE_VERIFY = "verify_email"
PURPOSE_RESET = "reset_password"

# One message for every login failure. Which half was wrong is exactly what a
# credential-stuffing run wants to learn.
LOGIN_FAILED = "Adresse e-mail ou mot de passe incorrect."
# One response for every forgot-password request, byte for byte.
FORGOT_ACK = "Si un compte existe pour cette adresse, un e-mail vient d'y être envoyé."
RESET_INVALID = "Ce lien de réinitialisation est invalide ou a expiré. Demande-en un nouveau."
EMAIL_TAKEN = "Un compte avec cette adresse e-mail existe déjà. Connecte-toi, ou réinitialise ton mot de passe."

# Longest token we will even hash. Real ones are 43 characters.
_MAX_TOKEN_CHARS = 256


# --- passwords ------------------------------------------------------------------

# argon2-cffi's defaults are Argon2id with RFC 9106's low-memory profile
# (t=3, m=64 MiB, p=4) - the OWASP-recommended algorithm at parameters its
# authors chose for interactive logins. Stated here, not re-tuned: when the
# library raises its defaults, check_needs_rehash() below upgrades stored
# hashes on the user's next login.
_hasher = PasswordHasher()


def normalize_password(password: str) -> str:
    """NFKC, as NIST 800-63B asks: the same passphrase typed on two keyboards
    (composed 'é' vs 'e' + combining accent) must hash the same."""
    return unicodedata.normalize("NFKC", password)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    return _hasher.hash(normalize_password(password))


def verify_password(password_hash: str, password: str) -> bool:
    """The library's own constant-time comparison - never a string compare."""
    try:
        return _hasher.verify(password_hash, normalize_password(password))
    except VerifyMismatchError:
        return False
    except (VerificationError, InvalidHashError):
        log.error("stored password hash could not be verified (corrupt or foreign format)")
        return False


@functools.lru_cache(maxsize=1)
def _dummy_hash() -> str:
    """A real Argon2id hash of a random secret, verified against when there is
    no account to check. Makes 'no such account' cost the same ~tens of ms as
    'wrong password', so response time does not reveal which it was."""
    return _hasher.hash(secrets.token_urlsafe(24))


def _check_password_rules(value: str) -> str:
    n = len(normalize_password(value))
    if n < PASSWORD_MIN_LENGTH:
        raise ValueError(
            f"Le mot de passe doit contenir au moins {PASSWORD_MIN_LENGTH} caractères."
        )
    if n > PASSWORD_MAX_LENGTH:
        raise ValueError(f"Le mot de passe ne peut pas dépasser {PASSWORD_MAX_LENGTH} caractères.")
    return value


# --- tokens ---------------------------------------------------------------------


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def issue_token(session, user_id: uuid.UUID, purpose: str, ttl_seconds: int) -> str:
    """Create a token and return the raw value (the only time it exists).

    Any earlier unspent token of the same purpose is retired first, so only
    the newest link in someone's inbox works - requesting a second reset email
    kills the first.
    """
    now = datetime.now(timezone.utc)
    session.execute(
        update(AuthToken)
        .where(
            AuthToken.user_id == user_id,
            AuthToken.purpose == purpose,
            AuthToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    raw = secrets.token_urlsafe(32)  # 256 bits
    session.add(
        AuthToken(
            user_id=user_id,
            purpose=purpose,
            token_hash=_hash_token(raw),
            expires_at=now + timedelta(seconds=ttl_seconds),
        )
    )
    return raw


def consume_token(raw: str | None, purpose: str) -> uuid.UUID | None:
    """Spend a token; return its user id, or None if it is unknown, of the
    wrong purpose, expired or already spent. One statement, so it is atomic:
    of two concurrent requests with the same token, exactly one gets the id."""
    if not raw or len(raw) > _MAX_TOKEN_CHARS:
        return None
    stmt = (
        update(AuthToken)
        .where(
            AuthToken.token_hash == _hash_token(raw),
            AuthToken.purpose == purpose,
            AuthToken.used_at.is_(None),
            AuthToken.expires_at > func.now(),
        )
        .values(used_at=func.now())
        .returning(AuthToken.user_id)
    )
    with session_scope() as s:
        return s.execute(stmt).scalar_one_or_none()


def verify_url(raw: str) -> str:
    return f"{PUBLIC_API_URL}/auth/verify-email?token={raw}"


def reset_url(raw: str) -> str:
    # Fragment, not query: see config.APP_BASE_URL.
    return f"{APP_BASE_URL}/reinitialiser-mot-de-passe#token={raw}"


def _find_password_account(session, email: str) -> User | None:
    return session.scalar(
        select(User).where(func.lower(User.email) == email, User.password_hash.is_not(None))
    )


# --- keep live tokens out of the access log ----------------------------------------


class _RedactTokens(logging.Filter):
    """uvicorn's access log prints the full request path, query string
    included, and GET /auth/verify-email carries a live token there. Redact
    it before the line is written; a log is not a place for credentials."""

    _pattern = re.compile(r"(token=)[^&\s\"']+")

    def filter(self, record: logging.LogRecord) -> bool:
        if record.args:
            record.args = tuple(
                self._pattern.sub(r"\1[redacted]", a) if isinstance(a, str) else a
                for a in record.args
            )
        return True


logging.getLogger("uvicorn.access").addFilter(_RedactTokens())


# --- request bodies ---------------------------------------------------------------


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str = Field(min_length=1, max_length=80)

    @field_validator("password")
    @classmethod
    def _password_rules(cls, v: str) -> str:
        return _check_password_rules(v)

    @field_validator("display_name")
    @classmethod
    def _name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Le nom ne peut pas être vide.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    # No length rule at login - that would tell a caller what the rule is and
    # reject old passwords if it ever changed. Only a cap, for Argon2's sake.
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH * 4)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=1, max_length=_MAX_TOKEN_CHARS)
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _password_rules(cls, v: str) -> str:
        return _check_password_rules(v)


class Ack(BaseModel):
    detail: str


# --- routes -----------------------------------------------------------------------

# Same /auth prefix as the Google router, separate module: the two identity
# methods share a URL space and a session, not code paths.
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@_ratelimit.limiter.limit(RATE_LIMIT_SIGNUP, key_func=_ratelimit.ip_key)
def signup(
    request: Request, payload: SignupRequest, response: Response, background: BackgroundTasks
) -> UserOut:
    """Create a password account and sign it in straight away.

    Verification is sent but not required - by design, nothing is gated on it.

    Enumeration: this route has to say "that address already has an account",
    which does reveal that it does. Every signup flow that signs the user in
    immediately has this property; hiding it would mean a generic answer and
    no session. It is bounded by the per-IP limit, and it only reveals
    *password* accounts - a Google account with the same address does not
    block signup, because the two are separate identities.
    """
    email = normalize_email(payload.email)
    password_hash = hash_password(payload.password)
    now = datetime.now(timezone.utc)

    try:
        with session_scope() as s:
            user = User(
                email=email,
                display_name=payload.display_name,
                password_hash=password_hash,
                email_verified=False,
                last_login_at=now,
            )
            s.add(user)
            s.flush()  # surfaces the unique-email violation here, not at commit
            raw = issue_token(s, user.id, PURPOSE_VERIFY, VERIFY_TOKEN_TTL_SECONDS)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=EMAIL_TAKEN)

    background.add_task(
        emails.send_quietly,
        emails.verification_email(email, payload.display_name, verify_url(raw)),
        PURPOSE_VERIFY,
    )
    set_session_cookie(response, create_session_token(user.id))
    return UserOut.of(user)


@router.post("/login", response_model=UserOut)
@_ratelimit.limiter.limit(RATE_LIMIT_LOGIN, key_func=_ratelimit.ip_key)
def login(request: Request, payload: LoginRequest, response: Response) -> UserOut:
    """Sign in with email + password.

    Two limits: per IP (the decorator) and per email (inside, since the body
    is not parsed until the handler runs). The per-email one is counted for
    every attempt on that address, existing or not, so its 429 reveals
    nothing either.
    """
    email = normalize_email(payload.email)
    _ratelimit.hit_keyed(RATE_LIMIT_LOGIN_EMAIL, "login-email", _ratelimit.email_key(email))

    with session_scope() as s:
        user = _find_password_account(s, email)

    if user is None:
        verify_password(_dummy_hash(), payload.password)  # equal cost, discarded
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=LOGIN_FAILED)
    if not verify_password(user.password_hash, payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=LOGIN_FAILED)

    now = datetime.now(timezone.utc)
    with session_scope() as s:
        row = s.get(User, user.id)
        row.last_login_at = now
        if _hasher.check_needs_rehash(row.password_hash):
            row.password_hash = hash_password(payload.password)
        user = row

    set_session_cookie(response, create_session_token(user.id))
    return UserOut.of(user)


@router.post("/forgot-password", response_model=Ack, status_code=status.HTTP_202_ACCEPTED)
@_ratelimit.limiter.limit(RATE_LIMIT_FORGOT, key_func=_ratelimit.ip_key)
def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    response: Response,
    background: BackgroundTasks,
) -> Ack:
    """Always the same answer. What happens behind it depends on the address:

    - a password account  -> a reset link (single-use, RESET_TOKEN_TTL)
    - only a Google account -> an email saying to use Google (no link exists)
    - nothing              -> nothing is sent

    Mail goes out as a background task after the response, so send latency
    cannot reveal which branch ran.
    """
    email = normalize_email(payload.email)
    _ratelimit.hit_keyed(RATE_LIMIT_FORGOT_EMAIL, "forgot-email", _ratelimit.email_key(email))

    mail: emails.Email | None = None
    kind = ""
    with session_scope() as s:
        account = _find_password_account(s, email)
        if account is not None:
            raw = issue_token(s, account.id, PURPOSE_RESET, RESET_TOKEN_TTL_SECONDS)
            mail, kind = emails.reset_email(account.email, reset_url(raw)), PURPOSE_RESET
        else:
            google_id = s.scalar(
                select(User.id)
                .where(func.lower(User.email) == email, User.google_sub.is_not(None))
                .limit(1)
            )
            if google_id is not None:
                mail, kind = emails.google_account_email(email), "google_account"

    if mail is not None:
        background.add_task(emails.send_quietly, mail, kind)
    return Ack(detail=FORGOT_ACK)


@router.post("/reset-password", response_model=UserOut)
@_ratelimit.limiter.limit(RATE_LIMIT_TOKEN, key_func=_ratelimit.ip_key)
def reset_password(request: Request, payload: ResetPasswordRequest, response: Response) -> UserOut:
    """Set a new password with a reset token, and sign the user in.

    Every other session for the account is ended: sessions_valid_after is set
    to now, and get_current_user() rejects any token issued before it. A reset
    is the moment someone is most likely to be locking out an intruder, so
    leaving the intruder's cookie working for its remaining 7 days would defeat
    the point. This is not general revocation (logout still only clears the
    local cookie) - it is the one revocation that cannot wait for it.

    Completing a reset also marks the address verified: the link could only be
    followed from its inbox.
    """
    new_hash = hash_password(
        payload.new_password
    )  # before consuming, so a failure here does not burn the token
    user_id = consume_token(payload.token, PURPOSE_RESET)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=RESET_INVALID)

    # Whole seconds: JWT `iat` is an integer, and a token issued in this same
    # second (the new one, below) must still be accepted.
    now = datetime.now(timezone.utc).replace(microsecond=0)
    with session_scope() as s:
        user = s.get(User, user_id)
        user.password_hash = new_hash
        user.sessions_valid_after = now
        user.email_verified = True
        user.last_login_at = now
        s.execute(
            update(AuthToken)
            .where(
                AuthToken.user_id == user_id,
                AuthToken.purpose == PURPOSE_RESET,
                AuthToken.used_at.is_(None),
            )
            .values(used_at=now)
        )

    set_session_cookie(response, create_session_token(user_id))
    return UserOut.of(user)


VERIFY_RESENT = "Un nouvel e-mail de confirmation vient d'être envoyé."
VERIFY_ALREADY = "Ton adresse e-mail est déjà confirmée."
VERIFY_NOT_APPLICABLE = "Ce compte se connecte avec Google : il n'y a pas d'adresse à confirmer."


@router.post("/resend-verification", response_model=Ack, status_code=status.HTTP_202_ACCEPTED)
@_ratelimit.limiter.limit(RATE_LIMIT_RESEND_VERIFY)
def resend_verification(
    request: Request,
    response: Response,
    background: BackgroundTasks,
    user: User = Depends(bind_user),
) -> Ack:
    """Send a fresh confirmation link to the signed-in user (Phase 5).

    Signed-in only, so there is nothing to enumerate: the caller can only ask
    about their own account. Rate-limited per user (bind_user publishes the id
    the default key function reads, exactly as for /solve).

    A new link retires the previous one (issue_token), so after a resend only
    the newest email in the inbox works.
    """
    if user.password_hash is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=VERIFY_NOT_APPLICABLE)
    if user.email_verified:
        response.status_code = status.HTTP_200_OK
        return Ack(detail=VERIFY_ALREADY)

    with session_scope() as s:
        raw = issue_token(s, user.id, PURPOSE_VERIFY, VERIFY_TOKEN_TTL_SECONDS)
    background.add_task(
        emails.send_quietly,
        emails.verification_email(user.email, user.display_name or "", verify_url(raw)),
        PURPOSE_VERIFY,
    )
    return Ack(detail=VERIFY_RESENT)


@router.get("/verify-email")
@_ratelimit.limiter.limit(RATE_LIMIT_TOKEN, key_func=_ratelimit.ip_key)
def verify_email(request: Request, token: str = "") -> RedirectResponse:
    """The link in the verification email. Marks the address and sends the
    browser on to the app with the outcome in the query string.

    A GET that changes state, on purpose: it is what a link in an email is.
    Mail scanners that pre-fetch links will spend it - harmless here, since the
    only effect is marking an address verified that the scanner's own mailbox
    received. (Reset is different, which is why its link goes to the app and
    the app POSTs.)

    No session required: the link may well be opened on another device.
    """
    user_id = consume_token(token, PURPOSE_VERIFY)
    if user_id is not None:
        with session_scope() as s:
            s.get(User, user_id).email_verified = True
    outcome = "1" if user_id is not None else "0"
    return RedirectResponse(f"{APP_BASE_URL}/?email_verifie={outcome}", status_code=303)
