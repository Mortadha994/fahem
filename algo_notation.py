"""Tunisian algorithm notation in the Algorithme column, whatever the model wrote.

The course writes `Q ← A div B`, `R ← A mod B`, `≠`, `≤`, `≥`, `ET`, `OU`,
`NON`, `Vrai`, `Faux`. Python writes `//`, `%`, `!=`, `<=`, `>=`, `and`, `or`,
`not`, `True`, `False`. The model knows both and sometimes lets a Python
operator slip into the Algorithme column (`Res ← X // Y`), which a student
copies into their exercise book and is marked wrong for - the one mistake
that most damages their trust in the tutor.

The prompts forbid it (prompts.py, rule 1); this module is the safety net for
when the model does it anyway. It rewrites the operators ONLY:

  - in the Algorithme column of an `Algorithme | Python` table (the Python
    column, the explanations and the student's own quoted lines are left
    alone - in a CODE answer, citing the student's `//` is the point);
  - outside double-quoted strings, so `Ecrire ("Remise de 5 %")` keeps its %.

The same rewrite runs in the browser (ui/src/lib/algoNotation.js) for the
streamed answer and for saved discussions; here it runs before the syntax
checker, so a line the student will see corrected is not reported as a
violation, and each correction is logged so the model's slips stay visible.
"""

from __future__ import annotations

import re

# Longest operators first: `<=` before `<-`, `//` before anything with `/`.
_OPERATORS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\s*//\s*"), " div "),
    (re.compile(r"\s*%\s*"), " mod "),
    (re.compile(r"\s*==\s*"), " = "),
    (re.compile(r"\s*!=\s*"), " ≠ "),
    (re.compile(r"\s*<=\s*"), " ≤ "),
    (re.compile(r"\s*>=\s*"), " ≥ "),
    (re.compile(r"\s*<-\s*"), " ← "),
    (re.compile(r"\band\b"), "ET"),
    (re.compile(r"\bor\b"), "OU"),
    (re.compile(r"\bnot\b"), "NON"),
    (re.compile(r"\bTrue\b"), "Vrai"),
    (re.compile(r"\bFalse\b"), "Faux"),
]
_INNER_SPACES = re.compile(r"(?<=\S) {2,}(?=\S)")


def _fix_code(segment: str) -> tuple[str, int]:
    count = 0
    for pattern, replacement in _OPERATORS:
        segment, n = pattern.subn(replacement, segment)
        count += n
    if count:
        leading = segment[: len(segment) - len(segment.lstrip(" "))]
        body = _INNER_SPACES.sub(" ", segment[len(leading) :])
        segment = leading + body
    return segment, count


def to_algo_notation(line: str) -> tuple[str, int]:
    """One Algorithme line in course notation, and how many operators changed.
    Text inside double quotes is copied as it is."""
    out: list[str] = []
    count = 0
    # Alternating code / "string" pieces; an unclosed quote runs to the end.
    for piece in re.split(r'("[^"]*"?)', line):
        if piece.startswith('"'):
            out.append(piece)
        else:
            fixed, n = _fix_code(piece)
            out.append(fixed)
            count += n
    # A rewrite next to a string can leave "div  (" or trailing spaces.
    result = "".join(out)
    return (result.rstrip() if count else result), count


def _cells(row: str) -> list[str]:
    inner = row.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    return inner.split("|")


def normalize_answer(markdown: str) -> tuple[str, int]:
    """The answer with every `Algorithme | Python` table's Algorithme column in
    course notation. Returns (text, number of operators rewritten)."""
    lines = markdown.split("\n")
    total = 0
    algo_index: int | None = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("|"):
            algo_index = None  # the table ended
            continue
        cells = _cells(stripped)
        headers = [c.strip().lower() for c in cells]
        if "algorithme" in headers and "python" in headers:
            algo_index = headers.index("algorithme")
            continue
        if algo_index is None or algo_index >= len(cells):
            continue
        if re.fullmatch(r"\s*:?-{2,}:?\s*", cells[algo_index]):
            continue  # the |---|---| separator
        fixed, n = to_algo_notation(cells[algo_index])
        if n:
            original = cells[algo_index]
            pad_left = original[: len(original) - len(original.lstrip())] or " "
            cells[algo_index] = f"{pad_left}{fixed.strip()} "
            indent = line[: len(line) - len(line.lstrip())]
            lines[i] = f"{indent}|{'|'.join(cells)}|"
            total += n
    return "\n".join(lines), total
