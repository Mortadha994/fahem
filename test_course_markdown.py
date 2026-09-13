"""Tests for course_markdown.py (Phase 9b). Pure parsing - no database.

    docker compose cp docs/modele-cours.md backend:/app/docs/modele-cours.md
    docker compose exec backend python test_course_markdown.py

The shipped template (docs/modele-cours.md) is parsed too when present, so the
file teachers copy can never drift into something the importer refuses.
"""

from __future__ import annotations

from pathlib import Path

from course_markdown import MAX_CHUNK_CHARS, ParseError, parse

failures = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global failures
    if not condition:
        failures += 1
    print(f"[{'PASS' if condition else 'FAIL'}] {label}" + (f" {detail}" if detail else ""))


def problems_of(text: str, **kw) -> list[str]:
    try:
        parse(text, **kw)
    except ParseError as exc:
        return exc.problems
    return []


HEADER = """---
niveau: 2eme
chapitre: 7
titre: Chapitre de test
notions: la forme simple, la forme alternative
---
"""

GOOD = HEADER + """
# Chapitre 7 : test

<!-- une note pour l'auteur, jamais importée : ## pas une section -->

## I. Introduction

Un paragraphe d'introduction assez long pour être un vrai morceau de cours.

## II. La structure Si

### 📌 Syntaxe : forme simple

```algorithme
Si <condition> Alors
    <Traitement>
Fin Si
```

```python
if <condition> :
    <Traitement>
```

### 1. Exemple

```algorithme
Si x > 0 Alors
    y ← x
Fin Si
```

## Série d'exercices

### Exercice 1

Lire un entier et afficher sa valeur absolue.

### Exercice 2

Lire deux entiers et afficher le plus grand.
"""


def main() -> None:
    c = parse(GOOD, expected_chapitre="7")
    check("header read", (c.niveau, c.chapitre, c.titre) == ("2eme", "7", "Chapitre de test"))
    check("notions read", c.notions == "la forme simple, la forme alternative")

    course = [x for x in c.chunks if x["type"] != "exercice"]
    check("the HTML comment never becomes course text",
          not any("note pour l'auteur" in x["content"] for x in c.chunks))
    check("sections become chunks", len(course) == 3, str([x["section"] for x in course]))
    pinned = [x for x in c.chunks if x["pinned"]]
    check("📌 section is pinned, with a clean label",
          len(pinned) == 1 and pinned[0]["pin_label"] == "Syntaxe : forme simple", str(pinned[:1]))
    check("pinned chunk holds both code blocks whole",
          pinned[0]["content"].count("```") == 4 and "Fin Si" in pinned[0]["content"])
    check("subsection chunks name their parent section",
          pinned[0]["section"] == "II. La structure Si — 📌 Syntaxe : forme simple".replace("📌 ", ""))
    check("chunks with code are 'table', plain text is 'prose'",
          [x["type"] for x in course] == ["prose", "table", "table"], str([x["type"] for x in course]))
    check("exercises extracted in order",
          [e["title"] for e in c.exercises] == ["Exercice 1", "Exercice 2"]
          and c.exercises[0]["question"].startswith("Lire un entier"))
    check("exercise chunks are typed 'exercice' (kept out of solve retrieval)",
          sum(1 for x in c.chunks if x["type"] == "exercice") == 2)
    check("no '📌' leaks into section names", not any("📌" in x["section"] for x in c.chunks))

    # --- long sections split between blocks, never inside a code fence --------
    para = "Texte de cours. " * 40
    code = "```algorithme\n" + "\n".join(f"x ← {i}" for i in range(60)) + "\n```"
    long_md = HEADER + "\n## I. Long\n\n" + "\n\n".join([para, code, para, para, code, para]) + (
        "\n\n### 📌 Syntaxe : ref\n\n```algorithme\nx ← 1\n```\n"
    )
    lc = parse(long_md)
    long_chunks = [x for x in lc.chunks if x["section"] == "I. Long"]
    check("a long section is split into several chunks", len(long_chunks) > 1, str(len(long_chunks)))
    check("no chunk cuts a code block in half",
          all(x["content"].count("```") % 2 == 0 for x in lc.chunks))
    check("continuation chunks repeat the heading",
          all(x["content"].startswith("## I. Long") for x in long_chunks))
    check("chunks stay near the size budget (one oversized block may stand alone)",
          all(len(x["content"]) <= MAX_CHUNK_CHARS + len(code) for x in long_chunks))

    # --- refusals ----------------------------------------------------------------
    p = problems_of("# Chapitre II\n\n## I. Intro\n\nTexte.\n")
    check("no header -> refused, says line 1", any("Ligne 1" in x for x in p), str(p))

    p = problems_of(HEADER.replace("notions: la forme simple, la forme alternative\n", "") + GOOD[len(HEADER):])
    check("missing 'notions' -> refused", any("notions" in x for x in p), str(p))

    p = problems_of(GOOD, expected_chapitre="8")
    check("header chapter differs from the upload -> refused", any("'7'" in x and "'8'" in x for x in p), str(p))

    untagged = GOOD.replace("```algorithme\nSi x > 0", "```\nSi x > 0")
    p = problems_of(untagged)
    check("untagged code block -> refused with its line number",
          any("sans langage" in x and "Ligne" in x for x in p), str(p))

    unclosed = HEADER + "\n## I. A\n\n### 📌 Syntaxe : x\n\n```algorithme\nx ← 1\n"
    p = problems_of(unclosed)
    check("unclosed code block -> refused", any("jamais fermé" in x for x in p), str(p))

    p = problems_of(GOOD.replace("📌 ", ""))
    check("no 📌 section -> refused (no reference sheet)", any("📌" in x for x in p), str(p))

    p = problems_of(GOOD.replace("### Exercice 2", "### Deuxième exercice"))
    check("a série heading that is not 'Exercice N' -> refused", any("Exercice N" in x for x in p), str(p))

    alt = GOOD.replace("## Série d'exercices", "# Série d'exercices").replace("### Exercice", "## Exercice")
    ac = parse(alt)
    check("'# Série' with '## Exercice N' is accepted too", len(ac.exercises) == 2, str(len(ac.exercises)))

    crlf = parse(GOOD.replace("\n", "\r\n"))
    check("Windows line endings parse identically", len(crlf.chunks) == len(c.chunks))

    template = Path("docs/modele-cours.md")
    if template.exists():
        t = parse(template.read_text(encoding="utf-8"))
        check("the shipped template imports cleanly",
              len(t.exercises) == 2 and sum(1 for x in t.chunks if x["pinned"]) == 3,
              f"{len(t.chunks)} chunks, {len(t.exercises)} exercises")
        check("the template's instruction comment is not imported",
              not any("MODÈLE DE COURS" in x["content"] for x in t.chunks))
    else:
        print("[SKIP] shipped template not found at docs/modele-cours.md")

    print(f"\n{failures} failure(s)")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
