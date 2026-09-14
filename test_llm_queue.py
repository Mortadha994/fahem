"""Tests for llm_queue.py alone: no Groq, no FastAPI, a real Redis.

Each case uses its own queue key and deletes it afterwards, so it can run
against the stack's Redis without touching anything else.

Run inside the backend container (needs REDIS_URL):
    docker compose exec -T backend python test_llm_queue.py
"""

from __future__ import annotations

import asyncio
import time
import uuid

import redis.asyncio as aioredis

import llm_queue
from config import REDIS_URL

results: list[bool] = []


def check(name: str, ok: bool, detail: object = "") -> None:
    results.append(ok)
    print(
        ("[PASS] " if ok else "[FAIL] ")
        + name
        + (f"  -> {detail!r}" if not ok and detail != "" else "")
    )


async def wait_until(predicate, timeout: float = 3.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if await predicate():
            return True
        await asyncio.sleep(0.02)
    return False


async def waiting_count(r, key: str) -> int:
    return (await llm_queue.snapshot(key, client=r)).waiting


async def cleanup(r, key: str) -> None:
    await r.delete(*llm_queue._keys(key))


# --- cases ----------------------------------------------------------------------


async def fifo_same_priority(r, key: str) -> None:
    """Two waiters with the same priority are served in arrival order."""
    release = asyncio.Event()
    order: list[str] = []

    async def holder():
        async with llm_queue.acquire(key, 1, 1, 5, client=r):
            order.append("holder")
            await release.wait()

    async def waiter(name: str):
        async with llm_queue.acquire(key, 1, 1, 5, client=r):
            order.append(name)
            await asyncio.sleep(0.05)

    h = asyncio.create_task(holder())
    await wait_until(lambda: asyncio.sleep(0, result="holder" in order))
    b = asyncio.create_task(waiter("B"))
    await wait_until(lambda: _eq(waiting_count(r, key), 1))
    c = asyncio.create_task(waiter("C"))
    await wait_until(lambda: _eq(waiting_count(r, key), 2))
    release.set()
    await asyncio.gather(h, b, c)
    check(
        "same priority: first to arrive is served first (FIFO)",
        order == ["holder", "B", "C"],
        order,
    )


async def priority_jumps_ahead(r, key: str) -> None:
    """A better-priority request that arrives later is served before a
    worse-priority one already waiting."""
    release = asyncio.Event()
    order: list[str] = []

    async def holder():
        async with llm_queue.acquire(key, llm_queue.PRIORITY_FREE, 1, 5, client=r):
            order.append("holder")
            await release.wait()

    async def waiter(name: str, priority: int):
        async with llm_queue.acquire(key, priority, 1, 5, client=r):
            order.append(name)
            await asyncio.sleep(0.05)

    h = asyncio.create_task(holder())
    await wait_until(lambda: asyncio.sleep(0, result="holder" in order))
    free = asyncio.create_task(waiter("free", llm_queue.PRIORITY_FREE))
    await wait_until(lambda: _eq(waiting_count(r, key), 1))
    paid = asyncio.create_task(waiter("paid", llm_queue.PRIORITY_PAID))
    await wait_until(lambda: _eq(waiting_count(r, key), 2))
    release.set()
    await asyncio.gather(h, free, paid)
    check(
        "higher priority jumps ahead of an already-waiting lower one",
        order == ["holder", "paid", "free"],
        order,
    )
    check(
        "priority_for: paid -> 0, free/unknown -> 1",
        (
            llm_queue.priority_for("paid"),
            llm_queue.priority_for("free"),
            llm_queue.priority_for(None),
        )
        == (0, 1, 1),
    )


async def concurrency_cap(r, key: str) -> None:
    """Never more than max_concurrent inside at once, and everyone gets in."""
    inside = 0
    peak = 0
    done = 0

    async def worker():
        nonlocal inside, peak, done
        async with llm_queue.acquire(key, 1, 2, 10, client=r):
            inside += 1
            peak = max(peak, inside)
            await asyncio.sleep(0.15)
            inside -= 1
        done += 1

    await asyncio.gather(*(worker() for _ in range(6)))
    snap = await llm_queue.snapshot(key, client=r)
    check("concurrency cap: at most 2 of 6 inside at once", peak == 2, peak)
    check("concurrency cap: all 6 eventually served", done == 6, done)
    check(
        "concurrency cap: no slot or waiter left behind",
        (snap.active, snap.waiting) == (0, 0),
        snap,
    )


async def timeout_releases_cleanly(r, key: str) -> None:
    """A waiter past its timeout raises QueueTimeout, leaves the line, and
    does not stop the next request from getting the slot."""
    release = asyncio.Event()
    holding = asyncio.Event()

    async def holder():
        async with llm_queue.acquire(key, 1, 1, 5, client=r):
            holding.set()
            await release.wait()

    h = asyncio.create_task(holder())
    await holding.wait()
    started = time.monotonic()
    error = None
    try:
        async with llm_queue.acquire(key, 1, 1, 0.3, client=r):
            pass
    except llm_queue.QueueTimeout as exc:
        error = exc
    elapsed = time.monotonic() - started
    check("timeout: QueueTimeout raised", error is not None, error)
    check("timeout: fires close to the requested 0.3s", 0.3 <= elapsed < 0.8, round(elapsed, 3))
    check(
        "timeout: reports the position it gave up at",
        error is not None and error.position == 0,
        getattr(error, "position", None),
    )
    check("timeout: the timed-out ticket left the line", await waiting_count(r, key) == 0)

    release.set()
    await h
    started = time.monotonic()
    async with llm_queue.acquire(key, 1, 1, 2, client=r):
        got_in = time.monotonic() - started
    check("timeout: next request still gets the slot promptly", got_in < 0.5, round(got_in, 3))


async def released_slot_picked_up(r, key: str) -> None:
    """When the holder exits - here by an exception - the next waiter gets the
    slot right away."""
    holding = asyncio.Event()
    fail_now = asyncio.Event()
    admitted_at: list[float] = []

    async def holder():
        async with llm_queue.acquire(key, 1, 1, 5, client=r):
            holding.set()
            await fail_now.wait()
            raise RuntimeError("Groq call failed")

    async def waiter():
        async with llm_queue.acquire(key, 1, 1, 5, client=r):
            admitted_at.append(time.monotonic())

    h = asyncio.create_task(holder())
    await holding.wait()
    w = asyncio.create_task(waiter())
    await wait_until(lambda: _eq(waiting_count(r, key), 1))
    failed_at = time.monotonic()
    fail_now.set()
    holder_error = None
    try:
        await h
    except RuntimeError as exc:
        holder_error = exc
    await w
    snap = await llm_queue.snapshot(key, client=r)
    check(
        "release: the holder's own exception still propagates",
        isinstance(holder_error, RuntimeError),
        holder_error,
    )
    check(
        "release: slot freed by an exception is picked up by the next waiter",
        bool(admitted_at) and admitted_at[0] - failed_at < 0.5,
        admitted_at and round(admitted_at[0] - failed_at, 3),
    )
    check("release: nothing left active afterwards", snap.active == 0, snap)


async def crashed_holder_lease_reclaimed(r, key: str) -> None:
    """A holder that vanished without releasing (process crash) only blocks
    the slot until its lease runs out."""
    _waiting, active, _seen, _stats = llm_queue._keys(key)
    seconds, micros = await r.time()
    now_ms = seconds * 1000 + micros // 1000
    await r.zadd(active, {"crashed-process": now_ms + 300})
    started = time.monotonic()
    async with llm_queue.acquire(key, 1, 1, 3, client=r):
        waited = time.monotonic() - started
    check(
        "lease: a crashed holder's slot is reclaimed once its lease expires",
        0.25 <= waited < 1.0,
        round(waited, 3),
    )


async def cancelled_waiter_leaves_line(r, key: str) -> None:
    """A request cancelled while waiting (the student closed the page) is
    removed from the line instead of blocking it."""
    release = asyncio.Event()
    holding = asyncio.Event()

    async def holder():
        async with llm_queue.acquire(key, 1, 1, 5, client=r):
            holding.set()
            await release.wait()

    async def waiter():
        async with llm_queue.acquire(key, 1, 1, 5, client=r):
            pass

    h = asyncio.create_task(holder())
    await holding.wait()
    w = asyncio.create_task(waiter())
    await wait_until(lambda: _eq(waiting_count(r, key), 1))
    w.cancel()
    try:
        await w
    except asyncio.CancelledError:
        pass
    check(
        "cancel: a cancelled waiter is removed from the line",
        await wait_until(lambda: _eq(waiting_count(r, key), 0)),
    )
    release.set()
    await h


async def reports_position_and_wait(r, key: str) -> None:
    """on_wait reports the position as it improves, with an estimate."""
    release = asyncio.Event()
    holding = asyncio.Event()
    seen: list[tuple[int, float]] = []

    async def holder():
        async with llm_queue.acquire(key, 1, 1, 5, client=r):
            holding.set()
            await release.wait()

    async def first():
        async with llm_queue.acquire(key, 1, 1, 5, client=r):
            await asyncio.sleep(0.2)

    async def second():
        async def on_wait(position, eta):
            seen.append((position, eta))

        async with llm_queue.acquire(key, 1, 1, 5, client=r, on_wait=on_wait):
            pass

    h = asyncio.create_task(holder())
    await holding.wait()
    a = asyncio.create_task(first())
    await wait_until(lambda: _eq(waiting_count(r, key), 1))
    b = asyncio.create_task(second())
    await wait_until(lambda: _eq(waiting_count(r, key), 2))
    release.set()
    await asyncio.gather(h, a, b)
    positions = [p for p, _ in seen]
    check("position: reported as it improves (1, then 0)", positions == [1, 0], seen)
    check(
        "position: each report carries a positive wait estimate",
        all(eta > 0 for _, eta in seen),
        seen,
    )


async def _eq(awaitable, expected):
    return (await awaitable) == expected


CASES = [
    fifo_same_priority,
    priority_jumps_ahead,
    concurrency_cap,
    timeout_releases_cleanly,
    released_slot_picked_up,
    crashed_holder_lease_reclaimed,
    cancelled_waiter_leaves_line,
    reports_position_and_wait,
]


async def main() -> None:
    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        for case in CASES:
            key = f"test-{case.__name__}-{uuid.uuid4().hex[:8]}"
            try:
                await asyncio.wait_for(case(r, key), timeout=30)
            except Exception as exc:  # a hung or crashed case is a failure, not a stop
                check(f"{case.__name__} ran to completion", False, repr(exc))
            finally:
                await cleanup(r, key)
    finally:
        await r.aclose()
    print("ALL PASSED" if all(results) else f"{results.count(False)} FAILED")


if __name__ == "__main__":
    asyncio.run(main())
