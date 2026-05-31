"""phase4: custom prompt assets

Revision ID: 0004_custom_prompt_assets
Revises: 0003_phase3
Create Date: 2026-05-25 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_custom_prompt_assets"
down_revision: str | None = "0003_phase3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "prompt_assets",
        sa.Column("id", sa.String(length=200), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("plugin", sa.String(length=100), nullable=False),
        sa.Column("purpose", sa.String(length=200), nullable=False),
        sa.Column("variables_json", sa.JSON(), nullable=False),
        sa.Column("template_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("prompt_assets")
