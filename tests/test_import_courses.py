"""Tests for app/core/chapter_ids.py and scripts/import_courses.py (merging).
Pure Python - no database, no network.

    python -m tests.test_import_courses

Inside the backend container:
    docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_import_courses
"""

from __future__ import annotations

import tempfile
from types import SimpleNamespace
from pathlib import Path

from app.core import chapter_ids
from app.rag.course_markdown import parse, student_text
from scripts.import_courses import Chapter, check, discover, series_files, split_serie

failures = 0


def check_(label: str, condition: bool, detail: str = "") -> None:
    global failures
    if not condition:
        failures += 1
    print(f"[{'PASS' if condition else 'FAIL'}] {label}" + (f" {detail}" if detail else ""))


CHAPTER = """---
niveau: 3eme
chapitre: 2
titre: Les tris
type: cours
notions: tri par sélection, tri à bulles
---

# Chapitre 2 : Les tris

## I. Le tri par sélection

### 📌 1. Syntaxe

```algorithme
Pour i de 0 à n - 2 Faire
    Echanger (T[i], T[min])
Fin Pour
```

```python
for i in range(n - 1):
    T[i], T[m] = T[m], T[i]
```

Un texte sous la fiche.
"""

SERIE_1 = """---
niveau: 3eme
chapitre: 2
titre: Série N° 1 : Les tris
type: serie
notions: tris
---

# Série N° 1 : Les tris

## Série d'exercices

### Exercice 1

Trier `[3, 1, 2]`.

```python
T = [3, 1, 2]
# commentaire qui ressemble à un titre
```

### Exercice 2

Compter les échanges.
"""

SERIE_2 = SERIE_1.replace("Série N° 1 : Les tris", "Série N° 2 : Les recherches")


def write(folder: Path, name: str, text: str) -> None:
    (folder / name).write_text(text, encoding="utf-8")


def main() -> None:
    # --- ids ---------------------------------------------------------------------------
    check_("2ème keeps its numbers", chapter_ids.platform_id("2eme", 3) == "3")
    check_("3ème chapter 1 is 31", chapter_ids.platform_id("3eme", "1") == "31")
    check_("bac chapter 6 is 66", chapter_ids.platform_id("bac", 6) == "66")
    check_("the display number undoes the offset",
           [chapter_ids.chapter_number(i) for i in ("4", "34", "66")] == ["4", "4", "6"])
    check_("an id belongs to exactly one niveau",
           [chapter_ids.niveau_of_id(i) for i in ("2", "31", "59", "61", "89", "30", "60", "90", "100")]
           == ["2eme", "3eme", "3eme", "bac", "bac", None, None, None, None])
    for niveau, number in (("5eme", 1), ("3eme", 0), ("3eme", 30), ("3eme", "x")):
        try:
            chapter_ids.platform_id(niveau, number)
            ok = False
        except ValueError:
            ok = True
        check_(f"platform_id({niveau!r}, {number!r}) refused", ok)

    # --- splitting a série ----------------------------------------------------------------
    before, exos = split_serie(SERIE_1.split("---\n", 2)[2])
    check_("two exercises found", [n for n, _ in exos] == [1, 2], str(exos))
    check_("a Python comment inside a fence is not a heading",
           any("# commentaire" in line for line in exos[0][1]))
    _b, mixed = split_serie("## Série d'exercices\n\n### Exercice 1\n\nA.\n\n### Problème 2 : (Carré magique)\n\nB.\n")
    check_("a « Problème N » is an exercise and keeps its title", [n for n, _ in mixed] == [1, 2]
           and mixed[1][1][0] == "**Problème 2 : (Carré magique)**", str(mixed))

    # --- merging --------------------------------------------------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        folder = root / "3eme" / "ch02-tris"
        folder.mkdir(parents=True)
        write(folder, "chapitre.md", CHAPTER)
        write(folder, "serie-2.md", SERIE_2)
        write(folder, "serie-1.md", SERIE_1)
        write(folder, "serie-10.md", SERIE_1.replace("Les tris", "Dix"))
        write(folder, "serie-revision.md", SERIE_1.replace("Les tris", "Révision"))
        (root / "3eme" / "ch03-sans-cours").mkdir()
        write(root / "3eme" / "ch03-sans-cours", "serie-1.md", SERIE_1)
        (root / "3eme" / "notes").mkdir()

        names = [p.name for p in series_files(folder)]
        check_("series are in numeric order, révision last",
               names == ["serie-1.md", "serie-2.md", "serie-10.md", "serie-revision.md"], str(names))

        found = discover(root, None, None)
        check_("folders without a chNN- prefix are ignored", [c.number for c in found] == [2, 3])
        check_("--chapter filters", [c.number for c in discover(root, "3eme", 3)] == [3])

        ch = found[0]
        check(ch)
        check_("the merged course parses", ch.course is not None and not ch.problems, str(ch.problems))
        check_("platform id derived from niveau + number", ch.platform_id == "32", ch.platform_id)
        check_("exercises renumbered across series", ch.exercises == 8, str(ch.exercises))
        merged = parse(ch.merged)
        check_("the pin survives the merge", sum(1 for c in merged.chunks if c["pinned"]) == 1)
        titles = [e["title"] for e in merged.exercises]
        check_("exercise titles run 1..8", titles == [f"Exercice {i}" for i in range(1, 9)], str(titles))
        check_("each exercise says which série it came from",
               "Série N° 2 : Les recherches" in merged.exercises[2]["question"]
               and "Série N° 1 : Les tris" in merged.exercises[0]["question"])
        check_("the course is not duplicated by the merge",
               ch.merged.count("## I. Le tri par sélection") == 1)

        orphan = found[1]
        check(orphan)
        check_("a folder with no chapitre.md is skipped, not refused",
               orphan.course is None and not orphan.merged and orphan.problems)

        # an unpinned course is refused by the real parser, with its reason
        write(folder, "chapitre.md", CHAPTER.replace("📌 ", ""))
        bad = Chapter(niveau="3eme", number=2, folder=folder)
        check(bad)
        check_("an unpinned chapter is refused", bad.course is None and any("📌" in p for p in bad.problems),
               str(bad.problems))

        # the built-in chapter is validated but never imported
        b = root / "2eme" / "ch01-integre"
        b.mkdir(parents=True)
        write(b, "chapitre.md", CHAPTER.replace("niveau: 3eme", "niveau: 2eme").replace("chapitre: 2", "chapitre: 1"))
        write(b, "serie-1.md", SERIE_1)
        builtin = Chapter(niveau="2eme", number=1, folder=b)
        check(builtin)
        check_("2ème chapter 1 is valid but marked not-imported",
               builtin.course is not None and builtin.skip and not builtin.problems, builtin.skip)

    # --- what a student reads on the chapter page ------------------------------------------
    sample = (
        CHAPTER
        + "\n![Schéma d'un tri](figures/tri.png)\n\n<!-- TODO vérifier: note de l'auteur -->\n"
        + "```python\n# Série d'exercices dans un commentaire\nx = 1\n```\n"
        + "\n## Série d'exercices\n\n### Exercice 1\n\nÉnoncé.\n"
    )
    shown = student_text(sample)
    check_("the header is not shown", "niveau:" not in shown and "notions:" not in shown)
    check_("the chapter H1 is not shown (the page has its own)", "# Chapitre 2" not in shown)
    check_("TODO notes are not shown", "TODO" not in shown)
    check_("a figure shows as its description", "*[Figure : Schéma d'un tri]*" in shown
           and "figures/tri.png" not in shown)
    check_("the exercises are cut (they have their own tab)", "Exercice 1" not in shown and "Énoncé" not in shown)
    check_("a comment inside a code block is not mistaken for the série heading",
           "# Série d'exercices dans un commentaire" in shown and "x = 1" in shown)
    check_("the pin marker is removed from headings but the heading stays",
           "📌" not in shown and "### 1. Syntaxe" in shown)

    real = Path("courses/3eme/ch01-tris-et-recherches/chapitre.md")
    if real.exists():
        text = student_text(real.read_text(encoding="utf-8"))
        check_("a real chapter reads as text", len(text) > 1000 and "TODO" not in text and "---" not in text.split("\n")[0])
    else:
        print("[SKIP] real chapter not found (run from the repository root)")

    # --- the T.D.N.T notion ----------------------------------------------------------------
    from app.llm import prompts

    check_("the solve prompt requires a T.D.N.T for types beyond the five simple ones",
           "T.D.N.T" in prompts.SYSTEM_PROMPT and "T.D.O.L" in prompts.SYSTEM_PROMPT)
    check_("the code-review prompt flags a student's missing T.D.N.T", "T.D.N.T" in prompts.CODE_SYSTEM_PROMPT)
    solve = prompts.SYSTEM_PROMPT
    check_("the declaration tables depend on the solution: T.D.N.T only for a new type, T.D.O.L per sous-programme",
           "UNIQUEMENT si la solution" in solve and "pour chaque sous-programme" in solve
           and "n'écris jamais un tableau vide" in solve)
    check_("the solve prompt no longer forbids what later chapters teach (matrices, enregistrements, sous-programmes)",
           "pas de structures/enregistrements" not in solve and "N'utilise aucune fonction ou procédure" not in solve
           and "SEULEMENT si le contexte" in solve and "QUE si le contexte" in solve)
    check_("every mode that shows a complete solution names the adapted tables",
           all("T.D.O.L" in getattr(prompts, n) for n in
               ("SYSTEM_PROMPT", "USER_PROMPT", "CODE_USER_PROMPT", "FOLLOW_UP_SYSTEM_PROMPT", "CHECK_USER_PROMPT")))
    source = open("app/llm/prompts.py", encoding="utf-8").read()
    check_("no prompt still asks for 'le tableau de déclaration (Objet | Nature/type)' as the one fixed table",
           "Le tableau de déclaration (Objet | Nature/type)" not in source
           and "le tableau de déclaration (Objet | Nature/type)" not in source)
    for rel in ("3eme/ch02-algorithmes-recurrents", "3eme/ch03-algorithmes-arithmetiques",
                "bac/ch02-recursivite", "bac/ch05-algorithmes-arithmetiques"):
        path = Path("courses") / rel / "chapitre.md"
        if path.exists():
            check_(f"{rel}: the course shows a T.D.N.T for its structured types",
                   "T.D.N.T" in path.read_text(encoding="utf-8"))

    # --- sentences announcing an unneeded declaration table are dropped -----------------
    from app.grading.algo_notation import strip_absent_table_notes

    seen = [
        "*(Aucun type supplémentaire n’est nécessaire, donc pas de T.D.N.T.)*",
        "*(Aucun type nouveau n’est nécessaire, donc pas de T.D.N.T.)*",
        "*Tableau des objets locaux du sousprogramme (T.D.O.L)* – aucun objet local supplémentaire n’est nécessaire pour la fonction `SomTab`.",
        "Pas de T.D.N.T nécessaire ici.",
    ]
    for sentence in seen:
        text, n = strip_absent_table_notes(f"**T.D.O**\n\n| Objet | Nature/type |\n|---|---|\n| a | Entier |\n\n{sentence}\n\n**Solution**")
        check_(f"dropped: {sentence[:48]}", n == 1 and sentence not in text and "| a | Entier |" in text and "**Solution**" in text, text)
    keep = [
        "**T.D.N.T** (type nouveau)",
        "Tableau des nouveaux types (T.D.N.T)",
        "| Aucun | pas de T.D.N.T |",
        "Il n'y a aucune erreur dans ta boucle.",
        "Un type nouveau se déclare dans le T.D.N.T.",
    ]
    for sentence in keep:
        text, n = strip_absent_table_notes(sentence)
        check_(f"kept: {sentence[:48]}", n == 0 and text == sentence, text)
    fenced = "```python\n# pas de T.D.N.T\n```"
    check_("a code block is never touched", strip_absent_table_notes(fenced) == (fenced, 0))

    # --- the request size budget (needs the app's dependencies: skipped on a bare host) ----
    try:
        from app.rag.context import MAX_CONTEXT_CHARS, PinnedChunk, _pin_cost, fit_prerequisites
    except ModuleNotFoundError as exc:
        print(f"[SKIP] context budget: {exc.name} not installed here (runs in the backend container)")
    else:
        def pin(label, text, i):
            return PinnedChunk(label, text, {"section": label}, f"id{i}")

        earlier = [
            pin("Ch. 1 — Entrée/sortie", "Lire Ecrire lire saisie " + "a" * 900, 1),
            pin("Ch. 2 — Boucle Pour", "Pour boucle compteur " + "b" * 900, 2),
            pin("Ch. 3 — Fichiers", "fichier ouvrir fermer " + "c" * 900, 3),
        ]
        one = _pin_cost(earlier[0])
        kept = fit_prerequisites(earlier, "Lire deux entiers puis Ecrire leur somme", one + 50)
        check_("a budget for one earlier sheet keeps the one that matches the problem",
               [p.chunk_id for p in kept] == ["id1"], str([p.chunk_id for p in kept]))
        kept = fit_prerequisites(earlier, "zzzz", 2 * one + 50)
        check_("with no match, the most recent chapters are kept (and stay in teaching order)",
               [p.chunk_id for p in kept] == ["id2", "id3"], str([p.chunk_id for p in kept]))
        check_("no room, no earlier sheets", fit_prerequisites(earlier, "Lire", 0) == [])
        check_("everything fits: nothing is dropped",
               [p.chunk_id for p in fit_prerequisites(earlier, "x", 10 * one)] == ["id1", "id2", "id3"])
        check_("the budget leaves room under the model's request limit", 4000 <= MAX_CONTEXT_CHARS <= 9000, str(MAX_CONTEXT_CHARS))

        from app.rag.context import earlier_chapters

        rows = [SimpleNamespace(id=i, niveau=n) for i, n in (
            ("66", "bac"), ("2", "2eme"), ("62", "bac"), ("31", "3eme"), ("4", "2eme"), ("33", "3eme"), ("61", "bac"))]
        check_("a 3ème chapter builds on all of 2ème, then on 3ème's earlier chapters, in teaching order",
               earlier_chapters("3eme", 33, rows) == [("2eme", "2"), ("2eme", "4"), ("3eme", "31")],
               str(earlier_chapters("3eme", 33, rows)))
        check_("a Bac chapter builds on 2ème, 3ème and Bac's earlier chapters",
               [i for _n, i in earlier_chapters("bac", 62, rows)] == ["2", "4", "31", "33", "61"],
               str(earlier_chapters("bac", 62, rows)))
        check_("a 2ème chapter builds on no later year", all(n == "2eme" for n, _i in earlier_chapters("2eme", 4, rows)))
        check_("the first chapter of a year still builds on the years before it",
               earlier_chapters("bac", 61, rows) == [("2eme", "2"), ("2eme", "4"), ("3eme", "31"), ("3eme", "33")])
        check_("an unknown year has no earlier chapters", earlier_chapters("1ere", 5, rows) == [])

    print(f"\n{failures} failure(s)")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
