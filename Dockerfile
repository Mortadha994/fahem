# Backend: FastAPI + the RAG pipeline.
#
# 3.12 rather than the 3.14 in .venv: requirements.txt pins no interpreter and
# no torch version, and 3.12 is the newest with full prebuilt wheel coverage
# for torch/sentence-transformers. Nothing in the code needs 3.14.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # sentence-transformers downloads the embedding model on first use. Point
    # its cache at a named volume so a container recreate does not re-download.
    HF_HOME=/cache/huggingface

WORKDIR /app

# torch is installed first, from the CPU-only index. sentence-transformers
# would otherwise pull the default CUDA build - ~2.5GB of GPU libraries that
# nothing in this compose stack can reach.
RUN pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        torch

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Source only. chunks.json and data/ are runtime state and arrive as bind
# mounts; the vector store lives in the qdrant service - see
# docker-compose.yml.
COPY *.py ./

# Migrations. Separate COPY lines because `COPY *.py` above matches neither the
# ini file nor the alembic/ directory, so `alembic upgrade head` inside the
# container would fail on a missing config rather than a missing database.
COPY alembic.ini ./
COPY alembic ./alembic

EXPOSE 8000

# curl is not in -slim, so the check goes through the interpreter that is.
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"

# Single process, no --reload: /solve/stream is a generator-backed
# StreamingResponse, and a reloader restart mid-stream would truncate it.
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
