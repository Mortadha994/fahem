"""Embedding + storage layer for the algorithmique RAG pipeline.

Reads chunks.json (output of extract_chapter.py), embeds each chunk with a
multilingual sentence-transformers model, and stores vectors + metadata in a
local persistent Chroma collection.

The embedding model is multilingual on purpose: the corpus is entirely French
(Tunisian 2eme/3eme/bac algorithmique). An English-only model retrieves poorly
on it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "algorithmique"
DEFAULT_DB_DIR = Path("chroma_db")
DEFAULT_CHUNKS = Path("chunks.json")

# Metadata keys we require on every chunk. niveau + chapitre drive the hard
# retrieval filter, so a chunk missing either of them is unusable.
REQUIRED_META = ("niveau", "chapitre")
OPTIONAL_META = ("section", "type", "format", "page", "source")


_model: SentenceTransformer | None = None


def get_model(model_name: str = MODEL_NAME) -> SentenceTransformer:
    """Load the embedding model once per process."""
    global _model
    if _model is None:
        _model = SentenceTransformer(model_name)
    return _model


def get_client(db_dir: Path = DEFAULT_DB_DIR):
    return chromadb.PersistentClient(
        path=str(db_dir),
        settings=Settings(anonymized_telemetry=False),
    )


def get_collection(db_dir: Path = DEFAULT_DB_DIR):
    """Return the algorithmique collection, creating it if needed.

    Cosine distance: the MiniLM sentence embeddings are trained for cosine
    similarity, and Chroma's default (l2) would rank them differently.
    """
    client = get_client(db_dir)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine", "embedding_model": MODEL_NAME},
    )


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
    """Flatten a chunk's metadata into Chroma-safe scalars.

    Chroma only accepts str/int/float/bool metadata values, so anything else is
    coerced to str. niveau/chapitre are lowercased and stripped so the `where`
    filter matches regardless of how the caller cases them.
    """
    raw: dict[str, Any] = {k: v for k, v in chunk.items() if k != "metadata"}
    raw.update(chunk.get("metadata") or {})

    meta: dict[str, Any] = {}
    for key in REQUIRED_META + OPTIONAL_META:
        value = raw.get(key)
        if value is None or value == "":
            continue
        meta[key] = value if isinstance(value, (int, float, bool)) else str(value).strip()

    # The filter keys are compared verbatim by Chroma, so normalise them here
    # and normalise the query the same way in retrieve().
    for key in REQUIRED_META:
        if key in meta:
            meta[key] = str(meta[key]).strip().lower()
    return meta


def make_id(text: str, meta: dict[str, Any]) -> str:
    """Stable id so re-ingesting the same chunk upserts instead of duplicating."""
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
    db_dir: Path = DEFAULT_DB_DIR,
    batch_size: int = 128,
    reset: bool = False,
) -> int:
    """Embed every chunk in chunks_path and upsert it into Chroma."""
    chunks = load_chunks(chunks_path)
    print(f"Loaded {len(chunks)} chunk(s) from {chunks_path}")

    if reset:
        client = get_client(db_dir)
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"Dropped existing collection '{COLLECTION_NAME}'")
        except Exception:
            pass

    collection = get_collection(db_dir)
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
        collection.upsert(
            ids=ids[start:stop],
            documents=docs[start:stop],
            metadatas=metas[start:stop],
            embeddings=embeddings,
        )
        print(f"  upserted {min(stop, len(ids))}/{len(ids)}")

    print(f"Collection '{COLLECTION_NAME}' holds {collection.count()} chunk(s) at {db_dir}/")
    return len(ids)


def describe(db_dir: Path = DEFAULT_DB_DIR) -> None:
    """Print what is in the store, grouped by niveau/chapitre/type."""
    collection = get_collection(db_dir)
    total = collection.count()
    print(f"Collection '{COLLECTION_NAME}': {total} chunk(s)")
    if not total:
        return
    got = collection.get(include=["metadatas"])
    counts: dict[tuple, int] = {}
    for meta in got["metadatas"]:
        key = (meta.get("niveau"), meta.get("chapitre"), meta.get("type", "?"))
        counts[key] = counts.get(key, 0) + 1
    print("{:<10} {:<10} {:<10} count".format("niveau", "chapitre", "type"))
    for (niveau, chapitre, ctype), n in sorted(counts.items(), key=lambda kv: str(kv[0])):
        print("{:<10} {:<10} {:<10} {}".format(str(niveau), str(chapitre), str(ctype), n))


def main() -> None:
    parser = argparse.ArgumentParser(description="Embed chunks.json into Chroma.")
    parser.add_argument("--chunks", type=Path, default=DEFAULT_CHUNKS)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_DIR)
    parser.add_argument("--reset", action="store_true", help="drop the collection first")
    parser.add_argument("--describe", action="store_true", help="only print store contents")
    args = parser.parse_args()

    if args.describe:
        describe(args.db)
        return
    ingest(args.chunks, args.db, reset=args.reset)


if __name__ == "__main__":
    main()
