"""uploaded chapters

Phase 9: chapters an admin uploads as a PDF, reviews, and publishes.

- chapters: one row per uploaded chapter, with a draft state (title, topics)
  and a publish snapshot (published_title, published_topics,
  published_exercises) that is all students ever read
- chapter_chunks: the extracted chunks as the admin reviews and edits them
- chapter_exercises: exercises detected in the série, editable

Chapter 1 is deliberately not migrated into these tables; see models.py.

Revision ID: 9d4b2e7a1c55
Revises: 7c1e4a9b2f83
Create Date: 2026-09-13

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "9d4b2e7a1c55"
down_revision: Union[str, Sequence[str], None] = "7c1e4a9b2f83"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chapters",
        sa.Column("id", sa.String(length=8), primary_key=True),
        sa.Column("niveau", sa.String(length=32), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("topics", sa.Text(), server_default="", nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("source_filename", sa.Text(), nullable=False),
        sa.Column("published_title", sa.Text(), nullable=True),
        sa.Column("published_topics", sa.Text(), nullable=True),
        sa.Column("published_exercises", postgresql.JSONB(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "has_unpublished_changes", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('processing', 'failed', 'draft', 'publishing', 'published')",
            name="ck_chapters_status",
        ),
        sa.CheckConstraint("id <> '1'", name="ck_chapters_not_builtin"),
    )

    op.create_table(
        "chapter_chunks",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "chapter_id",
            sa.String(length=8),
            sa.ForeignKey("chapters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("section", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("format", sa.String(length=16), nullable=False),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("pinned", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("pin_label", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "type IN ('prose', 'table', 'exercice')", name="ck_chapter_chunks_type"
        ),
    )
    op.create_index(
        "ix_chapter_chunks_chapter_position", "chapter_chunks", ["chapter_id", "position"]
    )

    op.create_table(
        "chapter_exercises",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "chapter_id",
            sa.String(length=8),
            sa.ForeignKey("chapters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
    )
    op.create_index(
        "ix_chapter_exercises_chapter_position", "chapter_exercises", ["chapter_id", "position"]
    )


def downgrade() -> None:
    # Drops every uploaded chapter's review work. The PDFs in the upload volume
    # and the published points in Qdrant are NOT removed by this - delete the
    # chapters through the console first if they should go too.
    op.drop_index("ix_chapter_exercises_chapter_position", table_name="chapter_exercises")
    op.drop_table("chapter_exercises")
    op.drop_index("ix_chapter_chunks_chapter_position", table_name="chapter_chunks")
    op.drop_table("chapter_chunks")
    op.drop_table("chapters")
