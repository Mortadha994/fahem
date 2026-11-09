# Fahem on a free container host (Render's free web service: 512 MB of RAM).
# ONE container:
#   nginx   :$PORT  the built UI + /api -> the backend (same origin, so the
#                   session cookie is first-party and CORS is not involved)
#   uvicorn :8000   the FastAPI backend
#   redis   :6379   rate-limit counters and the Groq queue (no persistence)
# Postgres (Neon) and Qdrant (Qdrant Cloud) are external; see deploy/cloud/README.md.
#
# 512 MB is why there is no torch here: the embedding model runs on
# onnxruntime (EMBEDDING_BACKEND=onnx, app/rag/onnx_embedder.py). The disk is
# not kept across deploys, hence MIRROR_UPLOADS_TO_DB.

FROM node:22-alpine AS ui
WORKDIR /ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci
COPY ui/ ./
# The UI calls the API on its own origin. The Google client id is the only
# build-time value (not a secret: it ships in the bundle by design).
ARG VITE_GOOGLE_CLIENT_ID=
ENV VITE_API_URL=/api \
    VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID
RUN npm run build

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/home/user \
    HF_HOME=/home/user/.cache/huggingface \
    EMBEDDING_BACKEND=onnx \
    CHAPTER_UPLOAD_DIR=/home/user/app/uploads/chapters \
    MIRROR_UPLOADS_TO_DB=true \
    REDIS_URL=redis://127.0.0.1:6379 \
    TRUSTED_CLIENT_IP_HEADER=X-Forwarded-For \
    SESSION_COOKIE_SECURE=true \
    PORT=10000

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx redis-server \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
WORKDIR /home/user/app

# requirements.txt without sentence-transformers (and so without torch), plus
# onnxruntime - make_bundle.py writes it.
COPY requirements-slim.txt ./
RUN pip install --no-cache-dir -r requirements-slim.txt

# WORKDIR created the folder as root; the app writes uploads under it.
RUN mkdir -p uploads/chapters && chown -R user:user /home/user/app

USER user

COPY --chown=user app ./app
# The quantized ONNX model and its tokenizer are baked in, so a cold start
# (the free plan sleeps after 15 idle minutes) never downloads them.
RUN python -c "from app.rag.onnx_embedder import model_files; print(model_files())"
ENV HF_HUB_OFFLINE=1

COPY --chown=user scripts ./scripts
COPY --chown=user alembic ./alembic
COPY --chown=user alembic.ini ./
# Chapter 1's hand-corrected exercise list and lesson PDF (gitignored in the
# main repository; make_bundle.py copies them in when it finds them).
COPY --chown=user runtime/ ./
COPY --chown=user deploy/nginx.conf deploy/start.sh ./
COPY --chown=user --from=ui /ui/dist ./ui-dist
RUN chmod +x start.sh

EXPOSE 10000
CMD ["./start.sh"]
