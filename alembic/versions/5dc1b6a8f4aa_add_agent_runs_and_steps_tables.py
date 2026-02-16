"""add agent_runs and agent_steps tables

Revision ID: 5dc1b6a8f4aa
Revises: e7f1c2a4b990
Create Date: 2026-02-09 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5dc1b6a8f4aa"
down_revision: Union[str, None] = "e7f1c2a4b990"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Guarda el estado global de cada ejecucion del workflow agente.
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workflow_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("run_input", sa.JSON(), nullable=False),
        sa.Column("run_output", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("total_cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_runs_id"), "agent_runs", ["id"], unique=False)
    op.create_index(
        op.f("ix_agent_runs_workflow_name"), "agent_runs", ["workflow_name"], unique=False
    )
    op.create_index(op.f("ix_agent_runs_status"), "agent_runs", ["status"], unique=False)

    # Guarda traza detallada por paso (input/output/decision/fallback/error).
    op.create_table(
        "agent_steps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("step_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("step_input", sa.JSON(), nullable=False),
        sa.Column("step_output", sa.JSON(), nullable=True),
        sa.Column("decision", sa.Text(), nullable=True),
        sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("step_cost_usd", sa.Float(), nullable=False, server_default="0"),
        sa.Column("step_latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["run_id"], ["agent_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_steps_id"), "agent_steps", ["id"], unique=False)
    op.create_index(op.f("ix_agent_steps_run_id"), "agent_steps", ["run_id"], unique=False)
    op.create_index(op.f("ix_agent_steps_status"), "agent_steps", ["status"], unique=False)


def downgrade() -> None:
    # Revierte tablas de ejecucion agente y su traza por pasos.
    op.drop_index(op.f("ix_agent_steps_status"), table_name="agent_steps")
    op.drop_index(op.f("ix_agent_steps_run_id"), table_name="agent_steps")
    op.drop_index(op.f("ix_agent_steps_id"), table_name="agent_steps")
    op.drop_table("agent_steps")

    op.drop_index(op.f("ix_agent_runs_status"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_workflow_name"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_id"), table_name="agent_runs")
    op.drop_table("agent_runs")
