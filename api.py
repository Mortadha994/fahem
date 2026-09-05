"""Thin HTTP wrapper around the solve pipeline.

Deliberately thin: retrieval, context assembly and generation all come from
the modules the test scripts already exercise (context.build_context,
prompts.build_messages, generate.generate). Nothing about the pipeline is
reimplemented here - this file only maps HTTP in and out of it, so the
endpoint cannot drift from what was verified by direct script calls.

No auth, no rate limiting, no persistence - this exists to prove the HTTP
path works.

    .venv/Scripts/python.exe -m uvicorn api:app --reload --port 8000
    curl -X POST localhost:8000/solve -H "Content-Type: application/json" \
         -d '{"problem": "...", "niveau": "2eme", "chapitre": "1"}'
"""

from __future__ import annotations

import re
import time
import urllib.error
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from context import build_context
from generate import GROQ_MODEL, check_constraints, generate, pick_backend
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
# preflights every POST. Localhost dev ports only - this list must be replaced
# with the real origin before the endpoint is reachable by anyone else (see
# the pre-launch items in README_API.md).
app.add_middleware(
    CORSMiddleware,
    # 5174 as well as 5173: another Vite project already holds 5173 on this
    # machine, so the dev server falls back a port.
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)


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
def solve(request: SolveRequest) -> SolveResponse:
    started = time.monotonic()

    try:
        context = build_context(
            request.problem,
            niveau=request.niveau,
            chapitre=request.chapitre,
            k=request.k,
        )
    except Exception as exc:  # pin resolution failure, empty scope, bad store
        raise HTTPException(
            status_code=422,
            detail=f"could not assemble context for niveau={request.niveau} "
            f"chapitre={request.chapitre}: {exc}",
        ) from exc

    if not context.pinned:
        raise HTTPException(status_code=422, detail="no pinned syntax core for this scope")

    rendered = context.render()
    messages = build_messages(
        context=rendered,
        query=request.problem,
        # The prompt shows the niveau to the student, so it gets the accented
        # display form; build_context above got the raw value the store keys
        # on. Keeping the two separate is deliberate.
        niveau=niveau_label(request.niveau),
        chapitre=request.chapitre,
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
        niveau=request.niveau,
        chapitre=request.chapitre,
        model=GROQ_MODEL,
        pinned=[PinnedTable(id=p.chunk_id, label=p.label) for p in context.pinned],
        retrieved=[
            RetrievedChunk(
                id=h.chunk_id, section=h.section, type=h.type, score=round(h.score, 4)
            )
            for h in context.retrieved
        ],
        warnings=violations,
        elapsed_ms=int((time.monotonic() - started) * 1000),
    )
