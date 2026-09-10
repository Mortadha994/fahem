"""Chapter catalogue, exercises and the lesson PDF.

Phase 3a, backend only - nothing in ui/ consumes these yet; a follow-up phase
wires the routing and screens, the same split Phase 0c and Phase 1 used.

All three routes require a signed-in user. The PDF one especially: it is
served through an authenticated endpoint rather than as a static file, so
there is no URL that reaches the document without a session. nginx serves
only the built bundle, and data/ is in .dockerignore, so the PDF is not in
the frontend image at all - the mounted copy on the backend is the only one.

Why the catalogue is a Python constant and not a JSON file: there are three
entries, exactly one of which is real, and nothing edits them at runtime. A
constant gets linted and formatted with the rest of the code, and - the part
that actually matters - it can carry a comment saying *why* a chapter is
coming_soon. A JSON file cannot, and the honest reason a chapter is not
available is worth writing down next to the claim.

Deliberately NOT built here: chapter CRUD, a chapters table, per-chapter
config files. One real chapter does not justify a management system; that is
the same call the project made choosing Qdrant over pgvector on the merits
rather than defaulting into infrastructure it did not need yet.

Deliberately NOT rate-limited: Phase 2's limiter exists to cap Groq spend,
and none of these endpoints reach a model. Metering a JSON list against the
same budget as a generation would let a student browsing chapters lock
themselves out of solving.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

import auth
import models
from config import DEFAULT_PROBLEMS, LESSON_PDF_PATH

ACTIVE = "active"
COMING_SOON = "coming_soon"


class Chapter(BaseModel):
    id: str
    title: str
    niveau: str
    status: str


class Exercise(BaseModel):
    id: str
    question: str


# The catalogue. Only chapter 1 has a corpus behind it - chunks.json holds
# 117 chunks, all niveau=2eme chapitre=1, and the pinned syntax tables in
# context.py are chapter-1 tables specifically. The other two are listed so
# the eventual UI can say "à venir" honestly instead of implying the app
# covers more of the programme than it does; a silently short list would read
# as "this is everything there is".
CHAPTERS: tuple[Chapter, ...] = (
    Chapter(
        id="1",
        title="Les structures de données et les structures simples",
        niveau="2eme",
        status=ACTIVE,
    ),
    Chapter(
        id="2",
        title="Les structures de contrôle conditionnelles",
        niveau="2eme",
        status=COMING_SOON,
    ),
    Chapter(
        id="3",
        title="Les structures de contrôle itératives",
        niveau="2eme",
        status=COMING_SOON,
    ),
)

_BY_ID = {c.id: c for c in CHAPTERS}


def _active_or_404(chapter_id: str) -> Chapter:
    """Resolve a chapter that actually has content, or raise 404.

    An unknown id and a coming_soon chapter both 404, and deliberately with
    the same body: from the caller's side "chapter 9 does not exist" and
    "chapter 2 has nothing in it yet" are the same outcome - there is nothing
    to fetch - and one message covers both without the endpoint pretending to
    know which the caller meant.

    This lookup is also what keeps the PDF route safe: chapter_id is only ever
    used as a dict key, never joined onto a filesystem path, so no value of it
    can traverse out of data/. The served path comes from config, not the URL.
    """
    chapter = _BY_ID.get(chapter_id)
    if chapter is None or chapter.status != ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no content available for chapter {chapter_id!r}",
        )
    return chapter


def load_exercises(chapter_id: str) -> list[Exercise]:
    """Exercises for a chapter, read from sample_problems.json.

    That file is the single source - its entries are already the regression
    baseline the retrieval checks run against, so duplicating them into a
    second catalogue would create two truths that drift.

    Its real shape is a flat list of {id, niveau, chapitre, question}. Only id
    and question are exposed: niveau/chapitre are scoping keys the caller
    already knows from the chapter it asked for, and echoing them back would
    invite a client to treat them as per-exercise settings rather than as the
    chapter's.
    """
    if not DEFAULT_PROBLEMS.exists():
        # Bind-mounted, not baked into the image, so a missing mount is a
        # deployment fault rather than a bad request - say so rather than
        # returning an empty list that reads like "this chapter has none".
        raise HTTPException(
            status_code=503,
            detail="exercise catalogue is unavailable",
        )

    raw: Any = json.loads(DEFAULT_PROBLEMS.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        raw = raw.get("problems", [])

    wanted = str(chapter_id).strip().lower()
    return [
        Exercise(id=str(p["id"]), question=str(p["question"]))
        for p in raw
        if str(p.get("chapitre", "")).strip().lower() == wanted
        and p.get("id")
        and p.get("question")
    ]


router = APIRouter(prefix="/chapters", tags=["chapters"])


@router.get("", response_model=list[Chapter])
def list_chapters(user: models.User = Depends(auth.get_current_user)) -> list[Chapter]:
    """Every chapter, real and planned, with its status."""
    return list(CHAPTERS)


@router.get("/{chapter_id}/exercises", response_model=list[Exercise])
def list_exercises(
    chapter_id: str,
    user: models.User = Depends(auth.get_current_user),
) -> list[Exercise]:
    """Exercises for one active chapter."""
    _active_or_404(chapter_id)
    return load_exercises(chapter_id)


@router.get("/{chapter_id}/pdf")
def chapter_pdf(
    chapter_id: str,
    user: models.User = Depends(auth.get_current_user),
) -> FileResponse:
    """Stream the lesson PDF for an active chapter.

    inline rather than attachment: this is meant to open in the browser's
    viewer next to the chat, not land in the downloads folder. FileResponse
    defaults to attachment once a filename is set, so the disposition is
    stated explicitly.
    """
    _active_or_404(chapter_id)

    if not LESSON_PDF_PATH.exists():
        # Same reasoning as the exercises catalogue: the file arrives by bind
        # mount, so its absence is a misconfigured deployment, not a 404 about
        # the chapter - which would wrongly tell the caller the chapter is
        # empty.
        raise HTTPException(
            status_code=503,
            detail="lesson document is unavailable",
        )

    return FileResponse(
        LESSON_PDF_PATH,
        media_type="application/pdf",
        filename=f"fahem-chapitre-{chapter_id}.pdf",
        content_disposition_type="inline",
    )
