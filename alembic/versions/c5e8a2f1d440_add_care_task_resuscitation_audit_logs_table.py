"""add care_task_resuscitation_audit_logs table

Revision ID: c5e8a2f1d440
Revises: b1f4a2c9d330
Create Date: 2026-02-12 23:40:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c5e8a2f1d440"
down_revision: Union[str, None] = "b1f4a2c9d330"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "care_task_resuscitation_audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("care_task_id", sa.Integer(), nullable=False),
        sa.Column("agent_run_id", sa.Integer(), nullable=False),
        sa.Column("ai_severity_level", sa.String(length=16), nullable=False),
        sa.Column("human_validated_severity_level", sa.String(length=16), nullable=False),
        sa.Column("classification", sa.String(length=40), nullable=False),
        sa.Column("ai_shock_recommended", sa.Boolean(), nullable=False),
        sa.Column("human_shock_recommended", sa.Boolean(), nullable=False),
        sa.Column("ai_reversible_causes_required", sa.Boolean(), nullable=False),
        sa.Column("human_reversible_causes_completed", sa.Boolean(), nullable=False),
        sa.Column("ai_airway_plan_adequate", sa.Boolean(), nullable=False),
        sa.Column("human_airway_plan_adequate", sa.Boolean(), nullable=False),
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
        op.f("ix_care_task_resuscitation_audit_logs_id"),
        "care_task_resuscitation_audit_logs",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_care_task_resuscitation_audit_logs_care_task_id"),
        "care_task_resuscitation_audit_logs",
        ["care_task_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_care_task_resuscitation_audit_logs_agent_run_id"),
        "care_task_resuscitation_audit_logs",
        ["agent_run_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_care_task_resuscitation_audit_logs_classification"),
        "care_task_resuscitation_audit_logs",
        ["classification"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_care_task_resuscitation_audit_logs_classification"),
        table_name="care_task_resuscitation_audit_logs",
    )
    op.drop_index(
        op.f("ix_care_task_resuscitation_audit_logs_agent_run_id"),
        table_name="care_task_resuscitation_audit_logs",
    )
    op.drop_index(
        op.f("ix_care_task_resuscitation_audit_logs_care_task_id"),
        table_name="care_task_resuscitation_audit_logs",
    )
    op.drop_index(
        op.f("ix_care_task_resuscitation_audit_logs_id"),
        table_name="care_task_resuscitation_audit_logs",
    )
    op.drop_table("care_task_resuscitation_audit_logs")
