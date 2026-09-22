"""Admin routes for uploaded chapters (Phase 9): upload, review, publish.

Same rule as app/routes/admin/admin.py: get_current_admin is declared once on the router, and
tests/test_chapters_admin.py asserts every route inherits it.

The PDF arrives as the raw request body (Content-Type: application/pdf) with
the chapter number and title in the query string, rather than as
multipart/form-data. FastAPI's multipart parsing needs python-multipart, which
nothing else in the backend uses; one file per request does not justify the
dependency.

Every edit is refused (409) while a chapter is processing or publishing: those
background tasks replace or read the draft rows, and an edit racing them would
be silently lost or half-published.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.auth import auth
from app.core.config import MAX_CHAPTER_PDF_BYTES
from app.core.db import session_scope
from app.core.models import (
    CHAPTER_PROCESSING,
    CHAPTER_PUBLISHING,
    ChapterChunk,
    ChapterExercise,
    UploadedChapter,
)
from app.llm import answer_cache
from app.rag import chapter_store as cs
from app.rag import course_markdown

router = APIRouter(
    prefix="/admin/chapters",
    tags=["admin"],
    dependencies=[Depends(auth.get_current_admin)],
)

_CHAPTER_ID = re.compile(r"^[0-9]{1,3}$")
_BUSY = (CHAPTER_PROCESSING, CHAPTER_PUBLISHING)


# --- schemas ------------------------------------------------------------------------


class AnswerCacheState(BaseModel):
    """How much of a chapter is precomputed. `total` is exercises × the modes
    the cache covers, so "12 / 38" reads as an amount of work left rather than
    a number needing explanation."""

    ready: int
    total: int


class ChapterSummary(BaseModel):
    id: str
    niveau: str
    title: str
    status: str
    error: str | None
    source_filename: str
    source_kind: str = "pdf"
    has_document: bool = False
    published_at: datetime | None
    has_unpublished_changes: bool
    updated_at: datetime
    chunk_count: int = 0
    flagged_count: int = 0
    pinned_count: int = 0
    exercise_count: int = 0


class ChunkOut(BaseModel):
    id: uuid.UUID
    position: int
    content: str
    section: str
    type: str
    format: str
    page: int | None
    pinned: bool
    pin_label: str | None
    flags: list[str]


class ExerciseOut(BaseModel):
    id: uuid.UUID
    position: int
    title: str
    question: str


class ChapterDetail(ChapterSummary):
    topics: str
    chunks: list[ChunkOut]
    exercises: list[ExerciseOut]
    publish_problems: list[str]


class ChapterUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    topics: str | None = Field(default=None, max_length=2000)


class ChunkUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1)
    section: str | None = Field(default=None, max_length=200)
    type: str | None = Field(default=None, pattern="^(prose|table|exercice)$")
    pinned: bool | None = None
    pin_label: str | None = Field(default=None, max_length=200)


class ExerciseIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    question: str = Field(min_length=1)


class ExerciseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    question: str | None = Field(default=None, min_length=1)


# --- helpers ----------------------------------------------------------------------------


def _valid_id(chapter_id: str) -> str:
    if not _CHAPTER_ID.match(chapter_id):
        raise HTTPException(status_code=422, detail="Le numéro de chapitre doit être un nombre (1 à 3 chiffres).")
    if chapter_id == cs.BUILTIN_CHAPTER_ID:
        raise HTTPException(
            status_code=409,
            detail="Le chapitre 1 est intégré à Fahem et ne peut pas être remplacé par un envoi.",
        )
    return chapter_id


def _get(session, chapter_id: str) -> UploadedChapter:
    row = session.get(UploadedChapter, chapter_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Chapitre introuvable.")
    return row


def _editable(session, chapter_id: str) -> UploadedChapter:
    row = _get(session, chapter_id)
    if row.status in _BUSY:
        raise HTTPException(
            status_code=409,
            detail="Le chapitre est en cours de traitement ; réessaie quand il sera terminé.",
        )
    return row


async def _read_body(request: Request) -> bytes:
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > MAX_CHAPTER_PDF_BYTES:
        raise HTTPException(status_code=413, detail="Le fichier est trop volumineux.")
    data = await request.body()
    if len(data) > MAX_CHAPTER_PDF_BYTES:
        raise HTTPException(status_code=413, detail="Le fichier est trop volumineux.")
    return data


async def _read_pdf(request: Request) -> bytes:
    data = await _read_body(request)
    # The magic bytes, not the Content-Type header or the filename: both are
    # whatever the client says.
    if not data.startswith(cs.PDF_MAGIC):
        raise HTTPException(status_code=415, detail="Le fichier envoyé n'est pas un PDF.")
    return data


async def _read_source(
    request: Request, filename: str, chapter_id: str
) -> tuple[str, bytes, course_markdown.ParsedCourse | None]:
    """A chapter source: a PDF, or a Markdown course (Phase 9b).

    A PDF is recognised by its magic bytes. Anything else must be a .md file
    that decodes as UTF-8 and follows the template - and it is parsed right
    here, so a malformed course is refused with its line-numbered problems
    before anything is stored, instead of failing later in the background.
    """
    data = await _read_body(request)
    if data.startswith(cs.PDF_MAGIC):
        return "pdf", data, None
    if not filename.lower().endswith((".md", ".markdown")):
        raise HTTPException(
            status_code=415, detail="Envoie un PDF ou un cours Markdown (.md)."
        )
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=415, detail="Le fichier .md doit être encodé en UTF-8.")
    try:
        course = course_markdown.parse(text, chapter_id)
    except course_markdown.ParseError as exc:
        raise HTTPException(
            status_code=422,
            detail={"message": "Le cours ne respecte pas le modèle.", "problems": exc.problems},
        )
    return "markdown", data, course


def _summary(row: UploadedChapter, **counts) -> dict:
    return {
        "id": row.id,
        "niveau": row.niveau,
        "title": row.title,
        "status": row.status,
        "error": row.error,
        "source_filename": row.source_filename,
        "source_kind": row.source_kind,
        "has_document": cs.pdf_path(row.id).exists(),
        "published_at": row.published_at,
        "has_unpublished_changes": row.has_unpublished_changes,
        "updated_at": row.updated_at,
        **counts,
    }


def _detail(chapter_id: str) -> ChapterDetail:
    with session_scope() as s:
        row = _get(s, chapter_id)
        chunks = [
            ChunkOut(
                id=c.id,
                position=c.position,
                content=c.content,
                section=c.section,
                type=c.type,
                format=c.format,
                page=c.page,
                pinned=c.pinned,
                pin_label=c.pin_label,
                flags=cs.review_flags(c.content, c.type),
            )
            for c in row.chunks
        ]
        exercises = [ExerciseOut(id=e.id, position=e.position, title=e.title, question=e.question) for e in row.exercises]
        base = _summary(
            row,
            chunk_count=len(chunks),
            flagged_count=sum(1 for c in chunks if c.flags),
            pinned_count=sum(1 for c in chunks if c.pinned),
            exercise_count=len(exercises),
        )
        topics = row.topics
    return ChapterDetail(
        **base,
        topics=topics,
        chunks=chunks,
        exercises=exercises,
        publish_problems=cs.publish_problems(chapter_id),
    )


def _touch(session, row: UploadedChapter) -> None:
    cs.mark_changed(session, row)
    row.updated_at = func.now()


# --- chapters ------------------------------------------------------------------------------


@router.get("", response_model=list[ChapterSummary])
def list_chapters() -> list[ChapterSummary]:
    with session_scope() as s:
        rows = s.scalars(select(UploadedChapter).order_by(UploadedChapter.id)).all()
        out = []
        for row in rows:
            chunks = row.chunks
            out.append(
                ChapterSummary(
                    **_summary(
                        row,
                        chunk_count=len(chunks),
                        flagged_count=sum(1 for c in chunks if cs.review_flags(c.content, c.type)),
                        pinned_count=sum(1 for c in chunks if c.pinned),
                        exercise_count=len(row.exercises),
                    )
                )
            )
    return out


@router.post("", response_model=ChapterSummary, status_code=status.HTTP_202_ACCEPTED)
async def upload_chapter(
    request: Request,
    background: BackgroundTasks,
    id: str = Query(..., description="chapter number, e.g. 2"),
    title: str | None = Query(None, max_length=200, description="required for a PDF"),
    filename: str = Query("chapitre.pdf", max_length=255),
) -> ChapterSummary:
    """Create a chapter from a PDF or a Markdown course; import in the background."""
    chapter_id = _valid_id(id.strip())
    kind, data, course = await _read_source(request, filename, chapter_id)
    # A Markdown course carries its own title in the header.
    final_title = course.titre if course else (title or "").strip()
    if not final_title:
        raise HTTPException(status_code=422, detail="Le titre du chapitre est requis.")

    with session_scope() as s:
        if s.get(UploadedChapter, chapter_id) is not None:
            raise HTTPException(
                status_code=409,
                detail=f"Le chapitre {chapter_id} existe déjà. Ouvre-le pour renvoyer le fichier.",
            )
        row = UploadedChapter(
            id=chapter_id,
            niveau="2eme",
            title=final_title,
            topics=course.notions if course else "",
            status=CHAPTER_PROCESSING,
            source_filename=filename,
            source_kind=kind,
        )
        s.add(row)
        s.flush()
        (cs.store_markdown if kind == "markdown" else cs.store_pdf)(chapter_id, data)
        summary = ChapterSummary(**_summary(row))

    background.add_task(cs.process_upload, chapter_id)
    return summary


@router.put("/{chapter_id}/source", response_model=ChapterSummary, status_code=status.HTTP_202_ACCEPTED)
async def replace_source(
    chapter_id: str,
    request: Request,
    background: BackgroundTasks,
    filename: str = Query("chapitre.pdf", max_length=255),
) -> ChapterSummary:
    """Upload a corrected source (PDF or .md): re-imports into a fresh draft.
    A published chapter stays live on its current snapshot until republished."""
    _valid_id(chapter_id)
    kind, data, _course = await _read_source(request, filename, chapter_id)
    with session_scope() as s:
        row = _editable(s, chapter_id)
        (cs.store_markdown if kind == "markdown" else cs.store_pdf)(chapter_id, data)
        row.source_filename = filename
        row.source_kind = kind
        row.status = CHAPTER_PROCESSING
        row.error = None
        summary = ChapterSummary(**_summary(row))
    background.add_task(cs.process_upload, chapter_id)
    return summary


@router.put("/{chapter_id}/document", response_model=ChapterSummary)
async def replace_document(chapter_id: str, request: Request) -> ChapterSummary:
    """The PDF students open on the chapter page, for a Markdown chapter.

    No re-import: the course content comes from the .md, this is only the
    document shown next to it. (For a PDF chapter the source is the document,
    so this simply replaces what students see without touching the draft.)
    """
    _valid_id(chapter_id)
    data = await _read_pdf(request)
    with session_scope() as s:
        row = _get(s, chapter_id)
        cs.store_pdf(chapter_id, data)
        return ChapterSummary(**_summary(row))


@router.get("/{chapter_id}", response_model=ChapterDetail)
def read_chapter(chapter_id: str) -> ChapterDetail:
    return _detail(chapter_id)


@router.get("/{chapter_id}/pdf")
def read_pdf(chapter_id: str) -> FileResponse:
    with session_scope() as s:
        _get(s, chapter_id)
    path = cs.pdf_path(chapter_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="PDF introuvable.")
    return FileResponse(path, media_type="application/pdf", content_disposition_type="inline")


@router.patch("/{chapter_id}", response_model=ChapterDetail)
def update_chapter(chapter_id: str, payload: ChapterUpdate) -> ChapterDetail:
    with session_scope() as s:
        row = _editable(s, chapter_id)
        if payload.title is not None:
            row.title = payload.title.strip()
        if payload.topics is not None:
            row.topics = payload.topics.strip()
        _touch(s, row)
    return _detail(chapter_id)


@router.delete("/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chapter(chapter_id: str) -> None:
    with session_scope() as s:
        _editable(s, chapter_id)
    cs.delete_chapter(chapter_id)


@router.post("/{chapter_id}/publish", response_model=ChapterSummary, status_code=status.HTTP_202_ACCEPTED)
def publish_chapter(chapter_id: str, background: BackgroundTasks) -> ChapterSummary:
    with session_scope() as s:
        _get(s, chapter_id)
    problems = cs.publish_problems(chapter_id)
    if problems:
        raise HTTPException(status_code=409, detail={"message": "Publication impossible.", "problems": problems})
    if not cs.begin_publish(chapter_id):
        raise HTTPException(status_code=409, detail="Une publication est déjà en cours.")
    background.add_task(cs.publish, chapter_id)
    # The exercises the students will see are about to change, so whatever was
    # cached for this chapter answers the previous ones. Dropped rather than
    # left to the statement hash: the hash would catch a changed exercise, but
    # a *removed* one would keep its answer in the table forever.
    background.add_task(answer_cache.forget_chapter, chapter_id)
    # Then fill it again, in the background, at a priority below every
    # student - see app/llm/answer_cache.py. Queued after publish so it reads
    # the new snapshot, and harmless if it fails: a missing answer is a live
    # request, not an error.
    background.add_task(answer_cache.warm_chapter, chapter_id)
    with session_scope() as s:
        return ChapterSummary(**_summary(_get(s, chapter_id)))


@router.get("/{chapter_id}/answers", response_model=AnswerCacheState)
def answer_cache_state(chapter_id: str) -> AnswerCacheState:
    """How many of this chapter's answers are precomputed."""
    return AnswerCacheState(**answer_cache.progress(chapter_id))


@router.post("/{chapter_id}/answers", response_model=AnswerCacheState, status_code=status.HTTP_202_ACCEPTED)
def warm_answers(chapter_id: str, background: BackgroundTasks) -> AnswerCacheState:
    """Generate the answers this chapter is still missing.

    Idempotent, so pressing it twice costs nothing the second time: the job
    looks each answer up before generating it. Returns the state as it is
    now - the count rises as the job works, and the console re-reads it.
    """
    background.add_task(answer_cache.warm_chapter, chapter_id)
    return AnswerCacheState(**answer_cache.progress(chapter_id))


@router.post("/{chapter_id}/unpublish", response_model=ChapterDetail)
def unpublish_chapter(chapter_id: str) -> ChapterDetail:
    with session_scope() as s:
        row = _editable(s, chapter_id)
        if row.published_at is None:
            raise HTTPException(status_code=409, detail="Ce chapitre n'est pas publié.")
    cs.unpublish(chapter_id)
    return _detail(chapter_id)


# --- chunks ----------------------------------------------------------------------------------


def _chunk(session, chapter_id: str, chunk_id: uuid.UUID) -> tuple[UploadedChapter, ChapterChunk]:
    row = _editable(session, chapter_id)
    chunk = session.get(ChapterChunk, chunk_id)
    if chunk is None or chunk.chapter_id != chapter_id:
        raise HTTPException(status_code=404, detail="Extrait introuvable.")
    return row, chunk


@router.patch("/{chapter_id}/chunks/{chunk_id}", response_model=ChunkOut)
def update_chunk(chapter_id: str, chunk_id: uuid.UUID, payload: ChunkUpdate) -> ChunkOut:
    with session_scope() as s:
        row, c = _chunk(s, chapter_id, chunk_id)
        for field in ("content", "section", "type", "pinned"):
            value = getattr(payload, field)
            if value is not None:
                setattr(c, field, value)
        if payload.pin_label is not None:
            c.pin_label = payload.pin_label.strip() or None
        if c.pinned and not c.pin_label:
            # A pin without a label cannot be published; default it to the
            # section so a single click on "épingler" is already valid.
            c.pin_label = c.section or "Référence"
        _touch(s, row)
        s.flush()
        return ChunkOut(
            id=c.id,
            position=c.position,
            content=c.content,
            section=c.section,
            type=c.type,
            format=c.format,
            page=c.page,
            pinned=c.pinned,
            pin_label=c.pin_label,
            flags=cs.review_flags(c.content, c.type),
        )


@router.delete("/{chapter_id}/chunks/{chunk_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chunk(chapter_id: str, chunk_id: uuid.UUID) -> None:
    with session_scope() as s:
        row, c = _chunk(s, chapter_id, chunk_id)
        s.delete(c)
        _touch(s, row)


# --- exercises ----------------------------------------------------------------------------------


def _exercise(session, chapter_id: str, exercise_id: uuid.UUID) -> tuple[UploadedChapter, ChapterExercise]:
    row = _editable(session, chapter_id)
    ex = session.get(ChapterExercise, exercise_id)
    if ex is None or ex.chapter_id != chapter_id:
        raise HTTPException(status_code=404, detail="Exercice introuvable.")
    return row, ex


@router.post("/{chapter_id}/exercises", response_model=ExerciseOut, status_code=status.HTTP_201_CREATED)
def add_exercise(chapter_id: str, payload: ExerciseIn) -> ExerciseOut:
    with session_scope() as s:
        row = _editable(s, chapter_id)
        last = s.scalar(
            select(func.max(ChapterExercise.position)).where(ChapterExercise.chapter_id == chapter_id)
        )
        ex = ChapterExercise(
            chapter_id=chapter_id,
            position=(last + 1) if last is not None else 0,
            title=payload.title.strip(),
            question=payload.question.strip(),
        )
        s.add(ex)
        _touch(s, row)
        s.flush()
        return ExerciseOut(id=ex.id, position=ex.position, title=ex.title, question=ex.question)


@router.patch("/{chapter_id}/exercises/{exercise_id}", response_model=ExerciseOut)
def update_exercise(chapter_id: str, exercise_id: uuid.UUID, payload: ExerciseUpdate) -> ExerciseOut:
    with session_scope() as s:
        row, ex = _exercise(s, chapter_id, exercise_id)
        if payload.title is not None:
            ex.title = payload.title.strip()
        if payload.question is not None:
            ex.question = payload.question.strip()
        _touch(s, row)
        s.flush()
        return ExerciseOut(id=ex.id, position=ex.position, title=ex.title, question=ex.question)


@router.delete("/{chapter_id}/exercises/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(chapter_id: str, exercise_id: uuid.UUID) -> None:
    with session_scope() as s:
        row, ex = _exercise(s, chapter_id, exercise_id)
        s.delete(ex)
        _touch(s, row)
