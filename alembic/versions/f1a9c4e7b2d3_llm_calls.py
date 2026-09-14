"""llm calls

One row per Groq call, for the admin console's AI monitoring page
(llm_usage.py): model, kind, status, token usage, queue wait, latency and the
429s it met. A time series read by created_at ranges, hence the index; rows
past LLM_USAGE_RETENTION_DAYS are pruned by the console.

Revision ID: f1a9c4e7b2d3
Revises: e5b2c8d1f7a4
Create Date: 2026-09-14

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "f1a9c4e7b2d3"
down_revision: Union[str, Sequence[str], None] = "e5b2c8d1f7a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "llm_calls",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("model", sa.String(length=80), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("completion_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_tokens", sa.Integer(), server_default="0", nullable=False),
        sa.Column("queue_wait_ms", sa.Integer(), server_default="0", nullable=False),
        sa.Column("latency_ms", sa.Integer(), server_default="0", nullable=False),
        sa.Column("rate_limit_hits", sa.Integer(), server_default="0", nullable=False),
        sa.Column("detail", sa.String(length=200), nullable=True),
        sa.CheckConstraint(
            "status IN ('ok', 'rate_limited', 'queue_timeout', 'error', 'cancelled')",
            name="ck_llm_calls_status",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_llm_calls_created_at", "llm_calls", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_llm_calls_created_at", table_name="llm_calls")
    op.drop_table("llm_calls")
