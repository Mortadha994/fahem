"""user full access

A student sees the chapters of their own niveau only. Test and legacy accounts
need to see every niveau, and an admin console switch is how an account gets
that: users.full_access. (Admins always have it, through their role.)

- users gains full_access, NOT NULL, defaulting to false
- Existing accounts WITHOUT a niveau keep what they have today - every niveau -
  so the test accounts keep working the day this ships. Every account with a
  niveau, and every account created from now on, is limited to its own.

Revision ID: b7c3e9a1d5f2
Revises: f2b9d6c4a815
Create Date: 2026-10-05

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "b7c3e9a1d5f2"
down_revision: Union[str, Sequence[str], None] = "f2b9d6c4a815"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("full_access", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.execute("UPDATE users SET full_access = true WHERE niveau IS NULL")


def downgrade() -> None:
    op.drop_column("users", "full_access")
