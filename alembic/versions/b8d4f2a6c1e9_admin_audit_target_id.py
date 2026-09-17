"""admin audit target id

admin_audit gains target_id: the id of what an action was about (a user's
uuid), so the console's action log can link to the account. Nullable - older
rows and actions without an id (settings, queues) have none.

Revision ID: b8d4f2a6c1e9
Revises: a7c3e9d1b5f2
Create Date: 2026-09-16

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "b8d4f2a6c1e9"
down_revision: Union[str, Sequence[str], None] = "a7c3e9d1b5f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("admin_audit", sa.Column("target_id", sa.String(length=64), nullable=True))
    op.create_index("ix_admin_audit_action", "admin_audit", ["action"])


def downgrade() -> None:
    op.drop_index("ix_admin_audit_action", table_name="admin_audit")
    op.drop_column("admin_audit", "target_id")
