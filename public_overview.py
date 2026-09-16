"""What Fahem offers right now, for the public landing page.

GET /public/overview - no sign-in - is the one place the landing page reads
its facts from, so the page follows the product instead of repeating it:
publish a chapter or add exercises in the admin console and, within a minute,
the landing page's numbers, programme list and FAQ say so. Nothing on the page
has to be edited by hand for content changes.

Every figure is counted, never estimated, in the same spirit as the landing
page's rule of "no invented numbers":
  chapters   chapters.catalogue() - built-in chapters merged with published
             uploads, every niveau - with each one's topics, exercise count
             and the number of course extracts the retriever holds for it.
  totals     sums of the above, and the niveaux that have content.
  features   switches the page can show or hide a claim on (photo reading is
             only claimed while a vision model is configured).

Deliberately absent: anything about students (how many, who) - a public page
has no business with it - and anything from a draft.

Cached in-process for CACHE_SECONDS: the page is public and polled by every
visitor, and counting Qdrant points per chapter on each hit would let a crowd
of visitors load the store. A minute of staleness after a publish is fine.
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Response
from pydantic import BaseModel

import chapter_store
import chapters
import rag_store
from config import COLLECTION_NAME, GROQ_VISION_MODEL
from models import NIVEAUX

log = logging.getLogger("fahem.public_overview")

router = APIRouter(prefix="/public", tags=["public"])

CACHE_SECONDS = 60.0

# What a built-in chapter covers, for chapters that are not uploads (an upload
# carries its own `topics`). Kept here, not in chapters.CHAPTERS, because only
# the public page uses it.
BUILTIN_TOPICS: dict[str, list[str]] = {
    "1": [
        "types et constantes",
        "affectation (←)",
        "entrées / sorties (Lire, Ecrire)",
        "opérateurs arithmétiques (mod, div)",
        "fonctions prédéfinies",
    ],
    "2": [
        "Si … Alors … Sinon",
        "conditions composées (ET, OU)",
        "Si imbriqués",
        "choix multiple (Selon)",
    ],
    "3": ["Pour", "Tant que", "Répéter … Jusqu'à"],
}


class ChapterCard(BaseModel):
    id: str
    niveau: str
    niveau_label: str
    title: str
    status: str  # chapters.ACTIVE | chapters.COMING_SOON
    topics: list[str]
    exercises: int
    excerpts: int | None  # None when the store could not be counted


class Totals(BaseModel):
    chapters_available: int
    chapters_coming: int
    exercises: int
    excerpts: int | None
    niveaux: list[str]  # labels of the niveaux that have an available chapter


class Features(BaseModel):
    photo_attachments: bool
    languages: list[str]


class Overview(BaseModel):
    generated_at: datetime
    chapters: list[ChapterCard]
    totals: Totals
    features: Features


# --- counting --------------------------------------------------------------------


def split_topics(text: str) -> list[str]:
    """Split "a, b (c, d), e" on the commas that are not inside parentheses."""
    parts, depth, current = [], 0, []
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def _excerpts(niveau: str, chapter_id: str) -> int | None:
    try:
        client = rag_store.get_client()
        if not client.collection_exists(COLLECTION_NAME):
            return 0
        return client.count(
            COLLECTION_NAME,
            count_filter=rag_store.scope_filter(niveau, chapter_id),
            exact=True,
        ).count
    except Exception:
        log.warning("could not count excerpts for %s/%s", niveau, chapter_id, exc_info=True)
        return None


def _card(chapter: chapters.Chapter) -> ChapterCard:
    active = chapter.status == chapters.ACTIVE
    upload = chapter_store.published_chapter(chapter.id) if active else None
    builtin_active = chapters._BY_ID.get(chapter.id)
    builtin_active = builtin_active is not None and builtin_active.status == chapters.ACTIVE

    if upload is not None and not builtin_active:
        topics = split_topics(upload.published_topics or "")
        exercises = len(upload.published_exercises or [])
    else:
        topics = BUILTIN_TOPICS.get(chapter.id, [])
        exercises = 0
        if active:
            try:
                exercises = len(chapters.load_exercises(chapter.id))
            except Exception:  # the problems file is a mount; a missing one is 0 here
                exercises = 0

    return ChapterCard(
        id=chapter.id,
        niveau=chapter.niveau,
        niveau_label=NIVEAUX.get(chapter.niveau, chapter.niveau),
        title=chapter.title,
        status=chapter.status,
        topics=topics,
        exercises=exercises,
        excerpts=_excerpts(chapter.niveau, chapter.id) if active else None,
    )


def build_overview() -> Overview:
    cards = [_card(c) for c in chapters.catalogue()]
    available = [c for c in cards if c.status == chapters.ACTIVE]
    excerpt_counts = [c.excerpts for c in available]
    niveaux: list[str] = []
    for c in available:
        if c.niveau_label not in niveaux:
            niveaux.append(c.niveau_label)
    return Overview(
        generated_at=datetime.now(timezone.utc),
        chapters=cards,
        totals=Totals(
            chapters_available=len(available),
            chapters_coming=len(cards) - len(available),
            exercises=sum(c.exercises for c in available),
            excerpts=None if any(n is None for n in excerpt_counts) else sum(excerpt_counts),
            niveaux=niveaux,
        ),
        features=Features(
            photo_attachments=bool(GROQ_VISION_MODEL),
            languages=["Algorithme", "Python"],
        ),
    )


# --- route -----------------------------------------------------------------------

_cache: tuple[float, Overview] | None = None
_lock = threading.Lock()


def cached_overview(now: float | None = None) -> Overview:
    global _cache
    now = time.monotonic() if now is None else now
    with _lock:
        if _cache is not None and now - _cache[0] < CACHE_SECONDS:
            return _cache[1]
        overview = build_overview()
        _cache = (now, overview)
        return overview


def clear_cache() -> None:
    global _cache
    with _lock:
        _cache = None


@router.get("/overview", response_model=Overview)
def overview(response: Response) -> Overview:
    # Browsers and any proxy in front may keep it as long as the server does.
    response.headers["Cache-Control"] = f"public, max-age={int(CACHE_SECONDS)}"
    return cached_overview()
