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

    .venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
    curl -X POST localhost:8000/solve -H "Content-Type: application/json" \
         --cookie "fahem_session=..." \
         -d '{"problem": "...", "niveau": "2eme", "chapitre": "1"}'
"""

from __future__ import annotations

import json
import logging
import re
import time
import urllib.error
import uuid
from contextlib import asynccontextmanager
from typing import Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from slowapi.errors import RateLimitExceeded

from app.auth import auth, password_auth
from app.core import models, ratelimit, runtime_settings
from app.core.config import CORS_ORIGINS
from app.grading import algo_notation, answer_check, session_memory
from app.grading.checker import check_constraints
from app.llm import ai_control, gatekeeper, llm_queue
from app.llm.generate import GROQ_MODEL, generate, pick_backend
from app.llm.llm_stream import stream_groq
from app.llm.prompts import CHECK_CORRECTION_HEADING, build_messages
from app.rag import chapter_store
from app.rag.context import build_context
from app.rag.rag_store import get_model
from app.routes import attachments, chapters, chat_history, progress, public_overview
from app.routes.admin import (
    admin,
    admin_chapters,
    admin_controls,
    admin_monitoring,
    admin_user_activity,
)

log = logging.getLogger("fahem.api")

# The 429 retry count follows the admin console's live setting (ai_control).
llm_queue.RETRY_MAX_SOURCE = ai_control.retry_max


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm the embedding model before the first request.

    get_model() caches into a module-level singleton, so loading it here means
    no request pays the ~6s SentenceTransformer initialisation. Without this
    the first caller saw 9.3s against 3.5s for everyone after.
    """
    get_model()
    # Phase 9: background extraction/publish tasks die with the process; put
    # any chapter a restart interrupted into a state the console can act on.
    chapter_store.recover_interrupted()
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
# cookie app/auth/auth.py issues. It is safe here only because allow_origins is an
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
    # PATCH/PUT/DELETE since the admin console (Phases 8-9): without them the
    # browser's preflight rejects every edit and delete from localhost:5173,
    # while curl - which does not preflight - reports the same routes working.
    allow_methods=["POST", "GET", "PATCH", "PUT", "DELETE"],
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
# Limits keyed on the request body (per-email on login and forgot-password,
# Phase 4). Same 429 shape as the one above.
app.add_exception_handler(ratelimit.KeyedRateLimitExceeded, ratelimit.keyed_rate_limit_handler)

# Sign-in, session read and sign-out. Included after app.state.limiter is set
# because app/auth/auth.py's /auth/google carries its own IP-based limit.
app.include_router(auth.router)

# Email + password accounts (Phase 4): same /auth prefix, same session
# functions, separate identity check - see app/auth/password_auth.py.
app.include_router(password_auth.router)

# Chapter catalogue, exercises and the lesson PDF (Phase 3a). Every route
# behind get_current_user; none rate-limited, since none of them reach a
# model - see app/routes/chapters.py's module docstring.
app.include_router(chapters.router)

# Admin-only routes (Phase 7). get_current_admin is a router-level dependency,
# so nothing mounted there can be reached by a student - see app/routes/admin/admin.py.
app.include_router(admin.router)

# Uploaded chapters (Phase 9): upload, review, publish. Same router-level gate.
app.include_router(admin_chapters.router)

# AI monitoring: Groq load and usage, chat activity. Same router-level gate.
app.include_router(admin_monitoring.router)

# AI controls: pause, daily budget guard, live limits, queue reset. Same gate.
app.include_router(admin_controls.router)

# One student's activity and spend over time, for the charts on their page.
app.include_router(admin_user_activity.router)

# Chat history, per account: each student's discussions, scoped to their own
# rows on every route - see app/routes/chat_history.py.
app.include_router(chat_history.router)

# The student's progress through the chapter exercises, derived from their
# discussions - see app/routes/progress.py.
app.include_router(progress.router)

# What the public landing page shows (chapters, counts, features), no sign-in -
# see app/routes/public_overview.py. Cached, and reaches no model.
app.include_router(public_overview.router)


def _meta_scope(payload) -> tuple[str, str]:
    """(chapitre, topics) for the gatekeeper's META answer, or 404.

    Phase 9. Checked before gatekeeper.classify, which is a paid Groq call: a
    request for a chapter that does not exist or is not published cannot
    succeed, so it should not spend anything finding that out. Chapter 1 keeps
    gatekeeper's built-in topic list; an uploaded chapter uses the topics
    frozen in its publish snapshot.
    """
    chapitre = str(payload.chapitre).strip()
    available = {c.id for c in chapters.catalogue() if c.status == chapters.ACTIVE}
    if chapitre not in available:
        raise HTTPException(status_code=404, detail=f"chapitre {chapitre!r} is not available")
    uploaded = chapters._published_upload(chapitre)
    if uploaded is not None:
        return chapitre, uploaded.published_topics or ""
    return chapitre, gatekeeper.CHAPTER_1_TOPICS


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


def student_profile(user: models.User) -> str | None:
    """The account's niveau and section as the prompt reads them, or None if
    the student has not answered the question yet."""
    if not user.niveau or not user.section:
        return None
    niveau = models.NIVEAUX.get(user.niveau, user.niveau)
    section = models.SECTIONS.get(user.section, user.section)
    return f"{niveau}, section {section}"


def meta_niveau(user: models.User, payload: "SolveRequest") -> str:
    """The student's class, for the meta-responder's "je suis à quel niveau ?".

    The account's own niveau and section when the student has answered the
    profile question - that is their class. Otherwise the niveau this
    discussion is scoped to, in its display form: the request's niveau is the
    corpus scope (2ème by default), not necessarily the student's class, so it
    is only the fallback."""
    return student_profile(user) or niveau_label(payload.niveau)


class SolveRequest(BaseModel):
    problem: str = Field(min_length=1, description="The problem pasted by the student")
    niveau: str = Field(min_length=1, examples=["2eme"])
    chapitre: str = Field(min_length=1, examples=["1"])
    note: str | None = Field(
        default=None,
        max_length=500,
        description="Student's own note sent with an attached exercise, kept "
        "separate from the exercise text",
    )
    k: int = Field(default=5, ge=1, le=20, description="Retrieved extras budget")
    # Where the exchange belongs, so the server saves it when the answer ends
    # (chat_history.record_exchange) - even if the tab is closed first. All
    # optional: without them nothing is saved server-side.
    session_id: uuid.UUID | None = None
    user_message_id: str | None = Field(default=None, max_length=80)
    assistant_message_id: str | None = Field(default=None, max_length=80)
    title: str | None = Field(default=None, max_length=200)
    attachment: dict[str, Any] | None = None
    # "guided": Mode guidé - the exercise led step by step (prompts.GUIDED).
    # "check": Vérifier ma réponse - the student's own solution corrected.
    # "practice": Exercice similaire - a new statement, no solution.
    mode: Literal["full", "guided", "check", "practice"] = "full"
    difficulty: Literal["easier", "same", "harder"] | None = None
    # Guided: the step the discussion is at (1-4); `action` is a button -
    # "next_step" / "show_solution" - which moves it on without asking the
    # classifier what "Indice suivant" means; `exercise` is the statement the
    # guided exercise started from, which the memory may no longer hold.
    step: int | None = Field(default=None, ge=1, le=4)
    action: Literal["next_step", "show_solution"] | None = None
    exercise: str | None = Field(default=None, max_length=2000)
    exercise_id: str | None = Field(default=None, max_length=80)
    # Set by the server (never by the client): the exercise above is one of
    # this student's own messages in this discussion - see trusted_exercise.
    exercise_trusted: bool = Field(default=False, exclude=True)
    history: list[session_memory.HistoryTurn] = Field(
        default_factory=list,
        max_length=20,
        description="The discussion's earlier messages, oldest first - the tutor's session memory. Compacted and capped server-side (session_memory.compact), so it cannot inflate a request.",
    )


def gate_text(payload: SolveRequest) -> str:
    """What the gatekeeper checks: the note, the message, and an exercise the
    request carries that the discussion does not vouch for.

    The note travels apart from the exercise so retrieval and the prompt can
    treat it as a question, but it must not get past the length cap or the
    classifier by doing so - an injection in a note is exactly as harmless as
    one typed into the box, because the gatekeeper still reads it."""
    note = (payload.note or "").strip()
    parts = [p for p in (note, payload.problem) if p]
    if payload.exercise and not payload.exercise_trusted:
        parts.append(payload.exercise)
    return "\n\n".join(parts)


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
@ratelimit.limiter.shared_limit(ai_control.solve_rate_limit, scope=ratelimit.SOLVE_SCOPE)
def solve(
    request: Request,
    response: Response,
    payload: SolveRequest,
    user: models.User = Depends(auth.bind_user),
    _available: None = Depends(ai_control.require_ai_available),
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
    # reach build_context/generate at all. See app/llm/gatekeeper.py's module
    # docstring for why this is a separate layer, not a pipeline change.
    if gatekeeper.is_input_too_long(gate_text(payload)):
        return SolveResponse(
            solution=gatekeeper.TOO_LONG_MESSAGE,
            niveau=payload.niveau,
            chapitre=payload.chapitre,
            model="gatekeeper",
            pinned=[],
            retrieved=[],
            warnings=[],
            elapsed_ms=int((time.monotonic() - started) * 1000),
        )

    meta_chapitre, meta_topics = _meta_scope(payload)
    # Queue priority from the account's plan (llm_queue.priority_for): every
    # Groq call this request makes waits its turn at this priority.
    priority = llm_queue.priority_for(user.plan)
    # One deadline for all of this request's waiting (llm_queue.WaitBudget).
    budget = llm_queue.WaitBudget(ai_control.queue_timeout_seconds())
    # What the tutor remembers of this discussion (app/grading/session_memory.py).
    memory = session_memory.compact(payload.history)
    try:
        route = gatekeeper.classify(
            gate_text(payload),
            priority=priority,
            budget=budget,
            previous=session_memory.router_excerpt(memory),
        )
    except gatekeeper.Busy as exc:
        raise HTTPException(status_code=429, detail="model backend busy") from exc

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
        try:
            answer = gatekeeper.respond_meta(
                gate_text(payload),
                meta_chapitre,
                meta_topics,
                priority=priority,
                budget=budget,
                niveau=meta_niveau(user, payload),
            )
        except gatekeeper.Busy as exc:
            raise HTTPException(status_code=429, detail="model backend busy") from exc
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

    # route is PROBLEM, CODE or QUESTION (gatekeeper.GROUNDED_ROUTES): the same
    # grounded pipeline for all three, each with its own prompt (app/llm/prompts.py).
    try:
        context = build_context(
            session_memory.retrieval_query(payload.problem, memory),
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
        # A short follow-up gets the FOLLOW_UP prompt (see /solve/stream).
        kind=(
            "FOLLOW_UP"
            if session_memory.is_follow_up(payload.problem, memory, payload.note)
            else route
        ),
        profile=student_profile(user),
        note=(payload.note or "").strip() or None,
        memory=session_memory.memory_block(memory),
    )

    try:
        answer = generate(messages, pick_backend(None), priority=priority, budget=budget)
    except llm_queue.QueueTimeout as exc:
        raise HTTPException(status_code=429, detail="model backend busy") from exc
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

    # Course notation in the Algorithme column (div, mod, ≠...), even if the
    # model slipped - the student reads and copies this answer as returned.
    answer, fixed = algo_notation.normalize_answer(answer)
    if fixed:
        log.warning(
            "rewrote %d Python operator(s) in the Algorithme column (route %s)", fixed, route
        )
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


def trusted_exercise(payload: SolveRequest, user: models.User) -> bool:
    """Whether the exercise the request carries really comes from this
    discussion - the student's own message, or the statement Fahem generated
    in it. Anything else is read by the gatekeeper first, so a hand-made
    request cannot use these modes to get past it."""
    if not payload.exercise:
        return False
    if not payload.session_id:
        return False
    wanted = " ".join(payload.exercise.split())
    if len(wanted) < 12:
        return False
    texts = chat_history.exercise_texts(user.id, payload.session_id)
    # `in`: a generated exercise reaches us without its heading, and a
    # statement can be quoted inside a longer message.
    return any(wanted == text or wanted in text for text in texts)


def skips_classifier(payload: SolveRequest, memory: list, note: str | None) -> bool:
    """Requests whose route is already known, so the gatekeeper's Groq call
    would be spent for nothing - or worse, would misread them:
      - "Vérifier ma réponse" (the button says what the student wants);
      - a guided exercise's buttons ("Indice suivant" is not an exercise);
      - a short reply in the middle of a guided exercise ("deux entiers ?"),
        which the classifier could decline as off topic.
    """
    if payload.mode == "check" and runtime_settings.get("check_answer_enabled"):
        return True
    if payload.mode == "practice" and runtime_settings.get("practice_enabled"):
        return payload.exercise_trusted
    if payload.mode != "guided" or not runtime_settings.get("guided_mode_enabled"):
        return False
    if not payload.exercise_trusted:
        return False
    return bool(payload.action) or bool(
        payload.step
        and session_memory.is_follow_up(payload.problem, memory, note)
        and not session_memory.looks_like_statement(payload.problem)
    )


def learning_route(
    payload: SolveRequest, route: str, memory: list, note: str | None
) -> tuple[str, int | None, bool]:
    """(prompt route, guided step, whether a guided exercise starts here).

    The admin switches decide first: with a mode turned off, a request in that
    mode is answered the normal way. Then:
      - CHECK: the button, or a message asking to check pasted work;
      - GUIDED: a new statement starts at step 1; a button moves the step on;
        anything else in an exercise under way stays at its step (a pasted
        solution there is checked);
      - otherwise FOLLOW_UP or the classifier's route, as before.
    """
    check_on = bool(runtime_settings.get("check_answer_enabled"))
    guided_on = bool(runtime_settings.get("guided_mode_enabled"))
    if (
        payload.mode == "practice"
        and payload.exercise_trusted
        and runtime_settings.get("practice_enabled")
    ):
        return "PRACTICE", None, False
    # A new statement is never a follow-up, however short.
    follow = session_memory.is_follow_up(
        payload.problem, memory, note
    ) and not session_memory.looks_like_statement(payload.problem)
    if check_on and (
        payload.mode == "check"
        or (route in ("CODE", "PROBLEM") and answer_check.looks_like_check(payload.problem))
    ):
        return "CHECK", None, False
    if guided_on and payload.mode == "guided":
        in_exercise = bool(payload.step and payload.exercise)
        in_exercise = in_exercise and payload.exercise_trusted
        if in_exercise and payload.action == "show_solution":
            return "GUIDED", 4, False
        if in_exercise and payload.action == "next_step":
            return "GUIDED", min(4, payload.step + 1), False
        if route == "PROBLEM" and not follow:
            return "GUIDED", 1, True
        if in_exercise:
            if route == "CODE" and check_on:
                return "CHECK", None, False
            return "GUIDED", payload.step, False
    return ("FOLLOW_UP" if follow else route), None, False


PRACTICE_LIMIT_MESSAGE = (
    "Tu as déjà demandé {limit} exercices similaires aujourd'hui. Reviens demain pour "
    "en avoir d'autres - en attendant, essaie de résoudre ceux que tu as déjà !"
)


def _practice_key(user_id) -> str:
    return f"fahem:practice:{user_id}:{time.strftime('%Y-%m-%d', time.gmtime())}"


def release_practice_slot(user_id) -> None:
    """Give today's slot back when nothing was generated (Groq refused, the
    student stopped): a failed request must not cost an exercise."""
    try:
        llm_queue._sync_client().decr(_practice_key(user_id))
    except Exception:
        log.exception("could not give the practice slot back")


def take_practice_slot(user_id) -> bool:
    """Count one generated exercise against today's per-student limit (Redis,
    reset at midnight UTC). False when the limit is reached. A Redis outage
    lets the request through: the global rate limits still apply."""
    limit = int(runtime_settings.get("practice_daily_limit"))
    key = _practice_key(user_id)
    try:
        client = llm_queue._sync_client()
        used = client.incr(key)
        if used == 1:
            client.expire(key, 2 * 86400)
        if used > limit:
            client.decr(key)
            return False
        return True
    except Exception:
        log.exception("practice limit unavailable")
        return True


def _correction_part(answer: str) -> str:
    """What the syntax checker reads in a CHECK answer: the corrected solution,
    not the table quoting the student's own mistakes."""
    _, _, after = answer.partition(CHECK_CORRECTION_HEADING)
    return after


def _has_solution_table(answer: str) -> bool:
    """An Algorithme | Python table with at least one ← in it - what makes an
    answer checkable (ui/src/lib/hasRealSolution.js follows the same idea)."""
    lowered = answer.lower()
    return "| algorithme" in lowered and "python" in lowered and "←" in answer


def _sse(event: str, payload: dict) -> str:
    """One Server-Sent Event frame."""
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _waiting_frame(waiting: llm_queue.Waiting) -> str:
    """The SSE frame for a request still waiting on Groq. `seconds` is Groq's
    own Retry-After for a rate_limited wait; for a queue wait it is this
    module's estimate, not yet shown to students (see llm_queue)."""
    return _sse(
        "waiting",
        {
            "position": waiting.position,
            "seconds": round(waiting.estimated_seconds, 1),
            "reason": waiting.reason,
            "kind": waiting.kind,
        },
    )


def _relay(steps):
    """Forward a step generator's llm_queue.Waiting markers as SSE frames and
    return its result (`route = yield from _relay(...)`). Closing the stream -
    a student who leaves while waiting - closes the steps too, which takes the
    request out of Groq's queue."""
    try:
        while True:
            try:
                waiting = next(steps)
            except StopIteration as stop:
                return stop.value
            yield _waiting_frame(waiting)
    finally:
        steps.close()


def _busy_stream():
    """The error frame for a request Groq is too saturated to classify: the
    same "busy" error the stream sends for Groq's own 429, so the chat shows
    "le service est très sollicité" with its retry."""
    yield _sse("error", {"message": "busy", "status": 429})


def _gatekeeper_stream(
    text: str,
    model_label: str,
    payload: SolveRequest,
    started: float,
    extra: dict | None = None,
):
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
            **(extra or {}),
        },
    )


@app.post("/solve/stream")
@ratelimit.limiter.shared_limit(ai_control.solve_rate_limit, scope=ratelimit.SOLVE_SCOPE)
def solve_stream(
    request: Request,
    response: Response,
    payload: SolveRequest,
    user: models.User = Depends(auth.bind_user),
    _available: None = Depends(ai_control.require_ai_available),
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
      waiting - the request is waiting on Groq: in its queue (reason
               "queue", with a position) or on a 429 inside its slot (reason
               "rate_limited", with Groq's seconds). `kind` says whether the
               gatekeeper's classification or the solve is waiting. May come
               before meta (the classification waits) and before the first
               delta (the solve waits).
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
    # Does the discussion vouch for the exercise this request carries? Decided
    # here, before the cap below reads it (gate_text) and before any route is
    # chosen from it.
    payload.exercise_trusted = trusted_exercise(payload, user)

    # The DoS cap and the chapter check still answer before the stream opens:
    # neither waits for Groq. See app/llm/gatekeeper.py's module docstring.
    if gatekeeper.is_input_too_long(gate_text(payload)):
        return StreamingResponse(
            _gatekeeper_stream(
                gatekeeper.TOO_LONG_MESSAGE, "gatekeeper", payload, started, {"route": "TOO_LONG"}
            ),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    meta_chapitre, meta_topics = _meta_scope(payload)
    priority = llm_queue.priority_for(user.plan)
    practice_on = (
        payload.mode == "practice"
        and payload.exercise_trusted
        and runtime_settings.get("practice_enabled")
    )
    if practice_on and not take_practice_slot(user.id):
        message = PRACTICE_LIMIT_MESSAGE.format(limit=runtime_settings.get("practice_daily_limit"))
        return StreamingResponse(
            _gatekeeper_stream(
                message, "gatekeeper", payload, started, {"route": "PRACTICE_LIMIT"}
            ),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )  # One deadline for everything this request waits on - the classifier's
    # place in Groq's queue, the solve's, and every 429 sleep - so a student
    # hears "busy" within GROQ_QUEUE_TIMEOUT_SECONDS, not a multiple of it.
    budget = llm_queue.WaitBudget(ai_control.queue_timeout_seconds())
    # What the tutor remembers of this discussion (app/grading/session_memory.py).
    memory = session_memory.compact(payload.history)
    memory_text = session_memory.memory_block(memory)
    memory_turns = sum(1 for m in memory if m["role"] == "user")
    note = (payload.note or "").strip() or None
    saved = {"done": False}

    def persist(
        content,
        status_value,
        route_label,
        warnings=None,
        pinned=None,
        retrieved=None,
        learning=None,
    ):
        """Save the exchange server-side (once), when the chat said where it
        belongs. Returns the discussion's new version, or None. `learning`:
        the answer's guided / check fields."""
        if saved["done"] or not content:
            return None
        if not (payload.session_id and payload.user_message_id and payload.assistant_message_id):
            return None
        saved["done"] = True
        return chat_history.record_exchange(
            user.id,
            payload.session_id,
            niveau=payload.niveau,
            chapitre=payload.chapitre,
            title=payload.title,
            user_message={
                "id": payload.user_message_id,
                "role": "user",
                "content": payload.problem,
                "note": note,
                "attachment": payload.attachment,
                "mode": payload.mode if payload.mode != "full" else None,
            },
            assistant_message={
                "id": payload.assistant_message_id,
                "role": "assistant",
                "content": content,
                "status": status_value,
                "warnings": warnings or [],
                "pinned": pinned or [],
                "retrieved": retrieved or [],
                "route": route_label,
                **(learning or {}),
            },
        )

    def give_slot_back(parts):
        """A generated exercise that never arrived costs no daily slot."""
        if practice_on and not "".join(parts).strip():
            release_practice_slot(user.id)

    def done_extra(route_label, version, learning=None):
        return {
            "route": route_label,
            "memory_turns": memory_turns,
            "session_version": version,
            **(learning or {}),
        }

    def events():
        # The gatekeeper runs inside the stream rather than before it: under
        # load its Groq call waits in the same queue as the solves, and only an
        # open stream can tell the student so. The order of decisions is
        # unchanged - classification first, META and OFF_TOPIC never reach
        # build_context.
        try:
            if skips_classifier(payload, memory, note):
                route = "CODE" if payload.mode == "check" else "PROBLEM"
            else:
                route = yield from _relay(
                    gatekeeper.classify_steps(
                        gate_text(payload),
                        priority,
                        budget,
                        previous=session_memory.router_excerpt(memory),
                    )
                )
            if route == "OFF_TOPIC":
                version = persist(gatekeeper.DECLINE_MESSAGE, "none", route)
                yield from _gatekeeper_stream(
                    gatekeeper.DECLINE_MESSAGE,
                    "gatekeeper",
                    payload,
                    started,
                    done_extra(route, version),
                )
                return
            if route == "META":
                answer = yield from _relay(
                    gatekeeper.respond_meta_steps(
                        gate_text(payload),
                        meta_chapitre,
                        meta_topics,
                        priority,
                        budget,
                        niveau=meta_niveau(user, payload),
                    )
                )
                version = persist(answer, "none", route)
                yield from _gatekeeper_stream(
                    answer, GROQ_MODEL, payload, started, done_extra(route, version)
                )
                return
        except gatekeeper.Busy:
            yield from _busy_stream()
            return

        # route is PROBLEM, CODE or QUESTION (gatekeeper.GROUNDED_ROUTES): the
        # same grounded pipeline for all three, each with its own prompt. Context
        # assembly depends on the route, so it now runs inside the stream too: a
        # store failure is an error frame instead of a 422 (the student sees the
        # same generic error either way), while an unavailable chapter is still
        # refused before the stream opens, by _meta_scope above.
        # Mode guide / Verifier ma reponse / a follow-up (learning_route): a
        # short message continuing a discussion gets the FOLLOW_UP prompt,
        # whichever of PROBLEM / QUESTION / CODE the classifier picked - it
        # hesitates between them on follow-ups, and one of them forbids
        # solving (session_memory.is_follow_up).
        prompt_route, step, starts_exercise = learning_route(payload, route, memory, note)
        exercise = payload.problem if starts_exercise else (payload.exercise or payload.problem)
        exercise_id = (
            payload.user_message_id
            if starts_exercise
            else (payload.exercise_id or payload.user_message_id)
        )
        findings = answer_check.precheck(payload.problem) if prompt_route == "CHECK" else []
        guided = {"step": step, "exerciseId": exercise_id} if prompt_route == "GUIDED" else None

        try:
            context = build_context(
                # A button's text ("Indice suivant") retrieves nothing useful;
                # the exercise does.
                session_memory.retrieval_query(
                    exercise if prompt_route == "GUIDED" else payload.problem, memory
                ),
                niveau=payload.niveau,
                chapitre=payload.chapitre,
                k=payload.k,
            )
        except Exception:
            log.exception(
                "could not assemble context for niveau=%s chapitre=%s",
                payload.niveau,
                payload.chapitre,
            )
            yield _sse("error", {"message": "backend", "status": 422})
            return
        if not context.pinned:
            log.error(
                "no pinned syntax core for niveau=%s chapitre=%s", payload.niveau, payload.chapitre
            )
            yield _sse("error", {"message": "backend", "status": 422})
            return

        rendered = context.render()
        messages = build_messages(
            context=rendered,
            query=payload.problem,
            niveau=niveau_label(payload.niveau),
            chapitre=payload.chapitre,
            kind=prompt_route,
            profile=student_profile(user),
            note=note,
            memory=memory_text,
            step=step,
            exercise=exercise,
            # Neither a new exercise nor a button: the student answering the
            # tutor's question at this step.
            reply=prompt_route == "GUIDED" and not starts_exercise and not payload.action,
            difficulty=payload.difficulty,
            precheck=answer_check.findings_block(findings) if prompt_route == "CHECK" else None,
        )

        pinned = [
            {"id": p.chunk_id, "label": p.label, "section": p.section, "content": p.content}
            for p in context.pinned
        ]
        retrieved = [
            {
                "id": h.chunk_id,
                "section": h.section,
                "type": h.type,
                "score": round(h.score, 4),
                "content": h.content,
            }
            for h in context.retrieved
        ]
        yield _sse(
            "meta",
            {
                "model": GROQ_MODEL,
                "niveau": payload.niveau,
                "chapitre": payload.chapitre,
                "route": prompt_route,
                **({"guided": guided} if guided else {}),
                "pinned": pinned,
                "retrieved": retrieved,
            },
        )

        parts: list[str] = []
        try:
            for fragment in stream_groq(
                messages,
                priority=priority,
                budget=budget,
                route=prompt_route,
                memory_chars=len(memory_text or ""),
                # Whose spend this was, for the per-student charts in the
                # console. Never the admin looking at them - this is the solve
                # path, and the user here is the student who asked.
                user_id=user.id,
            ):
                # Still waiting - for a slot, or on Groq's Retry-After inside
                # it. Sent before any delta, so the student sees why nothing
                # is arriving yet.
                if isinstance(fragment, llm_queue.Waiting):
                    yield _waiting_frame(fragment)
                    continue
                parts.append(fragment)
                yield _sse("delta", {"t": fragment})
        except llm_queue.QueueTimeout:
            # Waited as long as the request's budget allows: the same "busy"
            # the student already gets for Groq's own 429, with its retry.
            give_slot_back(parts)
            yield _sse("error", {"message": "busy", "status": 429})
            return
        except urllib.error.HTTPError as exc:
            give_slot_back(parts)
            yield _sse(
                "error",
                {"message": "busy" if exc.code == 429 else "backend", "status": exc.code},
            )
            return
        except (urllib.error.URLError, KeyError):
            give_slot_back(parts)
            yield _sse("error", {"message": "backend", "status": 502})
            return
        except GeneratorExit:
            give_slot_back(parts)
            # The student left mid-answer (tab closed, page changed): keep what
            # was written, marked as stopped - those tokens were paid for.
            persist(
                "".join(parts),
                "stopped",
                prompt_route,
                [],
                pinned,
                retrieved,
                {"guided": guided} if guided else None,
            )
            raise

        answer = "".join(parts)
        # The chat shows the Algorithme column in course notation whatever the
        # model wrote (ui/src/lib/algoNotation.js); check that version, so a
        # slip the student never sees is not reported as a violation - and
        # log it, so the model's slips stay visible.
        checked, fixed = algo_notation.normalize_answer(answer)
        if fixed:
            log.warning(
                "rewrote %d Python operator(s) in the Algorithme column (route %s)",
                fixed,
                route,
            )
        learning: dict[str, Any] = {}
        if prompt_route == "CHECK":
            # The table quoting the student's mistakes is not checked - only
            # the corrected solution under its heading, if there is one.
            checked = _correction_part(checked)
            learning["check"] = {
                "verdict": answer_check.parse_verdict(answer),
                "findings": sorted({f.kind for f in findings}),
            }
        if guided:
            learning["guided"] = guided
        if prompt_route == "PRACTICE":
            learning["practice"] = {"difficulty": payload.difficulty or "same"}
        violations, notes = check_constraints(checked, rendered)
        has_solution = _has_solution_table(checked)
        if guided and guided["step"] < 4:
            if has_solution:
                # The step rules forbid it; kept visible in the logs and the console.
                log.warning("guided step %d answered with a full solution table", guided["step"])
                learning["guided"] = {**guided, "leak": True}
            has_solution = False  # a hint is not a solution to vouch for
        version = persist(
            answer,
            "warned" if violations and has_solution else ("clean" if has_solution else "none"),
            prompt_route,
            violations if has_solution else [],
            pinned,
            retrieved,
            learning,
        )
        yield _sse(
            "done",
            {
                "warnings": violations if has_solution else [],
                "notes": notes,
                "chars": len(answer),
                "elapsed_ms": int((time.monotonic() - started) * 1000),
                **done_extra(prompt_route, version, learning),
            },
        )

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


class ExtractResponse(BaseModel):
    text: str = Field(description="The exercise as read from the file")
    source: str = Field(description="image | pdf (text layer) | pdf-scan")
    pages: int


@app.post("/solve/extract", response_model=ExtractResponse)
@ratelimit.limiter.shared_limit(ai_control.solve_rate_limit, scope=ratelimit.SOLVE_SCOPE)
async def solve_extract(
    request: Request,
    response: Response,
    user: models.User = Depends(auth.bind_user),
    _available: None = Depends(ai_control.require_ai_available),
    _attachments: None = Depends(ai_control.require_attachments),
) -> ExtractResponse:
    """Read an exercise from a photo or a PDF attached in the chat.

    Returns text only. The chat then sends that text through /solve/stream
    like a typed message, so the gatekeeper, the grounded pipeline and the
    checker all apply unchanged - see app/routes/attachments.py.

    The body is the raw file (its own Content-Type), not multipart: one file,
    nothing else to carry. Signed-in only, and drawing on the solve rate-limit
    budget: a transcription is a model call, and a separate bucket would let
    a caller double the spend.
    """
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > attachments.ATTACHMENT_MAX_BYTES:
        raise HTTPException(
            status_code=413, detail="Le fichier est trop volumineux (maximum 10 Mo)."
        )
    data = await request.body()
    try:
        # PDF parsing, image decoding and the model call all block; off the
        # event loop so one upload does not stall every other request.
        result = await run_in_threadpool(
            attachments.extract, data, llm_queue.priority_for(user.plan)
        )
    except attachments.AttachmentError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.message) from exc
    except KeyError as exc:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not set") from exc
    return ExtractResponse(text=result.text, source=result.source, pages=result.pages)
