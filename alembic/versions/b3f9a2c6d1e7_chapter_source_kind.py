"""chapter source kind

Phase 9b: an uploaded chapter's source is either a PDF (extracted by
extract_chapter.py) or a Markdown course written to docs/modele-cours.md
(read by course_markdown.py). Existing rows were all PDFs.

Revision ID: b3f9a2c6d1e7
Revises: 9d4b2e7a1c55
Create Date: 2026-09-13

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "b3f9a2c6d1e7"
down_revision: Union[str, Sequence[str], None] = "9d4b2e7a1c55"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chapters",
        sa.Column("source_kind", sa.String(length=16), server_default="pdf", nullable=False),
    )
    op.create_check_constraint(
        "ck_chapters_source_kind", "chapters", "source_kind IN ('pdf', 'markdown')"
    )


def downgrade() -> None:
    op.drop_constraint("ck_chapters_source_kind", "chapters", type_="check")
    op.drop_column("chapters", "source_kind")
