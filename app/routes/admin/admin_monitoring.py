"""The admin console's AI monitoring page: Groq load, usage, and chat activity.

One read, GET /admin/monitoring, polled by the page every few seconds:

  models     per Groq model: tokens in the last minute against the per-minute
             limit, tokens in the last 24h against the daily limit (and what
             Groq itself last reported, from a 429's body), the queue right
             now, and a "temperature" - the most loaded of those, as one state:
             cool < 50% <= warm < 80% <= hot < 100% <= saturated. A call
             refused with a 429 in the last five minutes is saturated whatever
             the ratios say: Groq has said no, the numbers are only estimates.
  kpis       the last 24h: calls, tokens, failures by kind of failure, 429s.
  by_kind    the same per kind (gatekeeper, solve, transcription), with median
             and p95 latency and queue wait - one average across a 0.3s
             classification and a 20s solve would describe neither.
  timeline   24 hourly buckets; minutes: the last 60 one-minute token buckets.
  chat       discussions and students active in the last 24h.
  failures   the last few calls that did not end well.

Rows come from llm_calls (app/llm/llm_usage.py). Same router-level admin gate as
app/routes/admin/admin.py, so no route here can be reached by a student.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import delete, distinct, func, select
from sqlalchemy.dialects.postgresql import array as pg_array

from app.auth import auth
from app.core.config import (
    GROQ_MODEL,
    GROQ_TPD_LIMIT,
    GROQ_TPM_LIMIT,
    GROQ_VISION_MODEL,
    GROQ_VISION_TPD_LIMIT,
    GROQ_VISION_TPM_LIMIT,
    LLM_USAGE_RETENTION_DAYS,
)
from app.core.db import session_scope
from app.core.models import (
    LLM_CALL_CANCELLED,
    LLM_CALL_ERROR,
    LLM_CALL_OK,
    LLM_CALL_QUEUE_TIMEOUT,
    LLM_CALL_RATE_LIMITED,
    AnswerFeedback,
    ChatMessage,
    ChatSession,
    LlmCall,
)
from app.llm import llm_queue, llm_usage

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_current_admin)],
)

STATE_COOL = "cool"
STATE_WARM = "warm"
STATE_HOT = "hot"
STATE_SATURATED = "saturated"

# Requests in line per slot at which the queue alone counts as fully loaded.
_QUEUE_FULL_PER_SLOT = 4
_SATURATED_WINDOW = timedelta(minutes=5)
_PRUNE_EVERY_SECONDS = 600
_last_prune = 0.0


def temperature(ratio: float, refused_recently: bool) -> str:
    if refused_recently or ratio >= 1.0:
        return STATE_SATURATED
    if ratio >= 0.8:
        return STATE_HOT
    if ratio >= 0.5:
        return STATE_WARM
    return STATE_COOL


# --- schemas -------------------------------------------------------------------


class QueueNow(BaseModel):
    waiting: int
    active: int
    max_concurrent: int


class ModelLoad(BaseModel):
    model: str
    label: str
    tpm_limit: int
    tpd_limit: int
    tokens_last_minute: int
    requests_last_minute: int
    tokens_24h: int
    requests_24h: int
    # Groq's own count, from the last daily-limit 429 in the past 24h.
    reported_tpd_used: int | None
    reported_at: datetime | None
    minute_ratio: float
    day_ratio: float | None
    queue_ratio: float
    load: float
    state: str
    refused_recently: bool
    queue: QueueNow | None


class Kpis(BaseModel):
    calls: int
    ok: int
    rate_limited: int
    queue_timeouts: int
    errors: int
    cancelled: int
    rate_limit_hits: int
    tokens: int
    success_rate: float | None


class KindStats(BaseModel):
    kind: str
    calls: int
    failures: int
    tokens: int
    avg_tokens: int
    latency_p50_ms: int
    latency_p95_ms: int
    wait_p50_ms: int
    wait_p95_ms: int


class HourBucket(BaseModel):
    at: datetime
    calls: int
    tokens: int
    failures: int


class MinuteBucket(BaseModel):
    at: datetime
    tokens: int
    calls: int


class ChatActivity(BaseModel):
    active_discussions_24h: int
    new_discussions_24h: int
    active_students_24h: int
    questions_in_active: int


class Failure(BaseModel):
    at: datetime
    model: str
    kind: str
    status: str
    detail: str | None
    queue_wait_ms: int
    rate_limit_hits: int


class RouteStats(BaseModel):
    """Solves per prompt (PROBLEM, QUESTION, CODE, FOLLOW_UP) over 24h."""

    route: str
    calls: int
    with_memory: int
    avg_prompt_tokens: int
    avg_memory_chars: int


class FeedbackStats(BaseModel):
    """Students' 👍 / 👎 on answers over 7 days, and the latest 👎."""

    up: int
    down: int
    recent_down: list[dict]


class LearningStats(BaseModel):
    """Mode guidé and Vérifier ma réponse over 7 days (discussions active since)."""

    guided_answers: int
    guided_by_step: dict[str, int]
    guided_leaks: int  # a step 1-3 answer that gave the full solution anyway
    checks: int
    verdicts: dict[str, int]  # correct / presque / a_revoir / unknown
    top_findings: list[dict]  # [{kind, count}] - the notation mistakes found most


class Monitoring(BaseModel):
    generated_at: datetime
    models: list[ModelLoad]
    kpis: Kpis
    by_kind: list[KindStats]
    timeline: list[HourBucket]
    minutes: list[MinuteBucket]
    chat: ChatActivity
    failures: list[Failure]
    routes: list[RouteStats] = []
    feedback: FeedbackStats | None = None
    learning: LearningStats | None = None


# --- helpers -------------------------------------------------------------------


def _models() -> list[tuple[str, str, int, int]]:
    seen: list[tuple[str, str, int, int]] = [
        (GROQ_MODEL, "Texte", GROQ_TPM_LIMIT, GROQ_TPD_LIMIT),
    ]
    if GROQ_VISION_MODEL != GROQ_MODEL:
        seen.append((GROQ_VISION_MODEL, "Vision", GROQ_VISION_TPM_LIMIT, GROQ_VISION_TPD_LIMIT))
    return seen


def _queue_now(model: str) -> QueueNow | None:
    try:
        snap = llm_queue.snapshot_sync(llm_queue.groq_queue_key(model))
    except Exception:
        return None
    return QueueNow(
        waiting=snap.waiting,
        active=snap.active,
        max_concurrent=llm_queue.groq_max_concurrent(model),
    )


def _prune(s, now: datetime) -> None:
    global _last_prune
    if time.monotonic() - _last_prune < _PRUNE_EVERY_SECONDS:
        return
    _last_prune = time.monotonic()
    s.execute(
        delete(LlmCall).where(LlmCall.created_at < now - timedelta(days=LLM_USAGE_RETENTION_DAYS))
    )


def _model_load(s, model, label, tpm, tpd, now) -> ModelLoad:
    minute_ago = now - timedelta(minutes=1)
    day_ago = now - timedelta(days=1)
    tokens_minute, requests_minute = s.execute(
        select(func.coalesce(func.sum(LlmCall.total_tokens), 0), func.count()).where(
            LlmCall.model == model, LlmCall.created_at >= minute_ago
        )
    ).one()
    tokens_day, requests_day = s.execute(
        select(func.coalesce(func.sum(LlmCall.total_tokens), 0), func.count()).where(
            LlmCall.model == model, LlmCall.created_at >= day_ago
        )
    ).one()
    refused = (
        s.scalar(
            select(func.count()).where(
                LlmCall.model == model,
                LlmCall.status == LLM_CALL_RATE_LIMITED,
                LlmCall.created_at >= now - _SATURATED_WINDOW,
            )
        )
        > 0
    )

    reported = llm_usage.daily_limits(model)
    reported_used = reported.get("tpd_used")
    reported_at = (
        datetime.fromtimestamp(reported["tpd_at"], tz=timezone.utc)
        if "tpd_at" in reported
        else None
    )
    if reported.get("tpd_limit"):
        tpd = reported["tpd_limit"]

    queue = _queue_now(model)
    minute_ratio = tokens_minute / tpm if tpm else 0.0
    # Groq's count is authoritative when it is fresh; otherwise ours.
    day_used = tokens_day
    if reported_used is not None and reported_at and now - reported_at < timedelta(hours=1):
        day_used = max(day_used, reported_used)
    day_ratio = day_used / tpd if tpd else None
    queue_ratio = (
        (queue.waiting + queue.active) / (queue.max_concurrent * _QUEUE_FULL_PER_SLOT)
        if queue
        else 0.0
    )
    load = max(minute_ratio, day_ratio or 0.0, queue_ratio)
    return ModelLoad(
        model=model,
        label=label,
        tpm_limit=tpm,
        tpd_limit=tpd,
        tokens_last_minute=int(tokens_minute),
        requests_last_minute=int(requests_minute),
        tokens_24h=int(tokens_day),
        requests_24h=int(requests_day),
        reported_tpd_used=reported_used,
        reported_at=reported_at,
        minute_ratio=round(minute_ratio, 4),
        day_ratio=None if day_ratio is None else round(day_ratio, 4),
        queue_ratio=round(queue_ratio, 4),
        load=round(max(load, 1.0) if refused else load, 4),
        state=temperature(load, refused),
        refused_recently=refused,
        queue=queue,
    )


def _kpis(s, day_ago) -> Kpis:
    by_status = dict(
        s.execute(
            select(LlmCall.status, func.count())
            .where(LlmCall.created_at >= day_ago)
            .group_by(LlmCall.status)
        ).all()
    )
    tokens, hits = s.execute(
        select(
            func.coalesce(func.sum(LlmCall.total_tokens), 0),
            func.coalesce(func.sum(LlmCall.rate_limit_hits), 0),
        ).where(LlmCall.created_at >= day_ago)
    ).one()
    calls = sum(by_status.values())
    ok = by_status.get(LLM_CALL_OK, 0)
    settled = calls - by_status.get(LLM_CALL_CANCELLED, 0)
    return Kpis(
        calls=calls,
        ok=ok,
        rate_limited=by_status.get(LLM_CALL_RATE_LIMITED, 0),
        queue_timeouts=by_status.get(LLM_CALL_QUEUE_TIMEOUT, 0),
        errors=by_status.get(LLM_CALL_ERROR, 0),
        cancelled=by_status.get(LLM_CALL_CANCELLED, 0),
        rate_limit_hits=int(hits),
        tokens=int(tokens),
        success_rate=round(ok / settled, 4) if settled else None,
    )


def _by_kind(s, day_ago) -> list[KindStats]:
    def pct(p, column):
        return func.coalesce(func.percentile_cont(p).within_group(column), 0)

    rows = s.execute(
        select(
            LlmCall.kind,
            func.count(),
            func.count().filter(LlmCall.status.notin_([LLM_CALL_OK, LLM_CALL_CANCELLED])),
            func.coalesce(func.sum(LlmCall.total_tokens), 0),
            pct(0.5, LlmCall.latency_ms),
            pct(0.95, LlmCall.latency_ms),
            pct(0.5, LlmCall.queue_wait_ms),
            pct(0.95, LlmCall.queue_wait_ms),
        )
        .where(LlmCall.created_at >= day_ago)
        .group_by(LlmCall.kind)
        .order_by(func.count().desc())
    ).all()
    return [
        KindStats(
            kind=kind,
            calls=calls,
            failures=failures,
            tokens=int(tokens),
            avg_tokens=int(tokens // calls) if calls else 0,
            latency_p50_ms=int(l50),
            latency_p95_ms=int(l95),
            wait_p50_ms=int(w50),
            wait_p95_ms=int(w95),
        )
        for kind, calls, failures, tokens, l50, l95, w50, w95 in rows
    ]


def _timeline(s, now) -> list[HourBucket]:
    this_hour = now.replace(minute=0, second=0, microsecond=0)
    start = this_hour - timedelta(hours=23)
    hour = func.date_trunc("hour", LlmCall.created_at)
    rows = s.execute(
        select(
            hour,
            func.count(),
            func.coalesce(func.sum(LlmCall.total_tokens), 0),
            func.count().filter(LlmCall.status.notin_([LLM_CALL_OK, LLM_CALL_CANCELLED])),
        )
        .where(LlmCall.created_at >= start)
        .group_by(hour)
    ).all()
    found = {at.astimezone(timezone.utc): (c, t, f) for at, c, t, f in rows}
    buckets = []
    for i in range(24):
        at = start + timedelta(hours=i)
        calls, tokens, failures = found.get(at, (0, 0, 0))
        buckets.append(HourBucket(at=at, calls=calls, tokens=int(tokens), failures=failures))
    return buckets


def _minutes(s, now) -> list[MinuteBucket]:
    this_minute = now.replace(second=0, microsecond=0)
    start = this_minute - timedelta(minutes=59)
    minute = func.date_trunc("minute", LlmCall.created_at)
    rows = s.execute(
        select(minute, func.coalesce(func.sum(LlmCall.total_tokens), 0), func.count())
        .where(LlmCall.created_at >= start)
        .group_by(minute)
    ).all()
    found = {at.astimezone(timezone.utc): (t, c) for at, t, c in rows}
    out = []
    for i in range(60):
        at = start + timedelta(minutes=i)
        tokens, calls = found.get(at, (0, 0))
        out.append(MinuteBucket(at=at, tokens=int(tokens), calls=calls))
    return out


def _chat(s, day_ago) -> ChatActivity:
    # Messages are re-inserted each time a discussion is saved, so their
    # created_at is not when they were sent; the session's updated_at is.
    active, new, students = s.execute(
        select(
            func.count().filter(ChatSession.updated_at >= day_ago),
            func.count().filter(ChatSession.created_at >= day_ago),
            func.count(distinct(ChatSession.user_id)).filter(ChatSession.updated_at >= day_ago),
        )
    ).one()
    questions = s.scalar(
        select(func.count())
        .select_from(ChatMessage)
        .join(ChatSession, ChatMessage.session_id == ChatSession.id)
        .where(ChatSession.updated_at >= day_ago, ChatMessage.role == "user")
    )
    return ChatActivity(
        active_discussions_24h=active,
        new_discussions_24h=new,
        active_students_24h=students,
        questions_in_active=questions or 0,
    )


def _failures(s, day_ago) -> list[Failure]:
    rows = s.scalars(
        select(LlmCall)
        .where(
            LlmCall.created_at >= day_ago,
            LlmCall.status.notin_([LLM_CALL_OK, LLM_CALL_CANCELLED]),
        )
        .order_by(LlmCall.created_at.desc())
        .limit(8)
    ).all()
    return [
        Failure(
            at=r.created_at,
            model=r.model,
            kind=r.kind,
            status=r.status,
            detail=r.detail,
            queue_wait_ms=r.queue_wait_ms,
            rate_limit_hits=r.rate_limit_hits,
        )
        for r in rows
    ]


def _routes(s, day_ago) -> list[RouteStats]:
    rows = s.execute(
        select(
            LlmCall.route,
            func.count(),
            func.count().filter(LlmCall.memory_chars > 0),
            func.coalesce(func.avg(LlmCall.prompt_tokens), 0),
            func.coalesce(func.avg(LlmCall.memory_chars).filter(LlmCall.memory_chars > 0), 0),
        )
        .where(LlmCall.created_at >= day_ago, LlmCall.route.is_not(None))
        .group_by(LlmCall.route)
        .order_by(func.count().desc())
    ).all()
    return [
        RouteStats(
            route=route,
            calls=calls,
            with_memory=with_memory,
            avg_prompt_tokens=int(avg_prompt),
            avg_memory_chars=int(avg_memory),
        )
        for route, calls, with_memory, avg_prompt, avg_memory in rows
    ]


def _feedback(s, now) -> FeedbackStats:
    since = now - timedelta(days=7)
    up, down = s.execute(
        select(
            func.count().filter(AnswerFeedback.rating == 1),
            func.count().filter(AnswerFeedback.rating == -1),
        ).where(AnswerFeedback.updated_at >= since)
    ).one()
    recent = s.execute(
        select(
            AnswerFeedback.updated_at,
            AnswerFeedback.comment,
            ChatSession.title,
            ChatSession.chapitre,
        )
        .join(ChatSession, ChatSession.id == AnswerFeedback.session_id)
        .where(AnswerFeedback.rating == -1, AnswerFeedback.updated_at >= since)
        .order_by(AnswerFeedback.updated_at.desc())
        .limit(6)
    ).all()
    return FeedbackStats(
        up=up,
        down=down,
        recent_down=[
            {"at": at, "comment": comment, "title": title, "chapitre": chapitre}
            for at, comment, title, chapitre in recent
        ],
    )


def _learning(s, now) -> LearningStats:
    since = now - timedelta(days=7)
    rows = s.scalars(
        select(ChatMessage.extra)
        .join(ChatSession, ChatSession.id == ChatMessage.session_id)
        .where(
            ChatMessage.role == "assistant",
            ChatSession.updated_at >= since,
            func.jsonb_exists_any(ChatMessage.extra, pg_array(["guided", "check"])),
        )
    ).all()
    by_step = {str(n): 0 for n in range(1, 5)}
    verdicts = {"correct": 0, "presque": 0, "a_revoir": 0, "unknown": 0}
    findings: dict[str, int] = {}
    guided = leaks = checks = 0
    for extra in rows:
        g = extra.get("guided") if isinstance(extra, dict) else None
        c = extra.get("check") if isinstance(extra, dict) else None
        if isinstance(g, dict) and str(g.get("step")) in by_step:
            guided += 1
            by_step[str(g["step"])] += 1
            leaks += bool(g.get("leak"))
        if isinstance(c, dict):
            checks += 1
            verdict = c.get("verdict")
            verdicts[verdict if verdict in verdicts else "unknown"] += 1
            for kind in c.get("findings") or []:
                findings[kind] = findings.get(kind, 0) + 1
    return LearningStats(
        guided_answers=guided,
        guided_by_step=by_step,
        guided_leaks=leaks,
        checks=checks,
        verdicts=verdicts,
        top_findings=[
            {"kind": k, "count": n} for k, n in sorted(findings.items(), key=lambda kv: -kv[1])[:6]
        ],
    )


# --- route ---------------------------------------------------------------------


@router.get("/monitoring", response_model=Monitoring)
def monitoring() -> Monitoring:
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)
    with session_scope() as s:
        _prune(s, now)
        return Monitoring(
            generated_at=now,
            models=[_model_load(s, *m, now) for m in _models()],
            kpis=_kpis(s, day_ago),
            by_kind=_by_kind(s, day_ago),
            timeline=_timeline(s, now),
            minutes=_minutes(s, now),
            chat=_chat(s, day_ago),
            failures=_failures(s, day_ago),
            routes=_routes(s, day_ago),
            feedback=_feedback(s, now),
            learning=_learning(s, now),
        )
