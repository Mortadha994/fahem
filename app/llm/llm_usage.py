"""What every Groq call cost, for the admin console's AI monitoring page.

llm_queue opens a CallRecord around each Groq call (groq_call_steps, and
llm_stream.stream_groq for the streamed solve): the time in line, the time
holding the slot, the 429s met, the token usage Groq reports, and how it
ended. finish() hands the row to one background writer thread, so recording
never adds a database round trip to a student's request - and never breaks
one: a database that is down loses monitoring rows, logged, nothing else.

Groq's daily token limit is not in its response headers, only in a 429's
body ("tokens per day (TPD): Limit 200000, Used 199009"). When a call meets
one, the figures are kept in Redis for a day (note_daily_limit), so the
console can show what Groq itself counts, not only what this app recorded.

Does not import llm_queue (llm_queue imports this).
"""

from __future__ import annotations

import logging
import queue
import re
import threading
import time
import uuid
from dataclasses import dataclass, field

from app.core.config import LLM_USAGE_RECORDING, REDIS_URL

log = logging.getLogger("fahem.llm_usage")

STATUS_OK = "ok"
STATUS_RATE_LIMITED = "rate_limited"
STATUS_QUEUE_TIMEOUT = "queue_timeout"
STATUS_ERROR = "error"
STATUS_CANCELLED = "cancelled"

_DAILY = re.compile(r"per day \((TPD|RPD)\): Limit (\d+), Used (\d+)")
# How much of today Groq says we have spent: about today, worthless tomorrow.
_LIMITS_TTL_SECONDS = 24 * 3600
# The ceiling itself: a property of the account's tier, not of the day, and
# only ever learned from a 429 - which can be a week apart. Kept long enough
# that the console shows a figure Groq actually stated rather than the
# compiled-in default, which it silently reverted to a day after the last one.
_CEILING_TTL_SECONDS = 30 * 24 * 3600


def limits_key(model: str) -> str:
    return f"groq:limits:{model}"


def ceiling_key(model: str) -> str:
    return f"groq:ceiling:{model}"


@dataclass
class CallRecord:
    """One Groq call, filled in as it goes. Times are monotonic seconds."""

    model: str
    kind: str
    started: float = field(default_factory=time.monotonic)
    admitted: float | None = None
    rate_limit_hits: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    status: str = STATUS_OK
    detail: str | None = None
    # Solves only: the prompt that answered, and the session memory it carried.
    route: str | None = None
    memory_chars: int = 0
    # The account the call was made for, when there is one. A warm-up or an
    # admin-triggered call leaves it None, which is what the column stores.
    user_id: uuid.UUID | None = None
    _done: bool = False

    def mark_admitted(self) -> None:
        self.admitted = time.monotonic()

    def add_usage(self, usage: dict | None) -> None:
        """Groq's `usage` object (non-streamed body, or a stream's last chunk)."""
        if not isinstance(usage, dict):
            return
        self.prompt_tokens = int(usage.get("prompt_tokens") or 0)
        self.completion_tokens = int(usage.get("completion_tokens") or 0)
        self.total_tokens = int(
            usage.get("total_tokens") or self.prompt_tokens + self.completion_tokens
        )

    def fail(self, status: str, detail: str | None = None) -> None:
        self.status = status
        self.detail = (detail or "")[:200] or None

    def row(self) -> dict:
        now = time.monotonic()
        admitted = self.admitted if self.admitted is not None else now
        return {
            "model": self.model,
            "kind": self.kind,
            "status": self.status,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "queue_wait_ms": int(max(0.0, admitted - self.started) * 1000),
            "latency_ms": int(max(0.0, now - admitted) * 1000) if self.admitted else 0,
            "rate_limit_hits": self.rate_limit_hits,
            "detail": self.detail,
            "route": self.route,
            "memory_chars": self.memory_chars,
            "user_id": self.user_id,
        }

    def finish(self) -> None:
        """Record once; later calls are ignored."""
        if self._done:
            return
        self._done = True
        if LLM_USAGE_RECORDING:
            submit(self.row())


def classify_failure(record: CallRecord, exc: BaseException, *, queue_timeout: type) -> None:
    """Set the record's status from the exception that ended the call."""
    import urllib.error

    if isinstance(exc, GeneratorExit):
        record.fail(STATUS_CANCELLED)
    elif isinstance(exc, queue_timeout):
        record.fail(STATUS_QUEUE_TIMEOUT, "no slot within the wait budget")
    elif isinstance(exc, urllib.error.HTTPError) and exc.code == 429:
        record.fail(STATUS_RATE_LIMITED, getattr(exc, "fahem_limit", None) or "HTTP 429")
    elif isinstance(exc, urllib.error.HTTPError):
        record.fail(STATUS_ERROR, f"HTTP {exc.code}")
    else:
        record.fail(STATUS_ERROR, type(exc).__name__)


def note_429(record: CallRecord | None, model: str, exc) -> None:
    """Count a 429 and, when its body names a daily limit, keep the figures.

    The body is read once here; nothing else in the app reads a 429's body.
    The limit name is left on the exception so the record's detail says which
    limit it was.
    """
    if record is not None:
        record.rate_limit_hits += 1
    if getattr(exc, "fahem_limit_read", False):
        return
    exc.fahem_limit_read = True
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        return
    match = _DAILY.search(body)
    if match:
        which, limit, used = match.group(1), int(match.group(2)), int(match.group(3))
        exc.fahem_limit = "tokens per day" if which == "TPD" else "requests per day"
        note_daily_limit(model, which, limit, used)
    elif "per minute" in body:
        exc.fahem_limit = "tokens per minute"


def note_daily_limit(model: str, which: str, limit: int, used: int) -> None:
    """Keep what a 429 body revealed: the ceiling, and where we were against it.

    Two different lifetimes, in two keys, because the two facts age
    differently. `used` describes one particular day and is worthless
    tomorrow. The *limit* is a property of the Groq account's tier: it does
    not change because a day passed, and it is only ever learned from a 429,
    which may not happen again for a week.

    Keeping both for a day - as this did - meant the console quietly fell back
    to config.GROQ_TPD_LIMIT 24 hours after the last daily 429, and went on
    presenting a compiled-in guess as a measurement. Observed doing exactly
    that: the last daily 429 was five days old and the figure had been a
    default for four of them.
    """
    now = int(time.time())
    name = which.lower()
    try:
        client = _redis()
        client.hset(
            limits_key(model),
            mapping={f"{name}_used": used, f"{name}_at": now},
        )
        client.expire(limits_key(model), _LIMITS_TTL_SECONDS)
        client.hset(
            ceiling_key(model),
            mapping={f"{name}_limit": limit, f"{name}_limit_at": now},
        )
        client.expire(ceiling_key(model), _CEILING_TTL_SECONDS)
    except Exception:
        log.warning("could not store Groq's daily %s figures for %s", which, model, exc_info=True)


def daily_limits(model: str) -> dict[str, int]:
    """What Groq's 429s have revealed: today's usage, and the ceiling.

    The two come from different keys with different lifetimes (see
    note_daily_limit) and are merged here, so callers still read one mapping.
    """
    try:
        client = _redis()
        raw = dict(client.hgetall(limits_key(model)))
        raw.update(client.hgetall(ceiling_key(model)))
    except Exception:
        return {}
    out: dict[str, int] = {}
    for name, value in raw.items():
        name = name.decode() if isinstance(name, bytes) else name
        try:
            out[name] = int(value)
        except (TypeError, ValueError):
            continue
    return out


# --- the writer -----------------------------------------------------------------

_rows: queue.Queue[dict] = queue.Queue(maxsize=10_000)
_writer: threading.Thread | None = None
_writer_lock = threading.Lock()
_redis_client = None


def _redis():
    global _redis_client
    if _redis_client is None:
        import redis

        _redis_client = redis.Redis.from_url(REDIS_URL, socket_timeout=2)
    return _redis_client


def submit(row: dict) -> None:
    global _writer
    try:
        _rows.put_nowait(row)
    except queue.Full:
        log.warning("llm usage queue full; dropping a monitoring row")
        return
    if _writer is None or not _writer.is_alive():
        with _writer_lock:
            if _writer is None or not _writer.is_alive():
                _writer = threading.Thread(target=_write_loop, name="llm-usage", daemon=True)
                _writer.start()


def _write_loop() -> None:
    while True:
        batch = [_rows.get()]
        while len(batch) < 100:
            try:
                batch.append(_rows.get_nowait())
            except queue.Empty:
                break
        try:
            write_rows(batch)
        except Exception:
            log.warning("could not record %d llm call(s)", len(batch), exc_info=True)
        finally:
            for _ in batch:
                _rows.task_done()


def write_rows(rows: list[dict]) -> None:
    from app.core.db import session_scope
    from app.core.models import LlmCall

    with session_scope() as s:
        s.add_all(LlmCall(**row) for row in rows)


def flush(timeout: float = 5.0) -> bool:
    """Wait for pending rows to be written (tests). True if all were."""
    deadline = time.monotonic() + timeout
    while _rows.unfinished_tasks and time.monotonic() < deadline:
        time.sleep(0.02)
    return not _rows.unfinished_tasks
