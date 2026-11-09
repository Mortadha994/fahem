"""Build the student-facing PDF of each course in courses/.

    python -m scripts.build_pdf                        # every importable chapter -> build/pdf/<id>.pdf
    python -m scripts.build_pdf --niveau 3eme --chapter 1
    python -m scripts.build_pdf --html-only            # write the HTML, skip the PDF (no browser needed)

The PDF is what the chapter page shows next to the exercises (the page falls
back to the course as text when a chapter has no PDF - see
app/routes/chapters.py). Its content is the course only, as a student reads it
(app/rag/course_markdown.student_text): no header, no author notes, no
exercises, which have their own tab.

Rendering: Markdown -> HTML (markdown-it-py) -> PDF with the machine's Edge or
Chrome in headless mode. A browser is used rather than a PDF library because
it handles what the courses need without a font to ship: ← ≤ ≠ √ π, tables,
code blocks that stay on a page. The file is named after the Fahem chapter id
(app/core/chapter_ids.py), which is how the platform finds it.

Installing: copy build/pdf/<id>.pdf to uploads/chapters/<id>.pdf in the
backend (see docs/importer-les-cours.md).
"""

from __future__ import annotations

import argparse
import html
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from markdown_it import MarkdownIt

from app.core.models import NIVEAUX
from app.rag import course_markdown
from scripts import import_courses as ic

BROWSERS = (
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/usr/bin/chromium",
    "/usr/bin/google-chrome",
)

CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10.5pt; line-height: 1.5; color: #1d2433; }
header { border-bottom: 2px solid #3b5bdb; margin-bottom: 14pt; padding-bottom: 8pt; }
header .kicker { color: #3b5bdb; font-size: 9pt; letter-spacing: .08em; text-transform: uppercase; }
header h1 { font-size: 20pt; line-height: 1.2; margin: 2pt 0 0; }
h2 { font-size: 15pt; margin: 18pt 0 6pt; color: #1b2a6b; break-after: avoid; }
h3 { font-size: 12.5pt; margin: 14pt 0 4pt; color: #243b9a; break-after: avoid; }
h4 { font-size: 11pt; margin: 10pt 0 3pt; break-after: avoid; }
p { margin: 0 0 7pt; orphans: 3; widows: 3; }
ul, ol { margin: 0 0 7pt; padding-left: 20pt; }
li { margin: 0 0 2pt; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9.4pt; background: #eef1f8; padding: 0 2pt; border-radius: 2pt; }
pre { background: #f5f7fb; border: 1px solid #d5dbea; border-left: 3px solid #3b5bdb; border-radius: 3pt;
      padding: 7pt 9pt; margin: 0 0 9pt; white-space: pre-wrap; overflow-wrap: anywhere; break-inside: avoid; }
pre code { background: none; padding: 0; font-size: 9.3pt; }
pre.algorithme { border-left-color: #2f9e44; }
pre.python { border-left-color: #f08c00; }
table { border-collapse: collapse; width: 100%; margin: 0 0 9pt; font-size: 9.6pt; }
th, td { border: 1px solid #b9c2d9; padding: 3pt 6pt; vertical-align: top; text-align: left; }
th { background: #e6ebf8; }
tr { break-inside: avoid; }
blockquote { margin: 0 0 8pt; padding: 3pt 10pt; border-left: 3px solid #adb5bd; color: #495057; }
em { color: #343a40; }
hr { border: 0; border-top: 1px solid #d5dbea; margin: 12pt 0; }
"""


def _md() -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": True}).enable("table")

    default = md.renderer.rules.get("fence")

    def fence(tokens, idx, options, env):
        token = tokens[idx]
        lang = (token.info or "").strip().split()[0] if token.info else ""
        cls = f' class="{html.escape(lang)}"' if lang else ""
        return f"<pre{cls}><code>{html.escape(token.content)}</code></pre>\n"

    md.renderer.rules["fence"] = fence if default is None or True else default
    return md


def render_html(title: str, niveau: str, number: str, body_markdown: str) -> str:
    kicker = f"{NIVEAUX.get(niveau, niveau)} · Chapitre {number}"
    return (
        '<!doctype html><html lang="fr"><head><meta charset="utf-8">'
        f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>"
        f'<header><div class="kicker">{html.escape(kicker)}</div><h1>{html.escape(title)}</h1></header>'
        f"{_md().render(body_markdown)}</body></html>"
    )


def find_browser(explicit: str | None) -> str | None:
    if explicit:
        return explicit if Path(explicit).exists() else None
    for candidate in BROWSERS:
        if Path(candidate).exists():
            return candidate
    return shutil.which("chromium") or shutil.which("google-chrome") or shutil.which("msedge")


def print_pdf(browser: str, html_path: Path, pdf_path: Path) -> None:
    pdf_path = pdf_path.resolve()  # the browser resolves a relative path against its own directory
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as profile:
        cmd = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            f"--user-data-dir={profile}",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            html_path.resolve().as_uri(),
        ]
        subprocess.run(cmd, check=True, timeout=180, capture_output=True)
    if not pdf_path.exists() or pdf_path.stat().st_size < 2000:
        raise RuntimeError(f"le navigateur n'a pas produit de PDF valide : {pdf_path}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=ic.ROOT)
    ap.add_argument("--niveau", choices=sorted(NIVEAUX))
    ap.add_argument("--chapter", type=int)
    ap.add_argument("--out", type=Path, default=Path("build/pdf"))
    ap.add_argument("--browser", help="path to msedge / chrome (default: auto-detect)")
    ap.add_argument("--html-only", action="store_true", help="write the HTML next to the PDFs, build no PDF")
    ap.add_argument("--include-builtin", action="store_true", help="also build 2ème chapter 1 (id 1)")
    args = ap.parse_args(argv)

    browser = None if args.html_only else find_browser(args.browser)
    if not args.html_only and browser is None:
        print("aucun navigateur trouvé (Edge/Chrome) ; --browser <chemin> ou --html-only")
        return 2

    failures = 0
    for ch in ic.discover(args.root, args.niveau, args.chapter):
        ic.check(ch)
        if ch.course is None:
            print(f"- {ch.label}: ignoré ({'; '.join(ch.problems) or 'rien à construire'})")
            continue
        if ch.skip and not args.include_builtin:
            print(f"- {ch.label}: ignoré ({ch.skip})")
            continue
        body = course_markdown.student_text(ch.merged)
        page = render_html(ch.course.titre, ch.niveau, str(ch.number), body)
        html_path = args.out / f"{ch.platform_id}.html"
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(page, encoding="utf-8")
        if args.html_only:
            print(f"- {ch.label}: id {ch.platform_id} → {html_path}")
            continue
        pdf_path = args.out / f"{ch.platform_id}.pdf"
        try:
            print_pdf(browser, html_path, pdf_path)
        except Exception as exc:  # noqa: BLE001 - report and carry on with the other chapters
            failures += 1
            print(f"- {ch.label}: ÉCHEC ({exc})")
            continue
        print(f"- {ch.label}: id {ch.platform_id} → {pdf_path} ({pdf_path.stat().st_size // 1024} Ko)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
