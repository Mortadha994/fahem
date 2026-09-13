"""Uploaded chapters: extraction, review flags, publishing (Phase 9).

The lifecycle, and which function moves it:

    upload ──store_pdf──> processing ──process_upload──> draft ──publish──> published
                                    └──(extraction raised)──> failed
    draft/published ──publish──> publishing ──> published   (republish)
    published ──unpublish──> draft

Students only ever read the publish snapshot: the points in Qdrant (chunks,
and the `pinned` payload that replaces context.PINS for these chapters) and
the chapters.published_* columns. The draft rows are the admin's workspace.

What is NOT automated, on purpose, and why: this module never rewrites chunk
text. Chapter 1's PDF decodes the assignment arrow as "-" and was corrected by
hand (patch_chunks.py explains why a pattern fix would also corrupt genuine
subtraction). The same author's PDFs will have the same problem, so
review_flags() points at the chunks that look like it and the admin fixes them
in the console - a human decides, the code only highlights.

Chapter 1 does not go through here at all; see models.py.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qdrant_client.http import models as qmodels
from sqlalchemy import delete, select, update

import course_markdown
import rag_store
from config import CHAPTER_UPLOAD_DIR
from db import session_scope
from extract_chapter import extract
from models import (
    CHAPTER_DRAFT,
    CHAPTER_FAILED,
    CHAPTER_PROCESSING,
    CHAPTER_PUBLISHED,
    CHAPTER_PUBLISHING,
    ChapterChunk,
    ChapterExercise,
    UploadedChapter,
)

log = logging.getLogger("fahem.chapters")

BUILTIN_CHAPTER_ID = "1"
PDF_MAGIC = b"%PDF-"

# --- review flags ----------------------------------------------------------------
#
# Heuristics that decide what the console highlights, never what gets changed.
# False positives cost a glance; false negatives are what the review exists to
# catch, so these lean towards flagging.

# An identifier, a lone "-", then an operand at the start of a line - the shape
# a decoded-as-dash assignment takes: "somme - a + b", "Variable - Valeur".
# Genuine subtraction usually has an assignment before it ("x ← a - b"), which
# this does not match because the line does not start "<name> - ". Spaces and
# tabs only, never \s: \s crosses newlines, so a word ending one line followed
# by a "- " bullet on the next would match - and no per-line fix could clear it.
_LOST_ARROW = re.compile(
    r"^[ \t]*[A-Za-zÀ-ÿ_][\wÀ-ÿ]*(?:\[[^\]\n]*\])?[ \t]+-[ \t]+\S", re.MULTILINE
)
# U+FFFD, or the private-use area a custom font glyph decodes into.
_GARBLED = re.compile("[\\ufffd\\ue000-\\uf8ff]")

FLAG_LOST_ARROW = "lost_arrow"
FLAG_GARBLED = "garbled"
FLAG_SHORT = "short"
FLAG_ASCII_ARROW = "ascii_arrow"

# The assignment typed as "<-" rather than drawn as "←" (chapter 2's PDF does
# this). The course notation is ←, and a pinned chunk showing "<-" teaches the
# model the wrong glyph - flagged so the admin replaces it by hand.
_ASCII_ARROW = re.compile(r"<-")
# Algorithme and Python laid out side by side without a drawn table: the
# extractor merges the two columns line by line, so one line holds an
# algorithm keyword and a Python keyword at once ("SI x > 0 ALORS if x > 0 :").
_MERGED_COLUMNS = re.compile(
    r"^.*\b(?:SI|Si|SINON|Sinon|SELON|Selon|Ecrire|Lire|POUR|Pour|TANT QUE)\b.*"
    r"\b(?:if|else|elif|match|case|print|input|for|while)\b.*$",
    re.MULTILINE,
)
FLAG_MERGED_COLUMNS = "merged_columns"


def review_flags(content: str, ctype: str) -> list[str]:
    flags = []
    if ctype != "exercice" and _LOST_ARROW.search(content):
        flags.append(FLAG_LOST_ARROW)
    if ctype != "exercice" and _ASCII_ARROW.search(content):
        flags.append(FLAG_ASCII_ARROW)
    if ctype != "exercice" and _MERGED_COLUMNS.search(content):
        flags.append(FLAG_MERGED_COLUMNS)
    if _GARBLED.search(content):
        flags.append(FLAG_GARBLED)
    if ctype == "prose" and len(content.strip()) < 40:
        flags.append(FLAG_SHORT)
    return flags


# --- files -------------------------------------------------------------------------


def pdf_path(chapter_id: str) -> Path:
    """The student-facing PDF. For a PDF chapter it is also the source."""
    # chapter_id is validated to digits by the router before it gets here, and
    # the file is named by it alone - the uploaded filename never becomes a path.
    return CHAPTER_UPLOAD_DIR / f"{chapter_id}.pdf"


def markdown_path(chapter_id: str) -> Path:
    return CHAPTER_UPLOAD_DIR / f"{chapter_id}.md"


def _atomic_write(path: Path, data: bytes) -> None:
    CHAPTER_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    tmp.write_bytes(data)
    tmp.replace(path)  # atomic: never a half-written file at the real name


def store_pdf(chapter_id: str, data: bytes) -> None:
    _atomic_write(pdf_path(chapter_id), data)


def store_markdown(chapter_id: str, data: bytes) -> None:
    _atomic_write(markdown_path(chapter_id), data)


def remove_pdf(chapter_id: str) -> None:
    pdf_path(chapter_id).unlink(missing_ok=True)
    markdown_path(chapter_id).unlink(missing_ok=True)


# --- extraction ----------------------------------------------------------------------

_EXERCISE_SECTION = re.compile(r"^Exercice\s+(\d+)$")
_EXERCISE_PREFIX = re.compile(r"^\s*Exercice\s*N\s*°\s*\d+\s*:?\s*", re.IGNORECASE)


def detect_exercises(chunks: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Group the série's chunks into exercises, the way extract_chapter.py
    sections them ("Exercice N"), in order of first appearance."""
    order: list[int] = []
    parts: dict[int, list[str]] = {}
    for chunk in chunks:
        if chunk["type"] != "exercice":
            continue
        m = _EXERCISE_SECTION.match(chunk.get("section", ""))
        if not m:
            continue
        n = int(m.group(1))
        if n not in parts:
            order.append(n)
            parts[n] = []
        parts[n].append(chunk["content"])
    exercises = []
    for n in order:
        question = _EXERCISE_PREFIX.sub("", "\n".join(parts[n]), count=1).strip()
        if question:
            exercises.append({"title": f"Exercice {n}", "question": question})
    return exercises


def process_upload(chapter_id: str) -> None:
    """Background task: extract the stored PDF into draft chunks and exercises.

    Replaces any previous draft content for the chapter (a re-upload), and
    leaves the publish snapshot alone - a re-upload of a live chapter is a new
    draft of it, not a takedown.
    """
    try:
        with session_scope() as s:
            row = s.get(UploadedChapter, chapter_id)
            if row is None or row.status != CHAPTER_PROCESSING:
                return
            niveau = row.niveau
            kind = row.source_kind

        header = None
        if kind == "markdown":
            # Validated at upload already; parsed again here so the stored
            # file, not the request, is the single source of what gets imported.
            course = course_markdown.parse(
                markdown_path(chapter_id).read_text(encoding="utf-8"), chapter_id
            )
            chunks, exercises = course.chunks, course.exercises
            header = course
        else:
            chunks = extract(pdf_path(chapter_id), niveau, chapter_id)
            if not chunks:
                raise ValueError(
                    "aucun texte extrait - le PDF est peut-être scanné (image) plutôt que du texte"
                )
            exercises = detect_exercises(chunks)

        with session_scope() as s:
            s.execute(delete(ChapterChunk).where(ChapterChunk.chapter_id == chapter_id))
            s.execute(delete(ChapterExercise).where(ChapterExercise.chapter_id == chapter_id))
            for i, c in enumerate(chunks):
                s.add(
                    ChapterChunk(
                        chapter_id=chapter_id,
                        position=i,
                        content=c["content"],
                        section=c.get("section") or "",
                        type=c["type"] if c["type"] in ("prose", "table", "exercice") else "prose",
                        format=c.get("format") or "prose",
                        page=c.get("page"),
                        # A markdown course marks its reference sheet with 📌;
                        # a PDF's pins are chosen by hand during review.
                        pinned=bool(c.get("pinned")),
                        pin_label=c.get("pin_label"),
                    )
                )
            for i, e in enumerate(exercises):
                s.add(ChapterExercise(chapter_id=chapter_id, position=i, **e))
            row = s.get(UploadedChapter, chapter_id)
            if header is not None:
                row.title = header.titre
                row.topics = header.notions
            row.status = CHAPTER_DRAFT
            row.error = None
            if row.published_at is not None:
                row.has_unpublished_changes = True
        log.info("chapter %s extracted: %d chunks, %d exercises", chapter_id, len(chunks), len(exercises))
    except Exception as exc:  # noqa: BLE001 - any failure becomes a visible status
        log.exception("chapter %s extraction failed", chapter_id)
        with session_scope() as s:
            row = s.get(UploadedChapter, chapter_id)
            if row is not None:
                row.status = CHAPTER_FAILED
                problems = getattr(exc, "problems", None)
                row.error = "Import impossible : " + (" ".join(problems) if problems else str(exc))


# --- publishing ----------------------------------------------------------------------


def publish_problems(chapter_id: str) -> list[str]:
    """What blocks a publish, in French for the console. Empty means go."""
    with session_scope() as s:
        row = s.get(UploadedChapter, chapter_id)
        if row is None:
            return ["Chapitre introuvable."]
        problems = []
        if row.status not in (CHAPTER_DRAFT, CHAPTER_PUBLISHED):
            problems.append("Le chapitre n'est pas prêt (extraction ou publication en cours).")
        if not row.title.strip():
            problems.append("Le titre est vide.")
        if not row.topics.strip():
            problems.append(
                "La liste des notions couvertes est vide (utilisée par l'assistant pour décrire le chapitre)."
            )
        chunks = row.chunks
        if not any(c.type in ("prose", "table") for c in chunks):
            problems.append("Aucun contenu de cours (prose ou tableau) à publier.")
        pinned = [c for c in chunks if c.pinned]
        if not pinned:
            problems.append(
                "Aucun tableau de syntaxe épinglé. Épingle au moins la fiche de référence du chapitre."
            )
        if any(not (c.pin_label or "").strip() for c in pinned):
            problems.append("Chaque élément épinglé doit avoir un libellé.")
        return problems


def begin_publish(chapter_id: str) -> bool:
    """Claim the chapter for publishing. False if it is not in a publishable
    state - one conditional UPDATE, so two clicks cannot run two publishes."""
    with session_scope() as s:
        result = s.execute(
            update(UploadedChapter)
            .where(
                UploadedChapter.id == chapter_id,
                UploadedChapter.status.in_((CHAPTER_DRAFT, CHAPTER_PUBLISHED)),
            )
            .values(status=CHAPTER_PUBLISHING, error=None)
        )
        return result.rowcount == 1


def publish(chapter_id: str) -> None:
    """Background task: snapshot the draft into Qdrant and the published_* columns.

    Upsert-then-prune, never delete-then-upsert: the previous version stays
    fully retrievable until the new one is completely written, so a republish
    never leaves students with an empty chapter, and a failure halfway leaves
    the old version live.
    """
    try:
        with session_scope() as s:
            row = s.get(UploadedChapter, chapter_id)
            niveau = row.niveau
            source = row.source_filename
            snapshot = {
                "title": row.title.strip(),
                "topics": row.topics.strip(),
                "exercises": [
                    {"id": f"ch{chapter_id}_ex{i + 1}", "title": e.title, "question": e.question}
                    for i, e in enumerate(row.exercises)
                    if e.question.strip()
                ],
            }
            chunk_dicts, extras = [], []
            for c in row.chunks:
                if not c.content.strip():
                    continue
                chunk_dicts.append(
                    {
                        "content": c.content,
                        "niveau": niveau,
                        "chapitre": chapter_id,
                        "section": c.section,
                        "type": c.type,
                        "format": c.format,
                        "page": c.page,
                        "source": source,
                    }
                )
                # position: so context.published_pins can order the reference
                # sheet as the course does. Payload only - never part of make_id.
                extras.append(
                    {"pinned": True, "pin_label": c.pin_label.strip(), "position": c.position}
                    if c.pinned
                    else {"position": c.position}
                )

        new_ids = set(rag_store.upsert_chunks(chunk_dicts, extras))

        stale = [
            r.id
            for r in rag_store.scroll_scope(niveau, chapter_id)
            if str((r.payload or {}).get("chunk_id")) not in new_ids
        ]
        if stale:

            rag_store.get_client().delete(
                collection_name=rag_store.COLLECTION_NAME,
                points_selector=qmodels.PointIdsList(points=stale),
                wait=True,
            )

        with session_scope() as s:
            row = s.get(UploadedChapter, chapter_id)
            row.published_title = snapshot["title"]
            row.published_topics = snapshot["topics"]
            row.published_exercises = snapshot["exercises"]

            row.published_at = datetime.now(timezone.utc)
            row.has_unpublished_changes = False
            row.status = CHAPTER_PUBLISHED
            row.error = None
        log.info("chapter %s published: %d chunks", chapter_id, len(new_ids))
    except Exception as exc:  # noqa: BLE001
        log.exception("chapter %s publish failed", chapter_id)
        with session_scope() as s:
            row = s.get(UploadedChapter, chapter_id)
            if row is not None:
                # Back to whatever students could see before: the old snapshot
                # is still intact in Qdrant (upsert-then-prune).
                row.status = CHAPTER_PUBLISHED if row.published_at else CHAPTER_DRAFT
                row.error = f"Publication échouée : {exc}"


def unpublish(chapter_id: str) -> None:
    with session_scope() as s:
        row = s.get(UploadedChapter, chapter_id)
        niveau = row.niveau
    rag_store.delete_scope(niveau, chapter_id)
    with session_scope() as s:
        row = s.get(UploadedChapter, chapter_id)
        row.status = CHAPTER_DRAFT
        row.published_at = None
        row.has_unpublished_changes = False


def delete_chapter(chapter_id: str) -> None:
    with session_scope() as s:
        row = s.get(UploadedChapter, chapter_id)
        if row is None:
            return
        niveau = row.niveau
    rag_store.delete_scope(niveau, chapter_id)
    remove_pdf(chapter_id)
    with session_scope() as s:
        row = s.get(UploadedChapter, chapter_id)
        if row is not None:
            s.delete(row)


def mark_changed(session, chapter: UploadedChapter) -> None:
    """Call after any draft edit: a live chapter now differs from what is live."""
    if chapter.published_at is not None:
        chapter.has_unpublished_changes = True


def recover_interrupted() -> int:
    """Run at startup. Background tasks die with the process, so a chapter
    left in processing/publishing by a restart would otherwise spin forever."""
    n = 0
    with session_scope() as s:
        rows = s.scalars(
            select(UploadedChapter).where(
                UploadedChapter.status.in_((CHAPTER_PROCESSING, CHAPTER_PUBLISHING))
            )
        ).all()
        for row in rows:
            if row.status == CHAPTER_PROCESSING:
                row.status = CHAPTER_FAILED
                row.error = "Extraction interrompue par un redémarrage du serveur. Renvoie le PDF."
            else:
                row.status = CHAPTER_PUBLISHED if row.published_at else CHAPTER_DRAFT
                row.error = "Publication interrompue par un redémarrage du serveur. Relance-la."
            n += 1
    return n


# --- student-side reads -------------------------------------------------------------


def published_chapters() -> list[UploadedChapter]:
    with session_scope() as s:
        return list(
            s.scalars(
                select(UploadedChapter)
                .where(UploadedChapter.status.in_((CHAPTER_PUBLISHED, CHAPTER_PUBLISHING)),
                       UploadedChapter.published_at.is_not(None))
                .order_by(UploadedChapter.id)
            ).all()
        )


def published_chapter(chapter_id: str) -> UploadedChapter | None:
    """The chapter as students see it, or None. A republish in progress still
    counts as published: the previous snapshot is live until it completes."""
    with session_scope() as s:
        row = s.get(UploadedChapter, chapter_id)
    if row is None or row.published_at is None:
        return None
    if row.status not in (CHAPTER_PUBLISHED, CHAPTER_PUBLISHING):
        return None
    return row
