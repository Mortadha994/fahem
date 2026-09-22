"""Answers to catalogue exercises, generated once and served from Postgres.

A student who clicks an exercise from the chapter page asks a question Fahem
has already been asked - the statement is fixed, the chapter is fixed, and the
answer does not depend on who is asking. Generating those answers ahead of
time and serving them from `exercise_answers` means such a request makes **no
Groq call at all**: no queue, no 429, no tokens against the daily budget, and
no wait before the first word.

  lookup(...)        the read path, called from /solve/stream before the
                     gatekeeper - so a hit skips even the classification.
  warm_chapter(...)  the write path, an admin-triggered background job.
  progress(...)      how much of a chapter is ready, for the console.

What is cached, and what deliberately is not
--------------------------------------------
Only answers whose whole input is the statement:

  full        « La solution »
  guided 1    « Mode guidé », the first step

« Vérifier ma réponse » is never cached - it answers what the student wrote.
Guided steps 2-4 are not cached either, and that is a real limit rather than
an oversight: step 3 is written knowing what steps 1 and 2 said, so caching it
in isolation would produce a step that does not follow from the ones the
student actually read. Serving those faithfully means storing the chain and
checking the discussion matches it, which is worth doing separately.

Staleness
---------
Two guards, both checked on every read, and a miss on either falls through to
the live pipeline. That direction is deliberate: a stale answer is worse than
a slow one, because it is confidently wrong about a question nobody asked.

  question_hash   the statement this was generated from. Chapter 1's
                  statements live in sample_problems.json, which is gitignored
                  and bind-mounted, so it can change with no publish to react
                  to; the hash notices anyway.
  prompt_version  bumped by hand when prompts.py changes what an answer looks
                  like, so old answers stop being served rather than becoming
                  a second voice beside the new ones.

Generation never competes with a student. It runs at WARM_PRIORITY, which is
below both the paid and the free tier in llm_queue, so a warm-up can only ever
use capacity nobody is waiting for.
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from typing import Any

from sqlalchemy import delete, func, select

from app.core.db import session_scope
from app.core.models import (
    ANSWER_MODE_FULL,
    ANSWER_MODE_GUIDED,
    ExerciseAnswer,
    niveau_label,
)
from app.grading import algo_notation
from app.grading.checker import check_constraints
from app.llm import llm_queue
from app.llm.generate import GROQ_MODEL, generate, pick_backend
from app.llm.prompts import build_messages
from app.rag.context import build_context

log = logging.getLogger("fahem.answer_cache")

# Bump when prompts.py changes the shape of an answer. Stored on every row, so
# answers written by an older prompt stop being served the moment this moves
# rather than lingering next to newly generated ones.
PROMPT_VERSION = "1"

# Strictly larger than any student priority (paid 0, free 1), so a warm-up
# waits behind every real request. A precompute job that made a student wait
# would defeat the point of the feature.
WARM_PRIORITY = 2

# What gets generated for one exercise: (mode, step).
WARM_TARGETS: tuple[tuple[str, int], ...] = (
    (ANSWER_MODE_FULL, 0),
    (ANSWER_MODE_GUIDED, 1),
)

# One deadline per generated answer. Generous compared with a student's, since
# nobody is watching, but finite so a stuck job ends.
WARM_TIMEOUT_SECONDS = 300.0


def question_hash(question: str) -> str:
    """sha256 of the statement, whitespace-normalised.

    Normalised because the same statement reaches us with different wrapping
    depending on where it was read from - the JSON file, a publish snapshot,
    the chat - and a reflowed line is not a different exercise.
    """
    return hashlib.sha256(" ".join((question or "").split()).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CachedAnswer:
    """A hit, in the shape /solve/stream needs to replay it."""

    answer: str
    pinned: list[dict[str, Any]]
    retrieved: list[dict[str, Any]]
    warnings: list[str]
    model: str


def lookup(
    chapter_id: str, exercise_id: str, mode: str, step: int, question: str
) -> CachedAnswer | None:
    """The stored answer for this exercise, or None to take the live path.

    None on anything unexpected, including a database that cannot be read: the
    cache is an optimisation, and losing it must slow Fahem down rather than
    break it.
    """
    if not chapter_id or not exercise_id:
        return None
    wanted = question_hash(question)
    try:
        with session_scope() as s:
            row = s.get(ExerciseAnswer, (chapter_id, exercise_id, mode, int(step)))
            if row is None:
                return None
            if row.question_hash != wanted:
                log.info(
                    "answer cache: %s/%s %s step %s is for a different statement, ignoring",
                    chapter_id,
                    exercise_id,
                    mode,
                    step,
                )
                return None
            if row.prompt_version != PROMPT_VERSION:
                return None
            return CachedAnswer(
                answer=row.answer,
                pinned=list(row.pinned or []),
                retrieved=list(row.retrieved or []),
                warnings=list(row.warnings or []),
                model=row.model,
            )
    except Exception:
        log.warning("answer cache unavailable; falling back to the live path", exc_info=True)
        return None


def _generate_one(
    *, question: str, niveau: str, chapter_id: str, mode: str, step: int
) -> CachedAnswer:
    """One answer, through the same pipeline a live request uses.

    Deliberately the same calls in the same order as /solve - build_context,
    build_messages, generate, normalize_answer, check_constraints - so a
    cached answer cannot drift into being a different kind of answer than the
    one a student would have got.

    No `profile` is passed: a stored answer is read by every student, so the
    per-student tone note has nothing to key on. That is the one thing a hit
    gives up.
    """
    context = build_context(question, niveau=niveau, chapitre=chapter_id, k=5)
    if not context.pinned:
        raise RuntimeError(f"no pinned syntax core for niveau={niveau} chapitre={chapter_id}")
    rendered = context.render()
    messages = build_messages(
        context=rendered,
        query=question,
        niveau=niveau_label(niveau),
        chapitre=chapter_id,
        kind="GUIDED" if mode == ANSWER_MODE_GUIDED else "PROBLEM",
        step=step or None,
        exercise=question if mode == ANSWER_MODE_GUIDED else None,
    )
    budget = llm_queue.WaitBudget(WARM_TIMEOUT_SECONDS)
    answer = generate(messages, pick_backend(None), priority=WARM_PRIORITY, budget=budget)
    answer, fixed = algo_notation.normalize_answer(answer)
    if fixed:
        log.info("answer cache: rewrote %d Python operator(s) for %s", fixed, question[:40])
    warnings, _ = check_constraints(answer, rendered)
    return CachedAnswer(
        answer=answer,
        pinned=[
            {"id": p.chunk_id, "label": p.label, "section": p.section, "content": p.content}
            for p in context.pinned
        ],
        retrieved=[
            {
                "id": h.chunk_id,
                "section": h.section,
                "type": h.type,
                "score": round(h.score, 4),
                "content": h.content,
            }
            for h in context.retrieved
        ],
        warnings=warnings,
        model=GROQ_MODEL,
    )


def store(
    *, chapter_id: str, exercise_id: str, mode: str, step: int, question: str, built: CachedAnswer
) -> None:
    with session_scope() as s:
        s.merge(
            ExerciseAnswer(
                chapter_id=chapter_id,
                exercise_id=exercise_id,
                mode=mode,
                step=int(step),
                answer=built.answer,
                pinned=built.pinned,
                retrieved=built.retrieved,
                warnings=built.warnings,
                question_hash=question_hash(question),
                prompt_version=PROMPT_VERSION,
                model=built.model,
            )
        )


def _exercises(chapter_id: str) -> list[tuple[str, str]]:
    """(exercise id, statement) for a chapter, from whichever source has it.

    Imported here rather than at module scope: app.routes.chapters reaches
    into the chapter store, and importing it eagerly would tie this module to
    the HTTP layer it is meant to run without.
    """
    from app.routes import chapters

    return [(e.id, e.question) for e in chapters.load_exercises(chapter_id)]


def _niveau_of(chapter_id: str) -> str:
    from app.routes import chapters

    for chapter in chapters.catalogue():
        if chapter.id == chapter_id:
            return chapter.niveau
    return "2eme"


def progress(chapter_id: str) -> dict[str, int]:
    """How many of a chapter's answers are ready, for the console.

    Derived by counting rows rather than tracked in a job table: a count
    cannot disagree with reality, and it needs no row for chapter 1, which has
    no record in `chapters` to hang a status on.
    """
    total = len(_exercises(chapter_id)) * len(WARM_TARGETS)
    try:
        with session_scope() as s:
            ready = int(
                s.scalar(
                    select(func.count())
                    .select_from(ExerciseAnswer)
                    .where(
                        ExerciseAnswer.chapter_id == chapter_id,
                        ExerciseAnswer.prompt_version == PROMPT_VERSION,
                    )
                )
                or 0
            )
    except Exception:
        log.warning("could not count cached answers for %s", chapter_id, exc_info=True)
        ready = 0
    return {"ready": min(ready, total), "total": total}


def forget_chapter(chapter_id: str) -> int:
    """Drop a chapter's cached answers. Used when its exercises change."""
    with session_scope() as s:
        result = s.execute(
            delete(ExerciseAnswer).where(ExerciseAnswer.chapter_id == chapter_id)
        )
        return int(result.rowcount or 0)


def warm_chapter(chapter_id: str) -> dict[str, int]:
    """Generate every missing or stale answer for one chapter.

    Idempotent: it looks each target up first and skips the ones already
    stored against the current statement and prompt, so a run interrupted by a
    restart resumes instead of starting over - which matters, because these
    are the expensive calls this whole module exists to avoid repeating.

    One failure does not end the run. A chapter with one unanswerable exercise
    should still get the other eighteen.
    """
    niveau = _niveau_of(chapter_id)
    exercises = _exercises(chapter_id)
    done = skipped = failed = 0
    started = time.monotonic()
    for exercise_id, question in exercises:
        for mode, step in WARM_TARGETS:
            if lookup(chapter_id, exercise_id, mode, step, question) is not None:
                skipped += 1
                continue
            try:
                built = _generate_one(
                    question=question,
                    niveau=niveau,
                    chapter_id=chapter_id,
                    mode=mode,
                    step=step,
                )
                store(
                    chapter_id=chapter_id,
                    exercise_id=exercise_id,
                    mode=mode,
                    step=step,
                    question=question,
                    built=built,
                )
                done += 1
            except Exception:
                failed += 1
                log.warning(
                    "answer cache: could not generate %s/%s %s step %s",
                    chapter_id,
                    exercise_id,
                    mode,
                    step,
                    exc_info=True,
                )
    log.info(
        "answer cache: chapter %s warmed in %.1fs - %d generated, %d already there, %d failed",
        chapter_id,
        time.monotonic() - started,
        done,
        skipped,
        failed,
    )
    return {"generated": done, "skipped": skipped, "failed": failed}
