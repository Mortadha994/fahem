"""Streaming variant of the model call.

Kept in its own module so generate.py's verified call path stays untouched -
the non-streaming `call_groq` is what every test round was validated against.
This only adds a second way to reach the same endpoint.

One thing this must get right: gpt-oss emits its chain of thought first, as
`delta.reasoning` on `channel: "analysis"`, and only then `delta.content`.
Measured on a real solve prompt: 407 reasoning deltas over the first 1.23s,
then 384 content deltas. Forwarding raw deltas would show a student the
model's private monologue, so only `content` is yielded.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Iterator

from generate import GROQ_MODEL, GROQ_URL


def stream_groq(
    messages: list[dict],
    temperature: float = 0.2,
    timeout: int = 300,
) -> Iterator[str]:
    """Yield answer-content fragments as they arrive. Reasoning is discarded."""
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

    with urllib.request.urlopen(request, timeout=timeout) as response:
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
