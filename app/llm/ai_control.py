"""The admin's AI controls, applied to student requests.

app/core/runtime_settings.py stores what the admin chose; this module is where it takes
effect, before any model call:

  require_ai_available   FastAPI dependency on /solve, /solve/stream and
                         /solve/extract. Refuses with 503 and a sentence for the
                         student while the AI is paused, or once the daily
                         budget guard is reached. A dependency, so it runs
                         before the rate limiter and a refused request does not
                         use up the student's quota.
  require_attachments    Same, for photo / PDF reading switched off.
  solve_rate_limit(key)  slowapi's limit provider: the account's personal limit
                         if an admin set one, else the global one - both live.

The 503 body is {"detail": {"code": ..., "message": ...}}; the chat shows the
message as it is.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select

from app.core import runtime_settings
from app.core.config import GROQ_MODEL, GROQ_TPD_LIMIT
from app.llm import llm_usage

log = logging.getLogger("fahem.ai_control")

BUDGET_CACHE_SECONDS = 15.0
USER_LIMIT_CACHE_SECONDS = 10.0

CODE_PAUSED = "paused"
CODE_BUDGET = "budget"
CODE_ATTACHMENTS_OFF = "attachments_off"

BUDGET_MESSAGE = (
    "Fahem a atteint sa limite d'utilisation pour aujourd'hui. Réessaie plus tard, ou demain matin."
)
ATTACHMENTS_OFF_MESSAGE = (
    "La lecture des photos et des PDF est désactivée pour le moment. "
    "Tape l'énoncé de l'exercice à la place."
)


def _refuse(code: str, message: str) -> HTTPException:
    return HTTPException(status_code=503, detail={"code": code, "message": message})


# --- daily budget ------------------------------------------------------------------

_budget_cache: tuple[float, dict[str, Any]] | None = None
_budget_lock = threading.Lock()


def _tokens_last_24h(model: str) -> int:
    from app.core.db import session_scope
    from app.core.models import LlmCall

    since = datetime.now(timezone.utc) - timedelta(days=1)
    with session_scope() as s:
        return int(
            s.scalar(
                select(func.coalesce(func.sum(LlmCall.total_tokens), 0)).where(
                    LlmCall.model == model, LlmCall.created_at >= since
                )
            )
        )


def budget_status(*, fresh: bool = False) -> dict[str, Any]:
    """The text model's daily token use against Groq's limit, and whether the
    guard is refusing requests because of it.

    Used is the larger of this app's own count (llm_calls, last 24h) and what
    Groq itself reported in a 429 within the last hour: Groq's figure also
    counts calls this app never recorded (another key user, a restart).
    """
    global _budget_cache
    now = time.monotonic()
    with _budget_lock:
        if not fresh and _budget_cache and now - _budget_cache[0] < BUDGET_CACHE_SECONDS:
            base = _budget_cache[1]
        else:
            base = None
    if base is None:
        try:
            used = _tokens_last_24h(GROQ_MODEL)
        except Exception:
            log.warning("could not count today's tokens", exc_info=True)
            used = 0
        # Where the ceiling comes from matters enough to travel with it. Groq
        # publishes the daily limit only inside a 429 body, so until one has
        # been met this is config.GROQ_TPD_LIMIT - a compiled-in default that
        # may be nothing like the account's real tier. A gauge that cannot say
        # which of the two it is drawn against invites reading a guess as a
        # measurement, which is exactly what it was doing.
        limit = GROQ_TPD_LIMIT
        limit_source = "default"
        reported = llm_usage.daily_limits(GROQ_MODEL)
        if reported.get("tpd_limit"):
            limit = reported["tpd_limit"]
            limit_source = "groq"
        at = reported.get("tpd_at")
        if reported.get("tpd_used") is not None and at and time.time() - at < 3600:
            used = max(used, reported["tpd_used"])
        base = {"used": used, "limit": limit, "limit_source": limit_source}
        with _budget_lock:
            _budget_cache = (now, base)

    pct = runtime_settings.get("daily_budget_guard_pct")
    threshold = int(base["limit"] * pct / 100) if pct and base["limit"] else None
    return {
        "used": base["used"],
        "limit": base["limit"],
        # "groq" when a 429 body stated it, "default" when it is the
        # compiled-in GROQ_TPD_LIMIT and therefore a guess.
        "limit_source": base.get("limit_source", "default"),
        "guard_pct": pct,
        "threshold": threshold,
        "blocking": threshold is not None and base["used"] >= threshold,
    }


def clear_budget_cache() -> None:
    global _budget_cache
    with _budget_lock:
        _budget_cache = None


# --- dependencies --------------------------------------------------------------------


def require_ai_available() -> None:
    if runtime_settings.get("ai_paused"):
        raise _refuse(CODE_PAUSED, runtime_settings.get("ai_pause_message"))
    if runtime_settings.get("daily_budget_guard_pct") and budget_status()["blocking"]:
        raise _refuse(CODE_BUDGET, BUDGET_MESSAGE)


def require_attachments() -> None:
    if not runtime_settings.get("attachments_enabled"):
        raise _refuse(CODE_ATTACHMENTS_OFF, ATTACHMENTS_OFF_MESSAGE)


def queue_timeout_seconds() -> float:
    return float(runtime_settings.get("queue_timeout_seconds"))


def retry_max() -> int:
    return int(runtime_settings.get("retry_max"))


# --- rate limit -------------------------------------------------------------------------

_user_limits: dict[str, tuple[float, str | None]] = {}
_user_lock = threading.Lock()


def _personal_limit(user_id: str) -> str | None:
    now = time.monotonic()
    with _user_lock:
        hit = _user_limits.get(user_id)
        if hit and now - hit[0] < USER_LIMIT_CACHE_SECONDS:
            return hit[1]
    value = None
    try:
        from app.core.db import session_scope
        from app.core.models import User

        with session_scope() as s:
            value = s.scalar(select(User.solve_rate_limit).where(User.id == uuid.UUID(user_id)))
    except Exception:
        log.warning("could not read the personal limit of %s", user_id, exc_info=True)
    with _user_lock:
        _user_limits[user_id] = (now, value)
    return value


def forget_user_limit(user_id: uuid.UUID | str) -> None:
    with _user_lock:
        _user_limits.pop(str(user_id), None)


def solve_rate_limit(key: str) -> str:
    """slowapi limit provider. `key` is ratelimit.user_key's "user:<id>"."""
    if key.startswith("user:"):
        personal = _personal_limit(key.removeprefix("user:"))
        if personal:
            return personal
    return runtime_settings.get("solve_rate_limit")
