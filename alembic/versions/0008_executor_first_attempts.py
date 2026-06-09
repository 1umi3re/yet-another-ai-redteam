"""executor first attempts

Revision ID: 0008_executor_first_attempts
Revises: 0007_attempt_original_prompt
Create Date: 2026-06-08 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_executor_first_attempts"
down_revision: str | None = "0007_attempt_original_prompt"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("runs", sa.Column("filtered_json", sa.JSON(), nullable=True))
    op.add_column("attempts", sa.Column("executor_name", sa.String(length=100), nullable=True))
    op.add_column("attempts", sa.Column("executor_kind", sa.String(length=40), nullable=True))
    op.add_column("attempts", sa.Column("dataset_item_language", sa.String(length=10), nullable=True))


def downgrade() -> None:
    op.drop_column("attempts", "dataset_item_language")
    op.drop_column("attempts", "executor_kind")
    op.drop_column("attempts", "executor_name")
    op.drop_column("runs", "filtered_json")
