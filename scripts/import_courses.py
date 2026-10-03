"""Import the Markdown courses in courses/ into Fahem (database + search index).

The sources are one file per Classroom document:

    courses/<niveau>/chNN-<slug>/chapitre.md      the cours (type: cours)
    courses/<niveau>/chNN-<slug>/serie-*.md       one file per série (type: serie)

Fahem imports one file per chapter (app/rag/course_markdown.py: a course needs
course text, a 📌 reference sheet, and its exercises under "## Série d'exercices"),
so this script builds that file from the pieces: the chapter, then every série's
exercises, renumbered one after the other and each headed by the série it came
from. The pieces stay the source of truth; the merged file is derived.

    python -m scripts.import_courses                      # check everything, change nothing
    python -m scripts.import_courses --write-merged out   # also write the merged files
    python -m scripts.import_courses --apply              # write drafts to the database
    python -m scripts.import_courses --apply --publish    # ...and make them live

--apply needs the backend's environment (database + Qdrant + embedding model), so it
runs inside the backend container; see docs/importer-les-cours.md. The check mode is
pure Python and runs anywhere.

Never imported, and why: 2ème chapter 1 is built into Fahem (id 1 cannot be
replaced by an upload), and a folder without chapitre.md has no course text.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from app.core import chapter_ids
from app.rag import course_markdown

ROOT = Path(__file__).resolve().parent.parent / "courses"
BUILTIN_ID = "1"

_FENCE = re.compile(r"^\s*(```+|~~~+)")
_H2 = re.compile(r"^##\s+(.*?)\s*#*\s*$")
_H1 = re.compile(r"^#\s+(.*?)\s*#*\s*$")
_EXO = re.compile(r"^(#{2,3})\s+Exercice\s*(?:n\s*°\s*)?(\d+)\b.*$", re.IGNORECASE)
_SERIE_H = re.compile(r"^s[ée]rie\b", re.IGNORECASE)
_DIR = re.compile(r"^ch(\d+)-")


@dataclass
class Chapter:
    niveau: str
    number: int
    folder: Path
    text: str = ""
    merged: str = ""
    platform_id: str = ""
    series: list[str] = field(default_factory=list)
    exercises: int = 0
    problems: list[str] = field(default_factory=list)
    skip: str = ""  # valid, but deliberately not imported
    course: course_markdown.ParsedCourse | None = None

    @property
    def label(self) -> str:
        return f"{self.niveau} ch{self.number:02d} ({self.folder.name})"


# --- reading the pieces -----------------------------------------------------------------


def split_front_matter(text: str) -> tuple[str, str]:
    """(header block incl. both '---', body). Header is '' when absent."""
    lines = text.replace("\r\n", "\n").lstrip("﻿").split("\n")
    if not lines or lines[0].strip() != "---":
        return "", "\n".join(lines)
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[: i + 1]), "\n".join(lines[i + 1 :])
    return "", "\n".join(lines)


def _outside_fences(lines: list[str]):
    """Yield (index, line, in_fence) so heading scans never read a Python comment."""
    marker = None
    for i, line in enumerate(lines):
        m = _FENCE.match(line)
        if m:
            token = m.group(1)[:3]
            if marker is None:
                marker = token
                yield i, line, True
                continue
            if token == marker:
                marker = None
                yield i, line, True
                continue
        yield i, line, marker is not None


def serie_title(body: str) -> str:
    for _i, line, in_fence in _outside_fences(body.split("\n")):
        if not in_fence:
            m = _H1.match(line)
            if m:
                return m.group(1).strip()
    return ""


def split_serie(body: str) -> tuple[str, list[tuple[int, list[str]]]]:
    """(text before the exercises, [(original number, body lines)]) of a série file.

    The exercises start at '## Série d'exercices' (or the first exercise heading);
    the part before it, minus the '# title' line, is an optional reminder of
    syntax that stays in the course.
    """
    lines = body.split("\n")
    start = None
    for i, line, in_fence in _outside_fences(lines):
        if in_fence:
            continue
        m = _H2.match(line)
        if m and _SERIE_H.match(m.group(1).replace(course_markdown.PIN, "").strip()):
            start = i
            break
    if start is None:
        for i, line, in_fence in _outside_fences(lines):
            if not in_fence and _EXO.match(line):
                start = i
                break
    if start is None:
        return "\n".join(lines), []
    before = "\n".join(
        line for i, line, in_fence in _outside_fences(lines[:start]) if in_fence or not _H1.match(line)
    ).strip()
    exercises: list[tuple[int, list[str]]] = []
    current: list[str] | None = None
    number = 0
    for i, line, in_fence in _outside_fences(lines[start:]):
        m = None if in_fence else _EXO.match(line)
        if m:
            current = []
            number = int(m.group(2))
            exercises.append((number, current))
            continue
        if current is not None:
            current.append(line)
    return before, exercises


def series_files(folder: Path) -> list[Path]:
    """Numbered séries in numeric order, then the others alphabetically."""

    def key(p: Path):
        nums = [int(n) for n in re.findall(r"\d+", p.stem)]
        return (0 if p.stem.startswith("serie-") and nums and "recap" not in p.stem
                and "revision" not in p.stem else 1, nums, p.stem)

    return sorted(folder.glob("serie-*.md"), key=key)


# --- building the merged course -----------------------------------------------------------


def build(ch: Chapter) -> None:
    text = (ch.folder / "chapitre.md").read_text(encoding="utf-8")
    header, body = split_front_matter(text)
    if not header:
        ch.problems.append("chapitre.md : en-tête '---' absent.")
        return

    # A chapter file may carry its own "## Série d'exercices"; it counts as a série.
    own_before, own_exos = split_serie(body)
    own_lines = body.split("\n")
    course_body = body
    if own_exos:
        cut = None
        for i, line, in_fence in _outside_fences(own_lines):
            m = None if in_fence else _H2.match(line)
            if m and _SERIE_H.match(m.group(1).replace(course_markdown.PIN, "").strip()):
                cut = i
                break
        if cut is not None:
            course_body = "\n".join(own_lines[:cut])

    pieces: list[tuple[str, list[tuple[int, list[str]]]]] = []
    extra_sections: list[str] = []
    if own_exos:
        pieces.append(("", own_exos))
    for path in series_files(ch.folder):
        s_header, s_body = split_front_matter(path.read_text(encoding="utf-8"))
        if not s_header:
            ch.problems.append(f"{path.name} : en-tête '---' absent.")
            continue
        label = serie_title(s_body) or path.stem
        before, exos = split_serie(s_body)
        if not exos:
            ch.problems.append(f"{path.name} : aucun « ### Exercice N » trouvé.")
            continue
        # Anything above the exercises other than the title is a reminder that
        # belongs to the course (a pinned syntax sheet, for example).
        if before.strip() and "##" in before:
            extra_sections.append(before.strip())
        ch.series.append(path.name)
        pieces.append((label, exos))

    out = [header.rstrip(), "", course_body.strip(), ""]
    for section in extra_sections:
        out += [section, ""]
    out += ["## Série d'exercices", ""]
    n = 0
    for label, exos in pieces:
        for _orig, body_lines in exos:
            n += 1
            statement = "\n".join(body_lines).strip()
            heading = f"### Exercice {n}"
            out += [heading, ""]
            if label:
                out += [f"*{label}*", ""]
            out += [statement or "", ""]
    ch.exercises = n
    ch.merged = "\n".join(out).rstrip() + "\n"


def check(ch: Chapter) -> None:
    """Build, then run the real parser on the result. Fills ch.problems."""
    if not (ch.folder / "chapitre.md").exists():
        ch.problems.append("pas de chapitre.md : rien à importer (séries seules).")
        return
    build(ch)
    if ch.problems or not ch.merged:
        return
    try:
        ch.platform_id = chapter_ids.platform_id(ch.niveau, ch.number)
    except ValueError as exc:
        ch.problems.append(str(exc))
        return
    try:
        course = course_markdown.parse(ch.merged)
    except course_markdown.ParseError as exc:
        ch.problems.extend(exc.problems)
        return
    ch.course = course
    if ch.platform_id == BUILTIN_ID:
        ch.skip = "chapitre 1 de 2ème : intégré à Fahem, jamais remplacé par un envoi"
    if course.niveau != ch.niveau:
        ch.problems.append(f"en-tête : niveau {course.niveau!r} ≠ dossier {ch.niveau!r}.")
    if str(course.chapitre) != str(ch.number):
        ch.problems.append(f"en-tête : chapitre {course.chapitre!r} ≠ dossier ch{ch.number:02d}.")


def discover(root: Path, niveau: str | None, chapter: int | None) -> list[Chapter]:
    found = []
    for level_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        if niveau and level_dir.name != niveau:
            continue
        for folder in sorted(p for p in level_dir.iterdir() if p.is_dir()):
            m = _DIR.match(folder.name)
            if not m:
                continue
            number = int(m.group(1))
            if chapter is not None and number != chapter:
                continue
            found.append(Chapter(niveau=level_dir.name, number=number, folder=folder))
    return found


# --- the database --------------------------------------------------------------------------


def apply(ch: Chapter, publish: bool) -> str:
    """Write one chapter as a draft (and publish it). Returns a one-line outcome."""
    # Imported here: they need the backend's environment, the check mode does not.
    from app.core.db import session_scope
    from app.core.models import CHAPTER_PROCESSING, CHAPTER_PUBLISHING, UploadedChapter
    from app.rag import chapter_store as cs

    pid = ch.platform_id
    filename = f"{ch.niveau}-ch{ch.number:02d}.md"
    with session_scope() as s:
        row = s.get(UploadedChapter, pid)
        if row is None:
            s.add(
                UploadedChapter(
                    id=pid,
                    niveau=ch.niveau,
                    title=ch.course.titre,
                    topics=ch.course.notions,
                    status=CHAPTER_PROCESSING,
                    source_filename=filename,
                    source_kind="markdown",
                )
            )
        else:
            if row.status in (CHAPTER_PROCESSING, CHAPTER_PUBLISHING):
                return "busy (traitement en cours), ignoré"
            if row.niveau != ch.niveau:
                return f"id {pid} déjà pris par un chapitre de {row.niveau}, ignoré"
            row.source_filename = filename
            row.source_kind = "markdown"
            row.status = CHAPTER_PROCESSING
            row.error = None
    cs.store_markdown(pid, ch.merged.encode("utf-8"))
    cs.process_upload(pid)
    with session_scope() as s:
        row = s.get(UploadedChapter, pid)
        status, error = row.status, row.error
    if status != "draft":
        return f"import échoué ({status}) : {error}"
    outcome = "brouillon importé"
    if publish:
        problems = cs.publish_problems(pid)
        if problems:
            return outcome + " ; publication refusée : " + " ".join(problems)
        if not cs.begin_publish(pid):
            return outcome + " ; publication déjà en cours"
        cs.publish(pid)
        with session_scope() as s:
            row = s.get(UploadedChapter, pid)
            status, error = row.status, row.error
        outcome = "publié" if status == "published" else f"publication échouée : {error}"
    return outcome


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=ROOT, help="courses directory")
    ap.add_argument("--niveau", choices=sorted(chapter_ids.ID_OFFSET))
    ap.add_argument("--chapter", type=int, help="only this chapter number")
    ap.add_argument("--write-merged", type=Path, metavar="DIR", help="write the merged files here")
    ap.add_argument("--apply", action="store_true", help="write to the database (drafts)")
    ap.add_argument("--publish", action="store_true", help="with --apply: publish after import")
    args = ap.parse_args(argv)
    if args.publish and not args.apply:
        ap.error("--publish needs --apply")
    if not args.root.is_dir():
        print(f"dossier introuvable : {args.root}")
        return 2

    chapters = discover(args.root, args.niveau, args.chapter)
    if not chapters:
        print("aucun chapitre trouvé.")
        return 1
    bad = 0
    for ch in chapters:
        check(ch)
        if ch.problems:
            skipped = ch.course is None and not ch.merged
            print(f"- {ch.label}: {'IGNORÉ' if skipped else 'REFUSÉ'}")
            for p in ch.problems:
                print(f"    · {p}")
            if not skipped:
                bad += 1
            continue
        pinned = sum(1 for c in ch.course.chunks if c.get("pinned"))
        print(
            f"- {ch.label}: id {ch.platform_id}, {len(ch.course.chunks)} extraits "
            f"({pinned} épinglés), {ch.exercises} exercices, séries : {', '.join(ch.series) or '—'}"
        )
        if args.write_merged:
            args.write_merged.mkdir(parents=True, exist_ok=True)
            (args.write_merged / f"{ch.niveau}-ch{ch.number:02d}.md").write_text(ch.merged, encoding="utf-8")
        if ch.skip:
            print(f"    → valide, non importé : {ch.skip}")
        elif args.apply:
            print(f"    → {apply(ch, args.publish)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
