"""Tests for llm_queue.py alone: no Groq, no FastAPI, a real Redis. Covers the
async `acquire`, its synchronous twin, and the 429 retry policy (with fake
Groq errors - nothing here calls Groq).

Each case uses its own queue key and deletes it afterwards, so it can run
against the stack's Redis without touching anything else.

Run inside the backend container (needs REDIS_URL):
    docker compose exec -T backend python test_llm_queue.py
"""

from __future__ import annotations

import asyncio
import email.message
import logging
import threading
import time
import urllib.error
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
    await r.delete(*llm_queue.all_keys(key))


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


# --- synchronous twin (Phase B) ---------------------------------------------------


def sync_fifo_and_positions(key: str) -> None:
    """Threads using SyncWaiter are served in arrival order, and a waiter's
    wait() yields its position as it improves."""
    release = threading.Event()
    holding = threading.Event()
    order: list[str] = []
    positions: list[int] = []

    def holder():
        with llm_queue.acquire_sync(key, 1, 1, 5):
            order.append("holder")
            holding.set()
            release.wait(5)

    def waiter(name: str, record: bool = False):
        with llm_queue.SyncWaiter(key, 1, 1, 5) as w:
            for waiting in w.wait():
                if record:
                    positions.append(waiting.position)
            order.append(name)
            time.sleep(0.05)

    threads = [threading.Thread(target=holder)]
    threads[0].start()
    holding.wait(5)
    b = threading.Thread(target=waiter, args=("B",))
    b.start()
    _wait_sync(lambda: llm_queue.snapshot_sync(key).waiting == 1)
    c = threading.Thread(target=waiter, args=("C", True))
    c.start()
    _wait_sync(lambda: llm_queue.snapshot_sync(key).waiting == 2)
    release.set()
    for t in (threads[0], b, c):
        t.join(10)
    check("sync: same priority served in arrival order", order == ["holder", "B", "C"], order)
    check(
        "sync: wait() yields the position as it improves (1, then 0)",
        positions == [1, 0],
        positions,
    )


def sync_timeout_and_release(key: str) -> None:
    """A sync waiter times out and leaves the line; a holder that raises frees
    its slot for the next request."""
    holding = threading.Event()
    release = threading.Event()

    def holder():
        try:
            with llm_queue.acquire_sync(key, 1, 1, 5):
                holding.set()
                release.wait(5)
                raise RuntimeError("Groq call failed")
        except RuntimeError:
            pass

    t = threading.Thread(target=holder)
    t.start()
    holding.wait(5)
    started = time.monotonic()
    error = None
    try:
        with llm_queue.acquire_sync(key, 1, 1, 0.3):
            pass
    except llm_queue.QueueTimeout as exc:
        error = exc
    elapsed = time.monotonic() - started
    check(
        "sync: QueueTimeout after the requested 0.3s",
        error is not None and 0.3 <= elapsed < 0.8,
        round(elapsed, 3),
    )
    check("sync: the timed-out ticket left the line", llm_queue.snapshot_sync(key).waiting == 0)
    release.set()
    t.join(5)
    started = time.monotonic()
    with llm_queue.acquire_sync(key, 1, 1, 2):
        got_in = time.monotonic() - started
    check(
        "sync: a slot freed by an exception is picked up promptly", got_in < 0.5, round(got_in, 3)
    )
    check("sync: nothing left active", llm_queue.snapshot_sync(key).active == 0)


def sync_generator_closed_while_waiting(key: str) -> None:
    """A stream closed while still in line - the student left the page - takes
    its ticket out of the line (this is how stream_groq is consumed)."""
    holding = threading.Event()
    release = threading.Event()

    def holder():
        with llm_queue.acquire_sync(key, 1, 1, 5):
            holding.set()
            release.wait(5)

    def stream():
        with llm_queue.SyncWaiter(key, 1, 1, 5) as w:
            yield from w.wait()
            yield "text"

    t = threading.Thread(target=holder)
    t.start()
    holding.wait(5)
    gen = stream()
    first = next(gen)
    in_line = llm_queue.snapshot_sync(key).waiting
    gen.close()
    check(
        "sync: a waiting stream yields a Waiting marker first",
        isinstance(first, llm_queue.Waiting),
        first,
    )
    check(
        "sync: closing the stream while waiting leaves the line",
        in_line == 1 and llm_queue.snapshot_sync(key).waiting == 0,
    )
    release.set()
    t.join(5)


async def async_holder_blocks_sync_waiter(r, key: str) -> None:
    """The sync twin shares the async queue: same keys, same scripts."""
    release = asyncio.Event()
    holding = asyncio.Event()

    async def holder():
        async with llm_queue.acquire(key, 1, 1, 5, client=r):
            holding.set()
            await release.wait()

    h = asyncio.create_task(holder())
    await holding.wait()

    def sync_attempt():
        started = time.monotonic()
        with llm_queue.acquire_sync(key, 1, 1, 5):
            return time.monotonic() - started

    attempt = asyncio.create_task(asyncio.to_thread(sync_attempt))
    await wait_until(lambda: _eq(waiting_count(r, key), 1))
    await asyncio.sleep(0.3)
    blocked = not attempt.done()
    release.set()
    await h
    waited = await attempt
    check(
        "interop: an async holder blocks a sync waiter", blocked and waited >= 0.3, round(waited, 3)
    )


# --- 429 policy --------------------------------------------------------------------


def _http_429(**headers: str) -> urllib.error.HTTPError:
    message = email.message.Message()
    for name, value in headers.items():
        message[name.replace("_", "-")] = value
    return urllib.error.HTTPError("https://api.groq.com", 429, "Too Many Requests", message, None)


def retry_policy() -> None:
    policy = llm_queue.next_retry_delay
    check(
        "429: Retry-After is used",
        policy(_http_429(retry_after="7"), 0, 120, max_retries=3) == 7.0,
    )
    check(
        "429: without Retry-After, the token reset is parsed (1m26.4s)",
        policy(_http_429(x_ratelimit_reset_tokens="1m26.4s"), 0, 120, max_retries=3) == 86.4,
    )
    check(
        "429: a millisecond reset is parsed (547ms -> 0.547s)",
        policy(_http_429(x_ratelimit_reset_tokens="547ms"), 0, 120, max_retries=3) == 0.547,
    )
    check(
        "429: a very short reset is floored to 0.5s (120ms)",
        policy(_http_429(x_ratelimit_reset_tokens="120ms"), 0, 120, max_retries=3) == 0.5,
    )
    check(
        "429: gives up after max_retries",
        policy(_http_429(retry_after="1"), 3, 120, max_retries=3) is None,
    )
    check(
        "429: a Retry-After longer than the remaining budget fails at once (30s > 20s left)",
        policy(_http_429(retry_after="30"), 1, 20, max_retries=3) is None,
    )
    check(
        "429: a Retry-After that fits the remaining budget is slept (20s <= 20s left)",
        policy(_http_429(retry_after="20"), 1, 20, max_retries=3) == 20.0,
    )
    other = urllib.error.HTTPError(
        "https://api.groq.com", 500, "boom", email.message.Message(), None
    )
    check("429: other errors are never retried", policy(other, 0, 120, max_retries=3) is None)


def groq_call_retries_in_slot() -> None:
    """groq_call sleeps Retry-After and tries again while holding the slot,
    and lets the 429 through once the retries are used up."""
    model = f"test-model-{uuid.uuid4().hex[:8]}"
    key = llm_queue.groq_queue_key(model)
    slept: list[float] = []
    calls = {"n": 0}
    active_during_sleep: list[int] = []

    def fake_sleep(seconds: float) -> None:
        slept.append(seconds)
        active_during_sleep.append(llm_queue.snapshot_sync(key).active)

    def flaky():
        calls["n"] += 1
        if calls["n"] <= 2:
            raise _http_429(retry_after="2")
        return {"ok": True}

    try:
        budget = llm_queue.WaitBudget(120)
        result = llm_queue.groq_call(model, 1, flaky, sleep=fake_sleep, budget=budget)
        check(
            "groq_call: succeeds after two 429s", result == {"ok": True} and calls["n"] == 3, calls
        )
        check("groq_call: slept Groq's Retry-After between tries", slept == [2.0, 2.0], slept)
        check(
            "groq_call: the slot stays held while sleeping",
            active_during_sleep == [1, 1],
            active_during_sleep,
        )
        check(
            "groq_call: both sleeps are charged to the request's budget",
            4.0 <= budget.spent < 4.5,
            round(budget.spent, 3),
        )

        slept.clear()

        def always_429():
            raise _http_429(retry_after="1")

        error = None
        try:
            llm_queue.groq_call(model, 1, always_429, sleep=fake_sleep)
        except urllib.error.HTTPError as exc:
            error = exc
        check(
            "groq_call: after GROQ_RETRY_MAX retries the 429 reaches the caller",
            error is not None and error.code == 429 and len(slept) == llm_queue.GROQ_RETRY_MAX,
            (getattr(error, "code", None), len(slept)),
        )
        check(
            "groq_call: the slot is released afterwards", llm_queue.snapshot_sync(key).active == 0
        )

        steps = llm_queue.groq_call_steps(
            model, 1, flaky_once(), kind=llm_queue.KIND_SOLVE, sleep=lambda s: None
        )
        seen = []
        try:
            while True:
                seen.append(next(steps))
        except StopIteration as stop:
            value = stop.value
        check(
            "groq_call_steps: a 429 is announced as a rate_limited Waiting of its kind",
            value == "answer"
            and [(w.reason, w.kind, w.estimated_seconds) for w in seen]
            == [("rate_limited", "solve", 3.0)],
            seen,
        )
    finally:
        llm_queue._sync_client().delete(*llm_queue.all_keys(key))


def flaky_once():
    state = {"n": 0}

    def send():
        state["n"] += 1
        if state["n"] == 1:
            raise _http_429(retry_after="3")
        return "answer"

    return send


def shared_deadline(key_prefix: str) -> None:
    """One WaitBudget covers the queue wait and the 429 sleeps together, and
    carries from one Groq call to the next within a request."""
    model = f"{key_prefix}-{uuid.uuid4().hex[:8]}"
    key = llm_queue.groq_queue_key(model)
    holding = threading.Event()
    release = threading.Event()

    def holder():
        with llm_queue.acquire_sync(key, 1, 1, 10):
            holding.set()
            release.wait(10)

    try:
        # 1. Most of the budget goes on the queue; the 429 that follows asks
        #    for more than is left, so it fails at once - no sleep.
        slept: list[float] = []
        budget = llm_queue.WaitBudget(3.0)
        t = threading.Thread(target=holder)
        t.start()
        holding.wait(5)
        threading.Timer(2.0, release.set).start()
        started = time.monotonic()
        error = None
        try:
            llm_queue.groq_call(
                model,
                1,
                lambda: (_ for _ in ()).throw(_http_429(retry_after="2")),
                budget=budget,
                sleep=slept.append,
            )
        except urllib.error.HTTPError as exc:
            error = exc
        elapsed = time.monotonic() - started
        t.join(5)
        check(
            "deadline: 2s in queue + a 2s Retry-After on a 3s budget fails without sleeping",
            error is not None and error.code == 429 and slept == [],
            (getattr(error, "code", None), slept),
        )
        check(
            "deadline: the request gave up within its 3s budget",
            elapsed < 3.0,
            round(elapsed, 3),
        )
        check(
            "deadline: the budget was charged for the queue wait",
            1.9 <= budget.spent < 2.6,
            round(budget.spent, 3),
        )

        # 2. The budget carries to the next call: after a 0.6s backoff on a
        #    1s budget, a busy queue gets only the ~0.4s that is left.
        budget = llm_queue.WaitBudget(1.0)
        llm_queue.groq_call(model, 1, flaky_after(0.6), budget=budget, sleep=time.sleep)
        holding.clear()
        release.clear()
        t = threading.Thread(target=holder)
        t.start()
        holding.wait(5)
        started = time.monotonic()
        timed_out = False
        try:
            llm_queue.groq_call(model, 1, lambda: "never", budget=budget)
        except llm_queue.QueueTimeout:
            timed_out = True
        waited = time.monotonic() - started
        release.set()
        t.join(5)
        check(
            "deadline: the second call times out on what the first left (~0.4s)",
            timed_out and 0.3 <= waited < 0.8,
            (timed_out, round(waited, 3)),
        )
        check(
            "deadline: total waiting across both calls stays within the 1s budget (+ polling)",
            budget.spent <= 1.0 + llm_queue.POLL_SECONDS + 0.05,
            round(budget.spent, 3),
        )
    finally:
        release.set()
        llm_queue._sync_client().delete(*llm_queue.all_keys(key))


def flaky_after(delay: float):
    state = {"n": 0}

    def send():
        state["n"] += 1
        if state["n"] == 1:
            raise _http_429(retry_after=str(delay))
        return "ok"

    return send


def per_kind_estimate(key: str) -> None:
    """Hold times are averaged per kind, and the estimate adds up the kinds
    actually ahead - a quick gatekeeper call does not make a solve look quick."""
    pure = llm_queue.estimate_seconds(
        ahead_kinds=[llm_queue.KIND_GATEKEEPER, llm_queue.KIND_SOLVE],
        active=[(llm_queue.KIND_SOLVE, 10.0)],
        avgs={llm_queue.KIND_GATEKEEPER: 0.2, llm_queue.KIND_SOLVE: 30.0},
        max_concurrent=1,
    )
    check(
        "estimate: 20s left on the solve holding + 0.2s gatekeeper + 30s solve ahead = 50.2s",
        abs(pure - 50.2) < 1e-9,
        pure,
    )

    for _ in range(3):
        with llm_queue.acquire_sync(key, 1, 1, 5, kind=llm_queue.KIND_GATEKEEPER):
            time.sleep(0.05)
    with llm_queue.acquire_sync(key, 1, 1, 5, kind=llm_queue.KIND_SOLVE):
        time.sleep(0.6)
    avgs = llm_queue.snapshot_sync(key).avg_hold
    check(
        "estimate: a separate average is kept per kind",
        0.04 <= avgs.get("gatekeeper", -1) < 0.2 and 0.55 <= avgs.get("solve", -1) < 0.9,
        avgs,
    )

    holding = threading.Event()
    release = threading.Event()

    def solve_holder():
        with llm_queue.acquire_sync(key, 1, 1, 5, kind=llm_queue.KIND_SOLVE):
            holding.set()
            release.wait(5)

    t = threading.Thread(target=solve_holder)
    t.start()
    holding.wait(5)
    eta = llm_queue.estimated_wait_sync(key, 0, 1)
    release.set()
    t.join(5)
    # A waiter right behind a solve waits about one solve (~0.6s here). The old
    # single blended average ((3 x 0.05 + 0.6) / 4 ~ 0.19s) would have said
    # a fraction of that.
    check(
        "estimate: a waiter behind a solve is told about a solve's time, not a blend",
        0.5 <= eta < 0.9,
        round(eta, 3),
    )


def _wait_sync(predicate, timeout: float = 3.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def kind_tier_priority(key: str) -> None:
    """Classifications rank ahead of solves whatever the plan; the plan still
    orders requests within a kind."""
    qp = llm_queue.queue_priority
    check(
        "priority: free classification (1) < paid solve (10) < free solve (11)",
        (qp("gatekeeper", 1), qp("solve", 0), qp("solve", 1)) == (1, 10, 11),
        (qp("gatekeeper", 1), qp("solve", 0), qp("solve", 1)),
    )
    check("priority: transcription ranks with solves", qp("transcription", 1) == qp("solve", 1))
    try:
        qp("solve", 10)
        check("priority: a plan tier that would reach the next kind tier is refused", False)
    except ValueError:
        check("priority: a plan tier that would reach the next kind tier is refused", True)

    holding = threading.Event()
    release = threading.Event()
    order: list[str] = []

    def holder():
        with llm_queue.acquire_sync(key, qp("solve", 1), 1, 10, kind="solve"):
            holding.set()
            release.wait(10)

    def waiter(name: str, kind: str, plan: int):
        with llm_queue.acquire_sync(key, qp(kind, plan), 1, 10, kind=kind):
            order.append(name)
            time.sleep(0.05)

    t = threading.Thread(target=holder)
    t.start()
    holding.wait(5)
    threads = []
    # Two solves are already in line when the classification arrives last.
    for name, kind, plan in (
        ("free solve", "solve", 1),
        ("paid solve", "solve", 0),
        ("free classification", "gatekeeper", 1),
    ):
        th = threading.Thread(target=waiter, args=(name, kind, plan))
        th.start()
        threads.append(th)
        _wait_sync(lambda n=len(threads): llm_queue.snapshot_sync(key).waiting == n)
    release.set()
    for th in (t, *threads):
        th.join(10)
    check(
        "priority: a classification arriving after two queued solves is served first",
        order == ["free classification", "paid solve", "free solve"],
        order,
    )


def classification_then_solve_all_served(key: str) -> None:
    """The real shape of the traffic: each request classifies, then solves. At
    a pace the slot can keep up with, every solve is served - the kind tier
    reorders the line, it does not stop solves."""
    qp = llm_queue.queue_priority
    done: list[float] = []
    started = time.monotonic()

    def request(i: int):
        time.sleep(i * 0.3)  # arrivals spread out, slower than the slot serves
        with llm_queue.acquire_sync(key, qp("gatekeeper", 1), 1, 10, kind="gatekeeper"):
            time.sleep(0.03)
        with llm_queue.acquire_sync(key, qp("solve", 1), 1, 10, kind="solve"):
            time.sleep(0.2)
        done.append(time.monotonic() - started)

    threads = [threading.Thread(target=request, args=(i,)) for i in range(6)]
    for th in threads:
        th.start()
    for th in threads:
        th.join(20)
    check(
        "mixed traffic: all 6 solves served when each classification is followed by its solve",
        len(done) == 6,
        len(done),
    )
    check(
        "mixed traffic: nothing left in line afterwards", llm_queue.snapshot_sync(key).waiting == 0
    )


def give_up_is_logged() -> None:
    """Giving up on a 429 leaves a warning saying why, with the numbers."""
    records: list[logging.LogRecord] = []

    class Capture(logging.Handler):
        def emit(self, record):
            records.append(record)

    handler = Capture(level=logging.WARNING)
    logger = logging.getLogger("fahem.llm_queue")
    logger.addHandler(handler)
    model = f"test-giveup-{uuid.uuid4().hex[:8]}"
    try:
        budget = llm_queue.WaitBudget(10)
        budget.charge(7.5)  # as if 7.5s were already spent in the queue
        try:
            llm_queue.groq_call(
                model,
                1,
                lambda: (_ for _ in ()).throw(_http_429(retry_after="28")),
                kind="solve",
                budget=budget,
                sleep=lambda s: None,
            )
        except urllib.error.HTTPError:
            pass
        lines = [r.getMessage() for r in records if "giving up" in r.getMessage()]
        check(
            "give-up log: budget case names the reason and the numbers",
            len(lines) == 1
            and "Retry-After exceeds the remaining wait budget" in lines[0]
            and "0 retries done" in lines[0]
            and "7.5s waited" in lines[0]
            and "2.5s of budget left" in lines[0]
            and "would need 28.0s" in lines[0],
            lines,
        )

        records.clear()
        try:
            llm_queue.groq_call(
                model,
                1,
                lambda: (_ for _ in ()).throw(_http_429(retry_after="1")),
                kind="gatekeeper",
                budget=llm_queue.WaitBudget(120),
                sleep=lambda s: None,
            )
        except urllib.error.HTTPError:
            pass
        lines = [r.getMessage() for r in records if "giving up" in r.getMessage()]
        check(
            "give-up log: retries-used-up case says so",
            len(lines) == 1
            and "retries used up" in lines[0]
            and f"{llm_queue.GROQ_RETRY_MAX} retries done" in lines[0],
            lines,
        )
    finally:
        logger.removeHandler(handler)
        llm_queue._sync_client().delete(*llm_queue.all_keys(llm_queue.groq_queue_key(model)))


SYNC_CASES = [
    sync_fifo_and_positions,
    sync_timeout_and_release,
    sync_generator_closed_while_waiting,
    per_kind_estimate,
    kind_tier_priority,
    classification_then_solve_all_served,
]


async def main() -> None:
    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        for case in CASES + [async_holder_blocks_sync_waiter]:
            key = f"test-{case.__name__}-{uuid.uuid4().hex[:8]}"
            try:
                await asyncio.wait_for(case(r, key), timeout=30)
            except Exception as exc:  # a hung or crashed case is a failure, not a stop
                check(f"{case.__name__} ran to completion", False, repr(exc))
            finally:
                await cleanup(r, key)
    finally:
        await r.aclose()


def run_sync_cases() -> None:
    client = llm_queue._sync_client()
    for case in SYNC_CASES:
        key = f"test-{case.__name__}-{uuid.uuid4().hex[:8]}"
        try:
            case(key)
        except Exception as exc:
            check(f"{case.__name__} ran to completion", False, repr(exc))
        finally:
            client.delete(*llm_queue.all_keys(key))
    for case in (retry_policy, groq_call_retries_in_slot, give_up_is_logged):
        try:
            case()
        except Exception as exc:
            check(f"{case.__name__} ran to completion", False, repr(exc))
    try:
        shared_deadline("test-deadline")
    except Exception as exc:
        check("shared_deadline ran to completion", False, repr(exc))


if __name__ == "__main__":
    asyncio.run(main())
    run_sync_cases()
    print("ALL PASSED" if all(results) else f"{results.count(False)} FAILED")
