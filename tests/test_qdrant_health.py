"""Tests for the Qdrant connection retries (rag_store.get_client) and the deep
health check (/health/qdrant).

Needs only Qdrant (the compose stack's, or any reachable QDRANT_URL):

    docker compose --env-file env/.env --project-directory . -f docker/docker-compose.yml exec -T backend python -m tests.test_qdrant_health
"""

from __future__ import annotations

import functools
import socket
import struct
import threading

from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from app.rag import rag_store

results: list[bool] = []


def check(name: str, ok: bool, detail: object = "") -> None:
    results.append(bool(ok))
    print(
        ("[PASS] " if ok else "[FAIL] ")
        + name
        + (f"  -> {detail!r}" if not ok and detail != "" else "")
    )


def resetting_server() -> tuple[int, dict]:
    """A local port that resets every connection mid TLS handshake, the way
    Qdrant Cloud did in production ("[Errno 104] Connection reset by peer")."""
    seen = {"connections": 0}
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen()

    def serve() -> None:
        while True:
            conn, _ = srv.accept()
            seen["connections"] += 1
            conn.recv(1024)  # the ClientHello
            conn.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
            conn.close()

    threading.Thread(target=serve, daemon=True).start()
    return srv.getsockname()[1], seen


def test_connection_retries() -> None:
    port, seen = resetting_server()
    # The real get_client, minus the client's background version probe, which
    # would open connections of its own and skew the count.
    original = rag_store.QdrantClient
    rag_store.QdrantClient = functools.partial(original, check_compatibility=False)
    try:
        client = rag_store.get_client(f"https://localhost:{port}")
    finally:
        rag_store.QdrantClient = original
    try:
        client.get_collections()
        check("a server that always resets still fails in the end", False, "no error raised")
    except Exception as exc:
        check(
            "a server that always resets still fails in the end",
            "reset" in str(exc).lower(),
            exc,
        )
    expected = 1 + rag_store.QDRANT_CONNECT_RETRIES
    check(
        f"the connection was attempted {expected} times",
        seen["connections"] == expected,
        seen["connections"],
    )


def test_health_endpoint() -> None:
    from app import main

    app = FastAPI()
    app.get("/health/qdrant")(main.health_qdrant)
    http = TestClient(app)

    r = http.get("/health/qdrant")
    body = r.json()
    if rag_store.get_client().collection_exists(rag_store.COLLECTION_NAME):
        check("200 with the point count when Qdrant answers", r.status_code == 200, body)
        check("the count is a number", isinstance(body.get("points"), int), body)
    else:
        check("503 when the collection is missing", r.status_code == 503, body)

    default = rag_store.get_client.__defaults__
    rag_store.get_client.__defaults__ = ("http://127.0.0.1:1",)
    try:
        r = http.get("/health/qdrant")
    finally:
        rag_store.get_client.__defaults__ = default
    check("503 when Qdrant is unreachable", r.status_code == 503, r.json())
    check(
        "no error details leak in the body",
        r.json() == {"status": "error", "qdrant": "unavailable"},
        r.json(),
    )

    check(
        "/health stays independent of Qdrant",
        isinstance(main.health(), dict) and not isinstance(main.health(), Response),
    )


if __name__ == "__main__":
    test_connection_retries()
    test_health_endpoint()
    print(f"\n{sum(results)}/{len(results)} passed")
    raise SystemExit(0 if all(results) else 1)
