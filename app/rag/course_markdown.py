"""Read a course written to Fahem's Markdown template into chunks (Phase 9b).

Why this exists next to scripts/extract_chapter.py: a PDF is a picture of a page, and
extracting it is guesswork - chapter 1 lost its assignment arrow, chapter 2
had its Algorithme and Python columns merged line by line. A course written to
docs/modele-cours.md states its structure explicitly, so reading it involves
no guessing at all:

    ---                         header: niveau, chapitre, titre, notions
    ## II. Section              a section (one chunk, or several if long)
    ### 📌 1. Simple choix      a subsection; 📌 = pinned reference syntax
    ```algorithme / ```python   code, never split across chunks
    ## Série d'exercices        everything below is the série
    ### Exercice 1              one exercise: title + énoncé

Structural mistakes are refused with line numbers (ParseError) rather than
imported half-right - an unclosed code block or an untagged one would put
wrong syntax in front of the model, which is the exact failure this format
exists to prevent. Content mistakes (a "<-" instead of "←") are left to the
console's review flags, like any other chunk.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

PIN = "📌"
MAX_CHUNK_CHARS = 1800
CODE_LANGS = {"algorithme", "algo", "python"}
REQUIRED_META = ("chapitre", "titre", "notions")

_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_FENCE = re.compile(r"^(\s*)(```+|~~~+)\s*([\w-]*)")
_SERIE = re.compile(r"^s[ée]rie\b", re.IGNORECASE)
_EXERCICE = re.compile(r"^exercice\s*(?:n\s*°\s*)?(\d+)\b", re.IGNORECASE)
_NUMBERING = re.compile(r"^(?:[IVXLC]+\.|\d+[.)])\s*")
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


class ParseError(ValueError):
    """The file does not follow the template. `problems` lists every issue."""

    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


@dataclass
class ParsedCourse:
    niveau: str
    chapitre: str
    titre: str
    notions: str
    chunks: list[dict] = field(default_factory=list)
    exercises: list[dict] = field(default_factory=list)


def _front_matter(lines: list[str], problems: list[str]) -> tuple[dict, int]:
    if not lines or lines[0].strip() != "---":
        problems.append(
            "Ligne 1 : l'en-tête est absent. Le fichier doit commencer par '---', "
            "puis niveau / chapitre / titre / notions, puis '---'."
        )
        return {}, 0
    meta: dict[str, str] = {}
    for i in range(1, len(lines)):
        line = lines[i].strip()
        if line == "---":
            missing = [k for k in REQUIRED_META if not meta.get(k)]
            if missing:
                problems.append(f"En-tête : champ(s) manquant(s) : {', '.join(missing)}.")
            return meta, i + 1
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            problems.append(f"Ligne {i + 1} : l'en-tête attend 'clé: valeur', trouvé {line!r}.")
            continue
        meta[key.strip().lower()] = value.strip().strip('"').strip("'")
    problems.append("En-tête : le '---' de fermeture est absent.")
    return meta, len(lines)


def _clean_label(title: str) -> str:
    title = title.replace(PIN, "").strip()
    title = _NUMBERING.sub("", title).strip()
    return title.rstrip(" :").strip() or "Référence"


def _blocks(body: list[tuple[int, str]], problems: list[str]) -> list[str]:
    """Group body lines into unsplittable blocks: a whole code fence, or a
    paragraph. Chunks are only ever cut between blocks."""
    blocks: list[str] = []
    current: list[str] = []
    i = 0
    while i < len(body):
        lineno, line = body[i]
        m = _FENCE.match(line)
        if m:
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            marker, lang = m.group(2), m.group(3).lower()
            if lang not in CODE_LANGS:
                problems.append(
                    f"Ligne {lineno} : bloc de code sans langage. Écris ```algorithme "
                    f"ou ```python" + (f" (trouvé {lang!r})" if lang else "") + "."
                )
            fence = [line]
            i += 1
            closed = False
            while i < len(body):
                fence.append(body[i][1])
                if body[i][1].strip().startswith(marker[:3]) and body[i][1].strip().strip(marker[0]) == "":
                    closed = True
                    break
                i += 1
            if not closed:
                problems.append(f"Ligne {lineno} : bloc de code jamais fermé (``` manquant).")
            blocks.append("\n".join(fence))
            i += 1
            continue
        if not line.strip():
            if current:
                blocks.append("\n".join(current).strip())
                current = []
        else:
            current.append(line)
        i += 1
    if current:
        blocks.append("\n".join(current).strip())
    return [b for b in blocks if b.strip()]


def _pack(heading: str, blocks: list[str]) -> list[str]:
    """Pack blocks into chunks under MAX_CHUNK_CHARS, repeating the heading so
    every chunk says what it is about. A single oversized block stays whole."""
    chunks: list[str] = []
    current = [heading]
    size = len(heading)
    for block in blocks:
        if size + len(block) > MAX_CHUNK_CHARS and len(current) > 1:
            chunks.append("\n\n".join(current))
            current = [f"{heading} (suite)"]
            size = len(current[0])
        current.append(block)
        size += len(block) + 2
    if len(current) > 1 or not chunks:
        chunks.append("\n\n".join(current))
    return chunks


def parse(text: str, expected_chapitre: str | None = None) -> ParsedCourse:
    text = text.replace("\r\n", "\n").lstrip("﻿")
    # HTML comments are notes for the author (the template's instructions live
    # in one) and must never become course text. Each is replaced by as many
    # newlines as it spanned, so every problem still reports the right line.
    text = _COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    lines = text.split("\n")
    problems: list[str] = []
    meta, start = _front_matter(lines, problems)

    chapitre = str(meta.get("chapitre", "")).strip()
    if expected_chapitre is not None and chapitre and chapitre != str(expected_chapitre):
        problems.append(
            f"En-tête : chapitre {chapitre!r}, mais le fichier est envoyé comme chapitre "
            f"{expected_chapitre!r}."
        )

    # Split the body into sections at ## and ### headings. A lone # (the
    # chapter title) opens nothing: the title lives in the header.
    sections: list[dict] = []
    current: dict | None = None
    in_fence = None
    for idx in range(start, len(lines)):
        line = lines[idx]
        fm = _FENCE.match(line)
        if fm:
            in_fence = None if in_fence else fm.group(2)[:3]
        hm = None if in_fence else _HEADING.match(line)
        if hm and len(hm.group(1)) in (2, 3):
            current = {"level": len(hm.group(1)), "title": hm.group(2), "line": idx + 1, "body": []}
            sections.append(current)
            continue
        if hm and len(hm.group(1)) == 1:
            # "# Série d'exercices" is accepted at the top level too.
            if _SERIE.match(hm.group(2).replace(PIN, "").strip()):
                current = {"level": 2, "title": hm.group(2), "line": idx + 1, "body": []}
                sections.append(current)
            continue
        if current is None:
            if line.strip():
                current = {"level": 2, "title": "Introduction", "line": idx + 1, "body": []}
                sections.append(current)
            else:
                continue
        current["body"].append((idx + 1, line))

    course = ParsedCourse(
        niveau=(meta.get("niveau") or "2eme").strip().lower(),
        chapitre=chapitre,
        titre=meta.get("titre", "").strip(),
        notions=meta.get("notions", "").strip(),
    )

    in_serie = False
    parent = ""
    for sec in sections:
        title = sec["title"].strip()
        plain = title.replace(PIN, "").strip()
        # Inside the série, "## Exercice N" and "### Exercice N" are both
        # exercises; any other ## heading ends the série.
        if sec["level"] == 2 and not (in_serie and _EXERCICE.match(plain)):
            in_serie = bool(_SERIE.match(plain))
            parent = plain
            if in_serie:
                continue
        blocks = _blocks(sec["body"], problems)

        if in_serie:
            m = _EXERCICE.match(plain)
            if not m:
                problems.append(
                    f"Ligne {sec['line']} : dans la série, chaque titre doit être "
                    f"'### Exercice N' (trouvé {title!r})."
                )
                continue
            question = "\n\n".join(blocks).strip()
            if not question:
                problems.append(f"Ligne {sec['line']} : {plain} n'a pas d'énoncé.")
                continue
            n = int(m.group(1))
            course.exercises.append({"title": f"Exercice {n}", "question": question})
            course.chunks.append(
                {
                    "content": f"Exercice N°{n} :\n{question}",
                    "section": f"Exercice {n}",
                    "type": "exercice",
                    "format": "markdown",
                    "pinned": False,
                    "pin_label": None,
                }
            )
            continue

        if not blocks:
            continue  # a ## that only introduces ### subsections
        pinned = PIN in title
        section = plain if sec["level"] == 2 else f"{parent} — {plain}"
        heading = f"{'#' * sec['level']} {plain}"
        has_code = any(_FENCE.match(b) for b in blocks)
        # A pinned reference sheet is never split: it is included whole in
        # every prompt, and half a syntax table is worse than none.
        pieces = ["\n\n".join([heading, *blocks])] if pinned else _pack(heading, blocks)
        for piece in pieces:
            course.chunks.append(
                {
                    "content": piece,
                    "section": section,
                    "type": "table" if (pinned or has_code) else "prose",
                    "format": "markdown",
                    "pinned": pinned,
                    "pin_label": _clean_label(title) if pinned else None,
                }
            )

    if not any(c["type"] != "exercice" for c in course.chunks):
        problems.append("Aucun contenu de cours trouvé (sections ## / ### avec du texte).")
    if not any(c["pinned"] for c in course.chunks):
        problems.append(
            "Aucune section marquée 📌. Marque les sections de syntaxe de référence, "
            "par exemple '### 📌 1. Simple choix'."
        )
    if problems:
        raise ParseError(problems)
    return course
