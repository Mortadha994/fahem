"""user niveau and section

The student's year (2ème, 3ème, Bac) and section, asked once right after the
first sign-in and kept on the account, so answers - and later the chapters
offered - can be aimed at where the student actually is.

- users gains niveau and section, both nullable: every existing account is
  simply "not answered yet", which is what makes the client ask
- CHECKs close both sets (see models.NIVEAUX / models.SECTIONS) and require
  the two to be set together

The 2ème année's narrower section list is enforced by the API, not here: the
pairing rule belongs to the school system and may change with a reform, and a
migration is the wrong place to have to follow it.

Revision ID: c7a1d3e5f902
Revises: b3f9a2c6d1e7
Create Date: 2026-09-13

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "c7a1d3e5f902"
down_revision: Union[str, Sequence[str], None] = "b3f9a2c6d1e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("niveau", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("section", sa.Text(), nullable=True))
    op.create_check_constraint(
        "ck_users_niveau", "users", "niveau IS NULL OR niveau IN ('2eme', '3eme', 'bac')"
    )
    op.create_check_constraint(
        "ck_users_section",
        "users",
        "section IS NULL OR section IN "
        "('informatique', 'math', 'sciences', 'lettres', 'technique', 'eco')",
    )
    op.create_check_constraint(
        "ck_users_profile_pair", "users", "(niveau IS NULL) = (section IS NULL)"
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_profile_pair", "users", type_="check")
    op.drop_constraint("ck_users_section", "users", type_="check")
    op.drop_constraint("ck_users_niveau", "users", type_="check")
    op.drop_column("users", "section")
    op.drop_column("users", "niveau")
