"""backfill chat message client ids written by the previous backend

A backend still running the code from before c9e5a3b7d1f4 kept rewriting
discussions without client_id after that migration ran. Those rows get the
same backfill: extra->>'id', else "m_<row id>" when missing or taken.

Revision ID: d7f2b9c4e6a1
Revises: c9e5a3b7d1f4
Create Date: 2026-09-17

"""

from typing import Sequence, Union

from alembic import op

revision: str = "d7f2b9c4e6a1"
down_revision: Union[str, Sequence[str], None] = "c9e5a3b7d1f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Row by row in id order, so a duplicate id keeps the first row and the
    # partial unique index is never violated mid-statement.
    op.execute(
        """
        DO $$
        DECLARE r record;
        BEGIN
          FOR r IN SELECT id, session_id, NULLIF(extra->>'id', '') AS eid
                   FROM chat_messages WHERE client_id IS NULL ORDER BY id LOOP
            IF r.eid IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM chat_messages o
                WHERE o.session_id = r.session_id AND o.client_id = r.eid) THEN
              UPDATE chat_messages SET client_id = r.eid WHERE id = r.id;
            ELSE
              UPDATE chat_messages SET client_id = 'm_' || r.id::text WHERE id = r.id;
            END IF;
          END LOOP;
        END $$;
        """
    )


def downgrade() -> None:
    # Data only; the ids stay valid under c9e5a3b7d1f4.
    pass
