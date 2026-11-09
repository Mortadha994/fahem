#!/bin/sh
# Start order: database schema -> redis -> nginx (so the host sees the port
# open straight away) -> the backend, in the foreground, so its death ends the
# container and the host restarts it.
set -e
cd /home/user/app

: "${DATABASE_URL:?set DATABASE_URL (the Neon connection string) in the host's environment}"
: "${QDRANT_URL:?set QDRANT_URL (the Qdrant Cloud cluster URL) in the host's environment}"
: "${GROQ_API_KEY:?set GROQ_API_KEY in the host's environment}"
: "${SESSION_SECRET_KEY:?set SESSION_SECRET_KEY in the host's environment}"

# The public address: given explicitly, or the one the host announces
# (Render: RENDER_EXTERNAL_URL).
export APP_BASE_URL="${APP_BASE_URL:-${RENDER_EXTERNAL_URL:-http://localhost:$PORT}}"
export PUBLIC_API_URL="${PUBLIC_API_URL:-$APP_BASE_URL/api}"

echo "[start] database migrations"
alembic upgrade head

echo "[start] redis"
redis-server --save "" --appendonly no --dir /tmp --maxmemory 32mb --daemonize yes >/dev/null

echo "[start] nginx on :$PORT"
sed "s/__PORT__/$PORT/" nginx.conf > /tmp/nginx.conf
nginx -c /tmp/nginx.conf -e /dev/stderr &

echo "[start] backend on :8000"
exec uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
