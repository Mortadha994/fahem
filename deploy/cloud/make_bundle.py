"""Assemble the folder the cloud host builds from.

    python deploy/cloud/make_bundle.py --out build/cloud [--runtime-from <main checkout>]

The host (Render) builds from its own private git repository, so what it needs
is copied into one folder, laid out the way deploy/cloud/Dockerfile expects:

    Dockerfile  README.md  requirements-slim.txt
    app/  scripts/  alembic/  alembic.ini  ui/
    deploy/nginx.conf  deploy/start.sh
    runtime/    chunks.json, sample_problems.json, data/<lesson pdf>  (the
                gitignored files of chapter 1, taken from --runtime-from)

Nothing secret goes in: keys are environment variables set on the host
(deploy/cloud/README.md).
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

README_HEADER = """# Fahem — paquet de déploiement

Généré par `deploy/cloud/make_bundle.py` dans le dépôt principal. Ne pas
modifier ici : regénérer puis pousser.
"""

# Torch-free: the embedding model runs on onnxruntime (EMBEDDING_BACKEND=onnx).
SLIM_EXTRA = ["onnxruntime>=1.18", "sentencepiece>=0.2", "huggingface_hub>=0.23", "numpy>=1.26"]


def slim_requirements(text: str) -> str:
    kept = [
        line
        for line in text.splitlines()
        if not line.strip().lower().startswith(("sentence-transformers", "torch"))
    ]
    return "\n".join(kept + ["", "# onnx embedding backend (make_bundle.py)"] + SLIM_EXTRA) + "\n"

IGNORE = shutil.ignore_patterns(
    "__pycache__", "*.pyc", "node_modules", "dist", ".venv", ".pytest_cache", "tests"
)


def find_runtime(start: Path) -> Path | None:
    """The checkout that holds chunks.json: this one, or one of its parents (a
    worktree lives under .claude/worktrees/ of the main checkout)."""
    for folder in (start, *start.parents):
        if (folder / "chunks.json").exists():
            return folder
    return None


def lf(path: Path) -> None:
    path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", type=Path, default=ROOT / "build" / "cloud")
    parser.add_argument("--runtime-from", type=Path, default=None)
    args = parser.parse_args()

    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    # Emptied, except its .git: the folder is a clone of the deploy repository.
    for child in out.iterdir():
        if child.name == ".git":
            continue
        shutil.rmtree(child) if child.is_dir() else child.unlink()

    for name in ("app", "scripts", "alembic", "ui"):
        shutil.copytree(ROOT / name, out / name, ignore=IGNORE)
    shutil.copy2(ROOT / "alembic.ini", out / "alembic.ini")
    (out / "requirements-slim.txt").write_text(
        slim_requirements((ROOT / "requirements.txt").read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    (out / ".gitattributes").write_text("*.sh text eol=lf\n", encoding="utf-8")

    (out / "deploy").mkdir()
    shutil.copy2(HERE / "Dockerfile", out / "Dockerfile")
    shutil.copy2(HERE / "nginx.conf", out / "deploy" / "nginx.conf")
    shutil.copy2(HERE / "start.sh", out / "deploy" / "start.sh")
    lf(out / "deploy" / "start.sh")  # a CRLF shebang line makes the script unrunnable
    (out / "README.md").write_text(README_HEADER, encoding="utf-8")
    (out / ".dockerignore").write_text("**/node_modules\n**/__pycache__\n", encoding="utf-8")

    runtime = out / "runtime"
    runtime.mkdir()
    (runtime / ".keep").write_text("", encoding="utf-8")
    source = args.runtime_from or find_runtime(ROOT)
    if source is None:
        print("WARNING: chunks.json not found - chapter 1's built-in exercises will be missing")
    else:
        for name in ("chunks.json", "sample_problems.json"):
            if (source / name).exists():
                shutil.copy2(source / name, runtime / name)
        lesson = next(source.glob("data/**/Chap1_Structures_donnees_simples.pdf"), None)
        if lesson is not None:
            (runtime / "data").mkdir()
            shutil.copy2(lesson, runtime / "data" / lesson.name)

    size = sum(f.stat().st_size for f in out.rglob("*") if f.is_file()) / 1e6
    print(f"bundle ready: {out}  ({size:.1f} MB)")
    for p in sorted(runtime.rglob("*")):
        if p.is_file() and p.name != ".keep":
            print("  runtime:", p.relative_to(out))


if __name__ == "__main__":
    main()
