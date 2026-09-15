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
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Index,
    String,
    Text,
    false,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# --- roles (Phase 7) ----------------------------------------------------------
#
# The closed set of values users.role may hold. Named constants rather than
# bare strings at each call site so that a typo is an ImportError here instead
# of a comparison that is silently always false - which, for an authorisation
# check, is the difference between a crash and a wrong answer.

ROLE_STUDENT = "student"
ROLE_ADMIN = "admin"
ROLES = (ROLE_STUDENT, ROLE_ADMIN)

# --- plans --------------------------------------------------------------------
#
# The account's subscription tier. Nothing is billed yet and every account is
# free; the column exists so the Groq queue (llm_queue.py) can already read a
# priority from it, and a paid tier can later jump the queue without a schema
# change. Same closed-set pattern as the role.

PLAN_FREE = "free"
PLAN_PAID = "paid"
PLANS = (PLAN_FREE, PLAN_PAID)


# --- student profile ------------------------------------------------------------
#
# The student's year and section, asked once right after the first sign-in.
# Closed sets, like the role, so a typo can never be stored and silently
# match nothing. The keys are what the API and the database hold; the labels
# are what the student reads.
#
# Tunisian secondary school: the 2ème année has four of these sections (no
# Math, no Technique - those open in 3ème); 3ème and the bac year share all six.

NIVEAUX = {"2eme": "2ème année", "3eme": "3ème année", "bac": "Bac"}
SECTIONS = {
    "informatique": "Informatique",
    "math": "Mathématiques",
    "sciences": "Sciences expérimentales",
    "lettres": "Lettres",
    "technique": "Sciences techniques",
    "eco": "Économie et gestion",
}
SECTIONS_BY_NIVEAU = {
    "2eme": ("informatique", "sciences", "lettres", "eco"),
    "3eme": tuple(SECTIONS),
    "bac": tuple(SECTIONS),
}


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Google's `sub` claim, not the email address: a user can change the email
    # on their Google account, but `sub` is stable for the life of the account.
    # Keying on email would silently orphan a user's history after a rename.
    # Nullable since Phase 4: a password account has no Google identity.
    google_sub: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)

    # Required since Phase 4 - it is how a password account is found at login.
    # Unique only among password accounts (see __table_args__): a Google account
    # and a password account are separate identities and may share an address.
    # They are never linked by it - that would let whoever registers a victim's
    # address with a password inherit the victim's later Google sign-in.
    email: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Argon2id PHC string (algorithm, parameters and salt are inside it). Null
    # for a Google account.
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Phase 7. A text role, not an is_admin boolean, and the reason is that a
    # third tier is genuinely plausible for this product: a teacher who can see
    # a class's exercises but must not touch accounts or spend. With a boolean
    # that arrives as a second column and every check becomes "which of the two
    # flags", with an ordering question nobody wrote down. One column with a
    # closed set answers it in the schema, and reads correctly in a bare
    # `SELECT id, email, role FROM users` during an incident.
    #
    # The CHECK is what makes the set closed: a typo'd 'admln' would otherwise
    # be stored happily and would simply never match, i.e. fail open into a
    # locked-out user rather than loudly.
    role: Mapped[str] = mapped_column(
        Text, nullable=False, default=ROLE_STUDENT, server_default=ROLE_STUDENT
    )

    # The subscription tier (see PLANS). Defaults to free in the database as
    # well as here, for the same reason the role does: a row written by
    # anything that does not know about plans must land on the unprivileged
    # value. Read by llm_queue.priority_for; not enforced anywhere yet.
    plan: Mapped[str] = mapped_column(
        String(16), nullable=False, default=PLAN_FREE, server_default=PLAN_FREE
    )

    # Set when the address owner clicks Fahem's verification link, or completes
    # a password reset (which proves the same thing). Tracked, deliberately not
    # enforced anywhere. Google accounts stay false: Fahem never sent them a link,
    # and Google's own claim is not recorded here.
    email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )

    # Session tokens issued before this instant are rejected. A password reset
    # sets it, so a reset actually evicts whoever else was signed in - the one
    # moment a user most expects that. Null means no cut-off.
    sessions_valid_after: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # The student profile (see NIVEAUX / SECTIONS). Null until the student
    # answers the one-time question after signing in - which is exactly how
    # the client knows to ask it. Set together or not at all (CHECK below).
    niveau: Mapped[str | None] = mapped_column(Text, nullable=True)
    section: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # Nullable because a row is created at first sign-in, before any *return*
    # visit exists to record.
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sessions: Mapped[list[ChatSession]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        # Defense in depth: the application never creates a user with no way to
        # sign in, and this makes that a database guarantee as well.
        CheckConstraint(
            "google_sub IS NOT NULL OR password_hash IS NOT NULL",
            name="ck_users_has_credential",
        ),
        # The role set, closed in the database as well as in the constants
        # above. See the column's comment for why this is not a boolean.
        CheckConstraint(
            "role IN ('student', 'admin')",
            name="ck_users_role",
        ),
        # The plan set, closed in the database like the role.
        CheckConstraint(
            "plan IN ('free', 'paid')",
            name="ck_users_plan",
        ),
        CheckConstraint(
            "niveau IS NULL OR niveau IN ('2eme', '3eme', 'bac')",
            name="ck_users_niveau",
        ),
        CheckConstraint(
            "section IS NULL OR section IN "
            "('informatique', 'math', 'sciences', 'lettres', 'technique', 'eco')",
            name="ck_users_section",
        ),
        CheckConstraint(
            "(niveau IS NULL) = (section IS NULL)",
            name="ck_users_profile_pair",
        ),
        # Case-insensitive, and only among password accounts - the one place an
        # email is used to find an account.
        Index(
            "uq_users_password_email",
            text("lower(email)"),
            unique=True,
            postgresql_where=text("password_hash IS NOT NULL"),
        ),
    )

    def __repr__(self) -> str:
        return f"<User {self.id} {self.email!r}>"


class AuthToken(Base):
    """A single-use emailed token: email verification or password reset.

    One table with a `purpose` column rather than two tables: both kinds have
    exactly the same columns and lifecycle (issue, email, consume once,
    expire), and the purpose is part of the consume query, so a verification
    token can never be spent as a reset token.

    Only a SHA-256 of the token is stored. The token itself is 256 bits of
    randomness, so a fast unsalted hash is safe here (there is nothing to
    dictionary-attack) - and unlike a salted password hash it can be looked up
    through an index. A database leak therefore yields no usable links.
    """

    __tablename__ = "auth_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    purpose: Mapped[str] = mapped_column(String(32), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Set when the token is spent - or superseded by a newer one of the same
    # purpose. Either way: no longer usable.
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "purpose IN ('verify_email', 'reset_password')", name="ck_auth_tokens_purpose"
        ),
        Index("ix_auth_tokens_user_id_purpose", "user_id", "purpose"),
    )

    def __repr__(self) -> str:
        return f"<AuthToken {self.id} {self.purpose}>"


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
        order_by="ChatMessage.position",
    )

    __table_args__ = (
        # The sidebar query is "this user's sessions, newest first".
        Index("ix_chat_sessions_user_id_updated_at", "user_id", "updated_at"),
    )

    def __repr__(self) -> str:
        return f"<ChatSession {self.id} {self.niveau}/{self.chapitre}>"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    # Order within the session. A discussion is saved as a whole, so its
    # messages are inserted in one transaction and share a created_at - that
    # timestamp cannot order them, this can.
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    # What the chat shows that is not part of the answer itself: an error
    # sentence, the attached file's name and kind, the client's message id.
    # Kept loose on purpose - display state, not something to query.
    extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

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


# --- AI monitoring ----------------------------------------------------------------
#
# One row per Groq call, written by llm_usage.py, read by the admin console's
# "IA" page. Kept small and flat on purpose: it is a time series queried by
# created_at ranges, pruned after LLM_USAGE_RETENTION_DAYS. No user id - the
# console measures the service's load, not who spent it.

LLM_CALL_OK = "ok"
LLM_CALL_RATE_LIMITED = "rate_limited"  # a 429 reached the caller
LLM_CALL_QUEUE_TIMEOUT = "queue_timeout"  # no slot within the request's budget
LLM_CALL_ERROR = "error"  # any other failure (HTTP 5xx, network, parse)
LLM_CALL_CANCELLED = "cancelled"  # the student left before it finished
LLM_CALL_STATUSES = (
    LLM_CALL_OK,
    LLM_CALL_RATE_LIMITED,
    LLM_CALL_QUEUE_TIMEOUT,
    LLM_CALL_ERROR,
    LLM_CALL_CANCELLED,
)


class LlmCall(Base):
    __tablename__ = "llm_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    # llm_queue's kinds: gatekeeper | solve | transcription | default.
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    # Time in line for a slot, then time holding it (Groq, 429 sleeps included).
    queue_wait_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    # 429s this call received, retried or not.
    rate_limit_hits: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    # A short, non-sensitive reason for a failure ("HTTP 503", "tokens per day").
    detail: Mapped[str | None] = mapped_column(String(200), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('ok', 'rate_limited', 'queue_timeout', 'error', 'cancelled')",
            name="ck_llm_calls_status",
        ),
        Index("ix_llm_calls_created_at", "created_at"),
    )


# --- uploaded chapters (Phase 9) ----------------------------------------------
#
# Chapter 1 is NOT in these tables. It stays on its original, hand-verified
# path (chapters.py's constant, the bind-mounted PDF, sample_problems.json,
# context.PINS and patch_chunks.py), because re-extracting it would throw away
# corrections checked by eye against the source. These tables hold chapters an
# admin uploads through the console.
#
# The draft/published split is the point of the design. Everything a student
# reads comes from a snapshot taken at publish time - the chunks and pins in
# Qdrant, and the published_* columns below - while the admin edits the draft
# rows freely. So fixing a chunk in a live chapter changes nothing for
# students until "Republier", and a half-reviewed edit never reaches a chat.

CHAPTER_PROCESSING = "processing"  # PDF stored, extraction running
CHAPTER_FAILED = "failed"  # extraction raised; `error` says why
CHAPTER_DRAFT = "draft"  # extracted, under review, invisible to students
CHAPTER_PUBLISHING = "publishing"  # embedding into Qdrant
CHAPTER_PUBLISHED = "published"  # live for students
CHAPTER_STATUSES = (
    CHAPTER_PROCESSING,
    CHAPTER_FAILED,
    CHAPTER_DRAFT,
    CHAPTER_PUBLISHING,
    CHAPTER_PUBLISHED,
)


class UploadedChapter(Base):
    __tablename__ = "chapters"

    # The chapter number as the student sees it ("2"), which is also the
    # `chapitre` key every Qdrant point and /solve request is scoped by.
    id: Mapped[str] = mapped_column(String(8), primary_key=True)
    niveau: Mapped[str] = mapped_column(String(32), nullable=False, default="2eme")
    title: Mapped[str] = mapped_column(Text, nullable=False)
    # The gatekeeper's "what this chapter covers" list, as a sentence of topics.
    topics: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_filename: Mapped[str] = mapped_column(Text, nullable=False)
    # Phase 9b: "pdf" (extracted by extract_chapter.py, then reviewed) or
    # "markdown" (a course written to docs/modele-cours.md, read exactly by
    # course_markdown.py). For a markdown chapter the student-facing PDF is a
    # separate, optional upload.
    source_kind: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pdf", server_default="pdf"
    )

    # The publish snapshot. Null until first published.
    published_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_topics: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_exercises: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Set by any draft edit after a publish, cleared by the next publish - so
    # the console can say "modifications non publiées".
    has_unpublished_changes: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    chunks: Mapped[list[ChapterChunk]] = relationship(
        back_populates="chapter",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ChapterChunk.position",
    )
    exercises: Mapped[list[ChapterExercise]] = relationship(
        back_populates="chapter",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ChapterExercise.position",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('processing', 'failed', 'draft', 'publishing', 'published')",
            name="ck_chapters_status",
        ),
        # "1" is the built-in chapter; an upload must never shadow it.
        CheckConstraint("id <> '1'", name="ck_chapters_not_builtin"),
        CheckConstraint("source_kind IN ('pdf', 'markdown')", name="ck_chapters_source_kind"),
    )

    def __repr__(self) -> str:
        return f"<UploadedChapter {self.id} {self.status}>"


class ChapterChunk(Base):
    """One extracted chunk, as the admin reviews and edits it."""

    __tablename__ = "chapter_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chapter_id: Mapped[str] = mapped_column(
        String(8), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    section: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Same vocabulary extract_chapter.py emits: prose | table | exercice.
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    format: Mapped[str] = mapped_column(String(16), nullable=False, default="prose")
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Part of the chapter's reference sheet: included in every prompt for this
    # chapter, the way context.PINS works for chapter 1.
    pinned: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    pin_label: Mapped[str | None] = mapped_column(Text, nullable=True)

    chapter: Mapped[UploadedChapter] = relationship(back_populates="chunks")

    __table_args__ = (
        CheckConstraint("type IN ('prose', 'table', 'exercice')", name="ck_chapter_chunks_type"),
        Index("ix_chapter_chunks_chapter_position", "chapter_id", "position"),
    )


class ChapterExercise(Base):
    __tablename__ = "chapter_exercises"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chapter_id: Mapped[str] = mapped_column(
        String(8), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)

    chapter: Mapped[UploadedChapter] = relationship(back_populates="exercises")

    __table_args__ = (Index("ix_chapter_exercises_chapter_position", "chapter_id", "position"),)
