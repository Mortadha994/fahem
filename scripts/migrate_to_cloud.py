"""One-time copy of Fahem's local data to the cloud services.

    # Qdrant: every point (vectors included - nothing is re-embedded)
    python -m scripts.migrate_to_cloud qdrant \\
        --source http://localhost:6333 \\
        --target https://<cluster>.cloud.qdrant.io:6333 --target-key <api key>

    # Uploaded chapter files (PDF / Markdown / exercise supplements) into the
    # target database's stored_uploads table, from a folder copied out of the
    # backend container (docker cp fahem-backend-1:/app/uploads/chapters ./u):
    python -m scripts.migrate_to_cloud uploads --folder ./u \\
        --database "postgresql://user:pass@host/db?sslmode=require"

Both commands are safe to repeat: points are upserted by id and files by name.
The Postgres data itself moves with pg_dump / psql (deploy/space/README.md).
"""

from __future__ import annotations

import argparse
from pathlib import Path

BATCH = 64


def copy_qdrant(source: str, target: str, target_key: str | None, collection: str) -> int:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qm

    src = QdrantClient(url=source)
    dst = QdrantClient(url=target, api_key=target_key or None)

    info = src.get_collection(collection)
    if not dst.collection_exists(collection):
        dst.create_collection(
            collection_name=collection, vectors_config=info.config.params.vectors
        )
        print(f"created collection {collection!r} on the target")

    copied = 0
    offset = None
    while True:
        points, offset = src.scroll(
            collection, limit=BATCH, offset=offset, with_payload=True, with_vectors=True
        )
        if points:
            dst.upsert(
                collection,
                points=[
                    qm.PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in points
                ],
            )
            copied += len(points)
            print(f"  {copied} points copied", end="\r")
        if offset is None:
            break
    expected = src.count(collection, exact=True).count
    got = dst.count(collection, exact=True).count
    print(f"\nsource {expected} points, target {got} points")
    if got < expected:
        raise SystemExit("the target has fewer points than the source - run it again")
    return copied


def copy_uploads(folder: Path, database: str) -> int:
    import sqlalchemy as sa

    for plain in ("postgresql://", "postgres://"):
        if database.startswith(plain):
            database = "postgresql+psycopg://" + database[len(plain) :]
    engine = sa.create_engine(database)
    sent = 0
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "CREATE TABLE IF NOT EXISTS stored_uploads ("
                " name varchar(128) PRIMARY KEY, data bytea NOT NULL,"
                " updated_at timestamptz NOT NULL DEFAULT now())"
            )
        )
        for path in sorted(folder.iterdir()):
            if not path.is_file() or path.suffix == ".part":
                continue
            conn.execute(
                sa.text(
                    "INSERT INTO stored_uploads (name, data) VALUES (:n, :d) "
                    "ON CONFLICT (name) DO UPDATE SET data = :d, updated_at = now()"
                ),
                {"n": path.name, "d": path.read_bytes()},
            )
            sent += 1
            print(f"  {path.name} ({path.stat().st_size // 1024} KB)")
    print(f"{sent} file(s) stored")
    return sent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    q = sub.add_parser("qdrant", help="copy the vector collection")
    q.add_argument("--source", default="http://localhost:6333")
    q.add_argument("--target", required=True)
    q.add_argument("--target-key", default=None)
    q.add_argument("--collection", default="algorithmique")

    u = sub.add_parser("uploads", help="copy uploaded chapter files into the database")
    u.add_argument("--folder", type=Path, required=True)
    u.add_argument("--database", required=True)

    args = parser.parse_args()
    if args.cmd == "qdrant":
        copy_qdrant(args.source, args.target, args.target_key, args.collection)
    else:
        copy_uploads(args.folder, args.database)


if __name__ == "__main__":
    main()
