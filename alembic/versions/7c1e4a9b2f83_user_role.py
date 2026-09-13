"""user role

Phase 7: a real, enforced admin role - the access-control foundation the
admin panel will sit on. No admin feature ships with this migration.

- users gains role, NOT NULL, defaulting to 'student'
- CHECK: role is one of 'student' | 'admin'

Every existing row becomes a student, which is what they already effectively
were: before this migration Fahem had no concept of an elevated account, so
there is no privilege to preserve and nothing to infer per row. The first
admin is created afterwards, deliberately and out of band, by
promote_admin.py - never by this migration and never by an API call.

The server_default stays on the column rather than being dropped once the
backfill is done: a row inserted by anything that does not know about roles
(a fixture, a psql session during an incident, a future code path that
forgets) must land as a student. Defaulting to the unprivileged value is the
only safe direction for this column to fail.

Revision ID: 7c1e4a9b2f83
Revises: 5b2f8c1d9e40
Create Date: 2026-09-12

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "7c1e4a9b2f83"
down_revision: Union[str, Sequence[str], None] = "5b2f8c1d9e40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.Text(), server_default="student", nullable=False),
    )
    op.create_check_constraint("ck_users_role", "users", "role IN ('student', 'admin')")


def downgrade() -> None:
    # Dropping this column destroys the record of who was an admin, and there
    # is nowhere else that fact is stored. Downgrading is therefore a
    # deliberate "this phase did not happen" - re-run promote_admin.py after
    # any later re-upgrade.
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.drop_column("users", "role")
