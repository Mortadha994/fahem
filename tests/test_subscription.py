"""Tests for the subscription: the plan, its end date, and the limits it buys.

Real Postgres and Redis through the real app; nothing here reaches Groq.

Covers the three places a plan decides something - the queue priority, the
request rate limit and the daily practice cap - plus the expiry rule that all
three go through, and the admin route that sets it.

    docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec -T backend python -m tests.test_subscription
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app import main as api
from app.auth import auth, password_auth
from app.core import runtime_settings
from app.core.db import session_scope
from app.core.models import (
    PLAN_FREE,
    PLAN_PAID,
    ROLE_ADMIN,
    AppSetting,
    User,
    effective_plan,
)
from app.llm import ai_control, llm_queue

results: list[bool] = []


def check(name: str, ok: bool, detail: object = "") -> None:
    results.append(bool(ok))
    print(
        ("[PASS] " if ok else "[FAIL] ")
        + name
        + (f"  -> {detail!r}" if not ok and detail != "" else "")
    )


def main() -> None:
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=30)
    past = now - timedelta(days=1)

    # --- the expiry rule, on its own ------------------------------------------------
    #
    # Pure, so it is worth pinning precisely: every limit below trusts it.
    check("effective: free stays free", effective_plan(PLAN_FREE, None) == PLAN_FREE)
    check(
        "effective: free with a date is still free (a leftover date buys nothing)",
        effective_plan(PLAN_FREE, future) == PLAN_FREE,
    )
    check(
        "effective: paid without an end date is paid",
        effective_plan(PLAN_PAID, None) == PLAN_PAID,
    )
    check(
        "effective: paid before the end date is paid",
        effective_plan(PLAN_PAID, future) == PLAN_PAID,
    )
    check(
        "effective: paid after the end date is free",
        effective_plan(PLAN_PAID, past) == PLAN_FREE,
    )
    check(
        "effective: a naive end date is read as UTC, not as local time",
        effective_plan(PLAN_PAID, past.replace(tzinfo=None)) == PLAN_FREE,
    )

    # --- the queue reads the same rule ----------------------------------------------
    check(
        "queue: a subscriber outranks a free account",
        llm_queue.priority_for(PLAN_PAID) < llm_queue.priority_for(PLAN_FREE),
    )
    check(
        "queue: a lapsed subscriber queues as free",
        llm_queue.priority_for(effective_plan(PLAN_PAID, past))
        == llm_queue.priority_for(PLAN_FREE),
    )

    run = uuid.uuid4().hex[:8]
    password = "correct-horse-battery"
    with session_scope() as s:
        saved_settings = [
            (r.key, r.value, r.updated_by, r.updated_at) for r in s.query(AppSetting).all()
        ]
        admin = User(
            email=f"sub-admin-{run}@example.com",
            display_name="Admin test",
            password_hash=password_auth.hash_password(password),
            role=ROLE_ADMIN,
        )
        free_user = User(
            email=f"sub-free-{run}@example.com",
            display_name="Élève gratuit",
            password_hash=password_auth.hash_password(password),
            niveau="2eme",
            section="informatique",
        )
        paid_user = User(
            email=f"sub-paid-{run}@example.com",
            display_name="Élève abonné",
            password_hash=password_auth.hash_password(password),
            niveau="2eme",
            section="informatique",
            plan=PLAN_PAID,
            plan_until=future,
        )
        lapsed_user = User(
            email=f"sub-lapsed-{run}@example.com",
            display_name="Élève expiré",
            password_hash=password_auth.hash_password(password),
            niveau="2eme",
            section="informatique",
            plan=PLAN_PAID,
            plan_until=past,
        )
        s.add_all([admin, free_user, paid_user, lapsed_user])
        s.flush()
        admin_id = admin.id
        free_id, paid_id, lapsed_id = free_user.id, paid_user.id, lapsed_user.id
        check("model: current_plan follows the end date", lapsed_user.current_plan == PLAN_FREE)
        check("model: current_plan is paid while it runs", paid_user.current_plan == PLAN_PAID)

    client = TestClient(api.app)

    def as_user(uid):
        client.cookies.clear()
        client.cookies.set(auth.SESSION_COOKIE_NAME, auth.create_session_token(uid))

    try:
        # --- which rate limit each account gets -------------------------------------
        for uid in (free_id, paid_id, lapsed_id):
            ai_control.forget_user_limit(uid)
        free_limit = runtime_settings.get("solve_rate_limit")
        paid_limit = runtime_settings.get("solve_rate_limit_paid")
        check(
            "settings: the subscriber limit ships larger than the free one",
            paid_limit != free_limit,
            (free_limit, paid_limit),
        )
        check(
            "limit: a free account gets the shared limit",
            ai_control.solve_rate_limit(f"user:{free_id}") == free_limit,
        )
        check(
            "limit: a subscriber gets the subscriber limit",
            ai_control.solve_rate_limit(f"user:{paid_id}") == paid_limit,
        )
        check(
            "limit: a lapsed subscriber is back on the shared limit",
            ai_control.solve_rate_limit(f"user:{lapsed_id}") == free_limit,
        )
        check(
            "limit: an unknown key falls back to the shared limit",
            ai_control.solve_rate_limit("ip:203.0.113.4") == free_limit,
        )

        # A personal limit is the escape hatch and outranks the plan.
        with session_scope() as s:
            s.get(User, paid_id).solve_rate_limit = "2/minute;7/hour"
        ai_control.forget_user_limit(paid_id)
        check(
            "limit: a personal limit wins over the subscriber limit",
            ai_control.solve_rate_limit(f"user:{paid_id}") == "2/minute;7/hour",
        )
        with session_scope() as s:
            s.get(User, paid_id).solve_rate_limit = None
        ai_control.forget_user_limit(paid_id)

        # --- the daily practice cap --------------------------------------------------
        check(
            "practice: the cap follows the plan",
            api.practice_daily_limit(PLAN_PAID) == runtime_settings.get(
                "practice_daily_limit_paid"
            )
            and api.practice_daily_limit(PLAN_FREE)
            == runtime_settings.get("practice_daily_limit"),
        )
        # Spend the free cap for one account, then check the paid cap is the
        # one that actually gates: same Redis key, higher ceiling.
        free_cap = int(runtime_settings.get("practice_daily_limit"))
        spender = uuid.uuid4()
        for _ in range(free_cap):
            api.take_practice_slot(spender, PLAN_FREE)
        check(
            "practice: a free account stops at the free cap",
            api.take_practice_slot(spender, PLAN_FREE) is False,
        )
        check(
            "practice: the same day's count keeps going under the subscriber cap",
            api.take_practice_slot(spender, PLAN_PAID) is True,
        )

        # --- the admin route ---------------------------------------------------------
        as_user(admin_id)
        response = client.patch(
            f"/admin/users/{free_id}",
            json={"plan": PLAN_PAID, "plan_until": future.isoformat()},
        )
        check("admin: setting a subscription succeeds", response.status_code == 200, response.text)
        body = response.json() if response.status_code == 200 else {}
        check("admin: the answer reports the plan", body.get("plan") == PLAN_PAID)
        check("admin: the answer reports it as running now", body.get("current_plan") == PLAN_PAID)
        check("admin: the answer carries the end date", bool(body.get("plan_until")))
        check(
            "admin: the new subscriber gets the subscriber limit at once "
            "(the cached row was dropped)",
            ai_control.solve_rate_limit(f"user:{free_id}") == paid_limit,
        )

        response = client.patch(
            f"/admin/users/{free_id}", json={"plan_until": past.isoformat()}
        )
        check(
            "admin: an end date already past is refused",
            response.status_code == 422,
            response.status_code,
        )
        response = client.patch(f"/admin/users/{free_id}", json={"plan": "platinum"})
        check("admin: an unknown plan is refused", response.status_code == 422)

        # Back to free: the end date goes with it rather than lingering.
        response = client.patch(
            f"/admin/users/{free_id}", json={"plan": PLAN_FREE, "plan_until": None}
        )
        check(
            "admin: ending a subscription puts the account back on the shared limit",
            response.status_code == 200
            and ai_control.solve_rate_limit(f"user:{free_id}") == free_limit,
        )

        # --- the settings are live, validated and visible ----------------------------
        # PUT /admin/controls takes the settings dict itself, not a wrapper:
        # an unknown key is refused, so a wrapped body would 422 for the wrong
        # reason and make the two refusal checks below pass without testing
        # anything.
        response = client.put(
            "/admin/controls", json={"solve_rate_limit_paid": "40/minute;400/hour"}
        )
        check(
            "controls: the subscriber limit can be changed",
            response.status_code == 200,
            response.text,
        )
        runtime_settings.clear_cache()
        ai_control.forget_user_limit(paid_id)
        check(
            "controls: the change reaches the subscriber",
            ai_control.solve_rate_limit(f"user:{paid_id}") == "40/minute;400/hour",
        )
        response = client.put(
            "/admin/controls", json={"solve_rate_limit_paid": "not a limit"}
        )
        check("controls: an unreadable subscriber limit is refused", response.status_code == 422)
        response = client.put("/admin/controls", json={"practice_daily_limit_paid": 0})
        check("controls: a zero daily cap is refused", response.status_code == 422)
    finally:
        with session_scope() as s:
            s.execute(delete(User).where(User.id.in_([admin_id, free_id, paid_id, lapsed_id])))
            s.execute(delete(AppSetting))
            for key, value, by, at in saved_settings:
                s.add(AppSetting(key=key, value=value, updated_by=by, updated_at=at))
        runtime_settings.clear_cache()
        for uid in (free_id, paid_id, lapsed_id):
            ai_control.forget_user_limit(uid)

    print("\nALL PASSED" if all(results) else f"\n{results.count(False)} FAILED")


if __name__ == "__main__":
    main()
