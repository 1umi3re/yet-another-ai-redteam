"""phase2: manual runs and reviewer fields

Revision ID: 0002_phase2
Revises: 0001_init
Create Date: 2026-04-23 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0002_phase2'
down_revision: Union[str, None] = '0001_init'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('runs',
        sa.Column('kind', sa.String(length=20), nullable=False, server_default='automated'))
    op.add_column('scores',
        sa.Column('reviewer_label', sa.Boolean(), nullable=True))
    op.add_column('scores',
        sa.Column('reviewer_notes', sa.Text(), nullable=True))
    op.add_column('scores',
        sa.Column('reviewer_id', sa.String(length=100), nullable=True))
    op.add_column('scores',
        sa.Column('reviewed_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('scores', 'reviewed_at')
    op.drop_column('scores', 'reviewer_id')
    op.drop_column('scores', 'reviewer_notes')
    op.drop_column('scores', 'reviewer_label')
    op.drop_column('runs', 'kind')
