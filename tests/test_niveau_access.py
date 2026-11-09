"""A student opens the chapters of their own niveau only (app/auth/access.py).

    python -m tests.test_niveau_access            # the rule itself: no database
    docker compose ... exec backend python -m tests.test_niveau_access   # + the real routes

The second half runs the chapter routes against the database in the container
(read-only: a few GETs) with a stand-in for the signed-in user, and is skipped
when no database answers.
"""

from __future__ import annotations

from types import SimpleNamespace

from fastapi import HTTPException

from app.auth import access

failures = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global failures
    if not condition:
        failures += 1
    print(f"[{'PASS' if condition else 'FAIL'}] {label}" + (f" {detail}" if detail else ""))


def user(role="student", niveau=None, full_access=False):
    return SimpleNamespace(role=role, niveau=niveau, full_access=full_access)


def refused(u, niveau) -> bool:
    try:
        access.require_niveau(u, niveau)
    except HTTPException as exc:
        return exc.status_code == 403
    return False


def main() -> None:
    s2, s3, sb = user(niveau="2eme"), user(niveau="3eme"), user(niveau="bac")
    check("a 2ème student opens 2ème", access.can_open(s2, "2eme"))
    check("a 2ème student cannot open 3ème", not access.can_open(s2, "3eme"))
    check("a 2ème student cannot open Bac", not access.can_open(s2, "bac"))
    check("a 3ème student opens 3ème only", access.can_open(s3, "3eme") and not access.can_open(s3, "bac"))
    check("a Bac student opens Bac only", access.can_open(sb, "bac") and not access.can_open(sb, "2eme"))
    check("a refusal is a 403", refused(s2, "bac"))
    check("niveau comparison ignores case and spaces", access.can_open(s2, " 2EME "))

    admin = user(role="admin")
    test_account = user(niveau="2eme", full_access=True)
    check("an admin opens every niveau", all(access.can_open(admin, n) for n in ("2eme", "3eme", "bac")))
    check("a test account opens every niveau, whatever its own",
          all(access.can_open(test_account, n) for n in ("2eme", "3eme", "bac")))
    check("a test account with no niveau opens every niveau",
          access.can_open(user(full_access=True), "bac"))

    blank = user()
    check("a student with no profile opens nothing",
          not any(access.can_open(blank, n) for n in ("2eme", "3eme", "bac")))
    check("...and an unknown niveau is refused", not access.can_open(s2, None) and not access.can_open(s2, ""))

    check("full accounts list every niveau (None)",
          access.listing_niveau(admin) is None and access.listing_niveau(test_account) is None)
    check("a student lists their own niveau", access.listing_niveau(s3) == "3eme")
    check("a student with no profile lists a filter that matches nothing, not 'everything'",
          access.listing_niveau(blank) not in (None, "2eme", "3eme", "bac"))

    # --- the real routes -------------------------------------------------------------------
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from app.auth import auth
        from app.core.db import session_scope
        from app.routes import chapters
        from sqlalchemy import text

        with session_scope() as s:
            s.execute(text("select 1"))
    except Exception as exc:  # noqa: BLE001 - no database here: the rule above is what runs anywhere
        print(f"[SKIP] routes: no database ({type(exc).__name__})")
        print(f"\n{failures} failure(s)")
        raise SystemExit(1 if failures else 0)

    app = FastAPI()
    app.include_router(chapters.router)
    current = {"u": s2}
    app.dependency_overrides[auth.get_current_user] = lambda: current["u"]
    client = TestClient(app)

    def ids():
        return [c["id"] for c in client.get("/chapters").json()]

    published = {c.id: c.niveau for c in chapters.catalogue() if c.status == chapters.ACTIVE}
    third = next((i for i, n in published.items() if n == "3eme"), None)
    bacc = next((i for i, n in published.items() if n == "bac"), None)
    if third is None or bacc is None:
        print("[SKIP] routes: no published 3ème / Bac chapter in this database")
    else:
        current["u"] = s2
        check("2ème student: the list holds 2ème chapters only",
              ids() and all(published[i] == "2eme" for i in ids()), str(ids()))
        for label, path in (("exercises", "exercises"), ("pdf", "pdf"), ("course", "course")):
            r = client.get(f"/chapters/{third}/{path}")
            check(f"2ème student: a 3ème chapter's {label} -> 403", r.status_code == 403, str(r.status_code))
        check("2ème student: a Bac chapter's exercises -> 403", client.get(f"/chapters/{bacc}/exercises").status_code == 403)

        current["u"] = s3
        check("3ème student: the list holds 3ème chapters only",
              ids() and all(published[i] == "3eme" for i in ids()), str(ids()))
        check("3ème student: own chapter's exercises -> 200", client.get(f"/chapters/{third}/exercises").status_code == 200)
        check("3ème student: Bac chapter's exercises -> 403", client.get(f"/chapters/{bacc}/exercises").status_code == 403)

        current["u"] = blank
        check("a student with no profile: empty list", ids() == [], str(ids()))
        check("...and no chapter opens", client.get(f"/chapters/{third}/exercises").status_code == 403)

        for who, u in (("admin", admin), ("test account", test_account)):
            current["u"] = u
            seen = set(ids())
            check(f"{who}: the list holds every niveau",
                  {published[i] for i in seen if i in published} == {"2eme", "3eme", "bac"}, str(sorted(seen)))
            check(f"{who}: opens a Bac chapter", client.get(f"/chapters/{bacc}/exercises").status_code == 200)

    print(f"\n{failures} failure(s)")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
