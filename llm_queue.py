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
groq_call_steps / groq_call) - same keys, same Lua scripts as the async
`acquire`. Groq limits each model separately, so each model has its own line
(groq_queue_key), and a slot holder that gets a 429 sleeps Groq's Retry-After
and retries in place (next_retry_delay) before the error reaches a student.

One deadline per student request (WaitBudget): the time spent in any queue
and every 429 sleep all come out of the same GROQ_QUEUE_TIMEOUT_SECONDS, so a
request that classifies, then solves, never waits longer than that in total.

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

Beside them, for the wait estimate only: `kinds` (ticket -> what the request
is: gatekeeper, solve, transcription), `starts` (ticket -> when it got its
slot) and `stats` (a running average hold time per kind). A gatekeeper call
holds a slot for ~0.2s and a solve for ~5-35s, so one shared average made a
~30s wait look like 1-2s; the estimate now adds up the actual kinds ahead.

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
import re
import threading
import time
import urllib.error
import uuid
import weakref
from contextlib import asynccontextmanager, contextmanager, suppress
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Generator, Iterator, TypeVar

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

# What a request is, for the per-kind wait estimate.
KIND_GATEKEEPER = "gatekeeper"
KIND_SOLVE = "solve"
KIND_TRANSCRIPTION = "transcription"
KIND_DEFAULT = "default"

# Two independent priority axes, combined into the one number the queue sorts
# by (queue_priority). The kind tier puts the gatekeeper's classification -
# ~686 tokens, ~0.2s - ahead of any solve or transcription, so a student is not
# kept waiting behind whole solves just to find out whether their message is an
# exercise. The plan tier (priority_for) still orders requests within a kind.
KIND_TIER = {
    KIND_GATEKEEPER: 0,
    KIND_SOLVE: 1,
    KIND_TRANSCRIPTION: 1,
    KIND_DEFAULT: 1,
}
# Larger than any plan tier, so a plan can never lift a solve above a
# classification (plan tiers are 0 and 1 today).
KIND_TIER_SPAN = 10

# A held slot whose heartbeat stops is reclaimed after this long. Longer than
# any heartbeat gap, shorter than a student will wait for nothing.
LEASE_SECONDS = 60.0
# A waiter that stops polling for this long is dropped from the line.
WAITER_TTL_SECONDS = 15.0
POLL_SECONDS = 0.1
# Used for the wait estimate until real hold times have been measured.
DEFAULT_HOLD_SECONDS = 8.0
DEFAULT_HOLD_BY_KIND = {
    KIND_GATEKEEPER: 1.0,
    KIND_SOLVE: 8.0,
    KIND_TRANSCRIPTION: 2.0,
}

_KEY_PREFIX = "llmq"
_PRIORITY_SPAN = 10**13
# Idle queue keys expire on their own rather than lingering in Redis forever.
_KEY_TTL_MS = 3_600_000


def priority_for(plan: str | None) -> int:
    """Queue priority for an account's plan: lower is served first."""
    return PRIORITY_PAID if plan == "paid" else PRIORITY_FREE


def queue_priority(kind: str, plan_priority: int) -> int:
    """The value a Groq call is queued at: kind first, then plan.

    kind_tier * KIND_TIER_SPAN + plan_tier - every classification ranks ahead
    of every solve, whatever the plans; within one kind a paid account ranks
    ahead of a free one. Callers pass the plan priority; this is the only
    place the two are combined.
    """
    if not 0 <= plan_priority < KIND_TIER_SPAN:
        raise ValueError(f"plan priority {plan_priority} outside 0..{KIND_TIER_SPAN - 1}")
    return KIND_TIER.get(kind, KIND_TIER[KIND_DEFAULT]) * KIND_TIER_SPAN + plan_priority


class QueueTimeout(Exception):
    """Waited longer than allowed without getting a slot. The caller turns
    this into the "le service est très sollicité" message."""

    def __init__(self, key: str, waited: float, position: int | None):
        super().__init__(f"queue {key!r}: no slot after {waited:.1f}s (position {position})")
        self.key = key
        self.waited = waited
        self.position = position


class WaitBudget:
    """How long one student request may spend waiting, in total.

    Shared by every Groq call the request makes (the classifier, then the
    solve) and charged for both kinds of wait: time in a queue, and every
    sleep on a 429. The Groq calls themselves - generating an answer - are not
    waiting and are not charged. Once it is spent, the next queue wait times
    out at once and no 429 is retried, so the student gets the busy error
    within GROQ_QUEUE_TIMEOUT_SECONDS rather than twice that.
    """

    def __init__(self, total: float | None = None):
        self.total = GROQ_QUEUE_TIMEOUT_SECONDS if total is None else total
        self.spent = 0.0

    def remaining(self) -> float:
        return max(0.0, self.total - self.spent)

    def charge(self, seconds: float) -> None:
        self.spent += max(0.0, seconds)


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
    # Measured average hold per kind; a kind not yet measured is absent.
    avg_hold: dict[str, float] = field(default_factory=dict)


@dataclass
class Waiting:
    """Yielded while a request cannot proceed yet.

    `reason` is "queue" (another request holds the slot; `position` is the
    0-based place in line) or "rate_limited" (this request holds the slot but
    Groq answered 429; `estimated_seconds` is Groq's Retry-After). `kind` is
    what is waiting: the gatekeeper's classification, the solve, a
    transcription."""

    position: int
    estimated_seconds: float
    reason: str = "queue"
    kind: str = KIND_DEFAULT


def _keys(key: str) -> tuple[str, str, str, str]:
    base = f"{_KEY_PREFIX}:{key}"
    return f"{base}:waiting", f"{base}:active", f"{base}:seen", f"{base}:stats"


def _meta_keys(key: str) -> tuple[str, str]:
    base = f"{_KEY_PREFIX}:{key}"
    return f"{base}:kinds", f"{base}:starts"


def all_keys(key: str) -> tuple[str, ...]:
    """Every Redis key a queue uses - for tests and cleanup."""
    return (*_keys(key), *_meta_keys(key))


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


# --- wait estimate (shared by the async and sync paths) ------------------------------


def _avg_hold(avgs: dict[str, float], kind: str) -> float:
    measured = avgs.get(kind)
    if measured is not None:
        return measured
    return DEFAULT_HOLD_BY_KIND.get(kind, DEFAULT_HOLD_SECONDS)


def estimate_seconds(
    ahead_kinds: list[str],
    active: list[tuple[str, float]],
    avgs: dict[str, float],
    max_concurrent: int,
) -> float:
    """Seconds until a waiter gets a slot: what is left of each current
    holder's average hold (for its own kind), plus a full average hold for
    each request ahead (for its own kind), spread over the slots. Exact in
    expectation for one slot, which is what Groq's budget allows today."""
    left_active = sum(max(0.0, _avg_hold(avgs, kind) - elapsed) for kind, elapsed in active)
    ahead = sum(_avg_hold(avgs, kind) for kind in ahead_kinds)
    return max(0.5, (left_active + ahead) / max(1, max_concurrent))


def _parse_avgs(stats: dict[str, str]) -> dict[str, float]:
    out: dict[str, float] = {}
    for name, value in (stats or {}).items():
        if name.startswith("avg_hold:"):
            with suppress(ValueError):
                out[name[len("avg_hold:") :]] = float(value)
    return out


def _new_average(previous: str | None, held: float) -> str:
    average = held if previous is None else 0.8 * float(previous) + 0.2 * held
    return f"{average:.3f}"


def _now_ms_from(redis_time: tuple[int, int] | list[int]) -> int:
    seconds, micros = redis_time
    return int(seconds) * 1000 + int(micros) // 1000


# --- async ---------------------------------------------------------------------------

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
    n_waiting, n_active, raw_stats = await asyncio.gather(
        r.zcard(waiting), r.zcard(active), r.hgetall(stats)
    )
    return Snapshot(int(n_waiting), int(n_active), _parse_avgs(raw_stats))


async def estimated_wait(
    key: str, position: int, max_concurrent: int, *, client: aioredis.Redis | None = None
) -> float:
    """Rough seconds until a waiter at `position` (0-based) gets a slot."""
    r = client or _client()
    waiting, active, _seen, stats = _keys(key)
    kinds, starts = _meta_keys(key)
    ahead = await r.zrange(waiting, 0, position - 1) if position > 0 else []
    holders = await r.zrange(active, 0, -1)
    tickets = [*ahead, *holders]
    kind_values = await r.hmget(kinds, tickets) if tickets else []
    start_values = await r.hmget(starts, holders) if holders else []
    raw_stats, redis_time = await asyncio.gather(r.hgetall(stats), r.time())
    now_ms = _now_ms_from(redis_time)
    ahead_kinds = [k or KIND_DEFAULT for k in kind_values[: len(ahead)]]
    holder_kinds = [k or KIND_DEFAULT for k in kind_values[len(ahead) :]]
    elapsed = [max(0.0, (now_ms - int(s)) / 1000) if s else 0.0 for s in start_values]
    return estimate_seconds(
        ahead_kinds, list(zip(holder_kinds, elapsed)), _parse_avgs(raw_stats), max_concurrent
    )


async def _discard(r: aioredis.Redis, key: str, ticket: str) -> None:
    waiting, active, seen, _stats = _keys(key)
    kinds, starts = _meta_keys(key)
    async with r.pipeline(transaction=True) as pipe:
        pipe.zrem(waiting, ticket).zrem(seen, ticket).zrem(active, ticket)
        pipe.hdel(kinds, ticket).hdel(starts, ticket)
        await pipe.execute()


async def _release(r: aioredis.Redis, key: str, ticket: str, kind: str, held: float) -> None:
    waiting, active, _seen, stats = _keys(key)
    kinds, starts = _meta_keys(key)
    await r.zrem(active, ticket)
    await r.hdel(kinds, ticket)
    await r.hdel(starts, ticket)
    # A running average of hold times per kind, for the wait estimate. Stats
    # only, so a lost update between two processes is harmless.
    field_name = f"avg_hold:{kind}"
    previous = await r.hget(stats, field_name)
    await r.hset(stats, field_name, _new_average(previous, held))
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
    kind: str = KIND_DEFAULT,
    on_wait: Callable[[int, float], Any] | None = None,
    lease_seconds: float = LEASE_SECONDS,
    waiter_ttl_seconds: float = WAITER_TTL_SECONDS,
    poll_seconds: float = POLL_SECONDS,
    client: aioredis.Redis | None = None,
) -> AsyncIterator[Slot]:
    """Wait for a slot on `key`, hold it for the `async with` block, release it.

        async with llm_queue.acquire("groq:model", priority, max_concurrent=4, timeout=60):
            ...call Groq...

    Admitted when fewer than `max_concurrent` requests hold a slot and no
    better-placed waiter is ahead (lower `priority` first, then arrival).
    Raises QueueTimeout after `timeout` seconds without a slot; the ticket is
    removed from the line either way, and on cancellation too (a client that
    disconnects while waiting). The slot is released when the block exits,
    by success or by exception.

    `on_wait(position, estimated_seconds)` - sync or async - is called each
    time the 0-based position changes while waiting, for a "you are Nth in
    line" message. `kind` feeds the per-kind wait estimate.
    """
    if max_concurrent < 1:
        raise ValueError("max_concurrent must be at least 1")
    r = client or _client()
    loop = asyncio.get_running_loop()
    waiting, active, seen, _stats = _keys(key)
    kinds, starts = _meta_keys(key)
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
        await r.hset(kinds, ticket, kind)
        await r.pexpire(kinds, _KEY_TTL_MS)
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
        await r.hset(starts, ticket, _now_ms_from(await r.time()))
        await r.pexpire(starts, _KEY_TTL_MS)
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
        await asyncio.shield(_release(r, key, ticket, kind, loop.time() - held_from))


# --- synchronous twin ------------------------------------------------------------
#
# The Groq call sites are synchronous (urllib, and a sync generator for the
# stream that FastAPI runs in a worker thread), so they need the same queue
# without an event loop. Same keys, same Lua scripts: a sync waiter and an
# async one share one line and one set of slots.

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
        n_waiting, n_active, raw_stats = pipe.zcard(waiting).zcard(active).hgetall(stats).execute()
    return Snapshot(int(n_waiting), int(n_active), _parse_avgs(raw_stats))


def estimated_wait_sync(key: str, position: int, max_concurrent: int, *, client=None) -> float:
    """`estimated_wait` for synchronous code."""
    r = client or _sync_client()
    waiting, active, _seen, stats = _keys(key)
    kinds, starts = _meta_keys(key)
    ahead = r.zrange(waiting, 0, position - 1) if position > 0 else []
    holders = r.zrange(active, 0, -1)
    tickets = [*ahead, *holders]
    kind_values = r.hmget(kinds, tickets) if tickets else []
    start_values = r.hmget(starts, holders) if holders else []
    now_ms = _now_ms_from(r.time())
    ahead_kinds = [k or KIND_DEFAULT for k in kind_values[: len(ahead)]]
    holder_kinds = [k or KIND_DEFAULT for k in kind_values[len(ahead) :]]
    elapsed = [max(0.0, (now_ms - int(s)) / 1000) if s else 0.0 for s in start_values]
    return estimate_seconds(
        ahead_kinds, list(zip(holder_kinds, elapsed)), _parse_avgs(r.hgetall(stats)), max_concurrent
    )


class SyncWaiter:
    """The queue for synchronous code, in two steps so a generator can report
    progress while it waits:

        with SyncWaiter(key, priority, max_concurrent, timeout) as waiter:
            for waiting in waiter.wait():   # yields Waiting while in line
                ...                          # e.g. forward it as an SSE event
            ...call Groq...                  # the slot is held here

    `wait()` returns once admitted and raises QueueTimeout past the timeout -
    or past what is left of `budget`, if one is given, which is then charged
    for the time spent in line. Leaving the `with` block releases the slot,
    or leaves the line if never admitted - on success, exception, or a
    generator closed early (a student who closes the page while waiting). A
    heartbeat thread renews the lease while the slot is held, including while
    sleeping on a 429.
    """

    def __init__(
        self,
        key: str,
        priority: int,
        max_concurrent: int,
        timeout: float,
        *,
        kind: str = KIND_DEFAULT,
        budget: WaitBudget | None = None,
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
        self.kind = kind
        self.budget = budget
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
        kinds, starts = _meta_keys(self.key)
        enqueue = self.r.register_script(_ENQUEUE)
        admit = self.r.register_script(_ADMIT)
        limit = self.timeout if self.budget is None else min(self.timeout, self.budget.remaining())
        started = time.monotonic()
        enqueued_ms = enqueue(
            keys=[waiting, seen],
            args=[self.ticket, self.priority, self.waiter_ttl_ms, _KEY_TTL_MS],
        )
        self._queued = True
        self.r.hset(kinds, self.ticket, self.kind)
        self.r.pexpire(kinds, _KEY_TTL_MS)
        last_position: int | None = None
        try:
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
                        args=[
                            self.ticket,
                            self.priority,
                            self.waiter_ttl_ms,
                            _KEY_TTL_MS,
                            enqueued_ms,
                        ],
                    )
                    continue
                waited = time.monotonic() - started
                if waited >= limit:
                    log.warning(
                        "queue %s (%s): giving up at position %d after %.1fs in line "
                        "(limit %.1fs%s)",
                        self.key,
                        self.kind,
                        result,
                        waited,
                        limit,
                        ""
                        if self.budget is None
                        else f", request had already waited {self.budget.spent:.1f}s",
                    )
                    raise QueueTimeout(self.key, waited, result)
                if result != last_position:
                    last_position = result
                    eta = estimated_wait_sync(self.key, result, self.max_concurrent, client=self.r)
                    yield Waiting(
                        position=result, estimated_seconds=eta, reason="queue", kind=self.kind
                    )
                time.sleep(self.poll_seconds)
        finally:
            if self.budget is not None:
                self.budget.charge(time.monotonic() - started)

        self._held_from = time.monotonic()
        self.r.hset(starts, self.ticket, _now_ms_from(self.r.time()))
        self.r.pexpire(starts, _KEY_TTL_MS)
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
        kinds, starts = _meta_keys(self.key)
        if self.slot is not None:
            self._stop.set()
            if self._heartbeat is not None:
                self._heartbeat.join(timeout=2)
            held = time.monotonic() - self._held_from
            field_name = f"avg_hold:{self.kind}"
            self.r.zrem(active, self.ticket)
            self.r.hdel(kinds, self.ticket)
            self.r.hdel(starts, self.ticket)
            self.r.hset(stats, field_name, _new_average(self.r.hget(stats, field_name), held))
            self.r.pexpire(stats, _KEY_TTL_MS)
            self.slot = None
        elif self._queued:
            # Also clears `active`, for an admission that landed just before
            # an exception reached us.
            with self.r.pipeline(transaction=True) as pipe:
                pipe.zrem(waiting, self.ticket).zrem(seen, self.ticket).zrem(active, self.ticket)
                pipe.hdel(kinds, self.ticket).hdel(starts, self.ticket)
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


def drain(steps: Generator[Waiting, None, T]) -> T:
    """Run a step generator to its end, ignoring its Waiting markers, and
    return its result - for callers with nowhere to report progress."""
    while True:
        try:
            next(steps)
        except StopIteration as stop:
            return stop.value


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
    remaining: float,
    *,
    max_retries: int | None = None,
) -> float | None:
    """The retry policy, in one place: seconds to sleep before trying the same
    Groq call again, or None to give up and let the error through.

    Only a 429 is retried; at most `max_retries` times; and only if Groq's
    Retry-After fits in what is `remaining` of the request's WaitBudget. A
    wait that does not fit fails at once rather than sleeping part of it and
    failing anyway: the student hears "busy" as early as it is certain.
    """
    max_retries = GROQ_RETRY_MAX if max_retries is None else max_retries
    if not isinstance(exc, urllib.error.HTTPError) or exc.code != 429:
        return None
    if attempts >= max_retries:
        return None
    delay = retry_after_seconds(exc.headers)
    if delay > remaining:
        return None
    return delay


def retry_steps(
    model: str,
    send: Callable[[], T],
    budget: WaitBudget,
    *,
    kind: str = KIND_DEFAULT,
    sleep: Callable[[float], None] = time.sleep,
) -> Generator[Waiting, None, T]:
    """Call `send`, sleeping and retrying on 429 per next_retry_delay; each
    sleep is charged to `budget` and announced as a rate_limited Waiting.
    Meant to run while a slot is held. Returns send()'s result, or raises the
    last HTTPError once retrying is not allowed."""
    attempts = 0
    while True:
        try:
            return send()
        except urllib.error.HTTPError as exc:
            delay = next_retry_delay(exc, attempts, budget.remaining())
            if delay is None:
                if exc.code == 429:
                    # The "why did this request fail" line: without it a
                    # give-up is only visible as a busy error at some time.
                    wanted = retry_after_seconds(exc.headers)
                    why = (
                        "retries used up"
                        if attempts >= GROQ_RETRY_MAX
                        else "Retry-After exceeds the remaining wait budget"
                    )
                    log.warning(
                        "groq 429 on %s (%s): giving up, %s - %d %s done, %.1fs waited "
                        "so far, %.1fs of budget left, next sleep would need %.1fs",
                        model,
                        kind,
                        why,
                        attempts,
                        "retry" if attempts == 1 else "retries",
                        budget.spent,
                        budget.remaining(),
                        wanted,
                    )
                raise
            log.warning(
                "groq 429 on %s (%s): retry %d/%d in %.1fs (holding the slot, %.0fs of wait left)",
                model,
                kind,
                attempts + 1,
                GROQ_RETRY_MAX,
                delay,
                budget.remaining(),
            )
            yield Waiting(position=0, estimated_seconds=delay, reason="rate_limited", kind=kind)
            sleep(delay)
            budget.charge(delay)
            attempts += 1


def groq_call_steps(
    model: str,
    priority: int,
    send: Callable[[], T],
    *,
    kind: str = KIND_DEFAULT,
    budget: WaitBudget | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> Generator[Waiting, None, T]:
    """One Groq request through its model's queue, as steps: yields Waiting
    while in line or backing off on a 429, returns the response. Raises
    QueueTimeout if no slot came within the budget, or the last HTTPError once
    retrying is not allowed."""
    budget = budget if budget is not None else WaitBudget()
    with SyncWaiter(
        groq_queue_key(model),
        queue_priority(kind, priority),
        groq_max_concurrent(model),
        budget.total,
        kind=kind,
        budget=budget,
    ) as waiter:
        yield from waiter.wait()
        return (yield from retry_steps(model, send, budget, kind=kind, sleep=sleep))


def groq_call(
    model: str,
    priority: int,
    send: Callable[[], T],
    *,
    kind: str = KIND_DEFAULT,
    budget: WaitBudget | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """`groq_call_steps` for callers with nowhere to report waiting."""
    return drain(groq_call_steps(model, priority, send, kind=kind, budget=budget, sleep=sleep))
