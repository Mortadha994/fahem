"""Assemble the context block that Phase 2's prompt will be built on.

Two parts, in this order:

1. A pinned syntax core - four reference tables that every exercise in this
   chapter draws on. They are included unconditionally, before any retrieval
   runs. Their relevance is not a ranking question: they are the reference
   sheet for the chapter, so making them compete with generic exposition for a
   top-k slot was solving the wrong problem.

2. Retrieved extras - the cours pool (prose + table), minus anything already
   pinned, supplying only the topic-specific supplement: which type applies,
   tableau declaration syntax, string functions, and so on.

Because the universal content is already guaranteed, retrieval only has to win
a much narrower contest, which is what the current symmetric embedding model
can actually do.

Deferred, deliberately: swapping to an asymmetric model (multilingual-e5-base
with query:/passage: prefixes). It is the real fix for symmetric embeddings
matching on shared vocabulary rather than on "what knowledge solves this", but
it is not needed while the always-relevant tables are hand-curated and small.
Revisit when either (a) a chapter's universal table set grows too big to
curate by hand, or (b) retrieval spans multiple chapters, where nothing is
universal any more.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rag_store import QDRANT_URL, TEXT_KEY, scroll_scope
from retrieval import SOLVE_TYPES, Hit, retrieve

ARROW = "←"


@dataclass(frozen=True)
class PinSpec:
    """One pinned table, located by an exact substring rather than an index.

    Chunk ids are content hashes, so they move whenever the extraction changes.
    An anchor line is stable across re-extraction and fails loudly if the table
    stops being extracted the way we expect.
    """

    label: str
    anchor: str
    min_arrows: int = 0  # assignment arrows that must survive extraction


# The chapter's reference sheet. "Entrée/sortie" is two chunks in the corpus -
# the PDF draws input and output as separate tables - so it is pinned as two.
PINS: tuple[PinSpec, ...] = (
    PinSpec(
        "Opérateurs arithmétiques et relationnels",
        "Opérateur | Python | algorithme | Exemple",
    ),
    PinSpec(
        "Affectation",
        "Variable ← Valeur | Variable =Valeur",
        min_arrows=1,
    ),
    PinSpec(
        "Entrée (lecture)",
        "Syntaxe en algorithme",
    ),
    PinSpec(
        "Sortie (écriture)",
        'print ("Message1", Objet1, "Message2", Objet2)',
    ),
    PinSpec(
        "Fonctions mathématiques",
        "arrondi (x) | round (x)",
        min_arrows=2,
    ),
    # Sixth pin. input() returns a string, so nearly every exercise in the
    # chapter needs a conversion before it can compute - as universal as the
    # other five. Its absence was not theoretical: without it, ex21's generated
    # solution used int(input(...)) for a moyenne and silently truncated 12.5
    # to 12, because int() was the only conversion the context offered (and
    # only as "partie entière", not as string parsing). The same chunk carries
    # Sous_chaine/Effacer, which the digit-manipulation exercises need.
    PinSpec(
        "Conversion de types et fonctions sur chaînes",
        "Valeur(ch) | int(ch) Ou float(ch)",
        min_arrows=11,
    ),
    # Seventh pin. Pinned as a whole chunk (657 chars), not just the ~90-char
    # Long/Len row: pins are located by anchor in the store, and slicing a row
    # out would mean editing corpus text and losing the verbatim guarantee.
    # The rest of the chunk earns its place anyway - concatenation is required
    # for the string-slice route, and Pos/Majus are chapter material.
    #
    # Why it is here despite not being universal: ex24 (Substitution) is
    # solvable with chapter-1 tools alone -
    #   C = Valeur(Sous_chaine(chA, 0, Long(chA)-n) + Sous_chaine(chB, 0, n))
    # - but its énoncé never says "chaîne", so it never ranks the string
    # table, and the model failed it twice for want of a length function.
    # Retrieval surfaces this table for queries that mention strings (ex20)
    # and correctly withholds it otherwise (ex19); the gap is queries that
    # need a length without saying so.
    PinSpec(
        "Fonctions sur les chaînes (longueur, concaténation, position)",
        "Long(ch) | Len(ch)",
    ),
)


@dataclass
class PinnedChunk:
    label: str
    content: str
    metadata: dict[str, Any]
    chunk_id: str

    @property
    def section(self) -> str:
        return str(self.metadata.get("section", "?"))


class PinResolutionError(RuntimeError):
    """Raised when a pinned table cannot be located exactly once."""


def resolve_pins(
    niveau: str,
    chapitre: str,
    url: str = QDRANT_URL,
    pins: tuple[PinSpec, ...] = PINS,
) -> list[PinnedChunk]:
    """Locate every pinned table in the store, or fail loudly.

    Silently dropping a pin would quietly remove the operator table from every
    prompt, so a miss is an error rather than a warning.

    This is a scoped scan, not a vector search - pins are located by exact
    anchor substring, and ranking has nothing to do with it. Phase 0b changed
    only the call that fetches the scope (Qdrant scroll instead of Chroma's
    collection.get); the matching rule below is untouched, which is why the
    same seven tables still resolve to the same seven chunks.
    """
    records = scroll_scope(niveau, chapitre, url=url)
    triples = [
        (
            str((r.payload or {}).get("chunk_id", r.id)),
            str((r.payload or {}).get(TEXT_KEY, "")),
            {k: v for k, v in (r.payload or {}).items() if k not in (TEXT_KEY, "chunk_id")},
        )
        for r in records
    ]

    resolved: list[PinnedChunk] = []
    problems: list[str] = []

    for pin in pins:
        matches = [(cid, doc, meta) for cid, doc, meta in triples if pin.anchor in doc]
        if len(matches) != 1:
            problems.append(
                f"{pin.label!r}: expected exactly 1 chunk containing "
                f"{pin.anchor!r}, found {len(matches)}"
            )
            continue

        cid, doc, meta = matches[0]
        arrows = doc.count(ARROW)
        if arrows < pin.min_arrows:
            problems.append(
                f"{pin.label!r}: expected at least {pin.min_arrows} '{ARROW}', "
                f"found {arrows} - run patch_chunks.py and re-embed"
            )
            continue

        resolved.append(PinnedChunk(pin.label, doc, meta or {}, cid))

    if problems:
        raise PinResolutionError(
            "pinned syntax core could not be assembled:\n  " + "\n  ".join(problems)
        )
    return resolved


@dataclass
class Context:
    query: str
    niveau: str
    chapitre: str
    pinned: list[PinnedChunk]
    retrieved: list[Hit]

    def render(self) -> str:
        parts = [
            "=== SYNTAXE DE REFERENCE (chapitre entier) ===",
            "",
        ]
        for pin in self.pinned:
            parts.append(f"--- {pin.label} [{pin.section}] ---")
            parts.append(pin.content)
            parts.append("")
        parts.append("=== EXTRAITS DU COURS LIES A CE PROBLEME ===")
        parts.append("")
        if not self.retrieved:
            parts.append("(aucun extrait supplementaire)")
        for hit in self.retrieved:
            parts.append(f"--- {hit.section} ({hit.type}) ---")
            parts.append(hit.content)
            parts.append("")
        return "\n".join(parts).rstrip() + "\n"


def build_context(
    query: str,
    niveau: str,
    chapitre: str,
    k: int = 5,
    url: str = QDRANT_URL,
) -> Context:
    """Pinned syntax core + k retrieved extras that are not already pinned."""
    pinned = resolve_pins(niveau, chapitre, url)
    pinned_ids = {p.chunk_id for p in pinned}

    # Over-fetch so that dropping pinned duplicates still leaves k extras.
    candidates = retrieve(
        query,
        niveau=niveau,
        chapitre=chapitre,
        k=k + len(pinned),
        url=url,
        types=SOLVE_TYPES,
    )
    extras = [h for h in candidates if h.chunk_id not in pinned_ids][:k]

    return Context(query, niveau, chapitre, pinned, extras)


def build_check(context: Context) -> list[str]:
    """Assertions for the Phase 1 build check. Returns a list of failures."""
    failures: list[str] = []

    labels = [p.label for p in context.pinned]
    for pin in PINS:
        if pin.label not in labels:
            failures.append(f"missing pinned table: {pin.label}")

    for pinned in context.pinned:
        spec = next((p for p in PINS if p.label == pinned.label), None)
        if spec and pinned.content.count(ARROW) < spec.min_arrows:
            failures.append(f"{pinned.label}: assignment arrow missing")
        if spec and spec.anchor not in pinned.content:
            failures.append(f"{pinned.label}: anchor text not present verbatim")

    pinned_ids = {p.chunk_id for p in context.pinned}
    duplicated = [h for h in context.retrieved if h.chunk_id in pinned_ids]
    if duplicated:
        failures.append(f"{len(duplicated)} retrieved chunk(s) duplicate pinned content")

    if not context.retrieved:
        failures.append("retrieval added nothing")

    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble and check context blocks.")
    parser.add_argument("--problems", type=Path, default=Path("sample_problems.json"))
    parser.add_argument("-k", type=int, default=5)
    parser.add_argument("--url", default=QDRANT_URL, help="Qdrant base URL")
    parser.add_argument("--show", action="store_true", help="print the full context block")
    args = parser.parse_args()

    problems = json.loads(args.problems.read_text(encoding="utf-8"))
    all_failures = 0

    for problem in problems:
        pid = problem.get("id", "?")
        context = build_context(
            problem["question"],
            niveau=str(problem["niveau"]),
            chapitre=str(problem["chapitre"]),
            k=args.k,
            url=args.url,
        )

        print("=" * 78)
        print(f"[{pid}] {problem['question'][:70]}...")
        print("-" * 78)
        print(f"  pinned ({len(context.pinned)}):")
        for pin in context.pinned:
            arrows = pin.content.count(ARROW)
            tag = f"  arrows={arrows}" if arrows else ""
            print(f"    - {pin.label} [{pin.section}] {len(pin.content)} chars{tag}")
        print(f"  retrieved extras ({len(context.retrieved)}):")
        for hit in context.retrieved:
            print(
                f"    - {hit.score:.3f}  {hit.type:<7} {hit.section[:40]:40s} "
                f"{len(hit.content)} chars"
            )

        failures = build_check(context)
        all_failures += len(failures)
        if failures:
            print("  BUILD CHECK FAILED:")
            for failure in failures:
                print(f"    ! {failure}")
        else:
            print("  build check: OK")

        if args.show:
            print("-" * 78)
            print(context.render())
        print()

    print("=" * 78)
    print("ALL BUILD CHECKS PASSED" if all_failures == 0 else f"{all_failures} FAILURE(S)")
    raise SystemExit(1 if all_failures else 0)


if __name__ == "__main__":
    main()
