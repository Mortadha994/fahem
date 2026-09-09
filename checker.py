"""Mechanical constraint checker for generated answers.

Extracted verbatim from generate.py, which was doing three unrelated jobs
(HTTP clients, this checker, and a CLI). Nothing about the rules changed in
the move - same patterns, same thresholds, same comments explaining why each
one exists. generate.py now imports check_constraints from here.

The checker is deliberately conservative and mechanical: `warnings` coming
back empty means no known pattern matched, not that the answer is correct.
"""

from __future__ import annotations

import re

# Control-structure constructs. Rule 2 does not forbid these outright - it
# forbids inventing them when the context does not supply their syntax. So a
# hit is a violation only if the same construct is absent from the context;
# once a control-structures chapter is ingested, these stop being violations
# on their own. Word-boundary matched so "Pour utiliser..." in prose does not
# trip the check.
# Start of a line, a markdown table cell, or a bold/`code` run - the places a
# code keyword can legitimately begin in the model's answer format.
_CELL = r"(?:^|\||\*\*|`|&nbsp;)\s*"

CONTROL_STRUCTURES = {
    "Si...Alors": re.compile(r"\bsi\b[^.\n]{0,60}\balors\b", re.IGNORECASE),
    "Tant que": re.compile(r"\btant\s+que\b", re.IGNORECASE),
    "Répéter": re.compile(r"\br[ée]p[ée]ter\b", re.IGNORECASE),
    "Pour...De...A": re.compile(r"\bpour\b\s+\w+\s+(de|allant)\b", re.IGNORECASE),
    # Anchored to a "cell start" rather than a line start: the model answers in
    # markdown tables, so Python lands mid-line after "| " and "**" and a
    # plain ^-anchored pattern silently misses it (it did - ex27's `def main():`
    # inside a table cell passed as clean).
    "python if": re.compile(rf"{_CELL}(if|elif|else)\b"),
    "python loop": re.compile(rf"{_CELL}(for|while)\b"),
    "def": re.compile(rf"{_CELL}def\s+\w"),
    # Named explicitly by rule 2, so checked explicitly. `return` outside a
    # function is a syntax error anyway, and the __main__ guard is a function
    # definition idiom regardless of intent.
    "return": re.compile(rf"{_CELL}return\b"),
    # The backslash is optional: markdown answers escape the quotes as \"...\".
    "__main__ guard": re.compile(r"__name__\s*==\s*\\?['\"]__main__"),
    # f-strings and comprehensions are, in spirit, the same over-reach as def/
    # return: Python beyond a linear chapter-1 script (rule 3's own language -
    # "script Python linéaire simple"). Checked the same context-exempted way
    # as every entry above, but in practice unconditional: verified against
    # the full corpus, real f-string/comprehension syntax appears nowhere in
    # it, so the exemption never fires today. Not preceded by a quote or a
    # word character, so a literal single-character string like `"f"` in an
    # exercise ("ch [2] = \"f\"") isn't mistaken for an f-string prefix.
    "f-string": re.compile(r"(?<!['\"\w])(?:r?f|fr)['\"]", re.IGNORECASE),
    "list/dict comprehension": re.compile(
        r"[\[{][^\[\]{}\n]{0,60}\bfor\b[^\[\]{}\n]{0,60}\bin\b[^\[\]{}\n]{0,60}[\]}]"
    ),
}

# Phrases that show the model disclosed a gap rather than inventing syntax -
# the behaviour rule 2 asks for when a problem needs an uncovered notion.
DISCLOSURE_RE = re.compile(
    r"(non couverte?|pas couverte?|n'est pas (?:couvert|présent|fourni)|"
    r"absente? du (?:contexte|chapitre)|ne figure pas dans le contexte)",
    re.IGNORECASE,
)


# A model that says "aucun contrôle de flux (Si, Tant que) n'est nécessaire" is
# complying with rule 2, not breaking it. Only a mention inside a negated clause
# is exempt - an actual construct in the solution still counts.
NEGATION_RE = re.compile(
    r"\b(aucune?|sans|pas de|n['’]est pas|ne sont pas|non n[ée]cessaire|"
    r"inutile|n['’]utilise pas|non couvert|pas encore|seront introduites?|"
    r"n[ée]cessitent?|ne permet(?:tent)? pas|impossible|chapitres? suivants?)\b",
    re.IGNORECASE,
)


_PARAGRAPH_BREAK = re.compile(r"\n\s*\n")


def _is_negated_mention(body: str, match: re.Match) -> bool:
    """True when the match sits in a clause that denies using the construct.

    Scoped to the enclosing paragraph (bounded by a blank line), not the
    physical line. Confirmed live: a model answer wrapped its remark across
    a literal newline mid-sentence - "...ne comporte pas de structure\n
    conditionnelle ( Si…Alors… )." - which put the negation phrase and the
    mention on different lines despite being one sentence. A same-line check
    missed it and reported a false violation; a same-paragraph check does
    not, while a real (non-negated) mention in a later paragraph still
    counts, since a blank line - not just any newline - ends the scope.
    """
    breaks_before = list(_PARAGRAPH_BREAK.finditer(body, 0, match.start()))
    start = breaks_before[-1].end() if breaks_before else 0
    break_after = _PARAGRAPH_BREAK.search(body, match.end())
    end = break_after.start() if break_after else len(body)
    return bool(NEGATION_RE.search(body[start:end]))


# Python builtins checked against the context. Matched with word boundaries:
# a plain substring test for "int(" is satisfied by "print(", which silently
# disabled the check.
#
# min/max added after a real leak: `alea ← Aléa(min(a,b), max(a,b))` in an
# Algorithme-column solution. Neither name appears anywhere in the corpus
# (verified directly), in either column, so this mechanism - already correct
# for randint et al. - now catches them the same way, with no new logic.
RULE1_NAMES = (
    "range",
    "len",
    "input",
    "print",
    "int",
    "float",
    "round",
    "sqrt",
    "abs",
    "randint",
    "str",
    "min",
    "max",
)


# Algorithme-side vocabulary from a chapter not yet ingested here. écrire_nl
# and lire_ligne are confirmed real curriculum syntax (file I/O), not
# invented and not a Python leak - so this isn't RULE1_NAMES's "Python
# builtin absent from context" case, it's the same context-membership idea
# CONTROL_STRUCTURES already uses: chapter 1's context never supplies them,
# so using them here is flagged, and the check stops flagging them on its
# own the day a file-I/O chapter's context actually does.
#
# Compiled patterns rather than plain names (unlike RULE1_NAMES/_uses):
# écrire_nl needs the same e/é spelling flexibility the corpus itself uses
# for écrire (pinned content spells it unaccented, "Ecrire").
FUTURE_CHAPTER_FUNCTIONS = {
    "écrire_nl": re.compile(r"(?<![A-Za-zÀ-ÿ_])[eé]crire_nl\s*\(", re.IGNORECASE),
    "lire_ligne": re.compile(r"(?<![A-Za-zÀ-ÿ_])lire_ligne\s*\(", re.IGNORECASE),
}


# Algorithme-column conventions.
#
# Everything else in this checker validates the Python column. The Algorithme
# column was never validated against corpus conventions, which is how
# `Lire moyenne1 ← réel` - a construct appearing nowhere in the corpus - passed
# as clean through every prior round. The corpus writes `Lire (variable)` alone
# and declares types in a separate `Objet | Nature/type` table.
#
# Matching is bounded to a single markdown cell (`[^|\n]*`) so the Python column
# on the same table row cannot satisfy the pattern.
TYPE_WORD = r"(?:entier|r[ée]els?|bool[ée]en|cha[îi]ne|caract[èe]re|int|float|str)"

ALGO_CONVENTIONS = {
    # `Lire x ← réel` / `Lire (x) : entier` - lecture fused with declaration.
    "Lire fusionné avec une déclaration": re.compile(
        rf"\bLire\b\s*\(?\s*\w+\s*\)?\s*(?:←|<-|:)\s*{TYPE_WORD}\b",
        re.IGNORECASE,
    ),
    # Any assignment arrow inside a Lire instruction, whatever follows it.
    # The gap excludes `<` and backticks as well as `|`: the model sometimes
    # packs a whole algorithm into one markdown cell with <br> separators, and
    # without those boundaries the pattern runs from a correct `Lire (coeff3)`
    # into the next instruction's `moyenne_arith ←` and reports a false
    # violation.
    "Lire avec une affectation": re.compile(
        r"\bLire\b[^|\n<`]{0,40}?(?:←|<-)",
        re.IGNORECASE,
    ),
    # Python-only operators leaking into the Algorithme column. `%`/`//` are
    # not themselves absent from context - the pinned operators table teaches
    # them explicitly, as `div`/`mod`'s Python-side spelling ("Division
    # entière | // | div | 21 // 4 donne 5") - so a context-membership check
    # (RULE1_NAMES's approach) would be wrong here: it would see them in
    # context and wave them through. The actual defect is column position,
    # not invention, so this follows the same shape as the Lire checks above:
    # anchored on ← (Algorithme-only; the Python column always uses =), no
    # unescaped `|` between the arrow and the operator, so a Python-column
    # cell on the same row can't satisfy it.
    #
    # Known gap, same as the Lire checks: a statement using one of these
    # without any assignment in the same cell (e.g. `Ecrire (a % b)` with no
    # ← anywhere in that cell) slips through. Not seen in practice yet - the
    # confirmed leak was `reste ← alea % 2` - but noted for the same reason
    # the file's other mechanical checks document their known blind spots.
    "% (modulo) Python dans la colonne Algorithme": re.compile(r"←[^|\n<`]{0,80}?%"),
    "// (division entière) Python dans la colonne Algorithme": re.compile(r"←[^|\n<`]{0,80}?//"),
    # Excludes `***` (a decorative separator the corpus itself uses in
    # exercise output, e.g. `Ecrire ("***", S, "***", ...)`) via lookaround
    # on both sides, not just a `{2}` count, so `****` doesn't slip through.
    "** (puissance) Python dans la colonne Algorithme": re.compile(
        r"←[^|\n<`]{0,80}?(?<!\*)\*\*(?!\*)"
    ),
}


def check_algorithme_column(body: str) -> list[str]:
    """Rule 1 violations in the Algorithme column."""
    found = []
    for label, pattern in ALGO_CONVENTIONS.items():
        match = pattern.search(body)
        if match:
            snippet = match.group(0).strip().replace("\n", " ")[:60]
            found.append(f"rule 1: {label} -> {snippet!r}")
    return found


def _uses(name: str, text: str) -> bool:
    """Case-insensitive on purpose.

    The corpus capitalises Python builtins inconsistently in its Algorithme /
    Python columns - it writes `Str(x)` and `Len(ch)` where Python has `str`
    and `len`. Matching case-sensitively made a correct lowercase `str(A)` look
    like invented syntax, because only `Str(` was in the context.
    """
    return re.search(rf"(?<![A-Za-z_]){re.escape(name)}\s*\(", text, re.IGNORECASE) is not None


def check_constraints(answer: str, context: str) -> tuple[list[str], list[str]]:
    """Mechanical rule-1 / rule-2 checks. Returns (violations, notes)."""
    violations: list[str] = []
    notes: list[str] = []

    # Strip any <think> block - reasoning models narrate about loops without
    # putting one in the answer.
    body = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL)

    for label, pattern in CONTROL_STRUCTURES.items():
        match = next((m for m in pattern.finditer(body) if not _is_negated_mention(body, m)), None)
        if not match:
            continue
        snippet = match.group(0).strip().replace("\n", " ")[:60]
        if pattern.search(context):
            # Context supplies this construct, so using it is allowed.
            notes.append(f"uses '{label}' (context supplies it) -> {snippet!r}")
        else:
            violations.append(f"rule 2: invented '{label}', absent from context -> {snippet!r}")

    if DISCLOSURE_RE.search(body):
        notes.append("discloses an uncovered notion rather than inventing it")

    violations.extend(check_algorithme_column(body))

    # Rule 2: the declaration table must be present, since it is what fixes
    # each variable's type now that inline annotation is forbidden.
    if not re.search(r"Objet\s*\|", body) and not re.search(
        r"Nature\s*/\s*type", body, re.IGNORECASE
    ):
        violations.append("rule 2: no `Objet | Nature/type` declaration table")

    # Rule 1 spot-check: Python builtins the context never introduces.
    for name in RULE1_NAMES:
        if _uses(name, body) and not _uses(name, context):
            violations.append(f"rule 1: uses {name}() which is absent from the context")

    # Rule 2: Algorithme-side vocabulary from a chapter not yet ingested -
    # see FUTURE_CHAPTER_FUNCTIONS. Context-membership, not invention: this
    # stops firing on its own once a later chapter's context supplies them.
    for label, pattern in FUTURE_CHAPTER_FUNCTIONS.items():
        if pattern.search(body) and not pattern.search(context):
            violations.append(f"rule 2: uses '{label}', absent from context")

    return violations, notes
