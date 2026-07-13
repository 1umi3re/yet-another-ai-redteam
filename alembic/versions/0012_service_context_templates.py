"""service context templates

Revision ID: 0012_service_context_templates
Revises: 0011_custom_scenarios
Create Date: 2026-07-10 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012_service_context_templates"
down_revision: str | None = "0011_custom_scenarios"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "service_context_templates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("target_config_id", sa.String(length=36), nullable=False),
        sa.Column("target_model", sa.String(length=200), nullable=False),
        sa.Column("generator_config_id", sa.String(length=36), nullable=True),
        sa.Column("generator_model", sa.String(length=200), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("topic", sa.String(length=500), nullable=True),
        sa.Column("template_text", sa.Text(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("verification_passed", sa.Boolean(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("trace_blob_path", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["generator_config_id"], ["target_configs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_config_id"], ["target_configs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "target_config_id", "target_model", "version", name="uq_service_context_template_version"
        ),
    )
    op.create_index(
        "ix_service_context_templates_target_config_id",
        "service_context_templates",
        ["target_config_id"],
    )
    op.add_column("attempts", sa.Column("service_context_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("attempts", "service_context_json")
    op.drop_index("ix_service_context_templates_target_config_id", table_name="service_context_templates")
    op.drop_table("service_context_templates")
