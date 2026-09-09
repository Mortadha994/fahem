"""Thin HTTP wrapper around the solve pipeline.

Deliberately thin: retrieval, context assembly and generation all come from
the modules the test scripts already exercise (context.build_context,
prompts.build_messages, generate.generate). Nothing about the pipeline is
reimplemented here - this file only maps HTTP in and out of it, so the
endpoint cannot drift from what was verified by direct script calls.

/solve and /solve/stream require a signed-in user (Phase 1) and share one
per-user rate limit (Phase 2). Both checks run ahead of the gatekeeper's
classifier, so a rejected request costs no LLM tokens. Nothing is persisted
against the account yet.

    .venv/Scripts/python.exe -m uvicorn api:app --reload --port 8000
    curl -X POST localhost:8000/solve -H "Content-Type: application/json" \
         --cookie "fahem_session=..." \
         -d '{"problem": "...", "niveau": "2eme", "chapitre": "1"}'
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from slowapi.errors import RateLimitExceeded

import auth
import chapters
import gatekeeper
import models
import ratelimit
from checker import check_constraints
from config import CORS_ORIGINS, RATE_LIMIT_SOLVE
from context import build_context
from generate import GROQ_MODEL, generate, pick_backend
from llm_stream import stream_groq
from prompts import build_messages
from rag_store import get_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm the embedding model before the first request.

    get_model() caches into a module-level singleton, so loading it here means
    no request pays the ~6s SentenceTransformer initialisation. Without this
    the first caller saw 9.3s against 3.5s for everyone after.
    """
    get_model()
    yield


app = FastAPI(
    title="Algorithmique solve API",
    description="Retrieval + pinned syntax context + generation, one endpoint.",
    version="0.1.0",
    lifespan=lifespan,
)


# The UI runs on the Vite dev server, a different origin, so the browser
# preflights every POST. Origins come from config.CORS_ORIGINS, which reads
# the CORS_ORIGINS env var (comma-separated) and defaults to the same
# localhost dev ports this list used to hardcode - so local dev is unchanged,
# but a deployment can set the real origin without editing this file.
#
# allow_credentials=True is what lets the browser send and store the session
# cookie auth.py issues. It is safe here only because allow_origins is an
# explicit allowlist - the CORS spec forbids pairing credentials with "*",
# and Starlette silently ignores the wildcard in that combination rather than
# erroring, so an origins list that ever becomes ["*"] would break auth
# quietly instead of loudly.
#
# This does not change anything for the existing anonymous requests: /solve
# and /solve/stream send no credentials, and a request without credentials is
# unaffected by the header this adds.
#
# expose_headers is not optional for the rate limiter to be usable from the
# browser. Only a handful of response headers are readable cross-origin by
# default, and Retry-After is not one of them - without this,
# `response.headers.get("Retry-After")` is null in fetch() even though the
# header is plainly on the wire, and the UI silently degrades to its vague
# "réessaie dans quelques instants" fallback. Verified by observing exactly
# that before adding this line.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
    expose_headers=[
        "Retry-After",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ],
)

# Rate limiting (Phase 2). slowapi reads the limiter off app.state, so this
# assignment is wiring, not decoration - without it every decorated route
# raises at request time.
app.state.limiter = ratelimit.limiter
app.add_exception_handler(RateLimitExceeded, ratelimit.rate_limit_handler)

# Sign-in, session read and sign-out. Included after app.state.limiter is set
# because auth.py's /auth/google carries its own IP-based limit.
app.include_router(auth.router)

# Chapter catalogue, exercises and the lesson PDF (Phase 3a). Every route
# behind get_current_user; none rate-limited, since none of them reach a
# model - see chapters.py's module docstring.
app.include_router(chapters.router)


# Store keys are normalised and unaccented ("2eme"); a student should not see
# that. Ordinal suffixes are the only difference in practice.
NIVEAU_LABELS = {"1ere": "1ère", "2eme": "2ème", "3eme": "3ème", "4eme": "4ème"}


def niveau_label(niveau: str) -> str:
    """Display form of a niveau, for text the student reads."""
    key = niveau.strip().lower()
    if key in NIVEAU_LABELS:
        return NIVEAU_LABELS[key]
    if key == "bac":
        return "Bac"
    # Generic fallback so an unlisted niveau still reads correctly.
    label = re.sub(r"(\d+)\s*eme\b", r"\1ème", key)
    return re.sub(r"(\d+)\s*ere\b", r"\1ère", label)


class SolveRequest(BaseModel):
    problem: str = Field(min_length=1, description="The problem pasted by the student")
    niveau: str = Field(min_length=1, examples=["2eme"])
    chapitre: str = Field(min_length=1, examples=["1"])
    k: int = Field(default=5, ge=1, le=20, description="Retrieved extras budget")


class RetrievedChunk(BaseModel):
    """A retrieved chunk, described - not the raw pipeline object."""

    id: str
    section: str
    type: str
    score: float


class PinnedTable(BaseModel):
    id: str
    label: str


class SolveResponse(BaseModel):
    # What a frontend renders.
    solution: str
    niveau: str
    chapitre: str
    # Debugging surface: cheap to include now, awkward to add later.
    model: str
    pinned: list[PinnedTable]
    retrieved: list[RetrievedChunk]
    warnings: list[str] = Field(
        default_factory=list,
        description="Constraint-checker findings. Advisory only - the checker "
        "has both missed real violations and raised false ones, so a frontend "
        "should not treat an empty list as a correctness guarantee.",
    )
    elapsed_ms: int


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": GROQ_MODEL}


@app.post("/solve", response_model=SolveResponse)
@ratelimit.limiter.shared_limit(RATE_LIMIT_SOLVE, scope=ratelimit.SOLVE_SCOPE)
def solve(
    request: Request,
    response: Response,
    payload: SolveRequest,
    user: models.User = Depends(auth.bind_user),
) -> SolveResponse:
    """Solve one problem. Requires a signed-in user (Phase 1), rate-limited
    per user (Phase 2).

    Two things run before this body, and both are cheap by design:

    1. The auth dependency. FastAPI resolves dependencies before the handler,
       so an anonymous request 401s before the gatekeeper's classifier call
       and costs no LLM tokens.
    2. The rate limit. slowapi's decorator wraps this function, so it is
       evaluated after dependency resolution but still before the first line
       here - an over-limit request costs a Redis INCR, not a generation.

    `request` is here because slowapi requires the Starlette Request by that
    exact name; the body model moved to `payload` for it. `response` is also
    required by slowapi, and only because headers_enabled=True: it injects the
    X-RateLimit-* headers into it, and with no Response to write to it raises
    - turning every successful call into a 500. FastAPI merges headers set on
    that injected object into the real response when the handler returns a
    model, which is what happens here.

    `user` is still intentionally unused by the body - this phase limits
    access, it does not attribute anything to the account
    (models.ChatSession/ChatMessage remain unused).

    shared_limit with SOLVE_SCOPE means this and /solve/stream draw on one
    budget. Separate buckets would let a caller double the spend by
    alternating between two endpoints that do identical work.
    """
    started = time.monotonic()

    # Gatekeeper: classify before the real pipeline ever sees the message.
    # PROBLEM falls through to the unchanged code below; META/OFF_TOPIC never
    # reach build_context/generate at all. See gatekeeper.py's module
    # docstring for why this is a separate layer, not a pipeline change.
    if gatekeeper.is_input_too_long(payload.problem):
        return SolveResponse(
            solution=gatekeeper.DECLINE_MESSAGE,
            niveau=payload.niveau,
            chapitre=payload.chapitre,
            model="gatekeeper",
            pinned=[],
            retrieved=[],
            warnings=[],
            elapsed_ms=int((time.monotonic() - started) * 1000),
        )

    route = gatekeeper.classify(payload.problem)

    if route == "OFF_TOPIC":
        return SolveResponse(
            solution=gatekeeper.DECLINE_MESSAGE,
            niveau=payload.niveau,
            chapitre=payload.chapitre,
            model="gatekeeper",
            pinned=[],
            retrieved=[],
            warnings=[],
            elapsed_ms=int((time.monotonic() - started) * 1000),
        )

    if route == "META":
        answer = gatekeeper.respond_meta(payload.problem)
        return SolveResponse(
            solution=answer,
            niveau=payload.niveau,
            chapitre=payload.chapitre,
            model=GROQ_MODEL,
            pinned=[],
            retrieved=[],
            warnings=[],
            elapsed_ms=int((time.monotonic() - started) * 1000),
        )

    # route == "PROBLEM": everything below is unchanged.
    try:
        context = build_context(
            payload.problem,
            niveau=payload.niveau,
            chapitre=payload.chapitre,
            k=payload.k,
        )
    except Exception as exc:  # pin resolution failure, empty scope, bad store
        raise HTTPException(
            status_code=422,
            detail=f"could not assemble context for niveau={payload.niveau} "
            f"chapitre={payload.chapitre}: {exc}",
        ) from exc

    if not context.pinned:
        raise HTTPException(status_code=422, detail="no pinned syntax core for this scope")

    rendered = context.render()
    messages = build_messages(
        context=rendered,
        query=payload.problem,
        # The prompt shows the niveau to the student, so it gets the accented
        # display form; build_context above got the raw value the store keys
        # on. Keeping the two separate is deliberate.
        niveau=niveau_label(payload.niveau),
        chapitre=payload.chapitre,
    )

    try:
        answer = generate(messages, pick_backend(None))
    except urllib.error.HTTPError as exc:
        # 429 from the upstream token-per-minute cap is the common one; pass the
        # status through rather than reporting it as a server fault.
        raise HTTPException(
            status_code=502 if exc.code != 429 else 429,
            detail=f"model backend returned {exc.code}: {exc.reason}",
        ) from exc
    except urllib.error.URLError as exc:
        raise HTTPException(status_code=502, detail=f"model backend unreachable: {exc}") from exc
    except KeyError as exc:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not set") from exc

    violations, _ = check_constraints(answer, rendered)

    return SolveResponse(
        solution=answer,
        niveau=payload.niveau,
        chapitre=payload.chapitre,
        model=GROQ_MODEL,
        pinned=[PinnedTable(id=p.chunk_id, label=p.label) for p in context.pinned],
        retrieved=[
            RetrievedChunk(id=h.chunk_id, section=h.section, type=h.type, score=round(h.score, 4))
            for h in context.retrieved
        ],
        warnings=violations,
        elapsed_ms=int((time.monotonic() - started) * 1000),
    )


def _sse(event: str, payload: dict) -> str:
    """One Server-Sent Event frame."""
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _gatekeeper_stream(text: str, model_label: str, payload: SolveRequest, started: float):
    """The meta/done/delta shape for a gatekeeper-produced reply (DoS cap,
    OFF_TOPIC, or META), reusing the exact SSE contract /solve/stream already
    emits for a real answer - empty pinned/retrieved, one delta, a clean
    done - so the frontend needs no changes to render either kind of reply,
    and the existing hasRealAlgorithmeSolution check already hides the
    constraint badge correctly (no Algorithme|Python table in this text).
    """
    yield _sse(
        "meta",
        {
            "model": model_label,
            "niveau": payload.niveau,
            "chapitre": payload.chapitre,
            "pinned": [],
            "retrieved": [],
        },
    )
    yield _sse("delta", {"t": text})
    yield _sse(
        "done",
        {
            "warnings": [],
            "notes": [],
            "chars": len(text),
            "elapsed_ms": int((time.monotonic() - started) * 1000),
        },
    )


@app.post("/solve/stream")
@ratelimit.limiter.shared_limit(RATE_LIMIT_SOLVE, scope=ratelimit.SOLVE_SCOPE)
def solve_stream(
    request: Request,
    response: Response,
    payload: SolveRequest,
    user: models.User = Depends(auth.bind_user),
):
    """Streaming counterpart of /solve. Requires a signed-in user (Phase 1),
    sharing /solve's per-user rate limit (Phase 2).

    Like the 401, the 429 is a plain JSON response rather than an `error`
    frame inside a 200 stream: both the dependency and slowapi's wrapper run
    before StreamingResponse is constructed, so the SSE stream never opens and
    api.js can branch on response.status before it reads a single frame.

    `response` exists only to satisfy slowapi's header injection (see /solve).
    Known limitation: this handler returns its own StreamingResponse, and
    FastAPI only merges the injected object's headers when the handler returns
    a model - so the informational X-RateLimit-* headers do NOT appear on this
    endpoint. The 429 and its Retry-After are unaffected, because those come
    from ratelimit.rate_limit_handler rather than from header injection.

    The 401 for an anonymous request is a plain JSON response, not an `error`
    frame inside a 200 stream: FastAPI resolves the dependency before the
    handler body runs, so StreamingResponse is never constructed and the SSE
    stream never opens. That matters for the client - api.js can branch on
    response.ok before it starts reading frames, which it could not do if the
    rejection arrived mid-stream.

    Event order:
      meta   - the grounding: pinned tables and retrieved excerpts, WITH their
               text, sent before generation so the citation strip can render
               while the answer is still arriving.
      delta  - one answer fragment. Reasoning tokens are filtered upstream in
               llm_stream, so nothing here is the model's private monologue.
      done   - constraint-checker findings and timings, once the full text
               exists. The checker is advisory: `warnings` being empty means
               no known pattern matched, not that the answer is correct.
      error  - something failed mid-stream; the frame carries a generic
               message, details stay server-side.

    /solve is unchanged and still serves the non-streaming path.
    """
    started = time.monotonic()

    # Gatekeeper: same three-way split as /solve, before build_context ever
    # runs. See gatekeeper.py's module docstring and _gatekeeper_stream above.
    if gatekeeper.is_input_too_long(payload.problem):
        return StreamingResponse(
            _gatekeeper_stream(gatekeeper.DECLINE_MESSAGE, "gatekeeper", payload, started),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    route = gatekeeper.classify(payload.problem)

    if route == "OFF_TOPIC":
        return StreamingResponse(
            _gatekeeper_stream(gatekeeper.DECLINE_MESSAGE, "gatekeeper", payload, started),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    if route == "META":
        answer = gatekeeper.respond_meta(payload.problem)
        return StreamingResponse(
            _gatekeeper_stream(answer, GROQ_MODEL, payload, started),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # route == "PROBLEM": everything below is unchanged. Context assembly
    # happens before the response starts, so a bad scope is still a clean
    # 422 rather than an error frame inside a 200 stream.
    try:
        context = build_context(
            payload.problem,
            niveau=payload.niveau,
            chapitre=payload.chapitre,
            k=payload.k,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"could not assemble context for niveau={payload.niveau} "
            f"chapitre={payload.chapitre}: {exc}",
        ) from exc

    if not context.pinned:
        raise HTTPException(status_code=422, detail="no pinned syntax core for this scope")

    rendered = context.render()
    messages = build_messages(
        context=rendered,
        query=payload.problem,
        niveau=niveau_label(payload.niveau),
        chapitre=payload.chapitre,
    )

    def events():
        yield _sse(
            "meta",
            {
                "model": GROQ_MODEL,
                "niveau": payload.niveau,
                "chapitre": payload.chapitre,
                "pinned": [
                    {"id": p.chunk_id, "label": p.label, "section": p.section, "content": p.content}
                    for p in context.pinned
                ],
                "retrieved": [
                    {
                        "id": h.chunk_id,
                        "section": h.section,
                        "type": h.type,
                        "score": round(h.score, 4),
                        "content": h.content,
                    }
                    for h in context.retrieved
                ],
            },
        )

        parts: list[str] = []
        try:
            for fragment in stream_groq(messages):
                parts.append(fragment)
                yield _sse("delta", {"t": fragment})
        except urllib.error.HTTPError as exc:
            yield _sse(
                "error",
                {"message": "busy" if exc.code == 429 else "backend", "status": exc.code},
            )
            return
        except (urllib.error.URLError, KeyError):
            yield _sse("error", {"message": "backend", "status": 502})
            return

        answer = "".join(parts)
        violations, notes = check_constraints(answer, rendered)
        yield _sse(
            "done",
            {
                "warnings": violations,
                "notes": notes,
                "chars": len(answer),
                "elapsed_ms": int((time.monotonic() - started) * 1000),
            },
        )

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
