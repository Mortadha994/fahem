#!/bin/sh
# Start order: database schema -> redis -> nginx (so the Space answers on 7860
# straight away) -> the backend, in the foreground, so its death ends the
# container and Hugging Face restarts it.
set -e
cd /home/user/app

: "${DATABASE_URL:?set DATABASE_URL (the Neon connection string) in the Space secrets}"
: "${QDRANT_URL:?set QDRANT_URL (the Qdrant Cloud cluster URL) in the Space secrets}"
: "${GROQ_API_KEY:?set GROQ_API_KEY in the Space secrets}"
: "${SESSION_SECRET_KEY:?set SESSION_SECRET_KEY in the Space secrets}"

# The public address is the Space's own *.hf.space URL unless one is given.
if [ -z "$APP_BASE_URL" ] && [ -n "$SPACE_HOST" ]; then
    export APP_BASE_URL="https://$SPACE_HOST"
fi
export PUBLIC_API_URL="${PUBLIC_API_URL:-$APP_BASE_URL/api}"

echo "[start] database migrations"
alembic upgrade head

echo "[start] redis"
redis-server --save "" --appendonly no --dir /tmp --daemonize yes >/dev/null

echo "[start] nginx on :7860"
nginx -c /home/user/app/nginx.conf -e /dev/stderr &

echo "[start] backend on :8000"
exec uvicorn app.main:app --host 127.0.0.1 --port 8000
