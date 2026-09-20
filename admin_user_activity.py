"""One student's activity over time, for the console's per-account charts.

What this exists to answer: is this person using Fahem enough to need more
room, are they learning with it or only taking solutions off it, and what are
they actually costing. Those are long-run questions, so everything here is
bucketed by week rather than served as a running total - a total says a
student asked 132 questions, a series says whether they are still asking.

Two sources, two different histories, and the split is deliberate:

- activity comes from chat_sessions / chat_messages, which go back to the
  account's first question;
- spend comes from llm_calls.user_id, which only exists from the migration
  that added it (a2c7e4b9d631). Rows older than that belong to nobody and
  are not guessed at, so `tokens.since` says when the meter actually starts
  and the console prints it rather than implying the whole history is there.

Admin-only, through the router's dependency, like every other /admin route.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import Integer, case, cast, distinct, func, select

import auth
from db import session_scope
from models import ChatMessage, ChatSession, LlmCall, User

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_current_admin)],
)

# Twelve weeks is a term. Long enough to see a habit form or fade, short
# enough that every bar is still wide enough to point at on a laptop.
DEFAULT_WEEKS = 12
MAX_WEEKS = 52


class Week(BaseModel):
    """One Monday-to-Sunday bucket. `start` is the Monday, as a date string."""

    start: str
    questions: int
    guided: int
    full: int
    check: int
    practice: int
    tokens: int
    calls: int


class Totals(BaseModel):
    questions: int
    active_days: int
    discussions: int
    first_question: datetime | None
    last_question: datetime | None


class Exercises(BaseModel):
    """Where this student's exercises ended up (the same vocabulary the
    student's own progress page uses)."""

    done: int
    solution_seen: int
    started: int


class Spend(BaseModel):
    """Only as far back as llm_calls.user_id goes; `since` is that boundary,
    or None when this student has no attributed call at all yet."""

    since: datetime | None
    tokens: int
    calls: int


class UserActivity(BaseModel):
    weeks: list[Week]
    totals: Totals
    exercises: Exercises
    spend: Spend


def _monday(moment: datetime) -> datetime:
    """The Monday 00:00 UTC of that moment's week."""
    day = moment.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return day - timedelta(days=day.weekday())


@router.get("/users/{user_id}/activity", response_model=UserActivity)
def user_activity(
    user_id: uuid.UUID,
    weeks: int = Query(DEFAULT_WEEKS, ge=1, le=MAX_WEEKS),
) -> UserActivity:
    with session_scope() as s:
        if s.get(User, user_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Compte introuvable")

        start = _monday(datetime.now(timezone.utc)) - timedelta(weeks=weeks - 1)

        # --- what they asked, by week -------------------------------------------------
        #
        # A "question" is one user message. The mode is on the message's own
        # extra blob, which is where the chat records it (chat_history stores
        # it only when set, and only as guided | check | practice). A message
        # with none is a plain "solution complète" ask, which is what every
        # message written before those modes existed was too.
        mode = ChatMessage.extra["mode"].astext
        bucket = func.date_trunc("week", ChatMessage.created_at)
        rows = s.execute(
            select(
                bucket.label("week"),
                func.count().label("questions"),
                func.sum(cast(mode == "guided", Integer)).label("guided"),
                func.sum(cast(mode == "check", Integer)).label("check"),
                func.sum(cast(mode == "practice", Integer)).label("practice"),
            )
            .select_from(ChatMessage)
            .join(ChatSession, ChatSession.id == ChatMessage.session_id)
            .where(
                ChatSession.user_id == user_id,
                ChatMessage.role == "user",
                ChatMessage.created_at >= start,
            )
            .group_by(bucket)
        ).all()
        asked = {
            r.week.astimezone(timezone.utc).date().isoformat(): r for r in rows
        }

        # --- what it cost, by week ----------------------------------------------------
        call_bucket = func.date_trunc("week", LlmCall.created_at)
        spend_rows = s.execute(
            select(
                call_bucket.label("week"),
                func.coalesce(func.sum(LlmCall.total_tokens), 0).label("tokens"),
                func.count().label("calls"),
            )
            .where(LlmCall.user_id == user_id, LlmCall.created_at >= start)
            .group_by(call_bucket)
        ).all()
        spent = {
            r.week.astimezone(timezone.utc).date().isoformat(): r for r in spend_rows
        }

        # Every week in the range, including the silent ones: a gap is the
        # signal here, and a series that skips empty weeks hides it.
        series: list[Week] = []
        for i in range(weeks):
            day = (start + timedelta(weeks=i)).date().isoformat()
            a = asked.get(day)
            sp = spent.get(day)
            guided = int(a.guided or 0) if a else 0
            checked = int(a.check or 0) if a else 0
            practised = int(a.practice or 0) if a else 0
            questions = int(a.questions or 0) if a else 0
            series.append(
                Week(
                    start=day,
                    questions=questions,
                    guided=guided,
                    check=checked,
                    practice=practised,
                    # Whatever carried no mode: a plain ask for the solution.
                    full=max(0, questions - guided - checked - practised),
                    tokens=int(sp.tokens or 0) if sp else 0,
                    calls=int(sp.calls or 0) if sp else 0,
                )
            )

        # --- headline numbers, over the whole history ---------------------------------
        totals_row = s.execute(
            select(
                func.count().label("questions"),
                func.count(distinct(func.date(ChatMessage.created_at))).label("days"),
                func.count(distinct(ChatSession.id)).label("discussions"),
                func.min(ChatMessage.created_at).label("first"),
                func.max(ChatMessage.created_at).label("last"),
            )
            .select_from(ChatMessage)
            .join(ChatSession, ChatSession.id == ChatMessage.session_id)
            .where(ChatSession.user_id == user_id, ChatMessage.role == "user")
        ).one()

        spend_all = s.execute(
            select(
                func.min(LlmCall.created_at).label("since"),
                func.coalesce(func.sum(LlmCall.total_tokens), 0).label("tokens"),
                func.count().label("calls"),
            ).where(LlmCall.user_id == user_id)
        ).one()

        exercises = _exercise_mix(s, user_id)

    return UserActivity(
        weeks=series,
        totals=Totals(
            questions=int(totals_row.questions or 0),
            active_days=int(totals_row.days or 0),
            discussions=int(totals_row.discussions or 0),
            first_question=totals_row.first,
            last_question=totals_row.last,
        ),
        exercises=exercises,
        spend=Spend(
            since=spend_all.since,
            tokens=int(spend_all.tokens or 0),
            calls=int(spend_all.calls or 0),
        ),
    )


def _exercise_mix(s, user_id: uuid.UUID) -> Exercises:
    """How this student's exercises ended, counted per discussion.

    A discussion counts once, at its best outcome: solved by the student
    (a correct check with no solution shown before it) beats having been
    shown the solution, which beats merely started. This mirrors progress.py's
    ranking rather than inventing a second vocabulary for the same thing.
    """
    # Both live inside the message's extra blob, as chat_history writes them:
    # the verdict under check, and the "this hint gave the whole solution"
    # flag under guided (not at the top level).
    checked = func.bool_or(ChatMessage.extra["check"]["verdict"].astext == "correct")
    saw_solution = func.bool_or(
        func.coalesce(ChatMessage.extra["guided"]["leak"].astext, "false") == "true"
    )

    rows = s.execute(
        select(
            ChatSession.id,
            checked.label("correct"),
            saw_solution.label("seen"),
        )
        .select_from(ChatSession)
        .join(ChatMessage, ChatMessage.session_id == ChatSession.id)
        .where(ChatSession.user_id == user_id)
        .group_by(ChatSession.id)
    ).all()

    done = sum(1 for r in rows if r.correct and not r.seen)
    seen = sum(1 for r in rows if r.seen)
    return Exercises(
        done=done,
        solution_seen=seen,
        started=max(0, len(rows) - done - seen),
    )
