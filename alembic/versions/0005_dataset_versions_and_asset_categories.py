"""dataset versions and prompt asset categories

Revision ID: 0005_ds_versions_asset_cats
Revises: 0004_custom_prompt_assets
Create Date: 2026-05-26 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_ds_versions_asset_cats"
down_revision: str | None = "0004_custom_prompt_assets"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "datasets",
        sa.Column("current_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "datasets",
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "dataset_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("blob_path", sa.String(length=500), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dataset_id", "version", name="uq_dataset_versions_dataset_version"),
    )
    op.create_index(
        "ix_dataset_versions_dataset_id",
        "dataset_versions",
        ["dataset_id"],
    )
    op.add_column(
        "prompt_assets",
        sa.Column("category", sa.String(length=200), nullable=False, server_default="custom"),
    )


def downgrade() -> None:
    op.drop_column("prompt_assets", "category")
    op.drop_index("ix_dataset_versions_dataset_id", table_name="dataset_versions")
    op.drop_table("dataset_versions")
    op.drop_column("datasets", "updated_at")
    op.drop_column("datasets", "current_version")
