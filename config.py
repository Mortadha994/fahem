"""Single place for configuration: env loading, endpoints, model names,
on-disk paths, and the gatekeeper's tunable limits.

Everything here is a constant or an env-with-default lookup - no logic, no
imports from the rest of the app, so this module can be imported from
anywhere without a cycle. The modules that *use* these values keep their
logic where it was; only the values moved.

Backwards compatibility note: generate.py and rag_store.py re-export the
names they previously defined, so existing imports elsewhere
(`from generate import GROQ_MODEL, GROQ_URL` in llm_stream.py,
`from rag_store import DEFAULT_DB_DIR` in context.py/test_retrieval.py)
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

# Both are CWD-relative on purpose: the container bind-mounts ./chroma_db and
# ./chunks.json onto /app, which is also the WORKDIR, so a relative path
# resolves to the mounted copy in Docker and to the repo copy locally.
# Changing these to absolute paths would break the compose mounts.
DEFAULT_DB_DIR = Path(os.environ.get("CHROMA_DB_DIR", "chroma_db"))
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
