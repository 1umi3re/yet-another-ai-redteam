from __future__ import annotations

import ast
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


def test_revision_ids_fit_alembic_version_column():
    """Alembic's default version_num column is VARCHAR(32)."""
    for path in Path("alembic/versions").glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in tree.body:
            if not isinstance(node, ast.AnnAssign) or not isinstance(node.target, ast.Name):
                continue
            if node.target.id != "revision":
                continue
            revision = ast.literal_eval(node.value)
            assert len(revision) <= 32, f"{path.name} revision ID is too long: {revision}"


def test_retest_provenance_has_alembic_migration():
    migration_text = Path("alembic/versions/0014_retest_provenance.py").read_text()

    for column in ("target_config_id", "executor_ref_json", "source_run_id", "source_attempt_id", "retest_mode"):
        assert f'sa.Column("{column}"' in migration_text


def test_target_reconnaissance_has_alembic_migration():
    migration_text = Path("alembic/versions/0015_target_recon.py").read_text()

    assert '"target_recon_reports"' in migration_text
    assert 'sa.Column("report_json", sa.JSON(), nullable=True)' in migration_text
    assert 'op.drop_table("target_recon_reports")' in migration_text


def test_oidc_login_has_alembic_migration():
    migration_text = Path("alembic/versions/0016_oidc_login.py").read_text()

    assert 'revision: str = "0016_oidc_login"' in migration_text
    assert 'down_revision: str | None = "0015_target_recon"' in migration_text
    assert '"oidc_login_tickets"' in migration_text
    assert '"ticket_hash"' in migration_text
    assert '"consumed_at"' in migration_text
    assert 'op.drop_table("oidc_login_tickets")' in migration_text
