"""llm_calls.user_id

Which account a Groq call was made for, so the admin console can show one
student's token use over time and answer "does this person need more quota"
with a number instead of an impression.

- llm_calls gains user_id, NULLABLE, ON DELETE SET NULL
- index on (user_id, created_at), which is how the per-student charts read it

Nullable on purpose, and it stays nullable:

- every row written before this migration has no user to attribute, and
  inventing one would be worse than leaving it blank;
- not every call belongs to a student. The gatekeeper classification runs for
  a student and does carry one, but a warm-up or an admin-triggered call has
  no account behind it, and NULL is the honest value there.

So per-student cost is only meaningful from this migration forward. The
activity charts, which read chat_sessions and chat_messages, still cover the
whole history.

ON DELETE SET NULL rather than CASCADE: deleting an account must not erase the
spend it caused, or the monthly totals would silently shrink and the budget
guard's history would stop matching what was actually paid for.

Revision ID: a2c7e4b9d631
Revises: d7f2b9c4e6a1
Create Date: 2026-09-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "a2c7e4b9d631"
down_revision: Union[str, Sequence[str], None] = "d7f2b9c4e6a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "llm_calls",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_llm_calls_user_id",
        "llm_calls",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_llm_calls_user_id_created_at",
        "llm_calls",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_llm_calls_user_id_created_at", table_name="llm_calls")
    op.drop_constraint("fk_llm_calls_user_id", "llm_calls", type_="foreignkey")
    op.drop_column("llm_calls", "user_id")
