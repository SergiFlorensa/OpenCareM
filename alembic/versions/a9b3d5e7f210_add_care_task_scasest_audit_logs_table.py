"""add care_task_scasest_audit_logs table

Revision ID: a9b3d5e7f210
Revises: f7a4c2d9e111
Create Date: 2026-02-12 10:15:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a9b3d5e7f210"
down_revision: Union[str, None] = "f7a4c2d9e111"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "care_task_scasest_audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("care_task_id", sa.Integer(), nullable=False),
        sa.Column("agent_run_id", sa.Integer(), nullable=False),
        sa.Column("ai_high_risk_scasest", sa.Boolean(), nullable=False),
        sa.Column("human_validated_high_risk_scasest", sa.Boolean(), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("ai_escalation_required", sa.Boolean(), nullable=False),
        sa.Column("human_escalation_required", sa.Boolean(), nullable=False),
        sa.Column("ai_immediate_antiischemic_strategy", sa.Boolean(), nullable=False),
        sa.Column("human_immediate_antiischemic_strategy", sa.Boolean(), nullable=False),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.String(length=80), nullable=True),
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
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["care_task_id"], ["care_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_run_id"),
    )
    op.create_index(
        op.f("ix_care_task_scasest_audit_logs_id"),
        "care_task_scasest_audit_logs",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_care_task_scasest_audit_logs_care_task_id"),
        "care_task_scasest_audit_logs",
        ["care_task_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_care_task_scasest_audit_logs_agent_run_id"),
        "care_task_scasest_audit_logs",
        ["agent_run_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_care_task_scasest_audit_logs_classification"),
        "care_task_scasest_audit_logs",
        ["classification"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_care_task_scasest_audit_logs_classification"),
        table_name="care_task_scasest_audit_logs",
    )
    op.drop_index(
        op.f("ix_care_task_scasest_audit_logs_agent_run_id"),
        table_name="care_task_scasest_audit_logs",
    )
    op.drop_index(
        op.f("ix_care_task_scasest_audit_logs_care_task_id"),
        table_name="care_task_scasest_audit_logs",
    )
    op.drop_index(
        op.f("ix_care_task_scasest_audit_logs_id"),
        table_name="care_task_scasest_audit_logs",
    )
    op.drop_table("care_task_scasest_audit_logs")
