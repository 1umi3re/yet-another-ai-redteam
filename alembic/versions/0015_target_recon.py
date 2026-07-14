"""target agent reconnaissance reports

Revision ID: 0015_target_recon
Revises: 0014_retest_provenance
Create Date: 2026-07-13 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0015_target_recon"
down_revision: str | None = "0014_retest_provenance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "target_recon_reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("target_config_id", sa.String(length=36), nullable=False),
        sa.Column("target_model", sa.String(length=200), nullable=False),
        sa.Column("generator_config_id", sa.String(length=36), nullable=True),
        sa.Column("generator_model", sa.String(length=200), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("report_json", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("trace_blob_path", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["target_config_id"], ["target_configs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["generator_config_id"], ["target_configs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "target_config_id",
            "target_model",
            "version",
            name="uq_target_recon_report_version",
        ),
    )
    op.create_index("ix_target_recon_reports_target_config_id", "target_recon_reports", ["target_config_id"])


def downgrade() -> None:
    op.drop_index("ix_target_recon_reports_target_config_id", table_name="target_recon_reports")
    op.drop_table("target_recon_reports")
