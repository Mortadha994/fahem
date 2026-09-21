"""users.plan_until

A subscription can now carry an end date. Nullable, and NULL keeps the
previous meaning exactly: a paid account with no end date stays paid until an
admin changes it, so every existing row keeps behaving as it did.

Nothing downgrades a row when the date passes - app.core.models.effective_plan
decides on every read - so this column needs no job and no backfill.

Revision ID: e1a4c8b2d7f3
Revises: a2c7e4b9d631
Create Date: 2026-09-21

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "e1a4c8b2d7f3"
down_revision: Union[str, Sequence[str], None] = "a2c7e4b9d631"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("plan_until", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "plan_until")
