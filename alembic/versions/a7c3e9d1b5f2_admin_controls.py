"""admin controls

What the admin console can now change, not only show:

- users gains suspended_at + suspended_reason (a suspended account's sessions
  and sign-ins are refused) and solve_rate_limit (a personal limit replacing
  the global one; null = global)
- app_settings: settings changed live from the console (runtime_settings.py);
  a missing row means the config.py default
- admin_audit: who changed what, and when

Revision ID: a7c3e9d1b5f2
Revises: f1a9c4e7b2d3
Create Date: 2026-09-16

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "a7c3e9d1b5f2"
down_revision: Union[str, Sequence[str], None] = "f1a9c4e7b2d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("suspended_reason", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("solve_rate_limit", sa.String(length=64), nullable=True))

    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_by", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("key"),
    )

    op.create_table(
        "admin_audit",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("admin_email", sa.Text(), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("target", sa.Text(), nullable=True),
        sa.Column("detail", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_audit_created_at", "admin_audit", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_admin_audit_created_at", table_name="admin_audit")
    op.drop_table("admin_audit")
    op.drop_table("app_settings")
    op.drop_column("users", "solve_rate_limit")
    op.drop_column("users", "suspended_reason")
    op.drop_column("users", "suspended_at")
