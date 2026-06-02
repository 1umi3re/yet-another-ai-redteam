"""attempt original prompt

Revision ID: 0007_attempt_original_prompt
Revises: 0006_attempt_work_keys
Create Date: 2026-06-02 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_attempt_original_prompt"
down_revision: str | None = "0006_attempt_work_keys"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("attempts", sa.Column("original_prompt_text", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("attempts", "original_prompt_text")
