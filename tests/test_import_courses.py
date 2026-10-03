"""Tests for app/core/chapter_ids.py and scripts/import_courses.py (merging).
Pure Python - no database, no network.

    python -m tests.test_import_courses

Inside the backend container:
    docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec backend python -m tests.test_import_courses
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.core import chapter_ids
from app.rag.course_markdown import parse
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

    print(f"\n{failures} failure(s)")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
