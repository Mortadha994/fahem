"""Tests for app/routes/public_overview.py: what the landing page is told.

Real Postgres (the published chapters) and Qdrant (the extract counts); the
catalogue is whatever this stack has published, so the checks compare the
overview against the same sources rather than hard-coding today's numbers.

    docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec -T backend python -m tests.test_public_overview
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.rag import chapter_store
from app.routes import chapters
from app.routes import public_overview as po

results: list[bool] = []


def check(name: str, ok: bool, detail: object = "") -> None:
    results.append(bool(ok))
    print(
        ("[PASS] " if ok else "[FAIL] ")
        + name
        + (f"  -> {detail!r}" if not ok and detail != "" else "")
    )


def main() -> None:
    # --- topics ------------------------------------------------------------------
    check(
        "split_topics: commas inside parentheses stay",
        po.split_topics("Si (simple choix, double choix), Si imbriqués, Selon")
        == ["Si (simple choix, double choix)", "Si imbriqués", "Selon"],
    )
    check("split_topics: empty text gives no topics", po.split_topics("  ") == [])

    # --- the overview matches its sources -----------------------------------------
    po.clear_cache()
    overview = po.build_overview()
    catalogue = chapters.catalogue()
    check(
        "chapters: every catalogue chapter, in catalogue order",
        [c.id for c in overview.chapters] == [c.id for c in catalogue],
    )
    for card in overview.chapters:
        upload = chapter_store.published_chapter(card.id)
        if card.status == chapters.ACTIVE and upload is not None and card.id not in ("1",):
            check(
                f"chapter {card.id}: exercise count is the published snapshot's",
                card.exercises == len(upload.published_exercises or []),
                (card.exercises, len(upload.published_exercises or [])),
            )
        if card.status != chapters.ACTIVE:
            check(
                f"chapter {card.id}: an announced chapter claims no exercises or extracts",
                card.exercises == 0 and card.excerpts is None,
            )
    ready = [c for c in overview.chapters if c.status == chapters.ACTIVE]
    check(
        "totals: available/coming add up",
        overview.totals.chapters_available == len(ready)
        and overview.totals.chapters_coming == len(overview.chapters) - len(ready),
    )
    check(
        "totals: exercises are the sum over available chapters",
        overview.totals.exercises == sum(c.exercises for c in ready),
    )
    check(
        "totals: niveaux are those of available chapters",
        set(overview.totals.niveaux) == {c.niveau_label for c in ready},
    )

    # --- cache ------------------------------------------------------------------------
    po.clear_cache()
    first = po.cached_overview(now=1000.0)
    check(
        "cache: a second read within the window is the same object",
        po.cached_overview(now=1030.0) is first,
    )
    check(
        "cache: after the window it is rebuilt",
        po.cached_overview(now=1000.0 + po.CACHE_SECONDS + 1) is not first,
    )

    # --- the route: public, cacheable, no student data ---------------------------------
    app = FastAPI()
    app.include_router(po.router)
    response = TestClient(app).get("/public/overview")
    check("route: 200 without any session", response.status_code == 200, response.status_code)
    check(
        "route: cacheable by the browser",
        response.headers.get("cache-control") == f"public, max-age={int(po.CACHE_SECONDS)}",
    )
    body = response.text.lower()
    check(
        "route: nothing about accounts or students",
        not any(word in body for word in ("email", "user", "student", "élève")),
    )

    print("\nALL PASSED" if all(results) else f"\n{results.count(False)} FAILED")


if __name__ == "__main__":
    main()
