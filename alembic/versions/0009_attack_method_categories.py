"""attack method categories

Revision ID: 0009_attack_method_categories
Revises: 0008_executor_first_attempts
Create Date: 2026-06-09 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009_attack_method_categories"
down_revision: str | None = "0008_executor_first_attempts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "attack_method_categories",
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("alias", sa.String(length=200), nullable=False),
        sa.Column("type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("is_builtin", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "executor_method_categories",
        sa.Column("executor_kind", sa.String(length=40), nullable=False),
        sa.Column("executor_name", sa.String(length=100), nullable=False),
        sa.Column("category_id", sa.String(length=80), nullable=False),
        sa.Column("technical_category", sa.String(length=100), nullable=True),
        sa.Column("is_builtin", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["attack_method_categories.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("executor_kind", "executor_name"),
    )
    op.create_index(
        "ix_executor_method_categories_category_id",
        "executor_method_categories",
        ["category_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_executor_method_categories_category_id", table_name="executor_method_categories")
    op.drop_table("executor_method_categories")
    op.drop_table("attack_method_categories")
