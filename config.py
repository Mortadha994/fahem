"""Single place for configuration: env loading, endpoints, model names,
on-disk paths, and the gatekeeper's tunable limits.

Everything here is a constant or an env-with-default lookup - no logic, no
imports from the rest of the app, so this module can be imported from
anywhere without a cycle. The modules that *use* these values keep their
logic where it was; only the values moved.

Backwards compatibility note: generate.py and rag_store.py re-export the
names they previously defined, so existing imports elsewhere
(`from generate import GROQ_MODEL, GROQ_URL` in llm_stream.py,
`from rag_store import QDRANT_URL` in context.py/test_retrieval.py)
keep working untouched.
"""

from __future__ import annotations

import os
from pathlib import Path


def load_env(path: Path = Path(".env")) -> None:
    """Read KEY=value lines from a local .env into os.environ.

    Kept dependency-free and non-overriding: a variable already exported in the
    shell wins, so a one-off `export GROQ_API_KEY=...` still beats the file.
    """
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


load_env()


# --- model backends ---------------------------------------------------------

GROQ_URL = os.environ.get("GROQ_URL", "https://api.groq.com/openai/v1/chat/completions")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:4b")


# --- retrieval store --------------------------------------------------------

EMBEDDING_MODEL_NAME = os.environ.get(
    "EMBEDDING_MODEL_NAME", "paraphrase-multilingual-MiniLM-L12-v2"
)
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "algorithmique")

# Qdrant replaced Chroma as the vector store in Phase 0b. The practical
# difference for this file: the store is no longer a directory on disk, it is
# a service over HTTP, so there is no path to keep CWD-relative any more.
#
# The default targets localhost, which is what a developer running scripts on
# the host gets through the published 6333 port. Inside Docker the compose
# file overrides the host portion with the `qdrant` service name - same
# reasoning as DATABASE_URL below.
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")

# Kept CWD-relative on purpose: the container bind-mounts ./chunks.json onto
# /app, which is also the WORKDIR, so a relative path resolves to the mounted
# copy in Docker and to the repo copy locally. Making it absolute would break
# the compose mount.
DEFAULT_CHUNKS = Path(os.environ.get("CHUNKS_PATH", "chunks.json"))


# --- HTTP API ---------------------------------------------------------------

# Comma-separated in the env var; defaults to the same localhost dev origins
# that were previously hardcoded in api.py. 5174 as well as 5173 because
# another Vite project can hold 5173 and the dev server falls back a port.
_DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"
)
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", _DEFAULT_CORS_ORIGINS).split(",")
    if origin.strip()
]


# --- relational store (PostgreSQL) ------------------------------------------

# SQLAlchemy URL for the Postgres instance holding users, chat sessions and
# chat messages. Nothing reads this yet beyond db.py and Alembic - server-side
# persistence exists but is not wired into any endpoint (see db.py's docstring).
#
# The default targets localhost, which is what a developer running scripts on
# the host gets. Inside Docker the compose file overrides the host portion with
# the `postgres` service name, because `localhost` in a container means the
# container itself, not the database next to it.
#
# `postgresql+psycopg://` selects psycopg v3. The bare `postgresql://` scheme
# would resolve to psycopg2, which is not installed - the driver has to be
# named explicitly or SQLAlchemy fails at connect time, not import time, which
# is a confusing place to discover it.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://fahem:fahem@localhost:5432/fahem",
)


# --- authentication (Google OAuth + session cookie) -------------------------

# The OAuth 2.0 Client ID from the project's Google Cloud console. No default
# on purpose: it is per-project, it is what the ID token's `aud` claim is
# checked against, and a wrong-but-present value would make every sign-in fail
# in a way that looks like a Google outage rather than a config mistake.
# Empty means "auth is not configured" - auth.py refuses to verify a token at
# all in that state rather than accepting one with an unchecked audience.
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")

# HMAC key for the session JWT.
#
# *** PRE-LAUNCH: this default MUST be replaced in any real deployment. ***
#
# It is not a weak secret, it is a *published* one - anyone reading this repo
# can sign a token for any user id and be authenticated as that user. It is a
# full authentication bypass, not a hardening nit. The dev default exists so
# `docker compose up` works out of the box; treat it like the fahem/fahem
# Postgres credentials, on the same pre-launch checklist.
# The default is >= 32 bytes so PyJWT does not raise InsecureKeyLengthWarning
# (RFC 7518 3.2) on every call - the length is not what makes it unsafe, its
# publication is.
SESSION_SECRET_KEY = os.environ.get(
    "SESSION_SECRET_KEY", "dev-only-insecure-session-key-do-not-use-in-production"
)

# 7 days. Long enough that a student is not re-authenticating every session,
# short enough that a stolen cookie expires on its own.
SESSION_TTL_SECONDS = int(os.environ.get("SESSION_TTL_SECONDS", str(7 * 24 * 60 * 60)))

SESSION_COOKIE_NAME = os.environ.get("SESSION_COOKIE_NAME", "fahem_session")

# Secure defaults to False *only* because local dev is plain http. Any
# deployment served over https must set it true - a session cookie without
# Secure can be sent over http and read off the wire.
SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"

# Lax is right when the UI and the API are same-site (app.example.tn +
# api.example.tn share a registrable domain, so Lax cookies are sent).
#
# It is NOT right for the current compose setup: the UI is served from
# localhost:5173 and VITE_API_URL points at 127.0.0.1:8000, and those are
# different hosts, so the browser treats the call as cross-site and withholds
# a Lax cookie entirely. Ports are irrelevant to same-site; hostnames are not.
# Resolving that is the frontend phase's job - either point VITE_API_URL at
# localhost:8000, or set this to "none" (which also forces Secure).
SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "lax").lower()


# --- gatekeeper limits ------------------------------------------------------

# DoS guard, checked before any LLM call at all - including the classifier.
# 2000 chars is ~5-8x the longest real problem statement in the chapter-1
# corpus (sample_problems.json: 109-372 chars, avg 239, measured directly) -
# generous against rejecting a legitimate paste, still a firm pre-LLM
# ceiling against a multi-KB or repeated-token payload.
GATEKEEPER_MAX_INPUT_CHARS = int(os.environ.get("GATEKEEPER_MAX_INPUT_CHARS", "2000"))

# Not "one word out, plus a little room": GROQ_MODEL (gpt-oss-120b) is a
# reasoning model that spends completion tokens on its `reasoning` channel
# BEFORE emitting the actual word into `content` - measured directly, a
# plain classification used ~58 completion tokens end to end ("We need to
# classify. The message: ... So category PROBLEM."). At max_tokens=8 the
# reasoning alone hits the cap (finish_reason: "length"), `content` comes
# back empty, and every message silently falls through to the OFF_TOPIC
# fallback - confirmed live: an early version classified every single
# adversarial-test case (including a genuine problem statement) as
# OFF_TOPIC for exactly this reason. A genuinely ambiguous message pushed
# reasoning past 150 too. 250 gives real margin for a harder decision while
# staying two orders of magnitude below a real generation.
GATEKEEPER_ROUTER_MAX_TOKENS = int(os.environ.get("GATEKEEPER_ROUTER_MAX_TOKENS", "250"))

# A few sentences of French prose, or the decline sentence - never a
# tableau de declaration + solution, which run into the thousands of chars.
GATEKEEPER_META_MAX_TOKENS = int(os.environ.get("GATEKEEPER_META_MAX_TOKENS", "250"))

# Output-side safety net: generous multiple of what META_MAX_TOKENS of
# French prose should produce, catching a run-on/repetition failure mode.
GATEKEEPER_OUTPUT_MAX_CHARS = int(os.environ.get("GATEKEEPER_OUTPUT_MAX_CHARS", "1500"))

# Fail fast: a routing/scope call should not hang the request the way a
# real generation legitimately can (generate.py uses 300s).
GATEKEEPER_TIMEOUT_SECONDS = int(os.environ.get("GATEKEEPER_TIMEOUT_SECONDS", "30"))
