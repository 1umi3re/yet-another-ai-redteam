"""phase3: prompt asset overrides and prompt snapshots

Revision ID: 0003_phase3
Revises: 0002_phase2
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_phase3"
down_revision: Union[str, None] = "0002_phase2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prompt_asset_overrides",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("asset_id", sa.String(length=200), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("template_text", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_prompt_asset_overrides_asset_id",
        "prompt_asset_overrides",
        ["asset_id"],
    )
    op.add_column(
        "attempts",
        sa.Column("prompt_snapshot_blob_path", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "scores",
        sa.Column("prompt_snapshot_blob_path", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("scores", "prompt_snapshot_blob_path")
    op.drop_column("attempts", "prompt_snapshot_blob_path")
    op.drop_index("ix_prompt_asset_overrides_asset_id", table_name="prompt_asset_overrides")
    op.drop_table("prompt_asset_overrides")
