"""add emergency_episodes table

Revision ID: f7a4c2d9e111
Revises: e4b7a1d9c220
Create Date: 2026-02-11 23:58:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f7a4c2d9e111"
down_revision: Union[str, None] = "e4b7a1d9c220"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "emergency_episodes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("care_task_id", sa.Integer(), nullable=True),
        sa.Column("origin", sa.String(length=32), nullable=False),
        sa.Column("current_stage", sa.String(length=64), nullable=False),
        sa.Column("priority_risk", sa.String(length=32), nullable=True),
        sa.Column("disposition", sa.String(length=32), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "arrived_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("triaged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("medical_evaluation_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("diagnostics_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disposition_decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["care_task_id"], ["care_tasks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_emergency_episodes_id"),
        "emergency_episodes",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_emergency_episodes_care_task_id"),
        "emergency_episodes",
        ["care_task_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_emergency_episodes_origin"),
        "emergency_episodes",
        ["origin"],
        unique=False,
    )
    op.create_index(
        op.f("ix_emergency_episodes_current_stage"),
        "emergency_episodes",
        ["current_stage"],
        unique=False,
    )
    op.create_index(
        op.f("ix_emergency_episodes_priority_risk"),
        "emergency_episodes",
        ["priority_risk"],
        unique=False,
    )
    op.create_index(
        op.f("ix_emergency_episodes_disposition"),
        "emergency_episodes",
        ["disposition"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_emergency_episodes_disposition"), table_name="emergency_episodes")
    op.drop_index(op.f("ix_emergency_episodes_priority_risk"), table_name="emergency_episodes")
    op.drop_index(op.f("ix_emergency_episodes_current_stage"), table_name="emergency_episodes")
    op.drop_index(op.f("ix_emergency_episodes_origin"), table_name="emergency_episodes")
    op.drop_index(op.f("ix_emergency_episodes_care_task_id"), table_name="emergency_episodes")
    op.drop_index(op.f("ix_emergency_episodes_id"), table_name="emergency_episodes")
    op.drop_table("emergency_episodes")
