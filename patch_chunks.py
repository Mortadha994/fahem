"""Pinned manual corrections to chunks.json.

NOT a general auto-fix. Every entry below is an exact literal string that was
verified by eye against the source PDF. Nothing is inferred, nothing is matched
by pattern - a regex for the assignment arrow would also rewrite genuine
subtraction in the same tables (the operator table's `4 - 2 = 2`), turning a
visible extraction bug into a silent correctness bug.

Why this exists: the PDF draws the assignment arrow with a custom font glyph
that has no usable Unicode mapping, so pdfplumber decodes it as "-". In the
Calcul_Somme worked example that renders `somme - entier1 + entier2`, which
reads as a subtraction rather than an assignment. A student-facing model
trained on that would emit the wrong operator.

extract_chapter.py regenerates chunks.json from scratch, so run this after
every extraction:

    python extract_chapter.py <pdf> --niveau 2eme --chapitre 1
    python patch_chunks.py
    python rag_store.py --chunks chunks.json --reset

It is idempotent, and it fails loudly if a target no longer matches - if the
source PDF changes, that is a signal to re-check the extraction by eye rather
than to loosen the patch.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ARROW = "←"  # LEFTWARDS ARROW

# (page, exact substring to replace, replacement, expected occurrences)
PATCHES: list[tuple[int, str, str, int]] = [
    (2, "| somme -entier1 + entier2 |", f"| somme {ARROW} entier1 + entier2 |", 1),
    (3, "| somme - entier1 + entier2 |", f"| somme {ARROW} entier1 + entier2 |", 1),
    # Found by verify() below, then confirmed against the PDF: section V's
    # output example is "X <- 474", an assignment, not "X minus 474". This one
    # sits in a `prose` chunk, so unlike the Exercice 8/10 hits it is inside the
    # solve-mode retrieval pool.
    (10, "X - 474", f"X {ARROW} 474", 1),
    # Page 11's math-functions table, same glyph bug in a different shape: here
    # the arrow collapses against the adjacent token instead of leaving an
    # isolated " - ", which is why the first verify() pass did not flag it.
    (11, "| X - int (9.499) X vaut 9", f"| X {ARROW} int (9.499) X vaut 9", 1),
    (11, "| X-Alea X vaut", f"| X {ARROW} Alea X vaut", 1),
    # Page 12's string-functions table, surfaced once the check was widened.
    # All cours content in section VI, so all inside the solve-mode pool.
    # Note "22-23" below is a real hyphen inside a string literal - which is
    # exactly why these are pinned rather than pattern-matched.
    (12, 'Ch - sous_chaine(', f"Ch {ARROW} sous_chaine(", 1),
    (12, 'Ch - Effacer(', f"Ch {ARROW} Effacer(", 1),
    (12, 'Ch1 - Convch (', f"Ch1 {ARROW} Convch (", 1),
    (12, 'CH2 - Convch(', f"CH2 {ARROW} Convch(", 1),
    (12, 'B - Estnum(', f"B {ARROW} Estnum(", 1),
    (12, 'X1 - valeur(', f"X1 {ARROW} valeur(", 1),
    (12, 'X2 - valeur(', f"X2 {ARROW} valeur(", 1),
    (12, 'X3 - valeur(', f"X3 {ARROW} valeur(", 1),
]


def apply(chunks_path: Path) -> int:
    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    applied = 0
    failures: list[str] = []

    for page, old, new, expected in PATCHES:
        targets = [c for c in chunks if c.get("page") == page and old in c.get("content", "")]

        if not targets:
            already = [
                c for c in chunks if c.get("page") == page and new in c.get("content", "")
            ]
            if already:
                print(f"  page {page}: already patched, skipping")
                continue
            failures.append(
                f"page {page}: target not found and not already patched:\n    {old!r}"
            )
            continue

        if len(targets) != expected:
            failures.append(
                f"page {page}: expected {expected} chunk(s) containing the target, "
                f"found {len(targets)} - re-check the extraction by eye"
            )
            continue

        for chunk in targets:
            count = chunk["content"].count(old)
            chunk["content"] = chunk["content"].replace(old, new)
            applied += count
            print(f"  page {page} [{chunk.get('section')}]: restored {count} arrow(s)")

    if failures:
        print("\nPATCH FAILED:", file=sys.stderr)
        for failure in failures:
            print("  " + failure, file=sys.stderr)
        raise SystemExit(1)

    if applied:
        chunks_path.write_text(
            json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return applied


# Shapes the corrupted arrow is known to take. The glyph degrades differently
# depending on what sits next to it, so each spacing variant needs its own
# pattern - `X - int(...)`, `X-Alea`, `X - 474` are all the same bug.
#
# THIS CHECK HAS A CEILING. It only catches shapes it has been told about, and
# page 11's collapsed form went unnoticed for two passes precisely because it
# did not leave an isolated " - ". Treat a clean run as necessary, not
# sufficient: a manual skim of every declaration- or affectation-heavy page is
# a required step when a new chapter is extracted.
SUSPECT_PATTERNS = [
    # "X - expr" / "X -expr" / "X- expr" / "X-expr", where X is an identifier
    # and the surrounding line has no comparison or result marker.
    re.compile(r"(?<![\w.])([A-Za-z_]\w{0,20})\s*-\s*(?=[A-Za-z_(\d\"'])"),
]

# Tokens that mean the line is arithmetic or a stated result, not an assignment.
SUBTRACTION_MARKERS = ("=", "donne", "vaut ", "<", ">", "≤", "≥", "≠")


def verify(chunks_path: Path) -> None:
    """Standing visual check: report every surviving arrow and every line shaped
    like a corrupted one, so a human can eyeball them against the PDF.

    This only reports. It never edits - deciding whether a given `-` is an
    assignment or a subtraction needs the PDF in front of you.
    """
    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    arrows = 0
    suspects: list[tuple[int, str, str]] = []

    for chunk in chunks:
        content = chunk.get("content", "")
        arrows += content.count(ARROW)
        for line in content.splitlines():
            for cell in line.split("|"):
                stripped = cell.strip()
                if not stripped or ARROW in stripped:
                    continue
                match = None
                for pattern in SUSPECT_PATTERNS:
                    match = pattern.search(stripped)
                    if match:
                        break
                if not match:
                    continue
                lhs = match.group(1)
                if lhs[0].isdigit():
                    continue
                # A cell that also states a result ("X vaut 9") is still worth
                # showing - that is exactly the page 11 shape - so only skip
                # when the marker sits before the candidate arrow.
                head = stripped[: match.start()]
                if any(tok in head for tok in SUBTRACTION_MARKERS):
                    continue
                suspects.append(
                    (chunk.get("page", 0), chunk.get("section", "?"), stripped)
                )

    print(f"\nVisual check: {arrows} '{ARROW}' present in chunks.json")
    if suspects:
        print(f"{len(suspects)} line(s) shaped like a corrupted assignment - eyeball these:")
        for page, section, line in suspects:
            print(f"  p{page} [{section}] {line[:110]}")
    else:
        print("No lines matching the corrupted-assignment shape.")
    print(
        "\nReminder: this check only catches known shapes. Skim any "
        "declaration/affectation-heavy page by hand before trusting a clean run."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply pinned manual fixes to chunks.json")
    parser.add_argument("--chunks", type=Path, default=Path("chunks.json"))
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    if not args.verify_only:
        print(f"Patching {args.chunks} ...")
        applied = apply(args.chunks)
        print(f"Applied {applied} replacement(s).")
    verify(args.chunks)


if __name__ == "__main__":
    main()
