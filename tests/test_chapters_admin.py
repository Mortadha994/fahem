"""End-to-end tests for uploaded chapters (Phase 9).

Uploads the real chapter-1 PDF (cours + série) as a throwaway chapter "97",
through the real admin router, then walks the whole lifecycle against real
Postgres and Qdrant with the real embedding model:

    upload -> extraction -> review flags -> blocked publish -> edits
    -> publish -> student catalogue + RAG context -> draft edit invisible
    -> republish without duplicates -> unpublish -> delete

Chapter 1's own PDF is used on purpose: it is known to decode the assignment
arrow as "-", so it proves the lost-arrow flag fires on the real defect rather
than on a synthetic string.

Inside compose (needs the embedding model, Postgres, Qdrant):

    docker compose exec backend python -m tests.test_chapters_admin

Everything it creates - users, the chapter row, the PDF, the Qdrant points -
is removed at the end, including after a failure.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from app.auth import auth
from app.core.db import session_scope
from app.core.models import ROLE_ADMIN, UploadedChapter, User
from app.rag import chapter_store as cs

CH = "97"
PDF = Path("data/2emme info/algo/chapitre 1/cours/chap 1 + série.pdf")
failures = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global failures
    if not condition:
        failures += 1
    print(f"[{'PASS' if condition else 'FAIL'}] {label}" + (f" {detail}" if detail else ""))


def scope_points() -> list:
    from app.rag import rag_store

    return rag_store.scroll_scope("2eme", CH)


def main() -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.rag.context import PinResolutionError, build_context, published_pins
    from app.routes import chapters
    from app.routes.admin import admin_chapters

    run = uuid.uuid4().hex[:8]
    users: list[uuid.UUID] = []
    with session_scope() as s:
        for tag, role in (("admin", ROLE_ADMIN), ("student", "student")):
            u = User(email=f"ch-{tag}-{run}@example.com", password_hash="x", role=role)
            s.add(u)
            s.flush()
            users.append(u.id)
    admin_id, student_id = users

    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(chapters.router)
    app.include_router(admin_chapters.router)
    client = TestClient(app)

    def as_user(uid):
        client.cookies.clear()
        client.cookies.set(auth.SESSION_COOKIE_NAME, auth.create_session_token(uid))

    cs.delete_chapter(CH)  # a leftover from an interrupted run
    pdf = PDF.read_bytes()

    try:
        # --- the gate ------------------------------------------------------------
        routes = list(admin_chapters.router.routes)
        ungated = [
            r.path for r in routes
            if not any(d.dependency is auth.get_current_admin for d in r.dependencies)
        ]
        check("every chapter-admin route inherits the admin gate (non-vacuous)",
              bool(routes) and not ungated, f"routes={len(routes)} ungated={ungated}")

        as_user(student_id)
        check("student: list chapters -> 403", client.get("/admin/chapters").status_code == 403)
        r = client.post("/admin/chapters", params={"id": CH, "title": "x"}, content=pdf)
        check("student: upload -> 403, nothing stored",
              r.status_code == 403 and not cs.pdf_path(CH).exists(), str(r.status_code))

        # --- upload validation -------------------------------------------------------
        as_user(admin_id)
        up = lambda cid, body=pdf: client.post(  # noqa: E731
            "/admin/chapters", params={"id": cid, "title": "Test", "filename": "t.pdf"}, content=body,
            headers={"Content-Type": "application/pdf"})
        check("upload as chapter 1 -> 409 (built-in)", up("1").status_code == 409)
        check("upload with id 'abc' -> 422", up("abc").status_code == 422)
        check("upload of a non-PDF -> 415", up(CH, b"hello, not a pdf").status_code == 415)
        check("...and no row was created", client.get(f"/admin/chapters/{CH}").status_code == 404)

        # --- upload + extraction (TestClient runs background tasks before returning)
        r = up(CH)
        check("upload -> 202 processing", r.status_code == 202 and r.json()["status"] == "processing", r.text[:200])
        d = client.get(f"/admin/chapters/{CH}").json()
        check("extraction finished as draft", d["status"] == "draft", f"{d['status']} {d.get('error')}")
        check("chunks extracted", d["chunk_count"] > 40, str(d["chunk_count"]))
        check("exercises detected from the série", d["exercise_count"] >= 5, str(d["exercise_count"]))
        lost = [c for c in d["chunks"] if "lost_arrow" in c["flags"]]
        check("the known '<-' decoded as '-' defect is flagged", bool(lost), f"{len(lost)} flagged")
        check("publish is blocked with reasons (no topics, no pins)", len(d["publish_problems"]) >= 2, str(d["publish_problems"]))
        check("duplicate upload -> 409", up(CH).status_code == 409)

        as_user(student_id)
        check("student catalogue does not list a draft",
              CH not in {c["id"] for c in client.get("/chapters").json()})
        check("student: draft exercises -> 404", client.get(f"/chapters/{CH}/exercises").status_code == 404)
        as_user(admin_id)

        r = client.post(f"/admin/chapters/{CH}/publish")
        check("publish while incomplete -> 409 with problems",
              r.status_code == 409 and r.json()["detail"]["problems"], r.text[:200])

        # --- review edits --------------------------------------------------------------
        r = client.patch(f"/admin/chapters/{CH}", json={
            "title": "Chapitre de test", "topics": "les opérateurs {et} l'affectation"})
        check("edit title/topics", r.status_code == 200 and r.json()["topics"].startswith("les opérateurs"), r.text[:120])

        op = next((c for c in d["chunks"] if "Opérateur | Python" in c["content"]), None)
        check("found the operator table to pin", op is not None)
        r = client.patch(f"/admin/chapters/{CH}/chunks/{op['id']}", json={"pinned": True})
        check("pin without a label gets a default label", r.status_code == 200 and r.json()["pin_label"], r.text[:160])
        client.patch(f"/admin/chapters/{CH}/chunks/{op['id']}", json={"pin_label": "Opérateurs"})

        target = lost[0]
        fixed = "\n".join(
            line.replace(" - ", " ← ", 1) if cs._LOST_ARROW.match(line) else line
            for line in target["content"].split("\n")
        )
        r = client.patch(f"/admin/chapters/{CH}/chunks/{target['id']}", json={"content": fixed})
        check("fixing the arrow by hand clears the flag",
              r.status_code == 200 and "lost_arrow" not in r.json()["flags"], str(r.json().get("flags")))
        check("empty chunk content -> 422",
              client.patch(f"/admin/chapters/{CH}/chunks/{target['id']}", json={"content": ""}).status_code == 422)

        first_ex = d["exercises"][0]
        check("delete an exercise",
              client.delete(f"/admin/chapters/{CH}/exercises/{first_ex['id']}").status_code == 204)
        r = client.post(f"/admin/chapters/{CH}/exercises", json={"title": "Exercice bonus", "question": "Calcule le double d'un entier."})
        check("add an exercise", r.status_code == 201, r.text[:120])

        other = str(uuid.uuid4())
        check("unknown chunk -> 404",
              client.patch(f"/admin/chapters/{CH}/chunks/{other}", json={"pinned": True}).status_code == 404)

        # --- publish -----------------------------------------------------------------------
        d = client.get(f"/admin/chapters/{CH}").json()
        check("publish_problems now empty", d["publish_problems"] == [], str(d["publish_problems"]))
        r = client.post(f"/admin/chapters/{CH}/publish")
        check("publish -> 202", r.status_code == 202, r.text[:200])
        d = client.get(f"/admin/chapters/{CH}").json()
        check("published", d["status"] == "published" and d["published_at"], f"{d['status']} {d.get('error')}")

        points = scope_points()
        check("chapter embedded in Qdrant", len(points) > 40, str(len(points)))
        check("every point is scoped to this chapter",
              all((p.payload or {}).get("chapitre") == CH for p in points))
        pins = published_pins("2eme", CH)
        check("the pinned table is served as the reference sheet",
              [p.label for p in pins] == ["Opérateurs"], str([p.label for p in pins]))

        ctx = build_context("Ecrire un programme qui lit deux entiers et affiche leur somme.", "2eme", CH)
        own = [p for p in ctx.pinned if str(p.metadata.get("chapitre")) == CH]
        check("build_context works for the uploaded chapter",
              len(own) == 1 and len(ctx.retrieved) > 0, f"own pins={len(own)} extras={len(ctx.retrieved)}")
        check("the reference sheet is cumulative: chapter 1's sheet comes first",
              ctx.pinned[0].label.startswith("Ch. 1 — ") and ctx.pinned[-1].label == "Opérateurs",
              str([p.label for p in ctx.pinned]))
        check("retrieval never leaves the chapter",
              all(str(h.metadata.get("chapitre")) == CH for h in ctx.retrieved))
        check("the hand-fixed arrow is what got embedded",
              any(fixed == (p.payload or {}).get("content") for p in points))

        # --- student side -------------------------------------------------------------------
        as_user(student_id)
        cat = {c["id"]: c for c in client.get("/chapters").json()}
        check("student catalogue lists the published chapter as active",
              cat.get(CH, {}).get("status") == "active" and cat[CH]["title"] == "Chapitre de test", str(cat.get(CH)))
        check("chapter 1 still active and unchanged", cat.get("1", {}).get("status") == "active")
        exos = client.get(f"/chapters/{CH}/exercises").json()
        check("student exercises = the reviewed list",
              any(e["question"] == "Calcule le double d'un entier." for e in exos)
              and not any(e["question"] == first_ex["question"] for e in exos), f"{len(exos)} exercises")
        r = client.get(f"/chapters/{CH}/pdf")
        check("student can open the lesson PDF",
              r.status_code == 200 and r.headers["content-type"] == "application/pdf" and r.content[:5] == b"%PDF-")
        check("chapter 1 exercises still served", len(client.get("/chapters/1/exercises").json()) > 0)

        # --- draft edits stay invisible until republish ----------------------------------------
        as_user(admin_id)
        client.patch(f"/admin/chapters/{CH}", json={"title": "Titre modifié"})
        check("draft edit marks unpublished changes",
              client.get(f"/admin/chapters/{CH}").json()["has_unpublished_changes"] is True)
        as_user(student_id)
        check("students still see the published title",
              {c["id"]: c for c in client.get("/chapters").json()}[CH]["title"] == "Chapitre de test")

        as_user(admin_id)
        before = len(scope_points())
        client.post(f"/admin/chapters/{CH}/publish")
        d = client.get(f"/admin/chapters/{CH}").json()
        after = len(scope_points())
        check("republish applies the edit and clears the marker",
              d["status"] == "published" and not d["has_unpublished_changes"])
        check("republish does not duplicate points", after == before, f"{before} -> {after}")
        as_user(student_id)
        check("students now see the new title",
              {c["id"]: c for c in client.get("/chapters").json()}[CH]["title"] == "Titre modifié")

        # --- unpublish, recovery, delete -----------------------------------------------------------
        as_user(admin_id)
        r = client.post(f"/admin/chapters/{CH}/unpublish")
        check("unpublish -> draft, points removed",
              r.status_code == 200 and r.json()["status"] == "draft" and not scope_points(), r.text[:120])
        try:
            build_context("somme", "2eme", CH)
            check("an unpublished chapter cannot build context", False)
        except PinResolutionError:
            check("an unpublished chapter cannot build context", True)
        as_user(student_id)
        check("unpublished chapter leaves the student catalogue",
              CH not in {c["id"] for c in client.get("/chapters").json()})

        with session_scope() as s:
            s.get(UploadedChapter, CH).status = "processing"
        cs.recover_interrupted()
        with session_scope() as s:
            row = s.get(UploadedChapter, CH)
            check("a chapter stuck in processing is recovered as failed",
                  row.status == "failed" and "redémarrage" in (row.error or ""), row.status)
            row.status = "draft"

        as_user(admin_id)
        check("delete -> 204", client.delete(f"/admin/chapters/{CH}").status_code == 204)
        check("row, PDF and points all gone",
              client.get(f"/admin/chapters/{CH}").status_code == 404
              and not cs.pdf_path(CH).exists() and not scope_points())

        markdown_flow(client, as_user, admin_id, student_id)
    finally:
        cs.delete_chapter(CH)
        cs.delete_chapter(CH_MD)
        with session_scope() as s:
            for uid in users:
                row = s.get(User, uid)
                if row is not None:
                    s.delete(row)

    print(f"\n{failures} failure(s)")
    raise SystemExit(1 if failures else 0)


CH_MD = "95"
MD = """---
niveau: 2eme
chapitre: 95
titre: Conditionnelles (test markdown)
notions: la forme simple (Si … Alors), la forme alternative (Si … Sinon)
---

## I. Introduction

Les structures conditionnelles permettent de choisir un traitement selon une condition.

## II. La structure Si

### 📌 Syntaxe : forme alternative

```algorithme
Si <condition> Alors
    <Traitement 1>
Sinon
    <Traitement 2>
Fin Si
```

```python
if <condition> :
    <Traitement 1>
else :
    <Traitement 2>
```

### 1. Exemple

```algorithme
Si Montant > 100 Alors
    Rem ← Montant * 0.05
Sinon
    Rem ← 0
Fin Si
```

## Série d'exercices

### Exercice 1

Lire un entier et afficher s'il est pair ou impair.
"""


def markdown_flow(client, as_user, admin_id, student_id) -> None:
    from app.rag.context import build_context, published_pins

    cs.delete_chapter(CH_MD)
    as_user(admin_id)
    up = lambda body, name="cours.md", cid=CH_MD: client.post(  # noqa: E731
        "/admin/chapters", params={"id": cid, "filename": name}, content=body.encode("utf-8"),
        headers={"Content-Type": "text/markdown"})

    r = up(MD.replace("```algorithme\nSi Montant", "```\nSi Montant"))
    check("md: a course breaking the template -> 422 with line-numbered problems",
          r.status_code == 422 and any("Ligne" in p for p in r.json()["detail"]["problems"]), r.text[:200])
    check("md: ...and nothing was created", client.get(f"/admin/chapters/{CH_MD}").status_code == 404)
    check("md: header chapter must match the upload number",
          up(MD, cid="94").status_code == 422)
    check("md: a .txt that is not a PDF -> 415", up(MD, name="cours.txt").status_code == 415)

    r = up(MD)
    check("md: upload -> 202 (no title needed, it is in the header)", r.status_code == 202, r.text[:200])
    d = client.get(f"/admin/chapters/{CH_MD}").json()
    check("md: imported as draft, source_kind markdown",
          d["status"] == "draft" and d["source_kind"] == "markdown", f"{d['status']} {d.get('error')}")
    check("md: title and topics come from the header",
          d["title"] == "Conditionnelles (test markdown)" and d["topics"].startswith("la forme simple"))
    check("md: the 📌 section arrives already pinned and labelled",
          [c["pin_label"] for c in d["chunks"] if c["pinned"]] == ["Syntaxe : forme alternative"])
    check("md: exercises imported", [e["title"] for e in d["exercises"]] == ["Exercice 1"])
    check("md: no review flags on a clean course", d["flagged_count"] == 0,
          str([c["flags"] for c in d["chunks"] if c["flags"]]))
    check("md: ready to publish with no manual step", d["publish_problems"] == [], str(d["publish_problems"]))
    check("md: no student PDF yet", d["has_document"] is False)

    r = client.post(f"/admin/chapters/{CH_MD}/publish")
    d = client.get(f"/admin/chapters/{CH_MD}").json()
    check("md: published", r.status_code == 202 and d["status"] == "published", f"{d['status']} {d.get('error')}")
    pins = published_pins("2eme", CH_MD)
    check("md: reference sheet served to the RAG exactly as written",
          len(pins) == 1 and "Sinon\n    <Traitement 2>" in pins[0].content and "<-" not in pins[0].content)
    ctx = build_context("Lire un montant et calculer la remise.", "2eme", CH_MD)
    own = [p for p in ctx.pinned if str(p.metadata.get("chapitre")) == CH_MD]
    check("md: build_context works", len(own) == 1 and ctx.retrieved, f"retrieved={len(ctx.retrieved)}")
    check("md: earlier chapters' sheets are included (mod, Lire/Ecrire...)",
          any(p.label.startswith("Ch. 1 — ") for p in ctx.pinned))

    as_user(student_id)
    check("md: student PDF absent -> 503, not a crash", client.get(f"/chapters/{CH_MD}/pdf").status_code == 503)
    as_user(admin_id)
    pdf_bytes = PDF.read_bytes()
    r = client.put(f"/admin/chapters/{CH_MD}/document", content=pdf_bytes, headers={"Content-Type": "application/pdf"})
    check("md: attach the student PDF", r.status_code == 200 and r.json()["has_document"] is True, r.text[:160])
    check("md: ...without re-importing", client.get(f"/admin/chapters/{CH_MD}").json()["status"] == "published")
    check("md: document must be a real PDF",
          client.put(f"/admin/chapters/{CH_MD}/document", content=b"nope").status_code == 415)
    as_user(student_id)
    check("md: students can open it", client.get(f"/chapters/{CH_MD}/pdf").status_code == 200)

    as_user(admin_id)
    check("md: delete", client.delete(f"/admin/chapters/{CH_MD}").status_code == 204)
    check("md: both files removed",
          not cs.pdf_path(CH_MD).exists() and not cs.markdown_path(CH_MD).exists() and not rag_points(CH_MD))


def rag_points(chapter_id: str) -> list:
    from app.rag import rag_store

    return rag_store.scroll_scope("2eme", chapter_id)


if __name__ == "__main__":
    main()
