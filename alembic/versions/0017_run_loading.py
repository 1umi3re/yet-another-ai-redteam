"""run loading indexes and normalized targets

Revision ID: 0017_run_loading
Revises: 0016_oidc_login
Create Date: 2026-07-14 00:00:00.000000
"""

import json
from collections.abc import Sequence

import sqlalchemy as sa
import yaml

from alembic import op

revision: str = "0017_run_loading"
down_revision: str | None = "0016_oidc_login"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _target_ids(kind: str, runspec: str) -> list[str]:
    try:
        spec = json.loads(runspec or "{}") if kind == "manual" else yaml.safe_load(runspec or "{}")
    except Exception:
        return []
    if not isinstance(spec, dict):
        return []
    if kind == "manual":
        target_id = spec.get("target_id")
        return [target_id] if isinstance(target_id, str) and target_id else []
    return [
        item["config_id"]
        for item in spec.get("targets") or []
        if isinstance(item, dict) and isinstance(item.get("config_id"), str) and item["config_id"]
    ]


def upgrade() -> None:
    op.create_table(
        "run_targets",
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("run_id", "target_id"),
    )
    op.create_index("ix_run_targets_target_id", "run_targets", ["target_id"])
    op.create_index("ix_runs_created_at", "runs", ["created_at"])
    op.create_index("ix_runs_status_kind", "runs", ["status", "kind"])
    op.create_index("ix_attempts_run_created_at", "attempts", ["run_id", "created_at"])

    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, kind, runspec_yaml FROM runs")).mappings()
    values = [
        {"run_id": row["id"], "target_id": target_id}
        for row in rows
        for target_id in dict.fromkeys(_target_ids(row["kind"], row["runspec_yaml"]))
    ]
    if values:
        table = sa.table(
            "run_targets",
            sa.column("run_id", sa.String(length=36)),
            sa.column("target_id", sa.String(length=36)),
        )
        op.bulk_insert(table, values)


def downgrade() -> None:
    op.drop_index("ix_attempts_run_created_at", table_name="attempts")
    op.drop_index("ix_runs_status_kind", table_name="runs")
    op.drop_index("ix_runs_created_at", table_name="runs")
    op.drop_index("ix_run_targets_target_id", table_name="run_targets")
    op.drop_table("run_targets")
