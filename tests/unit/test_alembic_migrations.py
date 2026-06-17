from __future__ import annotations

from pathlib import Path


def test_attempt_timing_columns_have_alembic_migration():
    migration_text = "\n".join(path.read_text() for path in Path("alembic/versions").glob("*.py"))

    assert 'op.add_column("attempts", sa.Column("started_at", sa.DateTime(), nullable=True))' in migration_text
    assert 'op.add_column("attempts", sa.Column("finished_at", sa.DateTime(), nullable=True))' in migration_text
    assert 'op.add_column("attempts", sa.Column("duration_ms", sa.Integer(), nullable=True))' in migration_text


def test_custom_scenarios_have_alembic_migration():
    migration_text = "\n".join(path.read_text() for path in Path("alembic/versions").glob("*.py"))

    assert '"custom_scenarios"' in migration_text
    assert 'sa.Column("template_json", sa.JSON(), nullable=False)' in migration_text
    assert 'op.drop_table("custom_scenarios")' in migration_text
