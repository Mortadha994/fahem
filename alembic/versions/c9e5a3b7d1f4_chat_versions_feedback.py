"""chat versions, message client ids, answer feedback, call routes

- chat_sessions.version: bumped by every save; a stale save is refused.
- chat_messages.client_id: the chat's own message id, unique per discussion,
  so saves update messages instead of replacing the discussion. Backfilled
  from extra->>'id', else "m_<row id>" (what the API already returned).
- answer_feedback: a student's thumbs up / down on an answer.
- llm_calls.route, llm_calls.memory_chars: which prompt answered a solve and
  how much session memory it carried (AI monitoring).

Revision ID: c9e5a3b7d1f4
Revises: b8d4f2a6c1e9
Create Date: 2026-09-16

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "c9e5a3b7d1f4"
down_revision: Union[str, Sequence[str], None] = "b8d4f2a6c1e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chat_sessions", sa.Column("version", sa.Integer(), server_default="0", nullable=False)
    )
    op.add_column("chat_messages", sa.Column("client_id", sa.String(length=80), nullable=True))
    # Duplicate client ids inside one discussion (should not exist) keep the
    # first; the others fall back to their row id.
    op.execute(
        """
        UPDATE chat_messages m SET client_id = COALESCE(NULLIF(m.extra->>'id', ''), 'm_' || m.id::text)
        """
    )
    op.execute(
        """
        UPDATE chat_messages m SET client_id = 'm_' || m.id::text
        WHERE EXISTS (
            SELECT 1 FROM chat_messages o
            WHERE o.session_id = m.session_id AND o.client_id = m.client_id AND o.id < m.id
        )
        """
    )
    op.create_index(
        "uq_chat_messages_session_client_id",
        "chat_messages",
        ["session_id", "client_id"],
        unique=True,
        postgresql_where=sa.text("client_id IS NOT NULL"),
    )

    op.create_table(
        "answer_feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_client_id", sa.String(length=80), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.CheckConstraint("rating IN (-1, 1)", name="ck_answer_feedback_rating"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_answer_feedback_message",
        "answer_feedback",
        ["session_id", "message_client_id"],
        unique=True,
    )
    op.create_index("ix_answer_feedback_created_at", "answer_feedback", ["created_at"])

    op.add_column("llm_calls", sa.Column("route", sa.String(length=16), nullable=True))
    op.add_column(
        "llm_calls", sa.Column("memory_chars", sa.Integer(), server_default="0", nullable=False)
    )


def downgrade() -> None:
    op.drop_column("llm_calls", "memory_chars")
    op.drop_column("llm_calls", "route")
    op.drop_index("ix_answer_feedback_created_at", table_name="answer_feedback")
    op.drop_index("uq_answer_feedback_message", table_name="answer_feedback")
    op.drop_table("answer_feedback")
    op.drop_index("uq_chat_messages_session_client_id", table_name="chat_messages")
    op.drop_column("chat_messages", "client_id")
    op.drop_column("chat_sessions", "version")
