"""user plan

The account's subscription tier, the foundation for a priority-aware queue in
front of Groq (llm_queue.py): a paid tier will be able to jump the queue.
Nothing is billed yet.

- users gains plan, NOT NULL, defaulting to 'free'
- CHECK: plan is one of 'free' | 'paid'

Every existing row becomes free, which is what every account is today. The
server_default stays on the column for the same reason as the role's: a row
inserted by anything that does not know about plans must land on the
unprivileged value.

Revision ID: e5b2c8d1f7a4
Revises: d4e8b1f6a3c2
Create Date: 2026-09-14

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "e5b2c8d1f7a4"
down_revision: Union[str, Sequence[str], None] = "d4e8b1f6a3c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("plan", sa.String(length=16), server_default="free", nullable=False),
    )
    op.create_check_constraint("ck_users_plan", "users", "plan IN ('free', 'paid')")


def downgrade() -> None:
    op.drop_constraint("ck_users_plan", "users", type_="check")
    op.drop_column("users", "plan")
