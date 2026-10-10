"""How a chapter's number inside its year maps to its Fahem id.

A chapter id is one global key (UploadedChapter.id, the `chapitre` scope of the
Qdrant corpus, the `/chapters/{id}` URLs). The courses are written per year -
"3ème, chapitre 1" - so two years would collide on "1". Each year therefore
gets its own block of ids:

    2eme  -> 1..29     (id = number; chapter 1 is built into Fahem)
    3eme  -> 31..59    (id = 30 + number)
    bac   -> 61..89    (id = 60 + number)

The block is wide enough that no year comes near the next one, and 2ème keeps
the ids it always had. The Markdown source keeps its natural number
("chapitre: 1" in courses/3eme/...): the id is derived from (niveau, number),
never written in the course.

ui/src/lib/chapterNumber.js is the same arithmetic for display, so a student
reads "Chapitre 1", not "Chapitre 31".
"""

from __future__ import annotations

ID_OFFSET: dict[str, int] = {"2eme": 0, "3eme": 30, "bac": 60}
BLOCK_SIZE = 30


def platform_id(niveau: str, number: int | str) -> str:
    """The chapter id for chapter `number` of `niveau`. ValueError if impossible."""
    key = niveau.strip().lower()
    if key not in ID_OFFSET:
        raise ValueError(f"niveau inconnu : {niveau!r}")
    try:
        n = int(str(number).strip())
    except ValueError:
        raise ValueError(f"numéro de chapitre invalide : {number!r}") from None
    if not 1 <= n < BLOCK_SIZE:
        raise ValueError(f"numéro de chapitre hors limites (1 à {BLOCK_SIZE - 1}) : {n}")
    return str(ID_OFFSET[key] + n)


def niveau_of_id(chapter_id: str) -> str | None:
    """The niveau whose block holds this id, or None (0, the offsets, ids >= 90)."""
    try:
        n = int(chapter_id)
    except ValueError:
        return None
    for niveau, offset in sorted(ID_OFFSET.items(), key=lambda kv: -kv[1]):
        if offset < n < offset + BLOCK_SIZE:
            return niveau
    return None


def chapter_number(chapter_id: str) -> str:
    """The number a student reads: the id minus its year's offset.

    Unknown shapes are returned untouched rather than guessed at.
    """
    niveau = niveau_of_id(chapter_id)
    if niveau is None:
        return str(chapter_id)
    return str(int(chapter_id) - ID_OFFSET[niveau])
