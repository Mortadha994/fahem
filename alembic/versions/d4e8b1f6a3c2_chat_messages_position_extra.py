"""chat_messages position and extra

Chat history moves from the browser to the account: each student's
discussions are saved to chat_sessions / chat_messages, which until now
nothing wrote to.

- position: the message's order in its discussion. A discussion is saved as a
  whole in one transaction, so created_at is identical for all its messages
  and cannot order them.
- extra: display state that is not the answer itself (an error sentence, the
  attached file's name and kind, the client's message id).

Both additive; the tables are empty in every existing deployment.

Revision ID: d4e8b1f6a3c2
Revises: c7a1d3e5f902
Create Date: 2026-09-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "d4e8b1f6a3c2"
down_revision: Union[str, Sequence[str], None] = "c7a1d3e5f902"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chat_messages",
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "chat_messages",
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index(
        "ix_chat_messages_session_id_position", "chat_messages", ["session_id", "position"]
    )


def downgrade() -> None:
    op.drop_index("ix_chat_messages_session_id_position", table_name="chat_messages")
    op.drop_column("chat_messages", "extra")
    op.drop_column("chat_messages", "position")
