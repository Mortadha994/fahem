"""Streaming variant of the model call.

Kept in its own module so generate.py's verified call path stays untouched -
the non-streaming `call_groq` is what every test round was validated against.
This only adds a second way to reach the same endpoint.

One thing this must get right: gpt-oss emits its chain of thought first, as
`delta.reasoning` on `channel: "analysis"`, and only then `delta.content`.
Measured on a real solve prompt: 407 reasoning deltas over the first 1.23s,
then 384 content deltas. Forwarding raw deltas would show a student the
model's private monologue, so only `content` is yielded.

The call goes through GROQ_MODEL's queue (llm_queue). While it waits - for a
slot, or on a 429 inside the slot - the generator yields llm_queue.Waiting
markers between (before) the text fragments, so /solve/stream can tell the
student instead of pausing in silence.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Iterator

import llm_queue
import llm_usage
from generate import GROQ_MODEL, GROQ_URL


def stream_groq(
    messages: list[dict],
    temperature: float = 0.2,
    timeout: int = 300,
    priority: int = llm_queue.PRIORITY_FREE,
    budget: llm_queue.WaitBudget | None = None,
) -> Iterator[str | llm_queue.Waiting]:
    """Yield answer-content fragments as they arrive, preceded by
    llm_queue.Waiting markers while the request waits. Reasoning is discarded.

    `budget` is the request's shared WaitBudget: whatever the gatekeeper's
    classification already spent waiting is not available again here.
    Raises llm_queue.QueueTimeout if no slot came within it, or the Groq
    HTTPError once the 429 retries are used up or no longer fit.
    """
    budget = budget if budget is not None else llm_queue.WaitBudget()
    key = os.environ["GROQ_API_KEY"]
    payload = json.dumps(
        {
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        GROQ_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            # Groq's edge 403s the default urllib agent - same as call_groq.
            "User-Agent": "algo-rag/0.1",
            "Accept": "text/event-stream",
        },
    )

    # Leaving this block - normally, on an error, or when the client
    # disconnects and the generator is closed - releases the slot or leaves
    # the line.
    age_after_seconds, aging_drop = llm_queue.aging_for(llm_queue.KIND_SOLVE)
    # What this solve cost, for the admin console (llm_usage).
    record = llm_usage.CallRecord(model=GROQ_MODEL, kind=llm_queue.KIND_SOLVE)
    try:
        with llm_queue.SyncWaiter(
            llm_queue.groq_queue_key(GROQ_MODEL),
            # A solve queues behind any classification waiting, then by plan -
            # until it has waited GROQ_QUEUE_AGING_SECONDS; after that it ranks
            # ahead of every classification that arrived after it
            # (llm_queue.aging_for).
            llm_queue.queue_priority(llm_queue.KIND_SOLVE, priority),
            llm_queue.groq_max_concurrent(GROQ_MODEL),
            # The request's own budget (the admin's live queue timeout).
            budget.total,
            kind=llm_queue.KIND_SOLVE,
            budget=budget,
            age_after_seconds=age_after_seconds,
            aging_drop=aging_drop,
        ) as waiter:
            yield from waiter.wait()
            record.mark_admitted()

            # A 429 arrives before any byte of the stream, so retrying here never
            # repeats text the student has already seen.
            response = yield from llm_queue.retry_steps(
                GROQ_MODEL,
                lambda: urllib.request.urlopen(request, timeout=timeout),
                budget,
                kind=llm_queue.KIND_SOLVE,
                record=record,
            )

            with response:
                for raw in response:
                    line = raw.decode("utf-8").strip()
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    # Groq reports the usage on the last chunk, under x_groq.
                    usage = chunk.get("usage") or (chunk.get("x_groq") or {}).get("usage")
                    if usage:
                        record.add_usage(usage)
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    # `reasoning` is deliberately ignored - see the module docstring.
                    fragment = delta.get("content")
                    if fragment:
                        yield fragment
    except BaseException as exc:
        llm_usage.classify_failure(record, exc, queue_timeout=llm_queue.QueueTimeout)
        raise
    finally:
        record.finish()
