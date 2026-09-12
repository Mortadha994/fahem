"""Tests for the admin role (Phase 7): the column, the get_current_admin gate,
the /admin router through real HTTP, the /auth/me role field, and
promote_admin.py - including its refusal to leave zero admins.

Same main() + __main__ shape as test_auth.py; importing this module touches
nothing. Runs the real auth, password_auth and admin routers through FastAPI's
TestClient against real Postgres and Redis, with emails.send_quietly stubbed
so nothing is mailed. Inside compose:

    docker compose exec backend python test_admin.py

Every row it creates is keyed by a per-run id and deleted at the end.

The last-admin tests need a database with no pre-existing admins, because
"last" is a global property: they cannot be made true without demoting a real
admin, which a test must never do. When admins already exist those tests are
reported as SKIP, loudly, rather than passing vacuously.
"""

from __future__ import annotations

import contextlib
import io
import threading
import time
import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

import auth
import promote_admin
from db import session_scope
from models import ROLE_ADMIN, ROLE_STUDENT, User

failures = 0
skips = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global failures
    if not condition:
        failures += 1
    print(f"[{'PASS' if condition else 'FAIL'}] {label}" + (f" {detail}" if detail else ""))


def skip(label: str, why: str) -> None:
    global skips
    skips += 1
    print(f"[SKIP] {label} - {why}")


def run_script(*argv: str) -> tuple[int, str]:
    """promote_admin.main with its stdout and stderr captured together."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        code = promote_admin.main(list(argv))
    return code, buf.getvalue()


def role_of(user_id: uuid.UUID) -> str | None:
    with session_scope() as s:
        row = s.get(User, user_id)
        return row.role if row else None


def main() -> None:
    run_id = uuid.uuid4().hex[:10]
    created: list[uuid.UUID] = []

    def make_user(tag: str, *, google: bool = False, email: str | None = None) -> uuid.UUID:
        with session_scope() as s:
            row = User(
                email=email or f"adm-{tag}-{run_id}@example.com",
                display_name=f"Test {tag}",
                google_sub=f"test-admin-{tag}-{run_id}" if google else None,
                # The CHECK needs *a* credential; nothing here logs in with it.
                password_hash=None if google else "not-a-real-hash",
            )
            s.add(row)
            s.flush()
            uid = row.id
        created.append(uid)
        return uid

    with session_scope() as s:
        preexisting_admins = len(s.scalars(select(User).where(User.role == ROLE_ADMIN)).all())
    print(f"(pre-existing admins in this database: {preexisting_admins})")

    try:
        # --- the column -----------------------------------------------------
        student = make_user("student")
        check("a new user defaults to role 'student'", role_of(student) == ROLE_STUDENT)

        try:
            with session_scope() as s:
                s.get(User, student).role = "admln"
            check("CHECK rejects a role outside the set", False, "typo'd role was stored")
        except IntegrityError:
            check("CHECK rejects a role outside the set", True)
        check("...and the row is unchanged", role_of(student) == ROLE_STUDENT)

        # --- the dependency, directly ---------------------------------------
        with session_scope() as s:
            student_row = s.get(User, student)
        try:
            auth.get_current_admin(student_row)
            check("get_current_admin rejects a student", False, "no exception")
        except HTTPException as exc:
            check("get_current_admin rejects a student with 403", exc.status_code == 403, str(exc.status_code))

        # --- promote_admin.py -------------------------------------------------
        target = make_user("target")
        code, out = run_script(f"adm-target-{run_id}@example.com")
        check("script: promote exits 0", code == 0, out.strip())
        # Verified in the database, not from the script's own message.
        check("script: role is 'admin' in the database", role_of(target) == ROLE_ADMIN)

        code, out = run_script(f"ADM-TARGET-{run_id}@EXAMPLE.COM")
        check("script: promote again is idempotent (exit 0, still admin)",
              code == 0 and role_of(target) == ROLE_ADMIN and "Already" in out, out.strip())

        code, out = run_script(f"nobody-{run_id}@example.com")
        check("script: unknown email exits 1", code == 1, out.strip())

        code, out = run_script()
        check("script: no arguments is a usage error (exit 2)", code == 2)

        shared = f"adm-shared-{run_id}@example.com"
        g_twin = make_user("g-twin", google=True, email=shared)
        p_twin = make_user("p-twin", email=shared)
        code, out = run_script(shared)
        check("script: an email shared by two accounts is refused (exit 1)", code == 1, out.strip())
        check("...and neither account was promoted",
              role_of(g_twin) == ROLE_STUDENT and role_of(p_twin) == ROLE_STUDENT)
        check("...and both ids are listed for the operator", str(g_twin) in out and str(p_twin) in out)

        code, out = run_script(shared, "--id", str(p_twin))
        check("script: --id disambiguates", code == 0 and role_of(p_twin) == ROLE_ADMIN, out.strip())
        check("...and only that account changed", role_of(g_twin) == ROLE_STUDENT)

        code, out = run_script(f"adm-student-{run_id}@example.com", "--id", str(p_twin))
        check("script: --id with a mismatched email is refused",
              code == 1 and role_of(p_twin) == ROLE_ADMIN and role_of(student) == ROLE_STUDENT, out.strip())

        code, out = run_script("--list")
        check("script: --list shows the admins", str(target) in out and str(p_twin) in out)

        code, out = run_script(shared, "--id", str(p_twin), "--demote")
        check("script: demote with another admin remaining succeeds",
              code == 0 and role_of(p_twin) == ROLE_STUDENT, out.strip())

        # --- the last-admin guard -------------------------------------------
        if preexisting_admins == 0:
            code, out = run_script(f"adm-target-{run_id}@example.com", "--demote")
            check("script: demoting the last admin is refused (exit 1)", code == 1, out.strip())
            check("...and they are still admin", role_of(target) == ROLE_ADMIN)

            # Two operators at once. A holds the admin rows locked and has
            # already demoted `target` but not committed; B tries to demote
            # `second`. B must block on the lock, then see only one admin left
            # and refuse. Without FOR UPDATE, both would see two and both win.
            second = make_user("second")
            run_script(f"adm-second-{run_id}@example.com")
            a_locked, a_release = threading.Event(), threading.Event()

            def operator_a() -> None:
                with session_scope() as s:
                    s.scalars(select(User).where(User.role == ROLE_ADMIN).with_for_update()).all()
                    s.get(User, target).role = ROLE_STUDENT
                    s.flush()
                    a_locked.set()
                    a_release.wait(10)

            result: dict = {}

            def operator_b() -> None:
                result["code"], result["out"] = run_script(
                    f"adm-second-{run_id}@example.com", "--demote"
                )

            ta = threading.Thread(target=operator_a)
            ta.start()
            a_locked.wait(10)
            tb = threading.Thread(target=operator_b)
            tb.start()
            time.sleep(0.5)
            check("concurrent demote: B blocks while A holds the admin rows", tb.is_alive())
            a_release.set()
            ta.join(10)
            tb.join(10)
            check("concurrent demote: B is refused once A commits",
                  result.get("code") == 1, result.get("out", "").strip())
            check("...leaving exactly one admin, never zero",
                  role_of(target) == ROLE_STUDENT and role_of(second) == ROLE_ADMIN)
            # Restore: target admin again for the HTTP section below.
            run_script(f"adm-target-{run_id}@example.com")
        else:
            skip("demoting the last admin is refused", "this database already has admins")
            skip("concurrent demotes never leave zero admins", "this database already has admins")

        # --- through real HTTP ----------------------------------------------
        http_section(run_id, created, student=student, admin=target)

    finally:
        with session_scope() as s:
            for uid in created:
                row = s.get(User, uid)
                if row is not None:
                    s.delete(row)
        with session_scope() as s:
            left = s.query(User).filter(User.email.like(f"%{run_id}@example.com")).count()
        check("test users cleaned up", left == 0, f"{left} left")

    print(f"\n{failures} failure(s), {skips} skip(s)")
    raise SystemExit(1 if failures else 0)


def http_section(run_id: str, created: list[uuid.UUID], *, student: uuid.UUID, admin: uuid.UUID) -> None:
    import redis
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from slowapi.errors import RateLimitExceeded

    import admin as admin_module
    import emails
    import password_auth
    import ratelimit
    from config import REDIS_URL

    # Production wiring for these routers (api.py's lines), without importing
    # api.py - which would load the embedding model.
    app = FastAPI()
    app.state.limiter = ratelimit.limiter
    app.add_exception_handler(RateLimitExceeded, ratelimit.rate_limit_handler)
    app.add_exception_handler(ratelimit.KeyedRateLimitExceeded, ratelimit.keyed_rate_limit_handler)
    app.include_router(auth.router)
    app.include_router(password_auth.router)
    app.include_router(admin_module.router)
    client = TestClient(app)

    r = redis.Redis.from_url(REDIS_URL)
    for key in r.scan_iter("*testclient*"):
        r.delete(key)
    real_send = emails.send_quietly
    emails.send_quietly = lambda email, kind: None

    def as_user(uid: uuid.UUID | None) -> None:
        client.cookies.clear()
        if uid is not None:
            client.cookies.set(auth.SESSION_COOKIE_NAME, auth.create_session_token(uid))

    try:
        as_user(None)
        resp = client.get("/admin/whoami")
        check("HTTP: /admin/whoami signed out -> 401", resp.status_code == 401, str(resp.status_code))

        client.cookies.set(auth.SESSION_COOKIE_NAME, "not-a-jwt")
        resp = client.get("/admin/whoami")
        check("HTTP: /admin/whoami with a forged cookie -> 401", resp.status_code == 401, str(resp.status_code))

        as_user(student)
        resp = client.get("/admin/whoami")
        check("HTTP: /admin/whoami as a student -> 403", resp.status_code == 403, str(resp.status_code))
        check("...and reveals nothing but the refusal", resp.json() == {"detail": "admin role required"}, resp.text)

        me = client.get("/auth/me").json()
        check("HTTP: /auth/me reports role 'student'", me.get("role") == ROLE_STUDENT, str(me))

        as_user(admin)
        resp = client.get("/admin/whoami")
        check("HTTP: /admin/whoami as an admin -> 200", resp.status_code == 200, f"{resp.status_code} {resp.text}")
        check("...with the admin's identity", resp.json().get("role") == ROLE_ADMIN)
        check("HTTP: /auth/me reports role 'admin'", client.get("/auth/me").json().get("role") == ROLE_ADMIN)

        # A demotion takes effect on the very next request, not at next login:
        # the role is read from the row on every request, never from the token.
        with session_scope() as s:
            s.get(User, admin).role = ROLE_STUDENT
        resp = client.get("/admin/whoami")
        check("HTTP: a demoted admin's existing session -> 403 immediately",
              resp.status_code == 403, str(resp.status_code))
        with session_scope() as s:
            s.get(User, admin).role = ROLE_ADMIN

        # No way in through the front door: a signup that asks to be an admin
        # is created as a student. (Pydantic drops the unknown field; this pins
        # that nobody later adds `role` to the signup model.)
        email = f"adm-signup-{run_id}@example.com"
        client.cookies.clear()
        resp = client.post(
            "/auth/signup",
            json={"email": email, "password": "correct horse battery staple",
                  "display_name": "Sneaky", "role": "admin"},
        )
        if resp.status_code in (200, 201):
            created.append(uuid.UUID(resp.json()["id"]))
        check("HTTP: signup with role=admin in the body is created",
              resp.status_code in (200, 201), f"{resp.status_code} {resp.text}")
        check("...as a student", resp.json().get("role") == ROLE_STUDENT, resp.text)
        check("...and cannot reach /admin", client.get("/admin/whoami").status_code == 403)

        # Structural: every route on the admin router carries the gate.
        # Read from the router itself, not app.routes: this FastAPI version keeps
        # an included router nested (_IncludedRouter) rather than flattening its
        # routes onto the app, so filtering app.routes finds nothing and the
        # check passes vacuously - which the first version of this test did.
        check("the admin router declares get_current_admin at router level",
              any(d.dependency is auth.get_current_admin for d in admin_module.router.dependencies))
        admin_routes = list(admin_module.router.routes)
        # r.dependencies is what the router injected, so a route that only
        # passes because it happens to repeat Depends() itself is not counted.
        ungated = [
            r.path for r in admin_routes
            if not any(d.dependency is auth.get_current_admin for d in r.dependencies)
        ]
        check("every /admin route inherits the gate (non-vacuous)",
              bool(admin_routes) and not ungated, f"routes={len(admin_routes)} ungated={ungated}")

        crud_section(client, as_user, run_id, created, student=student, admin=admin)
    finally:
        emails.send_quietly = real_send
        for key in r.scan_iter("*testclient*"):
            r.delete(key)


def crud_section(client, as_user, run_id: str, created: list[uuid.UUID], *,
                 student: uuid.UUID, admin: uuid.UUID) -> None:
    """Phase 8: user management through the real admin router."""
    good_pw = "correct horse battery staple"

    # --- every CRUD route refuses a student -------------------------------
    as_user(student)
    probes = [
        ("GET", "/admin/stats"), ("GET", "/admin/users"), ("GET", f"/admin/users/{admin}"),
        ("POST", "/admin/users"), ("PATCH", f"/admin/users/{admin}"),
        ("POST", f"/admin/users/{admin}/revoke-sessions"), ("DELETE", f"/admin/users/{admin}"),
    ]
    codes = {f"{m} {p.split(str(admin))[0]}": client.request(m, p, json={}).status_code for m, p in probes}
    check("CRUD: every admin route -> 403 for a student", set(codes.values()) == {403}, str(codes))
    check("...and the admin they targeted is untouched", role_of(admin) == ROLE_ADMIN)

    as_user(admin)

    # --- stats / list / read ------------------------------------------------
    st = client.get("/admin/stats")
    body = st.json()
    check("stats -> 200 with consistent totals",
          st.status_code == 200 and body["users"] == body["admins"] + body["students"]
          and body["users"] == body["password_accounts"] + body["google_accounts"], st.text)

    page = client.get("/admin/users", params={"q": run_id})
    emails_found = {u["email"] for u in page.json().get("items", [])}
    check("list: search by text finds this run's accounts",
          page.status_code == 200 and f"adm-student-{run_id}@example.com" in emails_found, page.text[:200])
    check("list: total matches items when under the limit", page.json()["total"] == len(page.json()["items"]))
    check("list: no password_hash or google_sub in the payload",
          "password_hash" not in page.text and "google_sub" not in page.text)

    only_admins = client.get("/admin/users", params={"q": run_id, "role": "admin"}).json()["items"]
    check("list: role filter", only_admins and all(u["role"] == "admin" for u in only_admins))
    check("list: an invalid role filter -> 422",
          client.get("/admin/users", params={"role": "root"}).status_code == 422)
    check("list: '%' in the search is literal, not a wildcard",
          client.get("/admin/users", params={"q": "%"}).json()["total"] == 0)
    p2 = client.get("/admin/users", params={"q": run_id, "limit": 1, "offset": 1}).json()
    check("list: limit/offset paginate", len(p2["items"]) == 1 and p2["offset"] == 1, str(p2)[:200])

    check("read: an unknown id -> 404", client.get(f"/admin/users/{uuid.uuid4()}").status_code == 404)
    check("read: a real id -> 200", client.get(f"/admin/users/{student}").json().get("id") == str(student))

    # --- create ---------------------------------------------------------------
    new_email = f"adm-created-{run_id}@example.com"
    resp = client.post("/admin/users", json={
        "email": new_email.upper(), "display_name": "  Créé par admin ", "password": good_pw,
        "email_verified": True, "role": "admin",
    })
    if resp.status_code == 201:
        created.append(uuid.UUID(resp.json()["id"]))
    made = resp.json()
    check("create: 201", resp.status_code == 201, resp.text)
    check("create: role=admin in the body is ignored -> student", made.get("role") == ROLE_STUDENT, str(made))
    check("create: email normalised, name trimmed, flag applied",
          made.get("email") == new_email and made.get("display_name") == "Créé par admin"
          and made.get("email_verified") is True, str(made))
    check("create: did not switch the admin's session to the new account",
          client.get("/admin/whoami").json().get("email") == f"adm-target-{run_id}@example.com")
    check("create: duplicate email -> 409",
          client.post("/admin/users", json={"email": new_email, "display_name": "x", "password": good_pw}).status_code == 409)
    check("create: a weak password -> 422",
          client.post("/admin/users", json={"email": f"weak-{run_id}@example.com", "display_name": "x", "password": "short"}).status_code == 422)
    login = client.post("/auth/login", json={"email": new_email, "password": good_pw})
    check("create: the account can actually sign in", login.status_code == 200, str(login.status_code))
    as_user(admin)  # the login above replaced the cookie

    # --- update ---------------------------------------------------------------
    new_id = created[-1]
    resp = client.patch(f"/admin/users/{new_id}", json={
        "display_name": "Renommé", "email_verified": False, "role": "admin", "email": "hijack@example.com",
    })
    got = resp.json()
    check("update: 200 with name and flag changed",
          resp.status_code == 200 and got["display_name"] == "Renommé" and got["email_verified"] is False, resp.text)
    check("update: role and email in the body are ignored",
          got["role"] == ROLE_STUDENT and got["email"] == new_email and role_of(new_id) == ROLE_STUDENT)
    check("update: a blank name -> 422",
          client.patch(f"/admin/users/{new_id}", json={"display_name": "   "}).status_code == 422)
    check("update: unknown id -> 404",
          client.patch(f"/admin/users/{uuid.uuid4()}", json={"display_name": "x"}).status_code == 404)

    # --- revoke sessions --------------------------------------------------------
    victim_cookie = auth.create_session_token(new_id)
    # The cut-off is compared in whole seconds (auth.get_current_user), so the
    # token must be issued in an earlier second than the revoke.
    time.sleep(1.1)
    resp = client.post(f"/admin/users/{new_id}/revoke-sessions")
    check("revoke: 200 and sets sessions_valid_after",
          resp.status_code == 200 and resp.json()["sessions_valid_after"], resp.text)
    client.cookies.clear()
    client.cookies.set(auth.SESSION_COOKIE_NAME, victim_cookie)
    check("revoke: the account's existing session is now rejected",
          client.get("/auth/me").status_code == 401)
    as_user(admin)

    # --- delete -------------------------------------------------------------------
    check("delete: your own account -> 400",
          client.delete(f"/admin/users/{admin}").status_code == 400)
    other_admin = uuid.UUID(client.post("/admin/users", json={
        "email": f"adm-other-{run_id}@example.com", "display_name": "Other", "password": good_pw}).json()["id"])
    created.append(other_admin)
    with session_scope() as s:
        s.get(User, other_admin).role = ROLE_ADMIN
    resp = client.delete(f"/admin/users/{other_admin}")
    check("delete: another admin -> 409, still exists and still admin",
          resp.status_code == 409 and role_of(other_admin) == ROLE_ADMIN, resp.text)

    resp = client.delete(f"/admin/users/{new_id}")
    check("delete: a student -> 204", resp.status_code == 204, resp.text)
    check("delete: the row is gone", role_of(new_id) is None)
    check("delete: again -> 404", client.delete(f"/admin/users/{new_id}").status_code == 404)


if __name__ == "__main__":
    main()
