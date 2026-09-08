"""Extract a chapter PDF into tagged chunks for the RAG pipeline.

Written to unblock the retrieval test - the original extract_chapter.py was
not present in this directory. Chunking rules, in priority order:

1. Tables are extracted first, as whole chunks (type="table"). The chapter's
   syntax references are two-column "Algorithme | Python" tables and operator
   tables; plain text extraction interleaves their columns into nonsense, so
   they must be pulled out via pdfplumber's table finder and rendered
   row-by-row.
2. Prose is whatever is left on the page once table regions are masked out.
3. Prose is grouped under the nearest preceding heading - roman-numeral
   sections (I., II., ...) in the cours, "Exercice N°n" in the serie.
4. A pseudocode block (Algorithme ... Fin) is never split across chunks.

Output: chunks.json, a list of
  {"content", "niveau", "chapitre", "section", "type", "page", "source"}
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import pdfplumber

# "I. Notion :"  /  "III. Les types standards :"
SECTION_RE = re.compile(r"^\s*([IVX]{1,5})\.\s*(.{2,80}?)\s*:?\s*$")
# "Exercice N°16 :" / "Exercice N° 8 :"
EXERCICE_RE = re.compile(r"^\s*Exercice\s*N°\s*(\d+)\s*:?\s*$", re.IGNORECASE)
EXERCICE_INLINE_RE = re.compile(r"^\s*Exercice\s*N°\s*(\d+)\s*:?\s*(.*)$", re.IGNORECASE)
SERIE_RE = re.compile(r"S[ée]rie\s+d['’]exercice", re.IGNORECASE)

# A pseudocode block runs from an "Algorithme <name>" line to its "Fin".
PSEUDO_START_RE = re.compile(r"^\s*(Algorithme|Début|Debut)\b", re.IGNORECASE)
PSEUDO_END_RE = re.compile(r"^\s*Fin\s*$", re.IGNORECASE)

# Structural sub-boundaries the document already uses inside a section. Prose is
# split on these rather than on a character count: a flat cap slices a chunk
# mid-example, while these markers are where the author changed topic anyway.
#
# "a) Définition :" / "b) Caractéristiques :" / "c) Déclarations :"
SUBPOINT_LETTER_RE = re.compile(r"^\s*[a-z]\)\s+\S")
# "2. Le type Réel : (float)" / "1. L'opération d'entrée :" - a numbered line is
# only a heading when it carries a colon. "1. La lecture de deux entiers" is a
# list item inside a worked example and must NOT start a new chunk.
SUBPOINT_NUMBER_RE = re.compile(r"^\s*\d{1,2}\.\s+\S.*:")
# "Exemple :", "Remarque :", "Activité :", "Solution :", "Application :", "N.B :"
MARKER_RE = re.compile(
    r"^\s*(Exemples?|Remarques?|Activit[ée]|Solution|Application|N\.?\s?B)\s*:",
    re.IGNORECASE,
)

MAX_CHARS = 1200  # backstop only, for a run with no internal boundary
MIN_CHARS = 60  # drop fragments shorter than this


def clean(text: str) -> str:
    """Normalise the mojibake pdfplumber leaves behind.

    The PDF uses Wingdings bullets (U+F0A7 etc.) in the private use area and
    non-breaking spaces; both confuse the embedding model and are worthless as
    signal, so they are flattened.
    """
    out = []
    for ch in text:
        if "" <= ch <= "":  # private use area (Wingdings bullets)
            out.append("-")
        elif ch in "   ":
            out.append(" ")
        else:
            out.append(ch)
    text = unicodedata.normalize("NFC", "".join(out))
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_page_number(line: str) -> bool:
    return bool(re.fullmatch(r"\s*\d{1,3}\s*", line))


def render_table(table: list[list[str | None]]) -> str:
    """Render an extracted table as pipe-separated rows.

    Kept as text rather than markdown pipes-with-alignment: the point is that
    the Algorithme column and the Python column stay on the same row and in the
    right order, which is what a downstream model needs to read the syntax off.
    """
    rows = []
    for row in table:
        cells = [clean(c or "").replace("\n", " ") for c in row]
        if not any(cells):
            continue
        rows.append(" | ".join(cells))
    return "\n".join(rows)


def table_is_real(text: str, n_rows: int, n_cols: int) -> bool:
    """pdfplumber's line-based finder picks up page borders and single cells
    that are really just prose in a box. Require some actual grid."""
    if n_cols < 2 or n_rows < 2:
        return False
    return len(text) >= 40


def is_boundary(line: str) -> bool:
    """True when a line starts a new sub-topic within its section."""
    return bool(
        SUBPOINT_LETTER_RE.match(line) or SUBPOINT_NUMBER_RE.match(line) or MARKER_RE.match(line)
    )


def split_pseudocode_aware(lines: list[str], max_chars: int = MAX_CHARS) -> list[str]:
    """Split a run of lines at the document's own sub-boundaries.

    A section like "III. Les types standards" runs to several thousand
    characters and covers definition, characteristics, examples and remarks. As
    one chunk it matches short queries on generic vocabulary rather than on the
    operation actually being asked about, so each sub-point becomes its own
    chunk - same section metadata, narrower topic, still semantically whole.

    A pseudocode block (Algorithme ... Fin) is never cut, and max_chars stays
    only as a backstop for a run that contains no boundary at all.
    """
    blocks: list[list[str]] = []
    current: list[str] = []
    in_pseudo = False

    for line in lines:
        if not in_pseudo and PSEUDO_START_RE.match(line):
            in_pseudo = True

        # Start a new block at a structural boundary, but never inside
        # pseudocode - "1. ..." lines occur inside worked examples too.
        if not in_pseudo and current and is_boundary(line):
            blocks.append(current)
            current = []

        current.append(line)

        if in_pseudo and PSEUDO_END_RE.match(line):
            in_pseudo = False
            blocks.append(current)
            current = []
            continue

        # Backstop: a boundary-free run that has grown past the cap.
        if not in_pseudo and sum(len(x) + 1 for x in current) >= max_chars:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)

    # Fold a block that is too small to stand alone back into its predecessor,
    # so a bare "Exemple :" line does not become its own chunk.
    merged: list[list[str]] = []
    for block in blocks:
        size = sum(len(x) + 1 for x in block)
        if merged and size < MIN_CHARS:
            merged[-1].extend(block)
        else:
            merged.append(list(block))

    return [text for text in ("\n".join(b).strip() for b in merged) if text]


def extract(pdf_path: Path, niveau: str, chapitre: str) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    source = pdf_path.name
    section = "Introduction"
    in_serie = False

    def add(content: str, ctype: str, page: int, section_name: str, fmt: str) -> None:
        content = clean(content)
        if len(content) < MIN_CHARS and fmt != "table":
            return
        chunks.append(
            {
                "content": content,
                "niveau": niveau,
                "chapitre": chapitre,
                "section": section_name,
                # `type` is the semantic role, decided by which section the
                # content sits in - it is what retrieval filters on.
                "type": ctype,
                # `format` is how it was laid out on the page. Kept separate so
                # that a worksheet grid inside the serie is tagged `exercice`
                # (and stays out of solve-mode retrieval) without losing the
                # fact that it is a table.
                "format": fmt,
                "page": page,
                "source": source,
            }
        )

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            # --- find the real tables and remember where they sit -------------
            table_boxes = []
            table_items: list[tuple[float, str]] = []
            for table in page.find_tables():
                data = table.extract()
                if not data:
                    continue
                text = render_table(data)
                n_cols = max((len(r) for r in data), default=0)
                if table_is_real(text, len(data), n_cols):
                    table_items.append((table.bbox[1], text))
                    table_boxes.append(table.bbox)
                # Not a real grid: leave the region to the prose pass so we do
                # not silently lose the text inside it.

            # --- prose: the page with table regions masked out ----------------
            def outside_tables(obj: dict) -> bool:
                if obj.get("object_type") not in ("char", "line", "rect", "curve"):
                    return True
                cx = (obj["x0"] + obj["x1"]) / 2
                cy = (obj["top"] + obj["bottom"]) / 2
                for x0, top, x1, bottom in table_boxes:
                    if x0 <= cx <= x1 and top <= cy <= bottom:
                        return False
                return True

            filtered = page.filter(outside_tables) if table_boxes else page

            # Walk the page in reading order so a table is tagged with the
            # heading that precedes it on the page, not the one left over from
            # the previous page.
            items: list[tuple[float, str, str]] = [
                (line["top"], "line", line["text"]) for line in filtered.extract_text_lines()
            ]
            items += [(top, "table", text) for top, text in table_items]
            items.sort(key=lambda it: it[0])

            buffer: list[str] = []

            def flush(sec: str) -> None:
                if not buffer:
                    return
                for piece in split_pseudocode_aware(buffer):
                    add(piece, "exercice" if in_serie else "prose", page_index, sec, "text")
                buffer.clear()

            for _top, kind, payload in items:
                if kind == "table":
                    flush(section)
                    # Tag by section context, not by rendering: a table drawn
                    # inside the serie is an exercise worksheet (often a blank
                    # answer grid), not chapter syntax reference.
                    add(
                        payload,
                        "exercice" if in_serie else "table",
                        page_index,
                        section,
                        "table",
                    )
                    continue

                line = clean(payload)
                if not line or is_page_number(line):
                    continue

                if SERIE_RE.search(line):
                    flush(section)
                    in_serie = True
                    section = "Serie d'exercices"
                    continue

                m_ex = EXERCICE_RE.match(line) or EXERCICE_INLINE_RE.match(line)
                if m_ex and in_serie:
                    flush(section)
                    section = f"Exercice {int(m_ex.group(1))}"
                    trailing = (
                        m_ex.group(2).strip() if m_ex.lastindex and m_ex.lastindex > 1 else ""
                    )
                    buffer.append(f"Exercice N°{int(m_ex.group(1))} :")
                    if trailing:
                        buffer.append(trailing)
                    continue

                m_sec = SECTION_RE.match(line)
                if m_sec and not in_serie:
                    flush(section)
                    section = f"{m_sec.group(1)}. {m_sec.group(2)}"
                    buffer.append(line)
                    continue

                buffer.append(line)

            flush(section)

    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract a chapter PDF into chunks.json")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--niveau", required=True)
    parser.add_argument("--chapitre", required=True)
    parser.add_argument("--out", type=Path, default=Path("chunks.json"))
    args = parser.parse_args()

    chunks = extract(args.pdf, args.niveau.strip().lower(), args.chapitre.strip().lower())
    args.out.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")

    by_type: dict[str, int] = {}
    for chunk in chunks:
        by_type[chunk["type"]] = by_type.get(chunk["type"], 0) + 1
    print(f"Wrote {len(chunks)} chunk(s) to {args.out}")
    for ctype, n in sorted(by_type.items()):
        print(f"  {ctype}: {n}")


if __name__ == "__main__":
    main()
