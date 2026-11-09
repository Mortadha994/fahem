"""The upload mirror: files written under CHAPTER_UPLOAD_DIR are kept in the
database and put back after the disk is wiped (Hugging Face Spaces).

Runs against an in-memory SQLite database - no live data is touched:

    docker compose ... run --rm backend python -m tests.test_upload_mirror
"""

from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core import models
from app.rag import chapter_store

failures = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global failures
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + ("" if ok else f"  {detail}"))
    failures += 0 if ok else 1


def main() -> None:
    engine = create_engine("sqlite://")
    models.StoredUpload.__table__.create(engine)
    Session = sessionmaker(engine)

    @contextmanager
    def session_scope():
        s = Session()
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp) / "chapters"
        chapter_store.session_scope = session_scope
        chapter_store.CHAPTER_UPLOAD_DIR = folder

        # Off (the default on a normal host): nothing reaches the database.
        chapter_store.MIRROR_UPLOADS_TO_DB = False
        chapter_store.store_pdf("31", b"%PDF-off")
        with session_scope() as s:
            check("off: no row is written", s.query(models.StoredUpload).count() == 0)
        check("off: restore does nothing", chapter_store.restore_uploads() == 0)

        # On: every write is mirrored.
        chapter_store.MIRROR_UPLOADS_TO_DB = True
        chapter_store.store_pdf("31", b"%PDF-1")
        chapter_store.store_markdown("31", "# cours é".encode("utf-8"))
        chapter_store.store_supplement("1", [{"id": "e1", "question": "Q ?"}])
        with session_scope() as s:
            names = sorted(r.name for r in s.query(models.StoredUpload))
        check("on: pdf, markdown and supplement are mirrored",
              names == ["1.exercises.json", "31.md", "31.pdf"], str(names))

        chapter_store.store_pdf("31", b"%PDF-2")
        with session_scope() as s:
            row = s.get(models.StoredUpload, "31.pdf")
            check("a rewrite replaces the copy", row is not None and row.data == b"%PDF-2")

        # The disk is wiped, then restored from the database.
        for f in folder.iterdir():
            f.unlink()
        n = chapter_store.restore_uploads()
        check("restore rewrites every file", n == 3 and (folder / "31.pdf").read_bytes() == b"%PDF-2", str(n))
        check("restored text is intact", (folder / "31.md").read_text(encoding="utf-8") == "# cours é")
        check("the supplement is readable again",
              chapter_store.supplement_exercises("1") == [{"id": "e1", "question": "Q ?"}])
        check("a second restore finds nothing missing", chapter_store.restore_uploads() == 0)

        # A deleted chapter leaves no copy behind.
        chapter_store.remove_pdf("31")
        with session_scope() as s:
            left = sorted(r.name for r in s.query(models.StoredUpload))
        check("remove drops pdf and markdown copies", left == ["1.exercises.json"], str(left))

        # A row whose name is a path never writes outside the folder.
        with session_scope() as s:
            s.add(models.StoredUpload(name="../evil.pdf", data=b"x"))
        for f in folder.iterdir():
            f.unlink()
        chapter_store.restore_uploads()
        check("a path-like name is ignored", not (Path(tmp) / "evil.pdf").exists())

    print(f"\n{failures} failure(s)")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
