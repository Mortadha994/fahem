"""SQLAlchemy models for the relational store: users, chat sessions, chat
messages.

Nothing in the running app reads or writes these yet. This is Phase 0a - the
schema and migrations exist so that later phases (auth, then server-side
session persistence) have a foundation to build on. `api.py`'s endpoints,
the checker, the gatekeeper and the RAG pipeline are all untouched, and
`ui/src/lib/sessions.js` still keeps chat history in localStorage.

Why the message rows carry checker/grounding columns even though nothing
writes them yet: the localStorage version stores a badge status computed once
at generation time and never recomputed, so fixing a checker bug does not
retroactively correct old sessions. Persisting the checker verdict and the
grounding excerpts *alongside* the message they describe is what eventually
makes that fixable - the data is queryable rather than frozen in a browser
blob. Reading it back is Phase 1's job.

Flat module, not a `db/` package: the rest of the repo is flat (config.py,
checker.py, gatekeeper.py), and the whole data layer is this file plus db.py.
Alembic keeps its own directory because it insists on one.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Google's `sub` claim, not the email address: a user can change the email
    # on their Google account, but `sub` is stable for the life of the account.
    # Keying on email would silently orphan a user's history after a rename.
    google_sub: Mapped[str] = mapped_column(Text, unique=True, nullable=False)

    email: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_name: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # Nullable because a row is created at first sign-in, before any *return*
    # visit exists to record.
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    sessions: Mapped[list[ChatSession]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<User {self.id} {self.email!r}>"


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Free text rather than an enum: these are corpus scope keys ("2eme", "1")
    # that the store already treats as strings, and a new chapter should not
    # need a schema migration to exist.
    niveau: Mapped[str] = mapped_column(String(32), nullable=False)
    chapitre: Mapped[str] = mapped_column(String(32), nullable=False)

    # The sidebar's short preview line. Nullable because a session exists from
    # the moment it is created, before the first message gives it a title.
    title: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="sessions")
    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ChatMessage.created_at",
    )

    __table_args__ = (
        # The sidebar query is "this user's sessions, newest first".
        Index("ix_chat_sessions_user_id_updated_at", "user_id", "updated_at"),
    )

    def __repr__(self) -> str:
        return f"<ChatSession {self.id} {self.niveau}/{self.chapitre}>"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Persisted as computed at generation time, deliberately never recomputed
    # on read - the verdict belongs to the answer as it was produced. Left
    # unconstrained (no CHECK) on purpose: the frontend already uses
    # "streaming", "stopped" and "error" alongside the clean/warned/none set,
    # and Phase 1 may well persist those too. A CHECK here would buy little and
    # cost an ALTER later.
    checker_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    checker_warnings: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # The pinned tables and retrieved excerpts backing the grounding strip,
    # stored with the message rather than recomputed: retrieval is not
    # deterministic across corpus changes, so re-running it later would show a
    # student different sources than the answer was actually built on.
    grounding_excerpts: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[ChatSession] = relationship(back_populates="messages")

    __table_args__ = (
        # Closed set, unlike checker_status: a message is from the student or
        # from the tutor, and a third value would be a bug worth failing on.
        CheckConstraint("role IN ('user', 'assistant')", name="ck_chat_messages_role"),
        Index("ix_chat_messages_session_id_created_at", "session_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ChatMessage {self.id} {self.role}>"
