"""Tests for the precomputed answers: the guards, the hit, and the cost of one.

Real Postgres and Redis through the real app. Groq is faked and - for the
tests that matter most - is rigged to raise if it is called at all, which is
how "a hit costs no model call" is asserted rather than assumed.

    docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec -T backend python -m tests.test_answer_cache
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app import main as api
from app.auth import auth, password_auth
from app.core.db import session_scope
from app.core.models import (
    ANSWER_MODE_FULL,
    ANSWER_MODE_GUIDED,
    ExerciseAnswer,
    User,
)
from app.llm import answer_cache, gatekeeper

results: list[bool] = []

CHAPTER = "1"
EXERCISE = "cache-test-ex"
QUESTION = "Ecrire un algorithme qui calcule le carré d'un entier saisi au clavier."
ANSWER = "## Tableau de déclaration\n\n| Objet | Nature/type |\n|---|---|\n| x | entier |\n"


def check(name: str, ok: bool, detail: object = "") -> None:
    results.append(bool(ok))
    print(
        ("[PASS] " if ok else "[FAIL] ")
        + name
        + (f"  -> {detail!r}" if not ok and detail != "" else "")
    )


def seed(question: str = QUESTION, *, mode: str = ANSWER_MODE_FULL, step: int = 0) -> None:
    answer_cache.store(
        chapter_id=CHAPTER,
        exercise_id=EXERCISE,
        mode=mode,
        step=step,
        question=question,
        built=answer_cache.CachedAnswer(
            answer=ANSWER,
            pinned=[{"id": "p1", "label": "Tableau", "section": "1", "content": "..."}],
            retrieved=[{"id": "r1", "section": "1", "type": "prose", "score": 0.9, "content": "."}],
            warnings=[],
            model="test-model",
        ),
    )


def main() -> None:
    # --- the hash ignores wrapping, not wording -----------------------------------
    check(
        "hash: reflowed whitespace is the same statement",
        answer_cache.question_hash("Ecrire  un\n algorithme")
        == answer_cache.question_hash("Ecrire un algorithme"),
    )
    check(
        "hash: different wording is a different statement",
        answer_cache.question_hash("Ecrire un algorithme")
        != answer_cache.question_hash("Ecrire deux algorithmes"),
    )

    with session_scope() as s:
        s.execute(delete(ExerciseAnswer).where(ExerciseAnswer.chapter_id == CHAPTER))

    try:
        # --- lookup and its guards -------------------------------------------------
        check(
            "lookup: nothing stored is a miss",
            answer_cache.lookup(CHAPTER, EXERCISE, ANSWER_MODE_FULL, 0, QUESTION) is None,
        )
        seed()
        hit = answer_cache.lookup(CHAPTER, EXERCISE, ANSWER_MODE_FULL, 0, QUESTION)
        check("lookup: a stored answer is found", hit is not None and hit.answer == ANSWER)
        check(
            "lookup: the grounding comes back with it",
            hit is not None and hit.pinned and hit.retrieved,
        )
        check(
            "lookup: a changed statement is a miss, not a wrong answer",
            answer_cache.lookup(
                CHAPTER, EXERCISE, ANSWER_MODE_FULL, 0, "Une toute autre question ?"
            )
            is None,
        )
        check(
            "lookup: another mode is a miss",
            answer_cache.lookup(CHAPTER, EXERCISE, ANSWER_MODE_GUIDED, 1, QUESTION) is None,
        )

        real_version = answer_cache.PROMPT_VERSION
        answer_cache.PROMPT_VERSION = f"{real_version}-moved"
        check(
            "lookup: a bumped prompt version stops old answers being served",
            answer_cache.lookup(CHAPTER, EXERCISE, ANSWER_MODE_FULL, 0, QUESTION) is None,
        )
        answer_cache.PROMPT_VERSION = real_version

        # --- progress ---------------------------------------------------------------
        state = answer_cache.progress(CHAPTER)
        check(
            "progress: counts stored answers against exercises x modes",
            state["total"] > 0 and state["ready"] >= 1,
            state,
        )

        # --- the request path --------------------------------------------------------
        run = uuid.uuid4().hex[:8]
        with session_scope() as s:
            student = User(
                email=f"cache-{run}@example.com",
                display_name="Élève test",
                password_hash=password_auth.hash_password("correct-horse-battery"),
                niveau="2eme",
                section="informatique",
            )
            s.add(student)
            s.flush()
            student_id = student.id

        client = TestClient(api.app)
        client.cookies.set(auth.SESSION_COOKIE_NAME, auth.create_session_token(student_id))

        def solve(**over):
            body = {
                "problem": QUESTION,
                "niveau": "2eme",
                "chapitre": CHAPTER,
                "exercise_id": EXERCISE,
                "mode": "full",
            }
            body.update(over)
            return client.post("/solve/stream", json=body)

        # Rigged so *any* Groq call fails loudly. A hit that quietly fell
        # through to the live path would otherwise still look like a pass.
        def explode(*a, **k):
            raise AssertionError("the cache hit reached Groq")

        def went_live(**over) -> bool:
            """Did this request fall through to the model?

            With Groq rigged to raise, a miss surfaces either as the
            AssertionError escaping the stream or as its text in the body,
            depending on whether the frame had been flushed yet. Both mean the
            same thing, and a hit produces neither.
            """
            try:
                return "reached Groq" in solve(**over).text
            except AssertionError as exc:
                return "reached Groq" in str(exc)

        real_classify_steps = gatekeeper.classify_steps
        real_stream = api.stream_groq
        gatekeeper.classify_steps = explode
        api.stream_groq = explode
        try:
            response = solve()
            body = response.text
            check("route: a cached exercise answers 200", response.status_code == 200)
            check("route: the stored answer is what streams", ANSWER[:24] in body, body[:200])
            check("route: no Groq call was made", "reached Groq" not in body)
            check("route: the grounding rides along", '"pinned"' in body and '"p1"' in body)

            # A second message in the same discussion carries memory the stored
            # answer never saw, so it must not be served from the cache.
            check(
                "route: a follow-up goes to the model, not to the cache",
                went_live(history=[{"role": "user", "content": "et avec deux nombres ?"}]),
            )
            # The exercise id is not enough on its own: the statement has to
            # hash equal to the one the answer was generated from.
            check(
                "route: a different statement under the same id goes to the model",
                went_live(problem="Ecrire un algorithme qui trie un tableau."),
            )
            # Guided step 1 is cached separately; nothing is stored for it here.
            check(
                "route: guided misses while only the full answer is stored",
                went_live(mode="guided"),
            )
        finally:
            gatekeeper.classify_steps = real_classify_steps
            api.stream_groq = real_stream

        # --- forget ------------------------------------------------------------------
        dropped = answer_cache.forget_chapter(CHAPTER)
        check("forget: the chapter's answers go", dropped >= 1)
        check(
            "forget: and the lookup misses afterwards",
            answer_cache.lookup(CHAPTER, EXERCISE, ANSWER_MODE_FULL, 0, QUESTION) is None,
        )
    finally:
        with session_scope() as s:
            s.execute(delete(ExerciseAnswer).where(ExerciseAnswer.chapter_id == CHAPTER))
            s.execute(delete(User).where(User.email.like("cache-%@example.com")))

    print("\nALL PASSED" if all(results) else f"\n{results.count(False)} FAILED")


if __name__ == "__main__":
    main()
