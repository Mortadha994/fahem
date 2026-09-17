"""Checking a student's own solution: the part that needs no model.

"Vérifier ma réponse" sends the student's algorithm (and often its Python) to
the CHECK prompt. Before that, this module reads the algorithm lines itself and
lists the notation mistakes it can prove - a Python operator in an algorithm
line (`Res ← X // Y`), `=` used to assign, `Lire (x ← entier)`, no declaration
table. Those findings go to the model as facts it must report (so a correction
can never miss the mistake that costs the student points), and their kinds are
kept with the answer for the admin console's most common mistakes.

It also recognizes a message that asks for a check without the button ("voici
ma solution, est-ce que c'est juste ?") and reads the verdict line the CHECK
prompt starts its answer with.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass

# Python operator in an algorithm line -> what the course writes.
_OPERATORS: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"//"), "//", "div"),
    (re.compile(r"%"), "%", "mod"),
    (re.compile(r"=="), "==", "="),
    (re.compile(r"!="), "!=", "≠"),
    (re.compile(r"<="), "<=", "≤"),
    (re.compile(r">="), ">=", "≥"),
    (re.compile(r"<-"), "<-", "←"),
    (re.compile(r"\band\b"), "and", "ET"),
    (re.compile(r"\bor\b"), "or", "OU"),
    (re.compile(r"\bnot\b"), "not", "NON"),
    (re.compile(r"\bTrue\b"), "True", "Vrai"),
    (re.compile(r"\bFalse\b"), "False", "Faux"),
]

# A line of algorithm (not of Python): an assignment arrow, or a course keyword.
_ALGO_KEYWORD = re.compile(
    r"^\s*(?:\d+[.)]\s*)?(lire|ecrire|écrire|début|debut|fin|algorithme|si|sinon|"
    r"fin\s*si|pour|tant\s*que|répéter|repeter|jusqu'à)\b",
    re.IGNORECASE,
)
_PYTHON_HINT = re.compile(r"\b(input|print|int|float|str|len|range)\s*\(|^\s*(if|for|while|def)\b")
# `x = expr` at the start of an algorithm-looking line: assignment written with =.
_EQ_ASSIGN = re.compile(r"^\s*(?:\d+[.)]\s*)?([A-Za-z_][\w]*)\s*=\s*[^=]")
_LIRE_TYPED = re.compile(r"\blire\s*\(?\s*\w+\s*(←|<-|:)\s*\w+", re.IGNORECASE)
_DECLARATION = re.compile(
    r"objet|nature\s*/?\s*type|\b(entier|réel|reel|booléen|booleen|chaîne|chaine)\b",
    re.IGNORECASE,
)
_QUOTED = re.compile(r'"[^"]*"?|«[^»]*»?')

# Asking for a check in words, and something that looks like the student's work.
_ASKS_CHECK = re.compile(
    r"ma (solution|réponse|reponse|proposition|correction|version|tentative)|"
    r"mon (algorithme|algo|programme|code|travail)|"
    r"(est[- ]ce que|c'est|est[- ]il) (c'est )?(juste|correct|bon|bien|faux)|"
    r"\b(vérifie|verifie|vérifier|verifier|corrige|corriger)\b|j'ai (écrit|ecrit|fait|essayé)",
    re.IGNORECASE,
)
_WORK_MARKER = re.compile(
    r"←|<-|\blire\s*\(|\becrire\s*\(|\bécrire\s*\(|input\s*\(|print\s*\(", re.I
)

VERDICTS = ("correct", "presque", "a_revoir")
_VERDICT_LINE = re.compile(r"verdict\s*[:：]\s*\**\s*([^\n*|]+)", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    kind: str  # operator | assignment | lire | declaration
    line: str  # the student's line, as written (trimmed)
    found: str  # what is wrong in it
    expected: str  # what the course writes

    def as_dict(self) -> dict:
        return asdict(self)


def _fold(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn"
    )


def _is_algo_line(line: str) -> bool:
    if _PYTHON_HINT.search(line):
        return False
    return "←" in line or "<-" in line or bool(_ALGO_KEYWORD.match(line))


def _table_algo_cells(text: str) -> list[str]:
    """The Algorithme column of a pasted `Algorithme | Python` table, if any."""
    cells: list[str] = []
    index: int | None = None
    for raw in text.split("\n"):
        row = raw.strip()
        if not row.startswith("|"):
            index = None
            continue
        parts = [c.strip() for c in row.strip("|").split("|")]
        lowered = [p.lower() for p in parts]
        if "algorithme" in lowered and "python" in lowered:
            index = lowered.index("algorithme")
            continue
        if (
            index is not None
            and index < len(parts)
            and not re.fullmatch(r":?-{2,}:?", parts[index])
        ):
            cells.append(parts[index])
    return cells


def algorithm_lines(text: str) -> list[str]:
    """The student's algorithm lines: a table's Algorithme column, or the lines
    of plain text that read as algorithm rather than Python."""
    cells = _table_algo_cells(text)
    if cells:
        return [c for c in cells if c]
    lines: list[str] = []
    in_block = False  # between Début and Fin, `b = a * 2` is algorithm too
    for raw in text.split("\n"):
        line = raw.strip().strip("`")
        if not line:
            continue
        head = _fold(line)
        if re.match(r"^(\d+[.)]\s*)?debut\b", head):
            in_block = True
        if _is_algo_line(line) or (in_block and not _PYTHON_HINT.search(line)):
            lines.append(line)
        if re.match(r"^(\d+[.)]\s*)?fin\b", head) and not head.startswith("fin si"):
            in_block = False
    return lines


def precheck(text: str) -> list[Finding]:
    """Notation mistakes that can be proven without understanding the program."""
    findings: list[Finding] = []
    seen: set[tuple[str, str, str]] = set()

    def add(f: Finding) -> None:
        key = (f.kind, f.line, f.found)
        if key not in seen and len(findings) < 20:
            seen.add(key)
            findings.append(f)

    lines = algorithm_lines(text)
    table = bool(_table_algo_cells(text))
    for line in lines:
        code = _QUOTED.sub('""', line)  # "Remise de 5 %" is a message, not an operator
        for pattern, found, expected in _OPERATORS:
            if pattern.search(code):
                add(Finding("operator", line[:160], found, expected))
        if "←" not in code and "<-" not in code and not _ALGO_KEYWORD.match(code):
            match = _EQ_ASSIGN.match(code)
            if match and (table or not _PYTHON_HINT.search(code)):
                add(Finding("assignment", line[:160], "=", "←"))
        if _LIRE_TYPED.search(code):
            add(Finding("lire", line[:160], "type dans Lire", "Lire (variable)"))
    if lines and not _DECLARATION.search(text):
        add(Finding("declaration", "", "pas de tableau de déclaration", "Objet | Nature/type"))
    return findings


def findings_block(findings: list[Finding]) -> str:
    """The findings as the CHECK prompt reads them."""
    if not findings:
        return (
            "VÉRIFICATION AUTOMATIQUE DE LA NOTATION : aucune erreur de notation détectée "
            "automatiquement (vérifie quand même la logique)."
        )
    rows = []
    for f in findings:
        if f.kind == "declaration":
            rows.append("- Il manque le tableau de déclaration (Objet | Nature/type).")
        elif f.kind == "lire":
            rows.append(f"- `{f.line}` : Lire ne prend pas de type, écrire Lire (variable).")
        else:
            rows.append(f"- `{f.line}` : `{f.found}` doit s'écrire `{f.expected}` en algorithme.")
    return (
        "VÉRIFICATION AUTOMATIQUE DE LA NOTATION (erreurs certaines, à signaler toutes "
        "dans ta correction) :\n" + "\n".join(rows)
    )


def looks_like_check(text: str) -> bool:
    """A message asking to check the student's own work, typed without the button."""
    return bool(_ASKS_CHECK.search(text)) and bool(_WORK_MARKER.search(text))


def parse_verdict(answer: str) -> str | None:
    """ "correct" | "presque" | "a_revoir" from the answer's "Verdict :" line."""
    match = _VERDICT_LINE.search(answer[:600])
    if not match:
        return None
    word = _fold(match.group(1))
    if "presque" in word:
        return "presque"
    if "revoir" in word or "incorrect" in word or "faux" in word:
        return "a_revoir"
    if "correct" in word or "juste" in word:
        return "correct"
    return None
