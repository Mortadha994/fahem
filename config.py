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
# That holds locally too, but only because VITE_API_URL was pointed at
# localhost:8000 rather than 127.0.0.1:8000. Ports are irrelevant to
# same-site; hostnames are not, so localhost:5173 -> 127.0.0.1:8000 would be
# cross-site and the browser would withhold this cookie entirely, leaving the
# app stuck on the sign-in screen. If the API host ever moves to a different
# registrable domain than the UI, this has to become "none" (which also
# forces Secure).
SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "lax").lower()


# --- password accounts + transactional email (Phase 4) ----------------------

# Where links in emails point. The verification link lands on the API (a
# one-click GET that marks the address and bounces to the app). The reset link
# lands on the app, carrying its token in the URL *fragment*: a fragment is
# never sent to any server, so it cannot end up in nginx's access log or a
# Referer header, and the app POSTs it to /auth/reset-password itself.
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:5173").rstrip("/")
PUBLIC_API_URL = os.environ.get("PUBLIC_API_URL", "http://localhost:8000").rstrip("/")

# Length is the only rule (NIST SP 800-63B, OWASP ASVS V2.1): no forced
# digits or symbols, which mostly produce "Password1!" and annoyed users. The
# maximum is not a security rule - it bounds how much work a single request can
# make Argon2 do, and 128 characters is far past any passphrase anyone types.
PASSWORD_MIN_LENGTH = int(os.environ.get("PASSWORD_MIN_LENGTH", "12"))
PASSWORD_MAX_LENGTH = int(os.environ.get("PASSWORD_MAX_LENGTH", "128"))

RESET_TOKEN_TTL_SECONDS = int(os.environ.get("RESET_TOKEN_TTL_SECONDS", str(60 * 60)))
VERIFY_TOKEN_TTL_SECONDS = int(os.environ.get("VERIFY_TOKEN_TTL_SECONDS", str(24 * 60 * 60)))

# Resend (https://resend.com). An empty key means email is not configured:
# sends are refused and logged as not sent, never faked. EMAIL_FROM must be on a
# domain verified in Resend - the onboarding@resend.dev default only delivers
# to the Resend account owner's own address, which is enough for local testing
# and nothing else.
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "Fahem <onboarding@resend.dev>")


# --- chapter content --------------------------------------------------------

# The exercise catalogue. Same file the retrieval and context build checks
# already run against, so the exercises a student sees and the ones the
# regression baselines use cannot drift apart.
#
# Bind-mounted like chunks.json, and CWD-relative for the same reason.
#
# Note: context.py, generate.py and test_retrieval.py each still carry their
# own `Path("sample_problems.json")` CLI default. Those are RAG-side files and
# out of scope for this phase, so they were left alone rather than pointed
# here - worth folding in whenever one of them is next touched.
DEFAULT_PROBLEMS = Path(os.environ.get("PROBLEMS_PATH", "sample_problems.json"))

# The lesson PDF a student reads in-app, served by GET /chapters/{id}/pdf.
#
# *** PLACEHOLDER: this document is stand-in content for the MVP and will be
# replaced. *** Swapping it must stay a one-line change here - never edit
# chapters.py or an endpoint to point at a different file.
#
# Two PDFs sit in data/, and they are not interchangeable:
#   Chap1_Structures_donnees_simples.pdf  - the cours itself, 15 pages,
#       opening straight on "Chapitre I". This is the one a student reads.
#   chap 1 + serie.pdf                    - the RAG extraction source that
#       every chunk in chunks.json cites, 17 pages, cover page plus the
#       exercise serie. Not the reading copy.
#
# CWD-relative for the same reason as DEFAULT_CHUNKS: compose bind-mounts
# ./data onto /app/data (read-only), and /app is the WORKDIR, so a relative
# path resolves to the mounted copy in Docker and the repo copy locally.
# data/*.pdf is gitignored and data/ is in .dockerignore, so the file only
# ever arrives through that mount - it is deliberately not baked into the
# image.
LESSON_PDF_PATH = Path(
    os.environ.get("LESSON_PDF_PATH", "data/Chap1_Structures_donnees_simples.pdf")
)


# --- rate limiting (Redis) --------------------------------------------------

# Counter store for slowapi. Same host-vs-service-name split as DATABASE_URL
# and QDRANT_URL: localhost for scripts on the host, overridden to the `redis`
# service name inside compose.
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

# EVERY LIMIT BELOW IS A STARTING POINT, NOT A TUNED VALUE. There is no real
# usage data yet - these were picked from what the app costs and how a student
# actually works, and they should be revisited against real traffic before or
# shortly after launch.
#
# /solve and /solve/stream share one budget (they are the same work behind two
# response shapes, and separate buckets would let a caller double the spend by
# alternating). Two windows, both enforced:
#
#   per minute - a burst guard. A real generation takes ~3s and a student
#                reads the answer before sending the next one, so 10/min is
#                far above human pace while still stopping a hot loop.
#   per hour   - the actual cost ceiling. A long revision session might be
#                20-40 exercises; 100 leaves generous headroom and still caps
#                what one compromised session can spend in an hour.
RATE_LIMIT_SOLVE = os.environ.get("RATE_LIMIT_SOLVE", "10/minute;100/hour")

# /auth/google is reachable before there is a user to key on, so it is limited
# per client IP instead.
#
# KNOWN WEAKNESS, deliberately left loose: a school behind one NAT presents
# every student as the same IP, so a class signing in together shares this
# budget. That is why it is 30/minute and not the 5/minute a login endpoint
# would normally get - it is sized to not break a classroom, which makes it a
# weak brute-force control. It is acceptable only because this endpoint does
# not accept a password: the credential is a Google-signed ID token, and
# guessing one is not a rate-limitable attack. It exists to stop hammering,
# not to stop credential stuffing.
RATE_LIMIT_AUTH = os.environ.get("RATE_LIMIT_AUTH", "30/minute")

# The password routes (Phase 4) DO accept a secret, so the per-IP reasoning
# above would make them the weak control it describes. The real brute-force
# control is per *email*: credential stuffing spreads one account's guesses
# across many IPs, and a per-IP limit loose enough for a classroom NAT never
# sees them. The email is hashed before it becomes a Redis key.
#
#   signup   per IP    - sized for a class creating accounts together
#   login    per IP    - same classroom reasoning as RATE_LIMIT_AUTH
#   login    per email - the limit that actually stops password guessing
#   forgot   per IP, and per email so nobody can use Fahem to flood someone
#            else's inbox with reset mails
#   token    per IP    - reset/verify tokens are 256-bit, so this is
#            protection against hammering, not against guessing
RATE_LIMIT_SIGNUP = os.environ.get("RATE_LIMIT_SIGNUP", "30/hour")
RATE_LIMIT_LOGIN = os.environ.get("RATE_LIMIT_LOGIN", "30/minute")
RATE_LIMIT_LOGIN_EMAIL = os.environ.get("RATE_LIMIT_LOGIN_EMAIL", "5/minute;20/hour")
RATE_LIMIT_FORGOT = os.environ.get("RATE_LIMIT_FORGOT", "10/hour")
RATE_LIMIT_FORGOT_EMAIL = os.environ.get("RATE_LIMIT_FORGOT_EMAIL", "3/hour")
RATE_LIMIT_TOKEN = os.environ.get("RATE_LIMIT_TOKEN", "20/minute")

# Sent as Retry-After on a 429. slowapi knows the true window reset, and the
# handler prefers it; this is only the fallback when it cannot be derived.
RATE_LIMIT_RETRY_AFTER_FALLBACK = int(os.environ.get("RATE_LIMIT_RETRY_AFTER_FALLBACK", "60"))


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
