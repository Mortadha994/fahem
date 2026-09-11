"""password accounts and auth tokens

Phase 4: email + password sign-in alongside Google.

- users.google_sub becomes nullable (a password account has none)
- users.email becomes NOT NULL
- users gains password_hash, email_verified, sessions_valid_after
- CHECK: every user has google_sub or password_hash
- unique lower(email) among password accounts only
- new auth_tokens table (hashed, single-use, expiring)

Revision ID: 5b2f8c1d9e40
Revises: 3745f6075e9d
Create Date: 2026-09-11

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "5b2f8c1d9e40"
down_revision: Union[str, Sequence[str], None] = "3745f6075e9d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Refuse rather than backfill. A user with no email cannot be given a
    # made-up one, and silently deleting them would destroy their history.
    # The Google flow has always stored the token's email, so this is expected
    # to be zero - the check is here so that expectation is verified, not
    # assumed, on whatever database this runs against.
    missing = conn.execute(sa.text("SELECT count(*) FROM users WHERE email IS NULL")).scalar()
    if missing:
        raise RuntimeError(
            f"{missing} user(s) have no email; email is about to become NOT NULL. "
            "Resolve those rows by hand, then re-run the migration."
        )

    op.alter_column("users", "google_sub", existing_type=sa.Text(), nullable=True)
    op.alter_column("users", "email", existing_type=sa.Text(), nullable=False)
    op.add_column("users", sa.Column("password_hash", sa.Text(), nullable=True))
    op.add_column(
        "users",
        sa.Column("email_verified", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column(
        "users", sa.Column("sessions_valid_after", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_check_constraint(
        "ck_users_has_credential", "users", "google_sub IS NOT NULL OR password_hash IS NOT NULL"
    )
    # No duplicate check needed before this index: it only covers rows with a
    # password_hash, and this migration is what introduces that column.
    op.create_index(
        "uq_users_password_email",
        "users",
        [sa.text("lower(email)")],
        unique=True,
        postgresql_where=sa.text("password_hash IS NOT NULL"),
    )

    op.create_table(
        "auth_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "purpose IN ('verify_email', 'reset_password')", name="ck_auth_tokens_purpose"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        "ix_auth_tokens_user_id_purpose", "auth_tokens", ["user_id", "purpose"], unique=False
    )


def downgrade() -> None:
    conn = op.get_bind()

    # google_sub goes back to NOT NULL, which a password-only account cannot
    # satisfy. Refuse rather than delete those accounts as a side effect of a
    # schema rollback - removing them has to be a deliberate, separate act.
    orphans = conn.execute(sa.text("SELECT count(*) FROM users WHERE google_sub IS NULL")).scalar()
    if orphans:
        raise RuntimeError(
            f"{orphans} password-only account(s) exist; downgrading would leave them "
            "without google_sub. Delete them deliberately first if that is intended."
        )

    op.drop_index("ix_auth_tokens_user_id_purpose", table_name="auth_tokens")
    op.drop_table("auth_tokens")
    op.drop_index("uq_users_password_email", table_name="users")
    op.drop_constraint("ck_users_has_credential", "users", type_="check")
    op.drop_column("users", "sessions_valid_after")
    op.drop_column("users", "email_verified")
    op.drop_column("users", "password_hash")
    op.alter_column("users", "email", existing_type=sa.Text(), nullable=True)
    op.alter_column("users", "google_sub", existing_type=sa.Text(), nullable=False)
