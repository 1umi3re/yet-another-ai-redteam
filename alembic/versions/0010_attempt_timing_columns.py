"""attempt timing columns

Revision ID: 0010_attempt_timing_columns
Revises: 0009_attack_method_categories
Create Date: 2026-06-15 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0010_attempt_timing_columns"
down_revision: str | None = "0009_attack_method_categories"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("attempts", sa.Column("started_at", sa.DateTime(), nullable=True))
    op.add_column("attempts", sa.Column("finished_at", sa.DateTime(), nullable=True))
    op.add_column("attempts", sa.Column("duration_ms", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("attempts", "duration_ms")
    op.drop_column("attempts", "finished_at")
    op.drop_column("attempts", "started_at")
