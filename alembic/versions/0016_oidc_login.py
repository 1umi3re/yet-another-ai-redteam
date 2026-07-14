"""OIDC login exchange tickets

Revision ID: 0016_oidc_login
Revises: 0015_target_recon
Create Date: 2026-07-14 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0016_oidc_login"
down_revision: str | None = "0015_target_recon"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "oidc_login_tickets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("ticket_hash", sa.String(length=64), nullable=False),
        sa.Column("account_json", sa.JSON(), nullable=False),
        sa.Column("next_path", sa.String(length=500), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_oidc_login_tickets_expires_at", "oidc_login_tickets", ["expires_at"])
    op.create_index(
        "ix_oidc_login_tickets_ticket_hash",
        "oidc_login_tickets",
        ["ticket_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_oidc_login_tickets_ticket_hash", table_name="oidc_login_tickets")
    op.drop_index("ix_oidc_login_tickets_expires_at", table_name="oidc_login_tickets")
    op.drop_table("oidc_login_tickets")
