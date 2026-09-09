"""Engine and session factory for the relational store.

Deliberately minimal and not imported by api.py: Phase 0a stands the database
up without wiring it into any request path. The only callers today are Alembic
(via alembic/env.py, for the URL and metadata) and test_db.py.

Kept separate from models.py so that importing the models - which Alembic must
do to autogenerate - does not construct an engine or open a connection as a
side effect of the import.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import DATABASE_URL

# pool_pre_ping because the common local failure is a Postgres container
# restarted underneath a long-lived engine: without it the first query after a
# restart fails on a dead socket instead of transparently reconnecting.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Transactional scope: commit on success, roll back on any exception.

    expire_on_commit=False above is what lets a caller keep reading attributes
    off an object after the block exits - otherwise every attribute access
    after commit would emit a fresh SELECT against a closed session.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
