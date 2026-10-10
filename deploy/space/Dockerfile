# Fahem on a Hugging Face Space (free tier): ONE container with
#   nginx   :7860  the built UI + /api -> the backend (same origin, so the
#                  session cookie is first-party and CORS is not involved)
#   uvicorn :8000  the FastAPI backend
#   redis   :6379  rate-limit counters and the Groq queue (no persistence)
# Postgres (Neon) and Qdrant (Qdrant Cloud) are external; see deploy/space/README.md.
#
# Hugging Face runs the image as uid 1000, not root, and wipes the disk on
# every restart - hence the non-root user, nginx paths under /tmp, and
# MIRROR_UPLOADS_TO_DB (uploaded PDFs live in Postgres too).

FROM node:22-alpine AS ui
WORKDIR /ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci
COPY ui/ ./
# The UI calls the API on its own origin. The Google client id is the only
# build-time value; set it as a Space *variable* (not a secret) so it reaches
# the build.
ARG VITE_GOOGLE_CLIENT_ID=
ENV VITE_API_URL=/api \
    VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID
RUN npm run build

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/home/user \
    HF_HOME=/home/user/.cache/huggingface \
    CHAPTER_UPLOAD_DIR=/home/user/app/uploads/chapters \
    MIRROR_UPLOADS_TO_DB=true \
    REDIS_URL=redis://127.0.0.1:6379 \
    TRUSTED_CLIENT_IP_HEADER=X-Forwarded-For \
    SESSION_COOKIE_SECURE=true

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx redis-server \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 user
WORKDIR /home/user/app

# CPU-only torch first (the default wheel drags in ~2.5 GB of GPU libraries).
RUN pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        torch
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# WORKDIR created the folder as root; the app writes uploads under it.
RUN mkdir -p uploads/chapters && chown -R user:user /home/user/app

USER user

# The embedding model is baked in: a cold start of a Space that slept must not
# download it again.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"
# Baked above: never ask the Hub again at start-up (faster, and no rate limit).
ENV HF_HUB_OFFLINE=1

COPY --chown=user app ./app
COPY --chown=user scripts ./scripts
COPY --chown=user alembic ./alembic
COPY --chown=user alembic.ini ./
# Chapter 1's hand-corrected exercise list and lesson PDF (gitignored in the
# main repository; make_bundle.py copies them in when it finds them).
COPY --chown=user runtime/ ./
COPY --chown=user deploy/nginx.conf deploy/start.sh ./
COPY --chown=user --from=ui /ui/dist ./ui-dist
RUN chmod +x start.sh

EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"

CMD ["./start.sh"]
