"""Precompute the answers to the catalogue exercises.

    docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec -T backend python -m scripts.warm_answers
    docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec -T backend python -m scripts.warm_answers --chapitre 1
    docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec -T backend python -m scripts.warm_answers --status

An uploaded chapter is warmed automatically when it is published. This exists
for chapter 1, which is built in and never published, and for re-running after
prompts.py changes (bump PROMPT_VERSION first, or the stored answers still
look current).

Every call goes through the queue at a priority below both student tiers, so
running this while students are working slows nobody down - it only uses
capacity nobody was waiting for.
"""

from __future__ import annotations

import argparse
import logging
import sys

from app.llm import answer_cache
from app.routes import chapters


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chapitre", help="only this chapter (default: every available one)")
    parser.add_argument(
        "--status", action="store_true", help="report what is ready, generate nothing"
    )
    parser.add_argument("--reset", action="store_true", help="drop what is stored first")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if args.chapitre:
        wanted = [args.chapitre]
    else:
        wanted = [c.id for c in chapters.catalogue() if c.status == chapters.ACTIVE]
    if not wanted:
        print("No available chapter to warm.")
        return 0

    if args.status:
        for chapter_id in wanted:
            state = answer_cache.progress(chapter_id)
            print(f"chapter {chapter_id}: {state['ready']}/{state['total']} ready")
        return 0

    failures = 0
    for chapter_id in wanted:
        if args.reset:
            dropped = answer_cache.forget_chapter(chapter_id)
            print(f"chapter {chapter_id}: dropped {dropped} stored answer(s)")
        print(f"chapter {chapter_id}: warming…")
        result = answer_cache.warm_chapter(chapter_id)
        state = answer_cache.progress(chapter_id)
        print(
            f"chapter {chapter_id}: {result['generated']} generated, "
            f"{result['skipped']} already there, {result['failed']} failed "
            f"- {state['ready']}/{state['total']} ready"
        )
        failures += result["failed"]
    # Non-zero on any failure, so a scripted run notices rather than reporting
    # success over a chapter that is half empty.
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
