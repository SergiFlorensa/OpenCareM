"""add care_task_triage_reviews table

Revision ID: b8f2d4c6e1aa
Revises: a4c2d1e9b7f0
Create Date: 2026-02-11 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8f2d4c6e1aa"
down_revision: Union[str, None] = "a4c2d1e9b7f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "care_task_triage_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("care_task_id", sa.Integer(), nullable=False),
        sa.Column("agent_run_id", sa.Integer(), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False),
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
        op.f("ix_care_task_triage_reviews_id"),
        "care_task_triage_reviews",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_care_task_triage_reviews_care_task_id"),
        "care_task_triage_reviews",
        ["care_task_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_care_task_triage_reviews_agent_run_id"),
        "care_task_triage_reviews",
        ["agent_run_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_care_task_triage_reviews_agent_run_id"),
        table_name="care_task_triage_reviews",
    )
    op.drop_index(
        op.f("ix_care_task_triage_reviews_care_task_id"),
        table_name="care_task_triage_reviews",
    )
    op.drop_index(op.f("ix_care_task_triage_reviews_id"), table_name="care_task_triage_reviews")
    op.drop_table("care_task_triage_reviews")
