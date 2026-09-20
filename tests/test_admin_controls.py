"""Tests for the admin console's controls: live AI settings and account actions.

Real Postgres and Redis, the real app through TestClient, and no Groq call:
every request that could reach a model is either refused by a control (which
is the point) or sent for chapter "99", which is refused with a 404 before any
model call - proof it got past the controls.

Settings rows that exist before the run are restored afterwards, and every
account and audit row the run creates is deleted.

    docker compose exec -T backend python -m tests.test_admin_controls
"""

from __future__ import annotations

import uuid

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app import main as api
from app.auth import auth, password_auth
from app.core import runtime_settings
from app.core.db import session_scope
from app.core.models import ROLE_ADMIN, AdminAuditEntry, AppSetting, User
from app.llm import ai_control
from app.routes.admin import admin_controls

results: list[bool] = []


def check(name: str, ok: bool, detail: object = "") -> None:
    results.append(bool(ok))
    print(
        ("[PASS] " if ok else "[FAIL] ")
        + name
        + (f"  -> {detail!r}" if not ok and detail != "" else "")
    )


def main() -> None:
    run = uuid.uuid4().hex[:8]
    password = "correct-horse-battery"
    admin_email = f"ctl-admin-{run}@example.com"
    student_email = f"ctl-student-{run}@example.com"

    with session_scope() as s:
        saved_settings = [
            (r.key, r.value, r.updated_by, r.updated_at)
            for r in s.scalars(select(AppSetting)).all()
        ]
        admin = User(
            email=admin_email,
            display_name="Admin test",
            password_hash=password_auth.hash_password(password),
            role=ROLE_ADMIN,
        )
        student = User(
            email=student_email,
            display_name="Élève test",
            password_hash=password_auth.hash_password(password),
            niveau="2eme",
            section="informatique",
        )
        s.add_all([admin, student])
        s.flush()
        admin_id, student_id = admin.id, student.id

    client = TestClient(api.app)

    def as_user(uid):
        client.cookies.clear()
        client.cookies.set(auth.SESSION_COOKIE_NAME, auth.create_session_token(uid))

    def solve(chapitre="99"):
        return client.post(
            "/solve/stream",
            json={"problem": "Ecrire un algorithme.", "niveau": "2eme", "chapitre": chapitre},
        )

    def detail_code(response):
        body = (
            response.json()
            if response.headers.get("content-type", "").startswith("application/json")
            else {}
        )
        detail = body.get("detail")
        return detail.get("code") if isinstance(detail, dict) else None

    try:
        # --- validation, without HTTP ---------------------------------------------
        for bad, why in (
            ({"solve_rate_limit": "beaucoup"}, "an unreadable limit"),
            ({"daily_budget_guard_pct": 30}, "a guard below 50 %"),
            ({"queue_timeout_seconds": 5}, "a wait under 15 s"),
            ({"ai_paused": "oui"}, "a non-boolean switch"),
            ({"nope": 1}, "an unknown setting"),
        ):
            try:
                runtime_settings.set_many(bad, admin_email)
                check(f"settings: {why} is refused", False)
            except runtime_settings.InvalidSetting:
                check(f"settings: {why} is refused", True)

        # --- the gate --------------------------------------------------------------
        routes = [r for r in admin_controls.router.routes if isinstance(r, APIRoute)]
        check(
            "gate: every controls route inherits get_current_admin",
            bool(routes)
            and all(
                any(d.dependency is auth.get_current_admin for d in r.dependencies) for r in routes
            ),
        )
        as_user(student_id)
        check(
            "gate: a student cannot change a setting",
            client.put("/admin/controls", json={"ai_paused": True}).status_code == 403,
        )

        # --- baseline: the request gets past the controls ---------------------------
        as_user(admin_id)
        client.put(
            "/admin/controls",
            json={"ai_paused": False, "daily_budget_guard_pct": 0, "attachments_enabled": True},
        )
        as_user(student_id)
        check(
            "baseline: an open request reaches the chapter check (404)", solve().status_code == 404
        )

        # --- pause --------------------------------------------------------------------
        as_user(admin_id)
        r = client.put(
            "/admin/controls", json={"ai_paused": True, "ai_pause_message": "Pause de test."}
        )
        check("pause: the admin can pause", r.status_code == 200, r.text[:200])
        check(
            "pause: the change is attributed to the admin",
            r.json()["settings"]["ai_paused"]["updated_by"] == admin_email,
        )
        as_user(student_id)
        r = solve()
        check(
            "pause: a solve is refused with 503 and the admin's message",
            r.status_code == 503
            and detail_code(r) == "paused"
            and r.json()["detail"]["message"] == "Pause de test.",
            (r.status_code, r.text[:200]),
        )
        r = client.post("/solve/extract", content=b"x", headers={"Content-Type": "image/png"})
        check("pause: photo reading is refused too", detail_code(r) == "paused", r.text[:200])
        as_user(admin_id)
        client.put("/admin/controls", json={"ai_paused": False})
        as_user(student_id)
        check("pause: resuming lets requests through again", solve().status_code == 404)

        # --- attachments --------------------------------------------------------------
        as_user(admin_id)
        client.put("/admin/controls", json={"attachments_enabled": False})
        as_user(student_id)
        r = client.post("/solve/extract", content=b"x", headers={"Content-Type": "image/png"})
        check(
            "photos off: /solve/extract refuses", detail_code(r) == "attachments_off", r.text[:200]
        )
        check("photos off: typed solves still work", solve().status_code == 404)
        as_user(admin_id)
        client.put("/admin/controls", json={"attachments_enabled": True})

        # --- budget guard -------------------------------------------------------------
        real_count = ai_control._tokens_last_24h
        ai_control._tokens_last_24h = lambda model: 195_000
        ai_control.clear_budget_cache()
        try:
            as_user(admin_id)
            r = client.put("/admin/controls", json={"daily_budget_guard_pct": 90})
            budget = r.json()["budget"]
            check(
                "budget: the console shows the guard reached",
                budget["blocking"] and budget["threshold"] == int(budget["limit"] * 0.9),
                budget,
            )
            as_user(student_id)
            r = solve()
            check(
                "budget: a solve is refused once the guard is reached", detail_code(r) == "budget"
            )
            as_user(admin_id)
            client.put("/admin/controls", json={"daily_budget_guard_pct": 0})
            as_user(student_id)
            check("budget: guard off lets requests through", solve().status_code == 404)
        finally:
            ai_control._tokens_last_24h = real_count
            ai_control.clear_budget_cache()

        # --- account edits --------------------------------------------------------------
        as_user(admin_id)
        path = f"/admin/users/{student_id}"
        check(
            "account: niveau without section is refused",
            client.patch(path, json={"niveau": "bac"}).status_code == 422,
        )
        check(
            "account: a section that does not exist for the niveau is refused",
            client.patch(path, json={"niveau": "2eme", "section": "math"}).status_code == 422,
        )
        r = client.patch(path, json={"niveau": "bac", "section": "math", "plan": "paid"})
        check(
            "account: class and plan are saved",
            r.status_code == 200
            and (r.json()["niveau"], r.json()["section"], r.json()["plan"])
            == ("bac", "math", "paid"),
            r.text[:200],
        )
        check(
            "account: an unreadable personal limit is refused",
            client.patch(path, json={"solve_rate_limit": "vite"}).status_code == 422,
        )

        # --- personal limit -------------------------------------------------------------
        r = client.patch(path, json={"solve_rate_limit": "1/minute"})
        check("limit: a personal limit is saved", r.json().get("solve_rate_limit") == "1/minute")
        as_user(student_id)
        first, second = solve().status_code, solve().status_code
        check(
            "limit: the student is held to it (second request 429)",
            (first, second) == (404, 429),
            (first, second),
        )
        as_user(admin_id)
        r = client.patch(path, json={"solve_rate_limit": None})
        check("limit: null goes back to the global limit", r.json().get("solve_rate_limit") is None)

        # --- suspension -------------------------------------------------------------------
        check(
            "suspend: an admin account cannot be suspended",
            client.post(f"/admin/users/{admin_id}/suspend", json={}).status_code in (400, 409),
        )
        r = client.post(f"/admin/users/{student_id}/suspend", json={"reason": "test"})
        check(
            "suspend: the student is suspended, with the reason",
            r.status_code == 200
            and r.json()["suspended_at"]
            and r.json()["suspended_reason"] == "test",
            r.text[:200],
        )
        as_user(student_id)
        check(
            "suspend: the student's session stops working",
            client.get("/auth/me").status_code == 401,
        )
        client.cookies.clear()
        r = client.post("/auth/login", json={"email": student_email, "password": password})
        check(
            "suspend: signing in again is refused with a readable reason",
            r.status_code == 403 and "suspendu" in r.json().get("detail", ""),
            (r.status_code, r.text[:200]),
        )
        r = client.post(
            "/auth/login", json={"email": student_email, "password": "wrong-password-1"}
        )
        check("suspend: a wrong password still gets the plain 401", r.status_code == 401)
        as_user(admin_id)
        r = client.get("/admin/users", params={"state": "suspended", "q": student_email})
        check("suspend: the list filters suspended accounts", r.json()["total"] == 1)
        r = client.post(f"/admin/users/{student_id}/reactivate")
        check("reactivate: the suspension is lifted", r.json()["suspended_at"] is None)
        client.cookies.clear()
        r = client.post("/auth/login", json={"email": student_email, "password": password})
        check("reactivate: the student can sign in again", r.status_code == 200, r.text[:200])

        # --- queue reset --------------------------------------------------------------------
        as_user(admin_id)
        check(
            "queue: an unknown model is refused",
            client.post("/admin/controls/queues/reset", json={"model": "nope"}).status_code == 404,
        )
        r = client.post("/admin/controls/queues/reset", json={"model": api.GROQ_MODEL})
        check("queue: a known model's queue is reset", r.status_code == 200, r.text[:200])

        # --- the action log: filters, links, pages ----------------------------------------
        r = client.get("/admin/audit", params={"category": "comptes", "q": student_email})
        items = r.json()["items"]
        check(
            "log: the accounts filter returns only account actions for this student",
            r.status_code == 200 and items and all(i["action"].startswith("user.") for i in items),
            r.text[:300],
        )
        check(
            "log: account actions link to the account",
            any(i["action"] == "user.suspend" and i["target_id"] == str(student_id) for i in items),
        )
        r = client.get(
            "/admin/audit", params={"category": "comptes", "q": student_email, "limit": 1}
        )
        page1 = r.json()
        page2 = client.get(
            "/admin/audit",
            params={
                "category": "comptes",
                "q": student_email,
                "limit": 1,
                "before": page1["next_before"],
            },
        ).json()
        check(
            "log: pages continue where the last one stopped",
            page1["next_before"] is not None
            and page2["items"]
            and page2["items"][0]["id"] < page1["items"][0]["id"],
        )

        # --- revert ----------------------------------------------------------------------------
        before_retry = client.get("/admin/controls").json()["settings"]["retry_max"]["value"]
        client.put("/admin/controls", json={"retry_max": 5 if before_retry != 5 else 4})
        entry = client.get("/admin/audit", params={"category": "ia", "limit": 1}).json()["items"][0]
        check(
            "revert: a settings change is marked revertible",
            entry["action"] == "settings.update" and entry["revertible"],
            entry,
        )
        r = client.post(f"/admin/audit/{entry['id']}/revert")
        check(
            "revert: the old value is back",
            r.status_code == 200 and r.json()["settings"]["retry_max"]["value"] == before_retry,
            r.text[:200],
        )
        latest = client.get("/admin/audit", params={"category": "ia", "limit": 1}).json()["items"][
            0
        ]
        check(
            "revert: logged as its own entry pointing at the reverted one",
            latest["action"] == "settings.revert" and latest["target"] == str(entry["id"]),
            latest,
        )
        check(
            "revert: reverting again changes nothing and says so",
            client.post(f"/admin/audit/{entry['id']}/revert").status_code == 422,
        )
        account_entry = client.get(
            "/admin/audit", params={"category": "comptes", "limit": 1}
        ).json()["items"][0]
        check(
            "revert: an account action cannot be reverted",
            client.post(f"/admin/audit/{account_entry['id']}/revert").status_code == 422,
        )
        check(
            "revert: an unknown entry is a 404",
            client.post("/admin/audit/999999999/revert").status_code == 404,
        )

        # --- audit -------------------------------------------------------------------------
        with session_scope() as s:
            actions = set(
                s.scalars(
                    select(AdminAuditEntry.action).where(AdminAuditEntry.admin_email == admin_email)
                ).all()
            )
        check(
            "audit: settings, account edits, suspension and queue reset are all logged",
            {"settings.update", "user.update", "user.suspend", "user.reactivate", "queue.reset"}
            <= actions,
            actions,
        )
    finally:
        with session_scope() as s:
            s.execute(delete(AppSetting))
            for key, value, by, at in saved_settings:
                # updated_at too: the console shows who changed a setting and
                # when, and a test run must not look like a change.
                s.add(AppSetting(key=key, value=value, updated_by=by, updated_at=at))
            s.execute(delete(AdminAuditEntry).where(AdminAuditEntry.admin_email == admin_email))
            s.execute(delete(User).where(User.id.in_([admin_id, student_id])))
        runtime_settings.clear_cache()

    print("\nALL PASSED" if all(results) else f"\n{results.count(False)} FAILED")


if __name__ == "__main__":
    main()
