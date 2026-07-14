"""queryable attempt and score state

Revision ID: 0018_query_state
Revises: 0017_run_loading
Create Date: 2026-07-14 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from airedteam.core.score_state import score_final_verdict
from airedteam.core.score_status import score_status
from alembic import op

revision: str = "0018_query_state"
down_revision: str | None = "0017_run_loading"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "attempts",
        sa.Column("converter_chain_key", sa.String(length=1000), nullable=False, server_default=""),
    )
    op.add_column(
        "attempts",
        sa.Column("converter_chain_search", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "attempts",
        sa.Column("executor_ref_present", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "scores",
        sa.Column("status", sa.String(length=20), nullable=False, server_default="completed"),
    )
    op.add_column("scores", sa.Column("final_verdict", sa.String(length=20), nullable=True))

    connection = op.get_bind()
    attempts = sa.table(
        "attempts",
        sa.column("id", sa.String(length=36)),
        sa.column("converter_chain", sa.JSON()),
        sa.column("converter_chain_key", sa.String(length=1000)),
        sa.column("converter_chain_search", sa.Text()),
        sa.column("executor_name", sa.String(length=100)),
        sa.column("executor_ref_json", sa.JSON()),
        sa.column("executor_ref_present", sa.Boolean()),
    )
    for row in connection.execute(
        sa.select(
            attempts.c.id,
            attempts.c.converter_chain,
            attempts.c.executor_name,
            attempts.c.executor_ref_json,
        )
    ).mappings():
        chain = [str(item) for item in (row["converter_chain"] or [])]
        values = {
            "converter_chain_key": " -> ".join(chain),
            "converter_chain_search": "".join(f"|{item}|" for item in chain),
            "executor_ref_present": bool(row["executor_ref_json"]),
        }
        if not row["executor_name"]:
            values["executor_name"] = " -> ".join(chain) if chain else "single_turn"
        connection.execute(sa.update(attempts).where(attempts.c.id == row["id"]).values(**values))

    scores = sa.table(
        "scores",
        sa.column("id", sa.String(length=36)),
        sa.column("scorer", sa.String(length=100)),
        sa.column("value_json", sa.JSON()),
        sa.column("reviewer_label", sa.Boolean()),
        sa.column("status", sa.String(length=20)),
        sa.column("final_verdict", sa.String(length=20)),
    )
    for row in connection.execute(
        sa.select(scores.c.id, scores.c.scorer, scores.c.value_json, scores.c.reviewer_label)
    ).mappings():
        connection.execute(
            sa.update(scores)
            .where(scores.c.id == row["id"])
            .values(
                status=score_status(row["value_json"]),
                final_verdict=score_final_verdict(
                    row["scorer"],
                    row["value_json"],
                    row["reviewer_label"],
                ),
            )
        )

    op.create_index("ix_attempts_run_executor", "attempts", ["run_id", "executor_name"])
    op.create_index("ix_attempts_run_chain_key", "attempts", ["run_id", "converter_chain_key"])
    op.create_index("ix_scores_attempt_verdict", "scores", ["attempt_id", "final_verdict"])
    op.create_index("ix_scores_attempt_status", "scores", ["attempt_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_scores_attempt_status", table_name="scores")
    op.drop_index("ix_scores_attempt_verdict", table_name="scores")
    op.drop_index("ix_attempts_run_chain_key", table_name="attempts")
    op.drop_index("ix_attempts_run_executor", table_name="attempts")
    op.drop_column("scores", "final_verdict")
    op.drop_column("scores", "status")
    op.drop_column("attempts", "converter_chain_search")
    op.drop_column("attempts", "converter_chain_key")
    op.drop_column("attempts", "executor_ref_present")
