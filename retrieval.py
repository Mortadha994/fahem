"""Scoped retrieval over the algorithmique Chroma collection.

The scoping rule is not optional: every query is filtered to a single
(niveau, chapitre) with a Chroma `where` clause *before* the vector search
runs. Chroma applies `where` as a pre-filter, so the nearest-neighbour search
only ever sees chunks from the requested level and chapter. That is what stops
bac-level syntax from surfacing in a 2eme session.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from rag_store import DEFAULT_DB_DIR, get_collection, get_model

# Solve-mode default: cours content only.
#
# A sibling exercise statement carries no syntax or method signal for solving a
# new problem - this chapter ships no solution key for the serie, so an
# `exercice` hit is just another problem's wording. Exercise statements also
# out-embed the cours on any "Ecrire un programme qui ..." query (same
# register), so leaving them in starves the top-k of actual syntax.
#
# `exercice` stays retrievable by passing types explicitly - that is the right
# pool for a future quiz mode ("find me a similar problem"), just not for
# solving.
SOLVE_TYPES = ("prose", "table")
EXERCICE_TYPES = ("exercice",)


@dataclass
class Hit:
    """One retrieved chunk."""

    content: str
    metadata: dict[str, Any]
    distance: float
    chunk_id: str

    @property
    def score(self) -> float:
        """Cosine similarity in [0, 1]-ish, easier to read than a distance."""
        return 1.0 - self.distance

    @property
    def niveau(self) -> str:
        return str(self.metadata.get("niveau", "?"))

    @property
    def chapitre(self) -> str:
        return str(self.metadata.get("chapitre", "?"))

    @property
    def section(self) -> str:
        return str(self.metadata.get("section", "?"))

    @property
    def type(self) -> str:
        return str(self.metadata.get("type", "?"))


def _scope_filter(niveau: str, chapitre: str) -> dict[str, Any]:
    """Build the Chroma where clause. Values are normalised the same way
    rag_store.normalise_metadata() normalised them at ingest time."""
    return {
        "$and": [
            {"niveau": {"$eq": str(niveau).strip().lower()}},
            {"chapitre": {"$eq": str(chapitre).strip().lower()}},
        ]
    }


def retrieve(
    query: str,
    niveau: str,
    chapitre: str,
    k: int = 5,
    db_dir: Path = DEFAULT_DB_DIR,
    types: Sequence[str] | None = SOLVE_TYPES,
) -> list[Hit]:
    """Return the k chunks closest to `query` *within* (niveau, chapitre).

    types restricts the chunk types searched. It defaults to SOLVE_TYPES
    (prose + table), so the whole k budget goes to cours content. Pass
    EXERCICE_TYPES for a similar-problem lookup, or None to search everything.
    """
    if not query or not query.strip():
        raise ValueError("query must not be empty")
    if not niveau or not chapitre:
        raise ValueError("niveau and chapitre are both required - retrieval is always scoped")

    where = _scope_filter(niveau, chapitre)
    if types:
        wanted_types = [str(t).strip().lower() for t in types]
        where["$and"].append({"type": {"$in": wanted_types}})

    collection = get_collection(db_dir)
    embedding = get_model().encode(
        [query.strip()], normalize_embeddings=True, show_progress_bar=False
    ).tolist()

    result = collection.query(
        query_embeddings=embedding,
        n_results=k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]
    ids = (result.get("ids") or [[]])[0]

    hits = [
        Hit(content=doc, metadata=meta or {}, distance=float(dist), chunk_id=cid)
        for doc, meta, dist, cid in zip(documents, metadatas, distances, ids)
    ]

    # Belt and braces: if a chunk ever slipped in with the wrong scope, drop it
    # here rather than hand it to the generation step.
    wanted = (str(niveau).strip().lower(), str(chapitre).strip().lower())
    clean = [h for h in hits if (h.niveau, h.chapitre) == wanted]
    if len(clean) != len(hits):
        print(
            "  WARNING: dropped {} out-of-scope hit(s) that passed the where clause".format(
                len(hits) - len(clean)
            )
        )
    return clean


def format_hit(hit: Hit, index: int, max_chars: int = 700) -> str:
    """Render one hit for terminal inspection."""
    body = hit.content
    truncated = len(body) > max_chars
    if truncated:
        body = body[:max_chars].rstrip() + " ..."
    header = (
        f"  [{index}] score={hit.score:.3f}  niveau={hit.niveau}  "
        f"chapitre={hit.chapitre}  type={hit.type}  section={hit.section}"
    )
    indented = "\n".join("      " + line for line in body.splitlines())
    tail = f"\n      (truncated, {len(hit.content)} chars total)" if truncated else ""
    return f"{header}\n{indented}{tail}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the algorithmique store.")
    parser.add_argument("query")
    parser.add_argument("--niveau", required=True)
    parser.add_argument("--chapitre", required=True)
    parser.add_argument("-k", type=int, default=5)
    parser.add_argument(
        "--types",
        default=",".join(SOLVE_TYPES),
        help="comma-separated chunk types to search, or 'all' (default: prose,table)",
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_DIR)
    args = parser.parse_args()

    types = None if args.types.strip().lower() == "all" else [
        t.strip() for t in args.types.split(",") if t.strip()
    ]

    hits = retrieve(
        args.query,
        niveau=args.niveau,
        chapitre=args.chapitre,
        k=args.k,
        db_dir=args.db,
        types=types,
    )
    print(f"Query: {args.query}")
    print(f"Scope: niveau={args.niveau} chapitre={args.chapitre} k={args.k} "
          f"types={','.join(types) if types else 'all'}")
    if not hits:
        print("  no chunks in scope - is this niveau/chapitre ingested?")
        return
    for i, hit in enumerate(hits, 1):
        print(format_hit(hit, i))
        print()


if __name__ == "__main__":
    main()
