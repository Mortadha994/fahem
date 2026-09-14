"""A priority-aware queue in front of Groq, on Redis.

Groq's per-minute token limit applies per model, to the whole account: every
solve and every gatekeeper call draw on gpt-oss-120b's budget, every photo
transcription on the vision model's. When it is exhausted Groq answers 429 at
once, and the student used to see "Le service est très sollicité" straight
away. This module lets a request wait its turn instead: callers acquire a slot
on a shared key (one per model), at most `max_concurrent` requests hold one at
a time, and the rest wait in priority order.

Named llm_queue, not queue: a top-level queue.py shadows the standard
library's `queue`, which redis-py, torch and concurrent.futures all import -
the backend would not start.

Every Groq call goes through it: generate.call_groq, llm_stream.stream_groq,
gatekeeper's classifier and meta-responder, and attachments' transcription.
They are synchronous, so they use the synchronous twin (SyncWaiter,
acquire_sync, groq_call) - same keys, same Lua scripts as the async
`acquire`. Groq limits each model separately, so each model has its own line
(groq_queue_key), and a slot holder that gets a 429 sleeps Groq's Retry-After
and retries in place (next_retry_delay) before the error reaches a student.

How it works - three sorted sets per key, all touched only by the Lua scripts
below, so every decision is atomic across processes:

  waiting  ticket -> priority * 10^13 + enqueued_at_ms
           Lowest score is served first: a lower priority number wins, and
           equal priorities break ties by arrival (FIFO). 10^13 ms is far past
           any real timestamp, so priority always dominates.
  active   ticket -> lease expiry (ms). A slot is a lease, renewed by a
           heartbeat while held, so a process that dies holding one cannot
           leak it: the lease runs out and the slot is reclaimed.
  seen     ticket -> waiter expiry (ms). A waiter refreshes this every time it
           polls; one that stops (crash, dropped client) is purged, so a dead
           request never blocks the line.

Time comes from Redis (TIME inside the scripts), not from each process, so
several backend processes agree on who arrived first and when a lease expires.

A waiter is admitted when a slot is free AND it is among the first `free`
tickets in line - never ahead of a better-placed waiter.

Priority: `priority_for(plan)` gives paid accounts 0 and everyone else 1.
Every account is free today, so everyone shares one priority and the queue is
plain FIFO; a paid tier later needs no change here.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import math
import re
import threading
import time
import urllib.error
import uuid
import weakref
from contextlib import asynccontextmanager, contextmanager, suppress
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable, Iterator, TypeVar

import redis as sync_redis
import redis.asyncio as aioredis

from config import (
    GROQ_MAX_CONCURRENT,
    GROQ_QUEUE_TIMEOUT_SECONDS,
    GROQ_RETRY_MAX,
    GROQ_VISION_MAX_CONCURRENT,
    GROQ_VISION_MODEL,
    REDIS_URL,
)

log = logging.getLogger("fahem.llm_queue")
T = TypeVar("T")

PRIORITY_PAID = 0
PRIORITY_FREE = 1

# A held slot whose heartbeat stops is reclaimed after this long. Longer than
# any heartbeat gap, shorter than a student will wait for nothing.
LEASE_SECONDS = 60.0
# A waiter that stops polling for this long is dropped from the line.
WAITER_TTL_SECONDS = 15.0
POLL_SECONDS = 0.1
# Used for the wait estimate until real hold times have been measured.
DEFAULT_HOLD_SECONDS = 8.0

_KEY_PREFIX = "llmq"
_PRIORITY_SPAN = 10**13
# Idle queue keys expire on their own rather than lingering in Redis forever.
_KEY_TTL_MS = 3_600_000


def priority_for(plan: str | None) -> int:
    """Queue priority for an account's plan: lower is served first."""
    return PRIORITY_PAID if plan == "paid" else PRIORITY_FREE


class QueueTimeout(Exception):
    """Waited longer than `timeout` without getting a slot. The caller turns
    this into the "le service est très sollicité" message."""

    def __init__(self, key: str, waited: float, position: int | None):
        super().__init__(f"queue {key!r}: no slot after {waited:.1f}s (position {position})")
        self.key = key
        self.waited = waited
        self.position = position


@dataclass
class Slot:
    """What `acquire` yields once admitted."""

    key: str
    ticket: str
    waited: float


@dataclass
class Snapshot:
    waiting: int
    active: int
    avg_hold_seconds: float


def _keys(key: str) -> tuple[str, str, str, str]:
    base = f"{_KEY_PREFIX}:{key}"
    return f"{base}:waiting", f"{base}:active", f"{base}:seen", f"{base}:stats"


_NOW_MS = "local t = redis.call('TIME') local now = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)"

# KEYS: waiting, seen. ARGV: ticket, priority, waiter_ttl_ms, key_ttl_ms, [enqueued_ms]
# A re-enqueue passes its original enqueued_ms, so it keeps its place.
_ENQUEUE = f"""
{_NOW_MS}
local enqueued = tonumber(ARGV[5]) or now
redis.call('ZADD', KEYS[1], tonumber(ARGV[2]) * {_PRIORITY_SPAN} + enqueued, ARGV[1])
redis.call('ZADD', KEYS[2], now + tonumber(ARGV[3]), ARGV[1])
redis.call('PEXPIRE', KEYS[1], ARGV[4])
redis.call('PEXPIRE', KEYS[2], ARGV[4])
return enqueued
"""

# KEYS: waiting, active, seen. ARGV: ticket, max_concurrent, lease_ms, waiter_ttl_ms, key_ttl_ms
# Returns -1 admitted, -2 ticket no longer in line (re-enqueue), else 0-based position.
_ADMIT = f"""
{_NOW_MS}
local ticket = ARGV[1]
redis.call('ZREMRANGEBYSCORE', KEYS[2], '-inf', now)
local dead = redis.call('ZRANGEBYSCORE', KEYS[3], '-inf', now)
for _, member in ipairs(dead) do
  if member ~= ticket then
    redis.call('ZREM', KEYS[1], member)
    redis.call('ZREM', KEYS[3], member)
  end
end
if not redis.call('ZSCORE', KEYS[1], ticket) then
  return -2
end
redis.call('ZADD', KEYS[3], now + tonumber(ARGV[4]), ticket)
local rank = redis.call('ZRANK', KEYS[1], ticket)
local free = tonumber(ARGV[2]) - redis.call('ZCARD', KEYS[2])
if free > 0 and rank < free then
  redis.call('ZREM', KEYS[1], ticket)
  redis.call('ZREM', KEYS[3], ticket)
  redis.call('ZADD', KEYS[2], now + tonumber(ARGV[3]), ticket)
  redis.call('PEXPIRE', KEYS[2], ARGV[5])
  return -1
end
return rank
"""

# KEYS: active. ARGV: ticket, lease_ms. Renews a lease only if still held.
_RENEW = f"""
{_NOW_MS}
return redis.call('ZADD', KEYS[1], 'XX', now + tonumber(ARGV[2]), ARGV[1])
"""

_clients: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, aioredis.Redis]" = (
    weakref.WeakKeyDictionary()
)


def _client() -> aioredis.Redis:
    """One async client per event loop: a redis.asyncio connection is bound to
    the loop that opened it."""
    loop = asyncio.get_running_loop()
    client = _clients.get(loop)
    if client is None:
        client = aioredis.from_url(REDIS_URL, decode_responses=True)
        _clients[loop] = client
    return client


async def _call(result: Any) -> None:
    if inspect.isawaitable(result):
        await result


async def snapshot(key: str, *, client: aioredis.Redis | None = None) -> Snapshot:
    """How busy a queue is right now."""
    r = client or _client()
    waiting, active, _seen, stats = _keys(key)
    n_waiting, n_active, avg = await asyncio.gather(
        r.zcard(waiting), r.zcard(active), r.hget(stats, "avg_hold")
    )
    return Snapshot(int(n_waiting), int(n_active), float(avg) if avg else DEFAULT_HOLD_SECONDS)


async def estimated_wait(
    key: str, position: int, max_concurrent: int, *, client: aioredis.Redis | None = None
) -> float:
    """Rough seconds until a waiter at `position` (0-based) gets a slot: each
    batch of `max_concurrent` ahead of it takes about one average hold."""
    snap = await snapshot(key, client=client)
    return snap.avg_hold_seconds * math.ceil((position + 1) / max(1, max_concurrent))


async def _discard(r: aioredis.Redis, key: str, ticket: str) -> None:
    waiting, active, seen, _stats = _keys(key)
    async with r.pipeline(transaction=True) as pipe:
        pipe.zrem(waiting, ticket).zrem(seen, ticket).zrem(active, ticket)
        await pipe.execute()


async def _release(r: aioredis.Redis, key: str, ticket: str, held: float) -> None:
    waiting, active, _seen, stats = _keys(key)
    await r.zrem(active, ticket)
    # A running average of hold times, for the wait estimate. Stats only, so a
    # lost update between two processes is harmless.
    previous = await r.hget(stats, "avg_hold")
    average = held if previous is None else 0.8 * float(previous) + 0.2 * held
    await r.hset(stats, "avg_hold", f"{average:.3f}")
    await r.pexpire(stats, _KEY_TTL_MS)


async def _heartbeat(r: aioredis.Redis, key: str, ticket: str, lease_seconds: float) -> None:
    _waiting, active, _seen, _stats = _keys(key)
    renew = r.register_script(_RENEW)
    while True:
        await asyncio.sleep(lease_seconds / 3)
        await renew(keys=[active], args=[ticket, int(lease_seconds * 1000)])


@asynccontextmanager
async def acquire(
    key: str,
    priority: int,
    max_concurrent: int,
    timeout: float,
    *,
    on_wait: Callable[[int, float], Any] | None = None,
    lease_seconds: float = LEASE_SECONDS,
    waiter_ttl_seconds: float = WAITER_TTL_SECONDS,
    poll_seconds: float = POLL_SECONDS,
    client: aioredis.Redis | None = None,
) -> AsyncIterator[Slot]:
    """Wait for a slot on `key`, hold it for the `async with` block, release it.

        async with llm_queue.acquire("groq", priority, max_concurrent=4, timeout=60):
            ...call Groq...

    Admitted when fewer than `max_concurrent` requests hold a slot and no
    better-placed waiter is ahead (lower `priority` first, then arrival).
    Raises QueueTimeout after `timeout` seconds without a slot; the ticket is
    removed from the line either way, and on cancellation too (a client that
    disconnects while waiting). The slot is released when the block exits,
    by success or by exception.

    `on_wait(position, estimated_seconds)` - sync or async - is called each
    time the 0-based position changes while waiting, for a "you are Nth in
    line" message.
    """
    if max_concurrent < 1:
        raise ValueError("max_concurrent must be at least 1")
    r = client or _client()
    loop = asyncio.get_running_loop()
    waiting, active, seen, _stats = _keys(key)
    enqueue = r.register_script(_ENQUEUE)
    admit = r.register_script(_ADMIT)
    ticket = uuid.uuid4().hex
    waiter_ttl_ms = int(waiter_ttl_seconds * 1000)
    started = loop.time()

    admitted = False
    try:
        enqueued_ms = await enqueue(
            keys=[waiting, seen], args=[ticket, priority, waiter_ttl_ms, _KEY_TTL_MS]
        )
        last_position: int | None = None
        while True:
            result = int(
                await admit(
                    keys=[waiting, active, seen],
                    args=[
                        ticket,
                        max_concurrent,
                        int(lease_seconds * 1000),
                        waiter_ttl_ms,
                        _KEY_TTL_MS,
                    ],
                )
            )
            if result == -1:
                admitted = True
                break
            if result == -2:
                # Purged as dead (this process stalled past the waiter TTL):
                # rejoin at the original arrival time, so the place is kept.
                await enqueue(
                    keys=[waiting, seen],
                    args=[ticket, priority, waiter_ttl_ms, _KEY_TTL_MS, enqueued_ms],
                )
                continue
            waited = loop.time() - started
            if waited >= timeout:
                raise QueueTimeout(key, waited, result)
            if on_wait is not None and result != last_position:
                last_position = result
                eta = await estimated_wait(key, result, max_concurrent, client=r)
                await _call(on_wait(result, eta))
            await asyncio.sleep(poll_seconds)
    except BaseException:
        if not admitted:
            # Also clears `active`: a cancellation can land after the script
            # admitted the ticket but before the result reached us.
            await asyncio.shield(_discard(r, key, ticket))
        raise

    heartbeat = asyncio.create_task(_heartbeat(r, key, ticket, lease_seconds))
    held_from = loop.time()
    try:
        yield Slot(key=key, ticket=ticket, waited=held_from - started)
    finally:
        heartbeat.cancel()
        # A heartbeat that died on a Redis error must not replace the block's
        # own exception; the release below still runs.
        with suppress(asyncio.CancelledError, Exception):
            await heartbeat
        await asyncio.shield(_release(r, key, ticket, loop.time() - held_from))


# --- synchronous twin ------------------------------------------------------------
#
# The Groq call sites are synchronous (urllib, and a sync generator for the
# stream that FastAPI runs in a worker thread), so they need the same queue
# without an event loop. Same keys, same Lua scripts: a sync waiter and an
# async one share one line and one set of slots.


@dataclass
class Waiting:
    """Yielded while a request cannot proceed yet.

    `reason` is "queue" (another request holds the slot; `position` is the
    0-based place in line) or "rate_limited" (this request holds the slot but
    Groq answered 429; `estimated_seconds` is Groq's Retry-After)."""

    position: int
    estimated_seconds: float
    reason: str = "queue"


_sync_clients: dict[str, Any] = {}
_sync_lock = threading.Lock()


def _sync_client():
    """One sync client for the process. redis-py's sync client is thread-safe
    (a connection pool underneath), so every worker thread shares it."""
    with _sync_lock:
        client = _sync_clients.get(REDIS_URL)
        if client is None:
            client = sync_redis.Redis.from_url(REDIS_URL, decode_responses=True)
            _sync_clients[REDIS_URL] = client
        return client


def snapshot_sync(key: str, *, client=None) -> Snapshot:
    r = client or _sync_client()
    waiting, active, _seen, stats = _keys(key)
    with r.pipeline(transaction=False) as pipe:
        n_waiting, n_active, avg = (
            pipe.zcard(waiting).zcard(active).hget(stats, "avg_hold").execute()
        )
    return Snapshot(int(n_waiting), int(n_active), float(avg) if avg else DEFAULT_HOLD_SECONDS)


class SyncWaiter:
    """The queue for synchronous code, in two steps so a generator can report
    progress while it waits:

        with SyncWaiter(key, priority, max_concurrent, timeout) as waiter:
            for waiting in waiter.wait():   # yields Waiting while in line
                ...                          # e.g. forward it as an SSE event
            ...call Groq...                  # the slot is held here

    `wait()` returns once admitted and raises QueueTimeout past `timeout`.
    Leaving the `with` block releases the slot, or leaves the line if never
    admitted - on success, exception, or a generator closed early (a student
    who closes the page while waiting). A heartbeat thread renews the lease
    while the slot is held, including while sleeping on a 429.
    """

    def __init__(
        self,
        key: str,
        priority: int,
        max_concurrent: int,
        timeout: float,
        *,
        lease_seconds: float = LEASE_SECONDS,
        waiter_ttl_seconds: float = WAITER_TTL_SECONDS,
        poll_seconds: float = POLL_SECONDS,
        client=None,
    ):
        if max_concurrent < 1:
            raise ValueError("max_concurrent must be at least 1")
        self.key = key
        self.priority = priority
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.lease_seconds = lease_seconds
        self.waiter_ttl_ms = int(waiter_ttl_seconds * 1000)
        self.poll_seconds = poll_seconds
        self.r = client or _sync_client()
        self.ticket = uuid.uuid4().hex
        self.slot: Slot | None = None
        self._queued = False
        self._held_from = 0.0
        self._stop = threading.Event()
        self._heartbeat: threading.Thread | None = None

    def __enter__(self) -> "SyncWaiter":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def wait(self) -> Iterator[Waiting]:
        waiting, active, seen, _stats = _keys(self.key)
        enqueue = self.r.register_script(_ENQUEUE)
        admit = self.r.register_script(_ADMIT)
        started = time.monotonic()
        enqueued_ms = enqueue(
            keys=[waiting, seen],
            args=[self.ticket, self.priority, self.waiter_ttl_ms, _KEY_TTL_MS],
        )
        self._queued = True
        last_position: int | None = None
        while True:
            result = int(
                admit(
                    keys=[waiting, active, seen],
                    args=[
                        self.ticket,
                        self.max_concurrent,
                        int(self.lease_seconds * 1000),
                        self.waiter_ttl_ms,
                        _KEY_TTL_MS,
                    ],
                )
            )
            if result == -1:
                break
            if result == -2:
                enqueue(
                    keys=[waiting, seen],
                    args=[self.ticket, self.priority, self.waiter_ttl_ms, _KEY_TTL_MS, enqueued_ms],
                )
                continue
            waited = time.monotonic() - started
            if waited >= self.timeout:
                raise QueueTimeout(self.key, waited, result)
            if result != last_position:
                last_position = result
                snap = snapshot_sync(self.key, client=self.r)
                eta = snap.avg_hold_seconds * math.ceil((result + 1) / self.max_concurrent)
                yield Waiting(position=result, estimated_seconds=eta)
            time.sleep(self.poll_seconds)

        self._held_from = time.monotonic()
        self.slot = Slot(key=self.key, ticket=self.ticket, waited=self._held_from - started)
        self._heartbeat = threading.Thread(target=self._renew, name="llm-queue-lease", daemon=True)
        self._heartbeat.start()

    def _renew(self) -> None:
        _waiting, active, _seen, _stats = _keys(self.key)
        renew = self.r.register_script(_RENEW)
        while not self._stop.wait(self.lease_seconds / 3):
            with suppress(Exception):  # a Redis blip must not kill the request
                renew(keys=[active], args=[self.ticket, int(self.lease_seconds * 1000)])

    def close(self) -> None:
        waiting, active, seen, stats = _keys(self.key)
        if self.slot is not None:
            self._stop.set()
            if self._heartbeat is not None:
                self._heartbeat.join(timeout=2)
            held = time.monotonic() - self._held_from
            self.r.zrem(active, self.ticket)
            previous = self.r.hget(stats, "avg_hold")
            average = held if previous is None else 0.8 * float(previous) + 0.2 * held
            self.r.hset(stats, "avg_hold", f"{average:.3f}")
            self.r.pexpire(stats, _KEY_TTL_MS)
            self.slot = None
        elif self._queued:
            # Also clears `active`, for an admission that landed just before
            # an exception reached us.
            with self.r.pipeline(transaction=True) as pipe:
                pipe.zrem(waiting, self.ticket).zrem(seen, self.ticket).zrem(active, self.ticket)
                pipe.execute()
        self._queued = False


@contextmanager
def acquire_sync(
    key: str,
    priority: int,
    max_concurrent: int,
    timeout: float,
    *,
    on_wait: Callable[[int, float], Any] | None = None,
    **options: Any,
) -> Iterator[Slot]:
    """`acquire` for synchronous code: hold a slot for the `with` block."""
    with SyncWaiter(key, priority, max_concurrent, timeout, **options) as waiter:
        for waiting in waiter.wait():
            if on_wait is not None:
                on_wait(waiting.position, waiting.estimated_seconds)
        assert waiter.slot is not None
        yield waiter.slot


# --- Groq: one queue per model, 429 backoff inside the slot -------------------------

_DURATION = re.compile(
    r"(?:(\d+(?:\.\d+)?)h)?(?:(\d+(?:\.\d+)?)m(?!s))?(?:(\d+(?:\.\d+)?)s)?(?:(\d+(?:\.\d+)?)ms)?$"
)
_FALLBACK_RETRY_SECONDS = 5.0


def groq_queue_key(model: str) -> str:
    """Groq limits each model separately, so each model has its own line."""
    return f"groq:{model}"


def groq_max_concurrent(model: str) -> int:
    return GROQ_VISION_MAX_CONCURRENT if model == GROQ_VISION_MODEL else GROQ_MAX_CONCURRENT


def _parse_duration(text: str | None) -> float | None:
    """Groq's reset headers: "547ms", "30.48s", "1m26.4s"."""
    if not text:
        return None
    match = _DURATION.match(text.strip())
    if not match or not any(match.groups()):
        return None
    hours, minutes, seconds, millis = (float(g) if g else 0.0 for g in match.groups())
    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def retry_after_seconds(headers) -> float:
    """How long Groq asks us to wait after a 429: Retry-After when present,
    else the token-bucket reset, else a short default."""
    if headers is not None:
        value = headers.get("retry-after")
        if value:
            with suppress(ValueError):
                return max(0.5, float(value))
        for name in ("x-ratelimit-reset-tokens", "x-ratelimit-reset-requests"):
            parsed = _parse_duration(headers.get(name))
            if parsed is not None:
                return max(0.5, parsed)
    return _FALLBACK_RETRY_SECONDS


def next_retry_delay(
    exc: Exception,
    attempts: int,
    waited: float,
    *,
    max_retries: int | None = None,
    budget: float | None = None,
) -> float | None:
    """The retry policy, in one place: seconds to sleep before trying the same
    Groq call again, or None to give up and let the error through.

    Only a 429 is retried; at most `max_retries` times; and never if the
    total sleep would pass `budget` (the queue timeout) - a student is not
    kept waiting longer than the queue itself would allow.
    """
    max_retries = GROQ_RETRY_MAX if max_retries is None else max_retries
    budget = GROQ_QUEUE_TIMEOUT_SECONDS if budget is None else budget
    if not isinstance(exc, urllib.error.HTTPError) or exc.code != 429:
        return None
    if attempts >= max_retries:
        return None
    delay = retry_after_seconds(exc.headers)
    if waited + delay > budget:
        return None
    return delay


def groq_call(
    model: str,
    priority: int,
    send: Callable[[], T],
    *,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Run one Groq request through its model's queue, retrying a 429 inside
    the held slot per next_retry_delay. Raises QueueTimeout if no slot came in
    time, or the last HTTPError once retrying is not allowed."""
    key = groq_queue_key(model)
    with acquire_sync(key, priority, groq_max_concurrent(model), GROQ_QUEUE_TIMEOUT_SECONDS):
        attempts = 0
        waited = 0.0
        while True:
            try:
                return send()
            except urllib.error.HTTPError as exc:
                delay = next_retry_delay(exc, attempts, waited)
                if delay is None:
                    raise
                log.warning(
                    "groq 429 on %s: retry %d/%d in %.1fs (holding the slot)",
                    model,
                    attempts + 1,
                    GROQ_RETRY_MAX,
                    delay,
                )
                sleep(delay)
                waited += delay
                attempts += 1
