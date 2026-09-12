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

    password_accounts(run_id)

    print()
    print("ALL PASSED" if failures == 0 else f"{failures} CHECK(S) FAILED")
    raise SystemExit(1 if failures else 0)


# =============================================================================
# Phase 4: email + password accounts
#
# Runs the REAL /auth routers, the real slowapi limiter and the real 429
# handlers through FastAPI's TestClient, against real Postgres and Redis.
# Only two things are stubbed, and both on purpose:
#   - emails.send_quietly -> a recorder, so a test run never mails anyone;
#     the real Resend send is verified separately, by hand, once.
#   - auth.verify_google_id_token, only inside the Google-parity section -
#     the same one-function seam the module docstring already names.
# Needs Postgres AND Redis (inside compose: `docker compose exec backend
# python test_auth.py`).
# =============================================================================


def password_accounts(run_id: str) -> None:
    import re
    import statistics
    import time as _time

    import redis
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from slowapi.errors import RateLimitExceeded

    import emails
    import password_auth as pa
    import ratelimit
    from config import REDIS_URL
    from models import AuthToken

    # A private app with exactly the production auth wiring (api.py's lines),
    # without importing api.py - which would load the embedding model.
    app = FastAPI()
    app.state.limiter = ratelimit.limiter
    app.add_exception_handler(RateLimitExceeded, ratelimit.rate_limit_handler)
    app.add_exception_handler(ratelimit.KeyedRateLimitExceeded, ratelimit.keyed_rate_limit_handler)
    app.include_router(auth.router)
    app.include_router(pa.router)
    client = TestClient(app)

    # TestClient always presents as host "testclient", so every run shares one
    # per-IP bucket. Clear it before and after, or a few runs in an hour would
    # trip the signup limit and fail for a reason that is not a bug.
    r = redis.Redis.from_url(REDIS_URL)

    def clear_test_limits() -> None:
        for key in r.scan_iter("*testclient*"):
            r.delete(key)

    clear_test_limits()

    sent: list[tuple[str, emails.Email]] = []
    real_send = emails.send_quietly
    emails.send_quietly = lambda email, kind: sent.append((kind, email))

    def token_from(email: emails.Email) -> str:
        m = re.search(r"token=([A-Za-z0-9_\-]+)", email.text)
        return m.group(1) if m else ""

    def addr(tag: str) -> str:
        # example.com, not example.test: EmailStr (email-validator) rejects
        # RFC 6761 special-use domains like .test as undeliverable - correctly,
        # for real signups. example.com is reserved for documentation and never
        # receives mail, and nothing here sends anyway (send_quietly is stubbed).
        return f"pw-{tag}-{run_id}@example.com"

    password = "correct horse battery staple"
    created: list[uuid.UUID] = []

    def signup(email: str, pw: str = password, name: str = "Élève <Test>"):
        client.cookies.clear()
        return client.post(
            "/auth/signup", json={"email": email, "password": pw, "display_name": name}
        )

    def login(email: str, pw: str):
        client.cookies.clear()
        return client.post("/auth/login", json={"email": email, "password": pw})

    try:
        # --- signup ------------------------------------------------------------
        print()
        print("--- password signup ---")
        a = addr("a")
        resp = signup(a.upper())  # stored normalised
        check("signup -> 201", resp.status_code == 201, str(resp.status_code))
        body = resp.json()
        user_a = uuid.UUID(body["id"])
        created.append(user_a)
        check("signup returns the normalised email", body["email"] == a, body["email"])
        check("signup sets the session cookie", auth.SESSION_COOKIE_NAME in resp.cookies)
        signup_cookie = resp.cookies[auth.SESSION_COOKIE_NAME]

        with session_scope() as s:
            row = s.get(User, user_a)
            stored_hash, verified, gsub = row.password_hash, row.email_verified, row.google_sub
        check(
            "password stored as an Argon2id PHC string",
            stored_hash.startswith("$argon2id$"),
            stored_hash[:30],
        )
        check("plaintext password appears nowhere in the hash", password not in stored_hash)
        check("email_verified starts false", verified is False)
        check("password account has no google_sub", gsub is None)

        verify_mails = [e for k, e in sent if k == pa.PURPOSE_VERIFY and e.to == a]
        check("one verification email queued", len(verify_mails) == 1, f"{len(verify_mails)}")
        vtoken = token_from(verify_mails[0]) if verify_mails else ""
        check("verification link carries a token", len(vtoken) >= 40, f"{len(vtoken)} chars")
        check(
            "display name is HTML-escaped in the email",
            "&lt;Test&gt;" in verify_mails[0].html and "<Test>" not in verify_mails[0].html,
        )

        with session_scope() as s:
            tok_rows = s.query(AuthToken).filter(AuthToken.user_id == user_a).all()
            token_columns = [(t.token_hash, t.purpose) for t in tok_rows]
        check(
            "token stored only as its SHA-256",
            token_columns == [(pa._hash_token(vtoken), pa.PURPOSE_VERIFY)],
        )
        check(
            "raw token appears in no stored column", all(vtoken not in h for h, _ in token_columns)
        )

        resp = signup(a)
        check("duplicate email -> 409", resp.status_code == 409, str(resp.status_code))
        resp = signup(a.replace("pw-a", "PW-A"))
        check(
            "duplicate differing only in case -> 409",
            resp.status_code == 409,
            str(resp.status_code),
        )
        resp = signup(addr("short"), pw="elevenchars")
        check("11-character password -> 422", resp.status_code == 422, str(resp.status_code))
        resp = signup(addr("exact"), pw="twelve chars")
        check(
            "12-character password (with a space) accepted",
            resp.status_code == 201,
            str(resp.status_code),
        )
        if resp.status_code == 201:
            created.append(uuid.UUID(resp.json()["id"]))
        resp = signup("not-an-email")
        check("malformed email -> 422", resp.status_code == 422, str(resp.status_code))

        # --- email verification ------------------------------------------------
        print()
        print("--- email verification ---")
        resp = client.get("/auth/verify-email", params={"token": vtoken}, follow_redirects=False)
        check(
            "verify link -> 303 to the app, outcome 1",
            resp.status_code == 303 and resp.headers["location"].endswith("?email_verifie=1"),
            f"{resp.status_code} {resp.headers.get('location')}",
        )
        with session_scope() as s:
            check("email_verified now true", s.get(User, user_a).email_verified is True)
        resp = client.get("/auth/verify-email", params={"token": vtoken}, follow_redirects=False)
        check(
            "verify link cannot be reused (outcome 0)",
            resp.headers.get("location", "").endswith("?email_verifie=0"),
        )

        # --- login ---------------------------------------------------------------
        print()
        print("--- password login ---")
        resp = login(a, password)
        check("correct password -> 200", resp.status_code == 200, str(resp.status_code))
        check("login sets the session cookie", auth.SESSION_COOKIE_NAME in resp.cookies)
        login_set_cookie = resp.headers.get("set-cookie", "")
        login_cookie = resp.cookies.get(auth.SESSION_COOKIE_NAME)
        check(
            "login cookie resolves to the right user",
            auth.get_current_user(login_cookie).id == user_a,
        )

        # A Google-only account with a known address, for the generic-error and
        # forgot-password checks below. Separate identity, same kind of address.
        g_email = addr("google")
        g_user = auth.upsert_user(
            {
                "sub": f"test-g-{run_id}",
                "email": g_email,
                "name": "G",
                "iss": "https://accounts.google.com",
            }
        )
        created.append(g_user.id)

        wrong = login(a, "definitely the wrong one")
        unknown = login(addr("nobody"), "definitely the wrong one")
        google_only = login(g_email, "definitely the wrong one")
        check("wrong password -> 401", wrong.status_code == 401, str(wrong.status_code))
        check(
            "unknown email / Google-only email / wrong password: byte-identical bodies",
            wrong.content == unknown.content == google_only.content,
            wrong.text,
        )
        check(
            "...and identical statuses",
            wrong.status_code == unknown.status_code == google_only.status_code == 401,
        )

        # Timing: 'no such account' must cost an Argon2 verification too.
        c = addr("timing")
        created.append(uuid.UUID(signup(c).json()["id"]))
        t_unknown, t_wrong = [], []
        for i in range(3):
            t0 = _time.perf_counter()
            login(addr(f"ghost{i}"), "some wrong password")
            t_unknown.append(_time.perf_counter() - t0)
            t0 = _time.perf_counter()
            login(c, "some wrong password")
            t_wrong.append(_time.perf_counter() - t0)
        mu, mw = statistics.median(t_unknown), statistics.median(t_wrong)
        check(
            "unknown email costs about the same as a wrong password",
            0.5 < mu / mw < 2.0,
            f"median {mu * 1000:.0f}ms vs {mw * 1000:.0f}ms",
        )

        # --- brute force ---------------------------------------------------------
        print()
        print("--- brute force on one account ---")
        d = addr("target")
        created.append(uuid.UUID(signup(d).json()["id"]))
        codes = [login(d, f"guess number {i}").status_code for i in range(5)]
        check("first 5 wrong guesses in a minute -> 401", codes == [401] * 5, str(codes))
        sixth = login(d, "guess number 6")
        check(
            "6th guess in the minute -> 429 (per-email limit)",
            sixth.status_code == 429,
            str(sixth.status_code),
        )
        check(
            "429 carries Retry-After",
            sixth.headers.get("retry-after", "").isdigit(),
            sixth.headers.get("retry-after"),
        )
        check(
            "429 body has the shared shape",
            set(sixth.json()) == {"detail", "limit", "retry_after"},
            sixth.text,
        )
        right = login(d, password)
        check(
            "even the correct password is refused while limited",
            right.status_code == 429,
            str(right.status_code),
        )
        ok_other = login(a, password)
        check(
            "another account from the same IP is unaffected",
            ok_other.status_code == 200,
            str(ok_other.status_code),
        )
        ghost = addr("ghost-brute")
        ghost_codes = [login(ghost, "x" * 12).status_code for _ in range(6)]
        check(
            "a nonexistent address is limited identically (no existence leak)",
            ghost_codes == [401] * 5 + [429],
            str(ghost_codes),
        )

        # --- forgot password -----------------------------------------------------
        print()
        print("--- forgot password ---")
        sent.clear()
        f_pw = client.post("/auth/forgot-password", json={"email": a})
        f_google = client.post("/auth/forgot-password", json={"email": g_email})
        f_none = client.post("/auth/forgot-password", json={"email": addr("never-registered")})
        check(
            "password / Google-only / unknown: byte-identical bodies",
            f_pw.content == f_google.content == f_none.content,
            f_pw.text,
        )
        check(
            "...and identical statuses (202)",
            f_pw.status_code == f_google.status_code == f_none.status_code == 202,
        )
        kinds = {e.to: k for k, e in sent}
        check("password account gets a reset link", kinds.get(a) == pa.PURPOSE_RESET, str(kinds))
        check(
            "Google-only account gets the 'use Google' email",
            kinds.get(g_email) == "google_account",
        )
        g_mail = next((e for k, e in sent if e.to == g_email), None)
        check(
            "'use Google' email contains no token",
            g_mail is not None and "token=" not in g_mail.text + g_mail.html,
        )
        check("unknown address gets nothing", addr("never-registered") not in kinds)
        first_reset = token_from(next(e for k, e in sent if e.to == a))
        check(
            "reset link carries its token in the URL fragment",
            "#token=" in next(e for k, e in sent if e.to == a).text,
        )

        # --- reset password ------------------------------------------------------
        print()
        print("--- reset password ---")
        sent.clear()
        client.post("/auth/forgot-password", json={"email": a})
        second_reset = token_from(sent[-1][1])
        new_password = "a brand new passphrase"

        bad = client.post(
            "/auth/reset-password", json={"token": first_reset, "new_password": new_password}
        )
        check(
            "an older link is dead once a newer one is issued",
            bad.status_code == 400,
            str(bad.status_code),
        )
        tampered = second_reset[:-1] + ("A" if second_reset[-1] != "A" else "B")
        bad = client.post(
            "/auth/reset-password", json={"token": tampered, "new_password": new_password}
        )
        check("tampered token -> 400", bad.status_code == 400, str(bad.status_code))
        bad = client.post(
            "/auth/reset-password",
            json={"token": pa.secrets.token_urlsafe(32), "new_password": new_password},
        )
        check("guessed token -> 400", bad.status_code == 400, str(bad.status_code))
        bad = client.post(
            "/auth/reset-password", json={"token": vtoken, "new_password": new_password}
        )
        check(
            "a verification token cannot reset a password",
            bad.status_code == 400,
            str(bad.status_code),
        )
        with session_scope() as s:
            expired_raw = pa.issue_token(s, user_a, pa.PURPOSE_RESET, ttl_seconds=-1)
        bad = client.post(
            "/auth/reset-password", json={"token": expired_raw, "new_password": new_password}
        )
        check("expired token -> 400", bad.status_code == 400, str(bad.status_code))
        # issuing that expired one retired second_reset - issue a fresh one directly
        with session_scope() as s:
            good_raw = pa.issue_token(s, user_a, pa.PURPOSE_RESET, ttl_seconds=3600)
        weak = client.post(
            "/auth/reset-password", json={"token": good_raw, "new_password": "short"}
        )
        check(
            "reset with a too-short password -> 422, token not burned",
            weak.status_code == 422,
            str(weak.status_code),
        )

        _time.sleep(1.1)  # so the old session's iat is strictly before the cut-off second
        client.cookies.clear()
        ok = client.post(
            "/auth/reset-password", json={"token": good_raw, "new_password": new_password}
        )
        check(
            "valid token -> 200 and a session",
            ok.status_code == 200 and auth.SESSION_COOKIE_NAME in ok.cookies,
            str(ok.status_code),
        )
        again = client.post(
            "/auth/reset-password",
            json={"token": good_raw, "new_password": "yet another passphrase"},
        )
        check(
            "the same token cannot be used twice", again.status_code == 400, str(again.status_code)
        )
        check("old password no longer works", login(a, password).status_code == 401)
        check("new password works", login(a, new_password).status_code == 200)
        expect_401("a session from before the reset is ended", signup_cookie)
        expect_401("...including the login from before the reset", login_cookie)
        check(
            "the session issued by the reset works",
            auth.get_current_user(ok.cookies[auth.SESSION_COOKIE_NAME]).id == user_a,
        )

        # --- same session mechanism as Google ------------------------------------
        print()
        print("--- same session mechanism as Google ---")
        real_verify = auth.verify_google_id_token
        auth.verify_google_id_token = lambda token: {
            "sub": f"test-parity-{run_id}",
            "email": addr("parity"),
            "name": "Parity",
            "iss": "https://accounts.google.com",
        }
        try:
            client.cookies.clear()
            g_resp = client.post("/auth/google", json={"id_token": "stubbed"})
        finally:
            auth.verify_google_id_token = real_verify
        check(
            "stubbed-verification /auth/google -> 200",
            g_resp.status_code == 200,
            str(g_resp.status_code),
        )
        created.append(uuid.UUID(g_resp.json()["id"]))
        g_set_cookie = g_resp.headers.get("set-cookie", "")

        def cookie_shape(header: str) -> tuple:
            parts = [p.strip() for p in header.split(";")]
            name = parts[0].split("=", 1)[0]
            attrs = sorted(
                p.split("=", 1)[0].lower()
                + (
                    "=" + p.split("=", 1)[1].lower()
                    if "=" in p and not p.lower().startswith("expires")
                    else ""
                )
                for p in parts[1:]
            )
            return name, tuple(attrs)

        check(
            "Set-Cookie: same name and attributes (HttpOnly, Max-Age, Path, SameSite)",
            cookie_shape(g_set_cookie) == cookie_shape(login_set_cookie),
            f"\n         google: {cookie_shape(g_set_cookie)}\n         password: {cookie_shape(login_set_cookie)}",
        )
        g_claims = jwt.decode(
            g_resp.cookies[auth.SESSION_COOKIE_NAME],
            auth.SESSION_SECRET_KEY,
            algorithms=[auth.JWT_ALGORITHM],
        )
        p_claims = jwt.decode(
            login_cookie, auth.SESSION_SECRET_KEY, algorithms=[auth.JWT_ALGORITHM]
        )
        check(
            "JWT claims: same keys",
            set(g_claims) == set(p_claims) == {"sub", "iat", "exp"},
            f"{sorted(g_claims)} / {sorted(p_claims)}",
        )
        check(
            "JWT: same TTL", g_claims["exp"] - g_claims["iat"] == p_claims["exp"] - p_claims["iat"]
        )
        check(
            "JWT header: same algorithm",
            jwt.get_unverified_header(g_resp.cookies[auth.SESSION_COOKIE_NAME])
            == jwt.get_unverified_header(login_cookie),
        )
        me = client.get("/auth/me")
        check(
            "Google session still resolves through /auth/me",
            me.status_code == 200 and me.json()["email"] == addr("parity"),
        )

        # --- schema guarantees ---------------------------------------------------
        print()
        print("--- schema guarantees ---")
        from sqlalchemy.exc import IntegrityError

        try:
            with session_scope() as s:
                s.add(User(email=addr("nocred"), display_name="x"))
            check("CHECK rejects a user with neither google_sub nor password", False, "inserted")
        except IntegrityError:
            check("CHECK rejects a user with neither google_sub nor password", True)
        try:
            with session_scope() as s:
                s.add(User(email=a.upper(), password_hash="$argon2id$dummy"))
            check("unique index rejects a second password account, any case", False, "inserted")
        except IntegrityError:
            check("unique index rejects a second password account, any case", True)
        both = signup(g_email)
        check(
            "a Google address can still get a separate password account (no linking)",
            both.status_code == 201,
            str(both.status_code),
        )
        if both.status_code == 201:
            created.append(uuid.UUID(both.json()["id"]))
            with session_scope() as s:
                rows = s.query(User).filter(func_lower(User.email) == g_email).all()
                ids = {row.id for row in rows}
            check(
                "...as two separate rows",
                ids == {g_user.id, uuid.UUID(both.json()["id"])},
                str(len(ids)),
            )

        # --- Phase 5: /auth/me reports verification + method ------------------
        print()
        print("--- /auth/me: email_verified and auth_method ---")

        def me_with(user_id: uuid.UUID) -> dict:
            client.cookies.clear()
            client.cookies.set(auth.SESSION_COOKIE_NAME, auth.create_session_token(user_id))
            resp = client.get("/auth/me")
            return resp.json() if resp.status_code == 200 else {"status": resp.status_code}

        e = addr("verify5")
        resp = signup(e)
        user_e = uuid.UUID(resp.json()["id"])
        created.append(user_e)
        check(
            "signup response already reports unverified + password",
            (resp.json().get("email_verified"), resp.json().get("auth_method"))
            == (False, "password"),
            str(resp.json()),
        )
        m = me_with(user_e)
        check(
            "/auth/me: unverified password account -> email_verified false",
            m.get("email_verified") is False,
            str(m),
        )
        check("/auth/me: auth_method is 'password'", m.get("auth_method") == "password", str(m))
        check(
            "/auth/me does not leak google_sub or password_hash",
            not ({"google_sub", "password_hash"} & set(m)),
            str(sorted(m)),
        )

        first_link = token_from([em for k, em in sent if k == pa.PURPOSE_VERIFY and em.to == e][-1])
        client.get("/auth/verify-email", params={"token": first_link}, follow_redirects=False)
        m = me_with(user_e)
        check(
            "/auth/me after clicking the link -> email_verified true",
            m.get("email_verified") is True,
            str(m),
        )

        m = me_with(g_user.id)
        check(
            "/auth/me: Google account -> auth_method 'google', email_verified false",
            (m.get("auth_method"), m.get("email_verified")) == ("google", False),
            str(m),
        )

        # --- Phase 5: resend verification -------------------------------------
        print()
        print("--- resend verification ---")
        client.cookies.clear()
        check(
            "resend without a session -> 401",
            client.post("/auth/resend-verification").status_code == 401,
        )

        h = addr("resend5")
        resp = signup(h)  # leaves h's session cookie on the client
        user_h = uuid.UUID(resp.json()["id"])
        created.append(user_h)
        original = token_from([em for k, em in sent if k == pa.PURPOSE_VERIFY and em.to == h][-1])

        sent.clear()
        r1 = client.post("/auth/resend-verification")
        check("resend -> 202", r1.status_code == 202, f"{r1.status_code} {r1.text}")
        resent = [em for k, em in sent if k == pa.PURPOSE_VERIFY and em.to == h]
        check(
            "resend queues exactly one real verification email", len(resent) == 1, str(len(resent))
        )
        new_link = token_from(resent[0]) if resent else ""
        check("the resent link is a different token", bool(new_link) and new_link != original)

        dead = client.get("/auth/verify-email", params={"token": original}, follow_redirects=False)
        check(
            "the original link is dead after a resend",
            dead.headers.get("location", "").endswith("?email_verifie=0"),
        )
        live = client.get("/auth/verify-email", params={"token": new_link}, follow_redirects=False)
        check(
            "the resent link works", live.headers.get("location", "").endswith("?email_verifie=1")
        )

        sent.clear()
        r2 = client.post("/auth/resend-verification")
        check(
            "resend once verified -> 200 'déjà confirmée', nothing sent",
            r2.status_code == 200 and not sent,
            f"{r2.status_code} {r2.text}",
        )
        r3 = client.post("/auth/resend-verification")
        check("3 calls within the hour are allowed", r3.status_code == 200, str(r3.status_code))
        r4 = client.post("/auth/resend-verification")
        check(
            "4th call within the hour -> 429 (per user)", r4.status_code == 429, str(r4.status_code)
        )
        check("...with Retry-After", r4.headers.get("retry-after", "").isdigit())

        client.cookies.clear()
        client.cookies.set(auth.SESSION_COOKIE_NAME, auth.create_session_token(user_e))
        other = client.post("/auth/resend-verification")
        check(
            "the limit is per user: another account is unaffected",
            other.status_code == 200,
            str(other.status_code),
        )

        client.cookies.clear()
        client.cookies.set(auth.SESSION_COOKIE_NAME, auth.create_session_token(g_user.id))
        g_resend = client.post("/auth/resend-verification")
        check(
            "resend for a Google account -> 400",
            g_resend.status_code == 400,
            f"{g_resend.status_code} {g_resend.text}",
        )

    finally:
        emails.send_quietly = real_send
        with session_scope() as s:
            for uid in created:
                row = s.get(User, uid)
                if row is not None:
                    s.delete(row)
        clear_test_limits()
        with session_scope() as s:
            left = s.query(User).filter(User.email.like(f"%{run_id}@example.com")).count()
        check("password-test users cleaned up (tokens cascade)", left == 0, f"{left} left")


def func_lower(column):
    from sqlalchemy import func

    return func.lower(column)


if __name__ == "__main__":
    main()
