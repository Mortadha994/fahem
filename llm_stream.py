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
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Iterator

import llm_queue
from config import GROQ_QUEUE_TIMEOUT_SECONDS, GROQ_RETRY_MAX
from generate import GROQ_MODEL, GROQ_URL

log = logging.getLogger("fahem.llm_stream")


def stream_groq(
    messages: list[dict],
    temperature: float = 0.2,
    timeout: int = 300,
    priority: int = llm_queue.PRIORITY_FREE,
) -> Iterator[str | llm_queue.Waiting]:
    """Yield answer-content fragments as they arrive, preceded by
    llm_queue.Waiting markers while the request waits. Reasoning is discarded.

    Raises llm_queue.QueueTimeout if no slot came in time, or the Groq
    HTTPError once the 429 retries are used up.
    """
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
    with llm_queue.SyncWaiter(
        llm_queue.groq_queue_key(GROQ_MODEL),
        priority,
        llm_queue.groq_max_concurrent(GROQ_MODEL),
        GROQ_QUEUE_TIMEOUT_SECONDS,
    ) as waiter:
        yield from waiter.wait()

        # A 429 arrives before any byte of the stream, so retrying here never
        # repeats text the student has already seen.
        attempts = 0
        waited = 0.0
        while True:
            try:
                response = urllib.request.urlopen(request, timeout=timeout)
                break
            except urllib.error.HTTPError as exc:
                delay = llm_queue.next_retry_delay(exc, attempts, waited)
                if delay is None:
                    raise
                log.warning(
                    "groq 429 on %s (stream): retry %d/%d in %.1fs (holding the slot)",
                    GROQ_MODEL,
                    attempts + 1,
                    GROQ_RETRY_MAX,
                    delay,
                )
                yield llm_queue.Waiting(position=0, estimated_seconds=delay, reason="rate_limited")
                time.sleep(delay)
                waited += delay
                attempts += 1

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
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                # `reasoning` is deliberately ignored - see the module docstring.
                fragment = delta.get("content")
                if fragment:
                    yield fragment
