"""Direct tests for the auth layer: session tokens, the current-user
dependency, the user upsert, and the logout cookie.

Follows test_db.py's main() + __main__ shape (importing this module must not
touch the database or the network).

What is NOT covered here, and cannot be without a live OAuth flow:
verify_google_id_token() against a real Google-signed ID token. Producing one
requires a browser sign-in against a configured GOOGLE_CLIENT_ID. Everything
downstream of verification - the upsert, the session, the dependency - is
exercised below with the claims dict Google would have returned, so the
untested seam is exactly one function call wide.

Needs a reachable Postgres:
    docker compose up -d postgres
    .venv/Scripts/python.exe test_auth.py

It writes and then deletes its own rows, keyed by a per-run UUID in
google_sub, so a leftover row from an interrupted run never collides.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException

import auth
from db import session_scope
from models import User

failures = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global failures
    if not condition:
        failures += 1
    print(f"[{'PASS' if condition else 'FAIL'}] {label}" + (f" {detail}" if detail else ""))


def expect_401(label: str, cookie) -> None:
    """The dependency must reject `cookie` with a 401 and nothing else."""
    try:
        auth.get_current_user(cookie)
    except HTTPException as exc:
        check(label, exc.status_code == 401, f"got {exc.status_code}")
    except Exception as exc:  # noqa: BLE001 - any other escape is the bug
        check(label, False, f"raised {type(exc).__name__}: {exc}")
    else:
        check(label, False, "no exception raised")


class FakeResponse:
    """Minimal stand-in for starlette's Response.

    Only set_cookie/delete_cookie are used by the code under test, and both
    are pure record-keeping, so recording the kwargs is enough to assert the
    cookie attributes without standing up an HTTP server.
    """

    def __init__(self) -> None:
        self.set_calls: list[dict] = []
        self.delete_calls: list[dict] = []

    def set_cookie(self, **kwargs):
        self.set_calls.append(kwargs)

    def delete_cookie(self, **kwargs):
        self.delete_calls.append(kwargs)


def main() -> None:
    run_id = uuid.uuid4().hex[:12]
    google_sub = f"test-google-sub-{run_id}"

    # --- 1. session token round-trip ---------------------------------------
    print("--- session tokens ---")
    user_id = uuid.uuid4()
    token = auth.create_session_token(user_id)
    check("token is a compact JWS (three dot-separated parts)", token.count(".") == 2)
    check("round-trips to the same user id", auth.decode_session_token(token) == user_id)

    payload = jwt.decode(token, auth.SESSION_SECRET_KEY, algorithms=[auth.JWT_ALGORITHM])
    ttl = payload["exp"] - payload["iat"]
    check("exp is iat + SESSION_TTL_SECONDS", ttl == auth.SESSION_TTL_SECONDS, f"{ttl}s")

    expired = auth.create_session_token(user_id, ttl_seconds=-1)
    try:
        auth.decode_session_token(expired)
        check("expired token is rejected", False, "decoded anyway")
    except jwt.ExpiredSignatureError:
        check("expired token is rejected", True)

    forged = jwt.encode({"sub": str(user_id)}, "not-the-real-key", algorithm="HS256")
    try:
        auth.decode_session_token(forged)
        check("token signed with the wrong key is rejected", False, "decoded anyway")
    except jwt.InvalidSignatureError:
        check("token signed with the wrong key is rejected", True)

    # alg=none is the classic JWT forgery: a token with no signature at all.
    none_alg = jwt.encode({"sub": str(user_id)}, key="", algorithm="none")
    try:
        auth.decode_session_token(none_alg)
        check("alg=none token is rejected", False, "decoded anyway")
    except jwt.InvalidTokenError:
        check("alg=none token is rejected", True)

    # --- 3. upsert (run before the dependency test, which needs a real row) -
    print()
    print("--- user upsert ---")
    first_claims = {
        "sub": google_sub,
        "email": f"{run_id}@example.test",
        "name": "Élève Test",
        "iss": "https://accounts.google.com",
    }
    user = auth.upsert_user(first_claims)
    first_id, first_login, created_at = user.id, user.last_login_at, user.created_at
    check("first sign-in creates a user", isinstance(first_id, uuid.UUID))
    check("display_name keeps accents", user.display_name == "Élève Test", repr(user.display_name))
    check("last_login_at set on first sign-in", first_login is not None)

    second_claims = dict(first_claims, email=f"{run_id}+renamed@example.test", name="Élève Renommé")
    user2 = auth.upsert_user(second_claims)
    check("second sign-in reuses the same row", user2.id == first_id, f"{user2.id} vs {first_id}")
    check("email updated on re-login", user2.email == second_claims["email"])
    check("display_name updated on re-login", user2.display_name == "Élève Renommé")
    check(
        "last_login_at advanced",
        user2.last_login_at > first_login,
        f"{first_login} -> {user2.last_login_at}",
    )
    check("created_at unchanged", user2.created_at == created_at)

    with session_scope() as s:
        rows = s.query(User).filter(User.google_sub == google_sub).count()
    check("exactly one row for this google_sub, not two", rows == 1, f"{rows} rows")

    # --- 2. get_current_user dependency ------------------------------------
    print()
    print("--- get_current_user ---")
    good = auth.create_session_token(first_id)
    resolved = auth.get_current_user(good)
    check("valid cookie resolves to the right user", resolved.id == first_id)
    check("resolved user carries the updated email", resolved.email == second_claims["email"])

    expect_401("missing cookie -> 401", None)
    expect_401("empty cookie -> 401", "")
    expect_401("malformed cookie -> 401", "not-a-jwt")
    expect_401("truncated JWT -> 401", good[: len(good) // 2])
    expect_401("expired cookie -> 401", auth.create_session_token(first_id, ttl_seconds=-1))
    expect_401("wrong-key cookie -> 401", forged)
    expect_401("alg=none cookie -> 401", none_alg)
    expect_401("valid signature, unknown user -> 401", auth.create_session_token(uuid.uuid4()))

    # A token whose `sub` is not a UUID at all must 401, not 500.
    bad_sub = jwt.encode(
        {
            "sub": "not-a-uuid",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        auth.SESSION_SECRET_KEY,
        algorithm=auth.JWT_ALGORITHM,
    )
    expect_401("non-UUID sub -> 401", bad_sub)

    # --- 4. cookie attributes ----------------------------------------------
    print()
    print("--- cookies ---")
    resp = FakeResponse()
    auth.set_session_cookie(resp, good)
    kw = resp.set_calls[0]
    check("cookie name matches config", kw["key"] == auth.SESSION_COOKIE_NAME, kw["key"])
    check("cookie is httponly", kw["httponly"] is True)
    check("cookie carries the token", kw["value"] == good)
    check("cookie max_age matches the TTL", kw["max_age"] == auth.SESSION_TTL_SECONDS)
    check("cookie path is /", kw["path"] == "/")
    check("samesite matches config", kw["samesite"] == auth.SESSION_COOKIE_SAMESITE)
    check("secure matches config", kw["secure"] == auth.SESSION_COOKIE_SECURE)

    resp = FakeResponse()
    auth.clear_session_cookie(resp)
    dk = resp.delete_calls[0]
    check("logout deletes the same cookie name", dk["key"] == auth.SESSION_COOKIE_NAME)
    check("logout matches path", dk["path"] == "/")
    check("logout matches samesite", dk["samesite"] == auth.SESSION_COOKIE_SAMESITE)
    check("logout matches secure", dk["secure"] == auth.SESSION_COOKIE_SECURE)

    # --- misconfiguration guard --------------------------------------------
    print()
    print("--- configuration guard ---")
    saved = auth.GOOGLE_CLIENT_ID
    try:
        auth.GOOGLE_CLIENT_ID = ""
        try:
            auth.verify_google_id_token("anything")
            check("empty GOOGLE_CLIENT_ID refuses to verify", False, "verified anyway")
        except auth.AuthConfigurationError:
            check("empty GOOGLE_CLIENT_ID refuses to verify", True)
        except Exception as exc:  # noqa: BLE001
            check("empty GOOGLE_CLIENT_ID refuses to verify", False, f"{type(exc).__name__}")
    finally:
        auth.GOOGLE_CLIENT_ID = saved

    # --- cleanup ------------------------------------------------------------
    with session_scope() as s:
        s.delete(s.get(User, first_id))
    with session_scope() as s:
        check("test user cleaned up", s.get(User, first_id) is None)

    print()
    print("ALL PASSED" if failures == 0 else f"{failures} CHECK(S) FAILED")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
