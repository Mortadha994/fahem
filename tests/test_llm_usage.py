"""Tests for AI monitoring: llm_usage's per-call records and the admin
console's /admin/monitoring read. No Groq - the calls are fakes through the
real queue; real Postgres and Redis.

Every row is written for a per-run fake model name and deleted at the end, so
it can run against the stack's database without touching the console's data.

    docker compose exec -T backend python -m tests.test_llm_usage
"""

from __future__ import annotations

import io
import urllib.error
import uuid
from datetime import datetime, timedelta, timezone

from fastapi.routing import APIRoute
from sqlalchemy import delete, select

from app.auth import auth
from app.core.db import session_scope
from app.core.models import LlmCall
from app.llm import llm_queue, llm_usage
from app.routes.admin import admin_monitoring

results: list[bool] = []

TPD_BODY = (
    b'{"error":{"message":"Rate limit reached for model `m` in organization `o` service '
    b"tier `on_demand` on tokens per day (TPD): Limit 200000, Used 199009, Requested 1822. "
    b'Please try again in 5m58.99s.","type":"tokens","code":"rate_limit_exceeded"}}'
)


def check(name: str, ok: bool, detail: object = "") -> None:
    results.append(bool(ok))
    print(
        ("[PASS] " if ok else "[FAIL] ")
        + name
        + (f"  -> {detail!r}" if not ok and detail != "" else "")
    )


def rows_for(model: str) -> list[LlmCall]:
    with session_scope() as s:
        return list(s.scalars(select(LlmCall).where(LlmCall.model == model).order_by(LlmCall.id)))


def http_429(retry_after: str, body: bytes = b"") -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        "https://api.groq.com",
        429,
        "Too Many Requests",
        {"retry-after": retry_after},
        io.BytesIO(body),
    )


def main() -> None:
    run = uuid.uuid4().hex[:8]
    model = f"test-usage-{run}"
    llm_usage.LLM_USAGE_RECORDING = True
    try:
        # --- a successful call records its usage -----------------------------
        body = {
            "choices": [{"message": {"content": "META"}}],
            "usage": {"prompt_tokens": 600, "completion_tokens": 86, "total_tokens": 686},
        }
        llm_queue.groq_call(model, 1, lambda: body, kind=llm_queue.KIND_GATEKEEPER)
        check("flush: the row reaches the database", llm_usage.flush())
        rows = rows_for(model)
        row = rows[-1] if rows else None
        check("ok call: one row", len(rows) == 1, len(rows))
        check(
            "ok call: kind, status and tokens as Groq reported them",
            row is not None
            and (row.kind, row.status, row.prompt_tokens, row.completion_tokens, row.total_tokens)
            == ("gatekeeper", "ok", 600, 86, 686),
            row and (row.kind, row.status, row.total_tokens),
        )

        # --- a 429 after a retry, then success: hits counted, status ok -------
        calls = {"n": 0}

        def flaky():
            calls["n"] += 1
            if calls["n"] == 1:
                raise http_429("0.5")
            return body

        llm_queue.groq_call(model, 1, flaky, kind=llm_queue.KIND_SOLVE, sleep=lambda s: None)
        llm_usage.flush()
        row = rows_for(model)[-1]
        check(
            "retried 429: status ok, the 429 counted",
            (row.status, row.rate_limit_hits, row.kind) == ("ok", 1, "solve"),
            (row.status, row.rate_limit_hits),
        )

        # --- a daily-limit 429 that cannot be waited out ----------------------
        error = None
        try:
            llm_queue.groq_call(model, 1, lambda: (_ for _ in ()).throw(http_429("359", TPD_BODY)))
        except urllib.error.HTTPError as exc:
            error = exc
        llm_usage.flush()
        row = rows_for(model)[-1]
        check("TPD 429: still reaches the caller", error is not None and error.code == 429)
        check(
            "TPD 429: recorded as rate_limited, naming the daily limit",
            (row.status, row.detail, row.rate_limit_hits) == ("rate_limited", "tokens per day", 1),
            (row.status, row.detail, row.rate_limit_hits),
        )
        limits = llm_usage.daily_limits(model)
        check(
            "TPD 429: Groq's own daily figures are kept",
            limits.get("tpd_limit") == 200000 and limits.get("tpd_used") == 199009,
            limits,
        )

        # --- a queue timeout ---------------------------------------------------
        key = llm_queue.groq_queue_key(model)
        with llm_queue.acquire_sync(key, 0, 1, 5):  # hold the only slot
            try:
                llm_queue.groq_call(model, 1, lambda: body, budget=llm_queue.WaitBudget(0.3))
            except llm_queue.QueueTimeout:
                pass
        llm_usage.flush()
        row = rows_for(model)[-1]
        check(
            "queue timeout: recorded, with the time spent in line",
            row.status == "queue_timeout" and row.queue_wait_ms >= 250 and row.latency_ms == 0,
            (row.status, row.queue_wait_ms, row.latency_ms),
        )

        # --- a closed generator is a cancellation, not a failure --------------
        with llm_queue.acquire_sync(key, 0, 1, 5):
            steps = llm_queue.groq_call_steps(
                model, 1, lambda: body, budget=llm_queue.WaitBudget(10)
            )
            next(steps)  # in line
            steps.close()
        llm_usage.flush()
        check("closed early: recorded as cancelled", rows_for(model)[-1].status == "cancelled")

        # --- recording off writes nothing --------------------------------------
        before = len(rows_for(model))
        llm_usage.LLM_USAGE_RECORDING = False
        llm_queue.groq_call(model, 1, lambda: body)
        llm_usage.flush()
        llm_usage.LLM_USAGE_RECORDING = True
        check("recording off: no row", len(rows_for(model)) == before)

        # --- a database that is down never breaks the call ---------------------
        saved = llm_usage.write_rows
        llm_usage.write_rows = lambda rows: (_ for _ in ()).throw(RuntimeError("db down"))
        try:
            result = llm_queue.groq_call(model, 1, lambda: body)
            check("db down: the call still returns", result is body)
            check("db down: the writer survives", llm_usage.flush())
        finally:
            llm_usage.write_rows = saved

        # --- temperature --------------------------------------------------------
        t = admin_monitoring.temperature
        check(
            "temperature: thresholds",
            [t(0.1, False), t(0.5, False), t(0.8, False), t(1.0, False), t(0.1, True)]
            == ["cool", "warm", "hot", "saturated", "saturated"],
        )

        # --- the console's read --------------------------------------------------
        data = admin_monitoring.monitoring()
        check(
            "monitoring: 24 hourly buckets and 60 minute buckets",
            (len(data.timeline), len(data.minutes)) == (24, 60),
        )
        check(
            "monitoring: the text model is listed with its limits",
            any(m.model == llm_queue.GROQ_VISION_MODEL or m.tpm_limit > 0 for m in data.models)
            and data.models[0].label == "Texte",
        )
        check(
            "monitoring: this run's calls are counted in the 24h KPIs",
            data.kpis.calls >= 5 and data.kpis.rate_limited >= 1 and data.kpis.queue_timeouts >= 1,
            data.kpis,
        )
        check(
            "monitoring: per kind, gatekeeper tokens include this run's 686",
            any(k.kind == "gatekeeper" and k.tokens >= 686 for k in data.by_kind),
            data.by_kind,
        )
        check(
            "monitoring: the TPD refusal is in the recent failures",
            any(f.model == model and f.detail == "tokens per day" for f in data.failures),
        )
        hour_sum = sum(b.calls for b in data.timeline)
        check(
            "monitoring: the timeline adds up to the 24h calls",
            hour_sum <= data.kpis.calls and hour_sum > 0,
            (hour_sum, data.kpis.calls),
        )

        # --- the gate ------------------------------------------------------------
        routes = [r for r in admin_monitoring.router.routes if isinstance(r, APIRoute)]
        check(
            "gate: every monitoring route is behind get_current_admin",
            bool(routes)
            and all(
                any(d.dependency is auth.get_current_admin for d in r.dependencies) for r in routes
            ),
        )

        # --- pruning ---------------------------------------------------------------
        with session_scope() as s:
            old = LlmCall(model=model, kind="solve", status="ok")
            s.add(old)
            s.flush()
            old.created_at = datetime.now(timezone.utc) - timedelta(days=30)
        admin_monitoring._last_prune = 0.0
        admin_monitoring.monitoring()
        check(
            "prune: rows past the retention are deleted",
            all(
                r.created_at > datetime.now(timezone.utc) - timedelta(days=8)
                for r in rows_for(model)
            ),
        )
    finally:
        llm_usage.flush()
        with session_scope() as s:
            s.execute(delete(LlmCall).where(LlmCall.model == model))
        llm_usage._redis().delete(llm_usage.limits_key(model))
        llm_queue._sync_client().delete(*llm_queue.all_keys(llm_queue.groq_queue_key(model)))

    print("\nALL PASSED" if all(results) else f"\n{results.count(False)} FAILED")


if __name__ == "__main__":
    main()
