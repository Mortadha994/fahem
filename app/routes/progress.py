"""A student's progress through the chapter exercises.

  GET /progress   per chapter: each exercise's status, the counts, the next
                  exercise to do; the latest checked solutions; the notation
                  mistakes found most often in the student's own work.

Derived from the student's discussions rather than recorded separately, so it
covers everything already done - and cannot drift from what the history shows:

  started        a discussion holds the exercise's statement (sent from the
                 chapter page, or pasted);
  solution_seen  one of those discussions shows a full, checked solution
                 (Solution complète, or Mode guidé's last step);
  done           "Vérifier ma réponse" said Correct BEFORE any full solution
                 was shown in that discussion - the student solved it
                 themselves. Reading the solution and then having it checked
                 back is "solution vue", not a win.

Nothing here reaches a model.
"""

from __future__ import annotations

import re
import uuid
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import case, literal, select

from app.auth import auth
from app.core.db import session_scope
from app.core.models import ChatMessage, ChatSession, User
from app.routes import chapters

STATUS_RANK = {"started": 1, "solution_seen": 2, "done": 3}
# How much of a statement has to appear in a message for the exercise to count
# as started: a photographed statement is transcribed, never character-perfect.
PREFIX_CHARS = 90
RECENT_CHECKS = 8


class ExerciseProgress(BaseModel):
    id: str
    question: str
    status: str | None  # None | started | solution_seen | done
    session_id: str | None  # the latest discussion about it, to reopen


class ChapterProgress(BaseModel):
    id: str
    title: str
    total: int
    started: int
    solution_seen: int
    done: int
    next_exercise: ExerciseProgress | None
    exercises: list[ExerciseProgress]


class ProgressOut(BaseModel):
    chapters: list[ChapterProgress]
    recent_checks: list[dict]
    mistakes: list[dict]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _exercises(chapter_id: str) -> list[chapters.Exercise]:
    """The same list the chapter page shows; a chapter without one has none."""
    uploaded = chapters._published_upload(chapter_id)
    if uploaded is not None:
        return [
            chapters.Exercise(id=e["id"], question=e["question"])
            for e in uploaded.published_exercises or []
        ]
    try:
        return chapters.load_exercises(chapter_id)
    except Exception:
        return []


def _discussions(db, user_id: uuid.UUID) -> list[dict[str, Any]]:
    """Each discussion as {id, title, updated_at, chapitre, user_texts, best, checks}."""
    rows = db.execute(
        select(
            ChatSession.id,
            ChatSession.title,
            ChatSession.chapitre,
            ChatSession.updated_at,
            ChatMessage.role,
            # Only the student's own text is read here (an exercise is matched
            # against it); an answer can be tens of kilobytes and is not needed.
            case((ChatMessage.role == "user", ChatMessage.content), else_=literal("")).label(
                "content"
            ),
            ChatMessage.checker_status,
            ChatMessage.extra,
            ChatMessage.position,
        )
        .join(ChatMessage, ChatMessage.session_id == ChatSession.id)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc(), ChatMessage.position)
    ).all()
    by_id: dict[uuid.UUID, dict[str, Any]] = {}
    for sid, title, chapitre, updated_at, role, content, status, extra, position in rows:
        d = by_id.setdefault(
            sid,
            {
                "id": str(sid),
                "title": title,
                "chapitre": chapitre,
                "updated_at": updated_at,
                "user_texts": [],
                "solution_seen": False,
                "correct": False,
                "checks": [],
                "solution_at": None,  # position of the first full solution
                "correct_at": None,  # position of the first Correct check
            },
        )
        extra = extra if isinstance(extra, dict) else {}
        if role == "user":
            d["user_texts"].append(_norm(content))
            continue
        check = extra.get("check") if isinstance(extra.get("check"), dict) else None
        guided = extra.get("guided") if isinstance(extra.get("guided"), dict) else None
        if check:
            d["checks"].append(check)
            if check.get("verdict") == "correct":
                d["correct"] = True
                if d["correct_at"] is None:
                    d["correct_at"] = position
        elif status in ("clean", "warned") and (not guided or guided.get("step") == 4):
            d["solution_seen"] = True
            if d["solution_at"] is None:
                d["solution_at"] = position
    return list(by_id.values())


def _about(discussion: dict[str, Any], key: str) -> bool:
    """Whether this discussion is about that exercise: the statement as sent
    from the chapter page, or a message that contains its opening (a photo of
    the same exercise is transcribed, so it never matches character for
    character)."""
    if key in discussion["user_texts"]:
        return True
    start = key[:PREFIX_CHARS]
    return len(start) >= 40 and any(start in text for text in discussion["user_texts"])


def _status(discussions: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    status, session_id = None, None
    for d in discussions:  # newest first
        alone = d["correct_at"] is not None and (
            d["solution_at"] is None or d["correct_at"] < d["solution_at"]
        )
        current = (
            "done"
            if alone
            else "solution_seen"
            if d["solution_seen"] or d["correct"]
            else "started"
        )
        if status is None or STATUS_RANK[current] > STATUS_RANK[status]:
            status = current
        session_id = session_id or d["id"]
    return status, session_id


def compute(user: User) -> ProgressOut:
    with session_scope() as db:
        discussions = _discussions(db, user.id)

    out: list[ChapterProgress] = []
    for chapter in chapters.catalogue(niveau=user.niveau):
        if chapter.status != chapters.ACTIVE:
            continue
        items: list[ExerciseProgress] = []
        for exercise in _exercises(chapter.id):
            key = _norm(exercise.question)
            about = [d for d in discussions if key and _about(d, key)]
            status, session_id = _status(about)
            items.append(
                ExerciseProgress(
                    id=exercise.id,
                    question=exercise.question,
                    status=status,
                    session_id=session_id,
                )
            )
        counts = {k: sum(1 for e in items if e.status == k) for k in STATUS_RANK}
        # Next: the first exercise not started, else the first not solved alone.
        next_exercise = next((e for e in items if e.status is None), None) or next(
            (e for e in items if e.status != "done"), None
        )
        out.append(
            ChapterProgress(
                id=chapter.id,
                title=chapter.title,
                total=len(items),
                started=sum(1 for e in items if e.status),
                solution_seen=counts["solution_seen"],
                done=counts["done"],
                next_exercise=next_exercise,
                exercises=items,
            )
        )

    recent: list[dict] = []
    mistakes: dict[str, int] = {}
    for d in discussions:
        for check in d["checks"]:
            for kind in check.get("findings") or []:
                mistakes[kind] = mistakes.get(kind, 0) + 1
        if d["checks"] and len(recent) < RECENT_CHECKS:
            last = d["checks"][-1]
            recent.append(
                {
                    "session_id": d["id"],
                    "title": d["title"],
                    "chapitre": d["chapitre"],
                    "at": d["updated_at"],
                    "verdict": last.get("verdict"),
                    "findings": last.get("findings") or [],
                    "checks": len(d["checks"]),
                }
            )
    return ProgressOut(
        chapters=out,
        recent_checks=recent,
        mistakes=[
            {"kind": k, "count": n} for k, n in sorted(mistakes.items(), key=lambda kv: -kv[1])
        ],
    )


router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("", response_model=ProgressOut)
def my_progress(user: User = Depends(auth.get_current_user)) -> ProgressOut:
    return compute(user)
