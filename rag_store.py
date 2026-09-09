"""Embedding + storage layer for the algorithmique RAG pipeline.

Reads chunks.json (output of extract_chapter.py), embeds each chunk with a
multilingual sentence-transformers model, and stores vectors + payloads in a
Qdrant collection.

The embedding model is multilingual on purpose: the corpus is entirely French
(Tunisian 2eme/3eme/bac algorithmique). An English-only model retrieves poorly
on it.

Phase 0b swapped Chroma for Qdrant. What deliberately did NOT change: the
embedding model, the chunking, the metadata normalisation, and make_id()'s
content-hash chunk ids. Only the storage/query backend moved, so retrieval
returns the same chunks in the same order - verified against a pre-migration
baseline rather than assumed.

Two Qdrant specifics worth knowing when reading this file:

1. Point ids must be unsigned ints or UUIDs. Qdrant rejects the sha1 hex
   strings make_id() produces, which Chroma accepted verbatim. point_id()
   maps a chunk id to a *deterministic* UUID5, so re-ingesting the same chunk
   overwrites its point instead of adding a duplicate. The original chunk id
   stays in the payload under "chunk_id" and is what every caller still sees.

2. Chroma returned a cosine *distance* (1 - similarity); Qdrant returns the
   cosine *similarity* directly. That conversion lives in retrieval.py where
   the Hit dataclass is built, so this module speaks Qdrant's units only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from pathlib import Path
from typing import Any, Iterable

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from sentence_transformers import SentenceTransformer

# Config moved to config.py; re-exported here so existing imports keep
# working unchanged - context.py and test_retrieval.py both do
# `from rag_store import QDRANT_URL, ...`.
from config import (  # noqa: F401  (re-exported for backwards compatibility)
    COLLECTION_NAME,
    DEFAULT_CHUNKS,
    EMBEDDING_MODEL_NAME,
    QDRANT_URL,
)

# Kept as the module's own name: this file's log lines and CLI help refer to
# MODEL_NAME, and the value is the embedding model specifically.
MODEL_NAME = EMBEDDING_MODEL_NAME

# Metadata keys we require on every chunk. niveau + chapitre drive the hard
# retrieval filter, so a chunk missing either of them is unusable.
REQUIRED_META = ("niveau", "chapitre")
OPTIONAL_META = ("section", "type", "format", "page", "source")

# Payload key holding the chunk text. Qdrant has no separate "documents"
# channel the way Chroma did - the text is just another payload field.
TEXT_KEY = "content"

# Fixed namespace for point_id(). Any constant UUID works; what matters is
# that it never changes, because changing it would remap every chunk onto a
# new point and turn the next ingest into a silent duplicate of the corpus.
POINT_NAMESPACE = uuid.UUID("6f2a1c58-0d4b-5a7e-9c3f-1b8e7d2a4c60")

# The embeddings are L2-normalised at encode time, so cosine is the metric the
# model was trained for. This mirrors the `hnsw:space: cosine` the Chroma
# collection carried. Qdrant's own default is also Cosine, but stating it is
# the point: a silent metric change reorders results with no error anywhere.
DISTANCE = qmodels.Distance.COSINE


_model: SentenceTransformer | None = None


def get_model(model_name: str = MODEL_NAME) -> SentenceTransformer:
    """Load the embedding model once per process."""
    global _model
    if _model is None:
        _model = SentenceTransformer(model_name)
    return _model


def get_client(url: str = QDRANT_URL) -> QdrantClient:
    return QdrantClient(url=url)


def point_id(chunk_id: str) -> str:
    """Deterministic UUID for a chunk id.

    Qdrant will not take make_id()'s sha1 hex string as a point id, so it is
    hashed into a UUID5 under a fixed namespace. Deterministic on purpose:
    the same chunk must land on the same point on every ingest, otherwise
    re-running the CLI grows the collection instead of refreshing it.
    """
    return str(uuid.uuid5(POINT_NAMESPACE, chunk_id))


def vector_size(model_name: str = MODEL_NAME) -> int:
    """Embedding dimension, read from the model rather than hardcoded.

    sentence-transformers renamed get_sentence_embedding_dimension() to
    get_embedding_dimension(); requirements.txt allows both sides of that
    rename, so ask for the new name and fall back rather than pin a version
    or ship a deprecation warning on every ingest.
    """
    model = get_model(model_name)
    getter = getattr(model, "get_embedding_dimension", None) or (
        model.get_sentence_embedding_dimension
    )
    return int(getter())


def scope_filter(niveau: str, chapitre: str, types: Iterable[str] | None = None):
    """Qdrant filter for one (niveau, chapitre), optionally narrowed by type.

    Values are normalised exactly the way normalise_metadata() normalised them
    at ingest time - Qdrant matches keyword payloads verbatim, so a casing
    mismatch here returns nothing rather than erroring.
    """
    must: list[Any] = [
        qmodels.FieldCondition(
            key="niveau", match=qmodels.MatchValue(value=str(niveau).strip().lower())
        ),
        qmodels.FieldCondition(
            key="chapitre", match=qmodels.MatchValue(value=str(chapitre).strip().lower())
        ),
    ]
    if types:
        wanted = [str(t).strip().lower() for t in types]
        must.append(qmodels.FieldCondition(key="type", match=qmodels.MatchAny(any=wanted)))
    return qmodels.Filter(must=must)


def ensure_collection(url: str = QDRANT_URL, recreate: bool = False) -> QdrantClient:
    """Return a client with the collection guaranteed to exist.

    The payload indexes on niveau/chapitre/type are not decoration: every read
    in this project is scope-filtered, and an unindexed filter makes Qdrant
    fall back to a full scan for the pre-filter. This corpus is small enough
    that it would still work; the index is what keeps scoping cheap once more
    chapters land.
    """
    client = get_client(url)
    if recreate and client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
        print(f"Dropped existing collection '{COLLECTION_NAME}'")

    if not client.collection_exists(COLLECTION_NAME):
        size = vector_size()
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=qmodels.VectorParams(size=size, distance=DISTANCE),
        )
        for field in ("niveau", "chapitre", "type"):
            client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name=field,
                field_schema=qmodels.PayloadSchemaType.KEYWORD,
            )
        print(f"Created collection '{COLLECTION_NAME}' (size={size}, distance={DISTANCE})")
    return client


def count(url: str = QDRANT_URL) -> int:
    """Number of points in the collection, or 0 if it does not exist yet."""
    client = get_client(url)
    if not client.collection_exists(COLLECTION_NAME):
        return 0
    return client.count(COLLECTION_NAME, exact=True).count


def scroll_scope(
    niveau: str | None = None,
    chapitre: str | None = None,
    url: str = QDRANT_URL,
) -> list[qmodels.Record]:
    """Every point in a scope, paged through Qdrant's scroll cursor.

    This is the non-vector read path. It backs context.resolve_pins(), which
    locates pinned tables by anchor substring rather than by similarity, and
    the describe / known-scopes reporting. Chroma exposed the same thing as
    collection.get(where=...).

    Scrolling rather than one large limit= is deliberate: a single call
    silently truncates at whatever limit is passed, and a truncated pin scan
    would drop a pinned syntax table without raising anything.
    """
    client = get_client(url)
    if not client.collection_exists(COLLECTION_NAME):
        return []

    flt = scope_filter(niveau, chapitre) if niveau and chapitre else None
    records: list[qmodels.Record] = []
    offset = None
    while True:
        batch, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=flt,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        records.extend(batch)
        if offset is None:
            break
    return records


def load_chunks(path: Path = DEFAULT_CHUNKS) -> list[dict[str, Any]]:
    """Load chunks.json.

    Accepts either a bare list of chunks or {"chunks": [...]} so we are not
    coupled to one exact shape of extract_chapter.py's output.
    """
    if not path.exists():
        raise SystemExit(
            f"{path} not found. Run extract_chapter.py first, e.g.:\n"
            "  python extract_chapter.py path/to/chapter.pdf "
            "--niveau 2eme --chapitre 1"
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("chunks", [])
    if not isinstance(data, list):
        raise SystemExit(f"{path}: expected a list of chunks, got {type(data).__name__}")
    return data


def chunk_text(chunk: dict[str, Any]) -> str:
    """Pull the text out of a chunk, tolerating a couple of key names."""
    for key in ("content", "text", "chunk"):
        value = chunk.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def normalise_metadata(chunk: dict[str, Any]) -> dict[str, Any]:
    """Flatten a chunk's metadata into scalar payload values.

    Kept as-is from the Chroma era even though Qdrant would accept nested
    payloads: this flat shape is what make_id() hashes and what the scope
    filter matches on, so loosening it here would change chunk ids.
    niveau/chapitre are lowercased and stripped so the filter matches
    regardless of how the caller cases them.
    """
    raw: dict[str, Any] = {k: v for k, v in chunk.items() if k != "metadata"}
    raw.update(chunk.get("metadata") or {})

    meta: dict[str, Any] = {}
    for key in REQUIRED_META + OPTIONAL_META:
        value = raw.get(key)
        if value is None or value == "":
            continue
        meta[key] = value if isinstance(value, (int, float, bool)) else str(value).strip()

    # The filter keys are compared verbatim by Qdrant, so normalise them here
    # and normalise the query the same way in scope_filter().
    for key in REQUIRED_META:
        if key in meta:
            meta[key] = str(meta[key]).strip().lower()
    return meta


def make_id(text: str, meta: dict[str, Any]) -> str:
    """Stable id so re-ingesting the same chunk upserts instead of duplicating.

    Unchanged across the Qdrant migration on purpose - these ids show up in
    Hit.chunk_id, in context.py's pinned-vs-retrieved dedup, and in the API's
    grounding excerpts, so changing them would ripple well past storage.
    """
    key = "{}|{}|{}|{}".format(
        meta.get("niveau", ""), meta.get("chapitre", ""), meta.get("section", ""), text
    )
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def prepare(chunks: Iterable[dict[str, Any]]):
    """Validate chunks and split them into (ids, documents, metadatas)."""
    ids: list[str] = []
    docs: list[str] = []
    metas: list[dict[str, Any]] = []
    skipped_empty = 0
    skipped_meta = 0
    seen: set[str] = set()

    for chunk in chunks:
        text = chunk_text(chunk)
        if not text:
            skipped_empty += 1
            continue
        meta = normalise_metadata(chunk)
        missing = [k for k in REQUIRED_META if k not in meta]
        if missing:
            skipped_meta += 1
            continue
        cid = make_id(text, meta)
        if cid in seen:
            continue
        seen.add(cid)
        ids.append(cid)
        docs.append(text)
        metas.append(meta)

    if skipped_empty:
        print("  skipped {} chunk(s) with no text".format(skipped_empty))
    if skipped_meta:
        print("  skipped {} chunk(s) missing niveau/chapitre".format(skipped_meta))
    return ids, docs, metas


def ingest(
    chunks_path: Path = DEFAULT_CHUNKS,
    url: str = QDRANT_URL,
    batch_size: int = 128,
    reset: bool = False,
) -> int:
    """Embed every chunk in chunks_path and upsert it into Qdrant."""
    chunks = load_chunks(chunks_path)
    print(f"Loaded {len(chunks)} chunk(s) from {chunks_path}")

    client = ensure_collection(url, recreate=reset)
    ids, docs, metas = prepare(chunks)
    if not ids:
        print("Nothing to ingest.")
        return 0

    model = get_model()
    print(f"Embedding {len(ids)} chunk(s) with {MODEL_NAME} ...")
    for start in range(0, len(ids), batch_size):
        stop = start + batch_size
        embeddings = model.encode(
            docs[start:stop],
            batch_size=32,
            show_progress_bar=False,
            normalize_embeddings=True,
        ).tolist()
        points = [
            qmodels.PointStruct(
                id=point_id(cid),
                vector=vector,
                payload={**meta, "chunk_id": cid, TEXT_KEY: doc},
            )
            for cid, doc, meta, vector in zip(
                ids[start:stop], docs[start:stop], metas[start:stop], embeddings
            )
        ]
        # wait=True so the tally printed below reflects the write. Qdrant
        # acknowledges asynchronously by default, which would let the final
        # count race the ingest and under-report on a fast machine.
        client.upsert(collection_name=COLLECTION_NAME, points=points, wait=True)
        print(f"  upserted {min(stop, len(ids))}/{len(ids)}")

    print(f"Collection '{COLLECTION_NAME}' holds {count(url)} chunk(s) at {url}")
    return len(ids)


def describe(url: str = QDRANT_URL) -> None:
    """Print what is in the store, grouped by niveau/chapitre/type."""
    total = count(url)
    print(f"Collection '{COLLECTION_NAME}': {total} chunk(s)")
    if not total:
        return
    counts: dict[tuple, int] = {}
    for record in scroll_scope(url=url):
        payload = record.payload or {}
        key = (payload.get("niveau"), payload.get("chapitre"), payload.get("type", "?"))
        counts[key] = counts.get(key, 0) + 1
    print("{:<10} {:<10} {:<10} count".format("niveau", "chapitre", "type"))
    for (niveau, chapitre, ctype), n in sorted(counts.items(), key=lambda kv: str(kv[0])):
        print("{:<10} {:<10} {:<10} {}".format(str(niveau), str(chapitre), str(ctype), n))


def main() -> None:
    parser = argparse.ArgumentParser(description="Embed chunks.json into Qdrant.")
    parser.add_argument("--chunks", type=Path, default=DEFAULT_CHUNKS)
    parser.add_argument("--url", default=QDRANT_URL, help="Qdrant base URL")
    parser.add_argument("--reset", action="store_true", help="drop the collection first")
    parser.add_argument("--describe", action="store_true", help="only print store contents")
    args = parser.parse_args()

    if args.describe:
        describe(args.url)
        return
    ingest(args.chunks, args.url, reset=args.reset)


if __name__ == "__main__":
    main()
