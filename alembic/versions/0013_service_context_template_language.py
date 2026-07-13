"""service context template language

Revision ID: 0013_service_context_template_language
Revises: 0012_service_context_templates
Create Date: 2026-07-13 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0013_service_context_template_language"
down_revision: str | None = "0012_service_context_templates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("service_context_templates", sa.Column("language", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("service_context_templates", "language")
