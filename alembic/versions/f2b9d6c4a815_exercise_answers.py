"""exercise_answers

Precomputed answers for the catalogue exercises, so clicking one costs no Groq
call. See app/llm/answer_cache.py for what fills it and app/core/models.py for
why the key is (chapter, exercise, mode, step) and not a hash.

Pure addition: nothing reads the table until answer_cache is asked to, and an
empty table simply means every request takes the live path it takes today.

Revision ID: f2b9d6c4a815
Revises: a2c7e4b9d631
Create Date: 2026-09-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "f2b9d6c4a815"
down_revision: Union[str, Sequence[str], None] = "a2c7e4b9d631"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "exercise_answers",
        sa.Column("chapter_id", sa.String(length=8), nullable=False),
        sa.Column("exercise_id", sa.String(length=64), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("step", sa.Integer(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("pinned", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("retrieved", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("question_hash", sa.String(length=64), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("chapter_id", "exercise_id", "mode", "step"),
        sa.CheckConstraint("mode IN ('full', 'guided')", name="ck_exercise_answers_mode"),
        sa.CheckConstraint("step >= 0 AND step <= 4", name="ck_exercise_answers_step"),
    )
    op.create_index("ix_exercise_answers_chapter", "exercise_answers", ["chapter_id"])


def downgrade() -> None:
    op.drop_index("ix_exercise_answers_chapter", table_name="exercise_answers")
    op.drop_table("exercise_answers")
