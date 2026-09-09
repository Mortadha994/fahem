"""Scoped retrieval over the algorithmique Qdrant collection.

The scoping rule is not optional: every query is filtered to a single
(niveau, chapitre) *before* the vector search runs. Qdrant applies the filter
as a pre-filter, the same way Chroma's `where` clause did, so the
nearest-neighbour search only ever sees chunks from the requested level and
chapter. That is what stops bac-level syntax from surfacing in a 2eme session.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any, Sequence

from rag_store import (
    COLLECTION_NAME,
    QDRANT_URL,
    TEXT_KEY,
    get_client,
    get_model,
    scope_filter,
)

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
        """Cosine similarity in [0, 1]-ish, easier to read than a distance.

        Qdrant returns this similarity directly; retrieve() stores it as
        `1 - similarity` so the `distance` field keeps the meaning it had
        under Chroma and every caller reading `.score` is unaffected.
        """
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


def retrieve(
    query: str,
    niveau: str,
    chapitre: str,
    k: int = 5,
    url: str = QDRANT_URL,
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

    flt = scope_filter(niveau, chapitre, types)

    client = get_client(url)
    embedding = (
        get_model()
        .encode([query.strip()], normalize_embeddings=True, show_progress_bar=False)
        .tolist()[0]
    )

    result = client.query_points(
        collection_name=COLLECTION_NAME,
        query=embedding,
        query_filter=flt,
        limit=k,
        with_payload=True,
    )

    hits: list[Hit] = []
    for point in result.points:
        payload = dict(point.payload or {})
        # The text and the chunk id ride in the payload; everything else left
        # in it is exactly the metadata dict Chroma used to return separately.
        content = payload.pop(TEXT_KEY, "")
        chunk_id = payload.pop("chunk_id", str(point.id))
        # Qdrant scores cosine *similarity*; Hit stores a distance.
        hits.append(
            Hit(
                content=content,
                metadata=payload,
                distance=1.0 - float(point.score),
                chunk_id=chunk_id,
            )
        )

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
    parser.add_argument("--url", default=QDRANT_URL, help="Qdrant base URL")
    args = parser.parse_args()

    types = (
        None
        if args.types.strip().lower() == "all"
        else [t.strip() for t in args.types.split(",") if t.strip()]
    )

    hits = retrieve(
        args.query,
        niveau=args.niveau,
        chapitre=args.chapitre,
        k=args.k,
        url=args.url,
        types=types,
    )
    print(f"Query: {args.query}")
    print(
        f"Scope: niveau={args.niveau} chapitre={args.chapitre} k={args.k} "
        f"types={','.join(types) if types else 'all'}"
    )
    if not hits:
        print("  no chunks in scope - is this niveau/chapitre ingested?")
        return
    for i, hit in enumerate(hits, 1):
        print(format_hit(hit, i))
        print()


if __name__ == "__main__":
    main()
