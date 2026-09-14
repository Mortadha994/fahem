"""A priority-aware queue in front of Groq, on Redis.

Groq's per-minute limit is account-wide: every solve, every gatekeeper call
and every photo transcription draws on the same budget. When it is exhausted
Groq answers 429 at once, and today the student sees "Le service est très
sollicité". This module lets a request wait its turn instead: callers
`acquire` a slot on a shared key ("groq"), at most `max_concurrent` requests
hold one at a time, and the rest wait in priority order.

Named llm_queue, not queue: a top-level queue.py shadows the standard
library's `queue`, which redis-py, torch and concurrent.futures all import -
the backend would not start.

Nothing calls this yet (Phase A). Wiring it into the Groq call sites is the
next step.

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
import math
import uuid
import weakref
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable

import redis.asyncio as aioredis

from config import REDIS_URL

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
