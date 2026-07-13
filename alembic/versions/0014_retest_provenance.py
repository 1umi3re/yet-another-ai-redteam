"""successful attempt retest provenance

Revision ID: 0014_retest_provenance
Revises: 0013_svc_ctx_language
Create Date: 2026-07-13 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
import yaml

from alembic import op

revision: str = "0014_retest_provenance"
down_revision: str | None = "0013_svc_ctx_language"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _backfill_target_config_ids() -> None:
    connection = op.get_bind()
    target_name_by_id = {
        row.id: row.name
        for row in connection.execute(sa.text("SELECT id, name FROM target_configs"))
    }
    for run in connection.execute(
        sa.text("SELECT id, runspec_yaml FROM runs WHERE kind = 'automated'")
    ):
        try:
            spec = yaml.safe_load(run.runspec_yaml or "{}") or {}
        except Exception:
            continue
        target_ids = [
            item.get("config_id")
            for item in spec.get("targets") or []
            if isinstance(item, dict) and item.get("config_id") in target_name_by_id
        ]
        if len(target_ids) == 1:
            connection.execute(
                sa.text("UPDATE attempts SET target_config_id = :target_id WHERE run_id = :run_id"),
                {"target_id": target_ids[0], "run_id": run.id},
            )
            continue
        for target_id in target_ids:
            connection.execute(
                sa.text(
                    "UPDATE attempts SET target_config_id = :target_id "
                    "WHERE run_id = :run_id AND target_name = :target_name"
                ),
                {
                    "target_id": target_id,
                    "run_id": run.id,
                    "target_name": target_name_by_id[target_id],
                },
            )


def upgrade() -> None:
    with op.batch_alter_table("attempts") as batch:
        batch.add_column(sa.Column("target_config_id", sa.String(length=36), nullable=True))
        batch.add_column(sa.Column("executor_ref_json", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("source_run_id", sa.String(length=36), nullable=True))
        batch.add_column(sa.Column("source_attempt_id", sa.String(length=36), nullable=True))
        batch.add_column(sa.Column("retest_mode", sa.String(length=24), nullable=True))
        batch.create_foreign_key(
            "fk_attempts_target_config_id",
            "target_configs",
            ["target_config_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch.create_index("ix_attempts_target_config_id", ["target_config_id"])
        batch.create_index("ix_attempts_source_run_id", ["source_run_id"])
        batch.create_index("ix_attempts_source_attempt_id", ["source_attempt_id"])
    _backfill_target_config_ids()


def downgrade() -> None:
    with op.batch_alter_table("attempts") as batch:
        batch.drop_index("ix_attempts_source_attempt_id")
        batch.drop_index("ix_attempts_source_run_id")
        batch.drop_index("ix_attempts_target_config_id")
        batch.drop_constraint("fk_attempts_target_config_id", type_="foreignkey")
        batch.drop_column("retest_mode")
        batch.drop_column("source_attempt_id")
        batch.drop_column("source_run_id")
        batch.drop_column("executor_ref_json")
        batch.drop_column("target_config_id")
