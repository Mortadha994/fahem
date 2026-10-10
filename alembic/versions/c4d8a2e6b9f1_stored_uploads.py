"""stored uploads

Files of the chapter upload directory (PDF, Markdown, exercise supplements),
mirrored in the database for hosts whose disk does not survive a restart.

Revision ID: c4d8a2e6b9f1
Revises: b7c3e9a1d5f2
Create Date: 2026-10-10

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "c4d8a2e6b9f1"
down_revision: Union[str, Sequence[str], None] = "b7c3e9a1d5f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stored_uploads",
        sa.Column("name", sa.String(128), primary_key=True),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("stored_uploads")
