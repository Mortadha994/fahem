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
import logging
import os
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from app.core.chapter_ids import chapter_number
from app.core.models import niveau_label
from app.rag.rag_store import QDRANT_URL, TEXT_KEY, scroll_scope
from app.rag.retrieval import SOLVE_TYPES, Hit, retrieve

ARROW = "←"

log = logging.getLogger("fahem.context")

# The model takes at most 8000 tokens per request (Groq, on-demand tier, for
# gpt-oss-120b), and these courses - French, code, tables - cost about 2.4
# characters per token: roughly 19 000 characters for the whole request. The
# system prompt takes about 9 500 of them, so the context gets what is left,
# with margin for the student's problem and the discussion so far. Past the
# limit the model answers 413 and the student gets no answer at all, which is
# worse than an answer with a slimmer reference sheet.
MAX_CONTEXT_CHARS = int(os.environ.get("CONTEXT_MAX_CHARS", "7500"))
MIN_EXTRAS_BUDGET = 1400  # kept for retrieved extras whenever the pins leave room
EXTRA_MAX_CHARS = 700  # one retrieved extract, cut


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
                f"found {arrows} - run scripts/patch_chunks.py and re-embed"
            )
            continue

        resolved.append(PinnedChunk(pin.label, doc, meta or {}, cid))

    if problems:
        raise PinResolutionError(
            "pinned syntax core could not be assembled:\n  " + "\n  ".join(problems)
        )
    return resolved


# Phase 9. PINS above is chapter 1's hand-curated reference sheet, located by
# anchor text that exists only in chapter 1's PDF. Uploaded chapters carry
# their reference sheet in the published Qdrant payload instead: the admin
# ticks which chunks are pinned during review, and chapter_store.publish writes
# `pinned`/`pin_label` onto those points. Reading them back from Qdrant (not
# from the draft rows in Postgres) is what keeps a half-reviewed edit out of a
# student's prompt until it is republished.
BUILTIN_PIN_SCOPE = ("2eme", "1")


def published_pins(niveau: str, chapitre: str, url: str = QDRANT_URL) -> list[PinnedChunk]:
    """The pinned chunks of a published uploaded chapter, or fail loudly.

    Same contract as resolve_pins: an empty reference sheet is an error, not an
    empty list - a prompt with no syntax core would let the model fall back on
    whatever notation it learned elsewhere. An unpublished chapter has no
    points at all, so it fails here too, and /solve answers 422.
    """
    pins = []
    for r in scroll_scope(niveau, chapitre, url=url):
        payload = r.payload or {}
        if not payload.get("pinned"):
            continue
        pins.append(
            PinnedChunk(
                label=str(payload.get("pin_label") or payload.get("section") or "Référence"),
                content=str(payload.get(TEXT_KEY, "")),
                metadata={
                    k: v
                    for k, v in payload.items()
                    if k not in (TEXT_KEY, "chunk_id", "pinned", "pin_label")
                },
                chunk_id=str(payload.get("chunk_id", r.id)),
            )
        )
    if not pins:
        raise PinResolutionError(
            f"no pinned syntax core published for niveau={niveau} chapitre={chapitre}"
        )
    # Scroll order is point-id order, which is arbitrary; the course's order is
    # the order a student reads the reference sheet in. `position` is written
    # at publish; `page` is the fallback for points published before it was.
    pins.sort(
        key=lambda p: (
            int(p.metadata.get("position", -1)),
            int(p.metadata.get("page") or 0),
            p.label,
        )
    )
    return pins


def prerequisite_pins(niveau: str, chapitre: str, url: str = QDRANT_URL) -> list[PinnedChunk]:
    """The reference sheets of every chapter before this one.

    The programme is cumulative - a chapter-2 exercise still reads input with
    Lire/input() and tests parity with mod, which are chapter-1 syntax. Scoping
    the syntax core to the current chapter alone made the model fall back on
    whatever notation it knew (`N % 2 = 0` in an algorithm instead of
    `N mod 2 = 0`) and made the checker flag input()/int() as invented.

    Chapter 1 is the built-in sheet (PINS) and must resolve, as everywhere
    else. A later chapter that is not published yet is simply absent: the
    student cannot have studied it on Fahem either. Labels are prefixed with
    the chapter so the prompt shows where each sheet comes from.

    The years are cumulative too: a 3ème student has done the whole 2ème
    programme (sous-programmes included) and a Bac student both before it, so
    what they learnt earlier stays theirs to use. Those sheets come first, in
    teaching order; build_context then keeps the ones that fit the budget.
    """
    try:
        n = int(str(chapitre).strip())
    except ValueError:
        return []
    key = str(niveau).strip().lower()
    pins: list[PinnedChunk] = []
    # The built-in 2ème chapter 1 is behind every chapter of every year, except
    # itself (it has no earlier chapter) and a 2ème chapter 1 lookalike.
    if key in YEAR_ORDER and not (key == BUILTIN_PIN_SCOPE[0] and n <= 1):
        try:
            builtin = resolve_pins(BUILTIN_PIN_SCOPE[0], BUILTIN_PIN_SCOPE[1], url)
        except PinResolutionError:
            if key == BUILTIN_PIN_SCOPE[0]:
                raise  # unchanged for 2ème: its own foundation must resolve
            builtin = []
        origin = "" if key == BUILTIN_PIN_SCOPE[0] else f"{niveau_label(BUILTIN_PIN_SCOPE[0])} "
        for p in builtin:
            p.label = f"{origin}Ch. 1 — {p.label}"
        pins.extend(builtin)
    for earlier_niveau, chapter_id in earlier_chapters(key, n, _published_rows()):
        try:
            sheets = published_pins(earlier_niveau, chapter_id, url)
        except PinResolutionError:
            continue
        where = f"Ch. {chapter_number(chapter_id)}"
        if earlier_niveau != key:
            where = f"{niveau_label(earlier_niveau)} {where}"
        for p in sheets:
            p.label = f"{where} — {p.label}"
        pins.extend(sheets)
    return pins


# The years in the order a student goes through them.
YEAR_ORDER = ("2eme", "3eme", "bac")


def _published_rows() -> list[Any]:
    """The published uploaded chapters (id, niveau); empty if the store is not
    reachable, which leaves a student with this chapter's own sheets only."""
    try:
        from app.rag import chapter_store

        return chapter_store.published_chapters()
    except Exception:  # noqa: BLE001 - no database in a bare script run
        log.warning("could not list the published chapters for the earlier-chapter sheets")
        return []


def earlier_chapters(niveau: str, chapitre: int, published: list[Any]) -> list[tuple[str, str]]:
    """(niveau, chapter id) of the published chapters studied before this one,
    in teaching order: every chapter of the earlier years, then the chapters of
    this year that come first. The built-in 2ème chapter 1 is not in the list
    (it is not an upload; prerequisite_pins adds it)."""
    if niveau not in YEAR_ORDER:
        return []
    mine = YEAR_ORDER.index(niveau)
    chosen = []
    for row in published:
        if row.niveau not in YEAR_ORDER or not str(row.id).isdigit():
            continue
        rank = YEAR_ORDER.index(row.niveau)
        number = int(chapter_number(row.id))
        if rank < mine or (rank == mine and int(row.id) < chapitre):
            chosen.append((rank, number, row.niveau, str(row.id)))
    return [(n, i) for _r, _num, n, i in sorted(chosen)]


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


def _pin_cost(pin: PinnedChunk) -> int:
    return len(pin.label) + len(pin.section) + len(pin.content) + 12


def _hit_cost(hit: Hit) -> int:
    return len(hit.section) + len(hit.type) + len(hit.content) + 12


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-zàâçéèêëîïôûùüÿ_]{4,}", text.lower()))


def fit_prerequisites(
    pins: list[PinnedChunk], query: str, budget: int
) -> list[PinnedChunk]:
    """The earlier chapters' reference sheets that fit `budget` characters.

    The programme is cumulative, but the whole of it no longer fits in one
    request. The sheets that share the most vocabulary with the problem go
    first (Lire/Ecrire for a problem that reads and writes), the most recent
    chapter breaking ties; what is kept stays in the order a student learnt it.
    """
    if budget <= 0 or not pins:
        return []
    wanted = _words(query)
    ranked = sorted(
        range(len(pins)),
        key=lambda i: (-len(wanted & _words(pins[i].label + " " + pins[i].content)), -i),
    )
    kept: set[int] = set()
    used = 0
    for i in ranked:
        cost = _pin_cost(pins[i])
        if used + cost <= budget:
            kept.add(i)
            used += cost
    if len(kept) < len(pins):
        log.info(
            "context budget: kept %d of %d earlier reference sheets (%d of %d chars)",
            len(kept), len(pins), used, budget,
        )
    return [pins[i] for i in sorted(kept)]


def build_context(
    query: str,
    niveau: str,
    chapitre: str,
    k: int = 5,
    url: str = QDRANT_URL,
) -> Context:
    """Pinned syntax core + k retrieved extras that are not already pinned,
    within MAX_CONTEXT_CHARS."""
    if (str(niveau).strip().lower(), str(chapitre).strip().lower()) == BUILTIN_PIN_SCOPE:
        pinned = resolve_pins(niveau, chapitre, url)
    else:
        # Earlier chapters first, then this one - the order a student learnt
        # them in. Retrieval below stays scoped to this chapter alone. This
        # chapter's own sheets always stay whole; the earlier ones are what
        # the budget trims.
        own = published_pins(niveau, chapitre, url)
        own_cost = sum(_pin_cost(p) for p in own)
        earlier = fit_prerequisites(
            prerequisite_pins(niveau, chapitre, url),
            query,
            MAX_CONTEXT_CHARS - own_cost - MIN_EXTRAS_BUDGET,
        )
        pinned = earlier + own
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
    room = MAX_CONTEXT_CHARS - sum(_pin_cost(p) for p in pinned)
    extras: list[Hit] = []
    for hit in (h for h in candidates if h.chunk_id not in pinned_ids):
        if len(extras) == k:
            break
        if len(hit.content) > EXTRA_MAX_CHARS:
            hit = replace(hit, content=hit.content[:EXTRA_MAX_CHARS].rstrip() + " ...")
        if _hit_cost(hit) > room:
            continue
        extras.append(hit)
        room -= _hit_cost(hit)

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
