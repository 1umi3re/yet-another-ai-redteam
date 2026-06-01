"""attempt work keys

Revision ID: 0006_attempt_work_keys
Revises: 0005_ds_versions_asset_cats
Create Date: 2026-05-31 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_attempt_work_keys"
down_revision: str | None = "0005_ds_versions_asset_cats"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("attempts", sa.Column("work_key", sa.String(length=128), nullable=True))
    op.create_index("uq_attempts_run_work_key", "attempts", ["run_id", "work_key"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_attempts_run_work_key", table_name="attempts")
    op.drop_column("attempts", "work_key")
