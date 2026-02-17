"""add care_tasks table

Revision ID: a4c2d1e9b7f0
Revises: 5dc1b6a8f4aa
Create Date: 2026-02-10 21:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a4c2d1e9b7f0"
down_revision: Union[str, None] = "5dc1b6a8f4aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tabla paralela para pivot de dominio a Clinical Ops.
    op.create_table(
        "care_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "clinical_priority", sa.String(length=20), nullable=False, server_default="medium"
        ),
        sa.Column("specialty", sa.String(length=80), nullable=False, server_default="general"),
        sa.Column("sla_target_minutes", sa.Integer(), nullable=False, server_default="240"),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
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
        sa.CheckConstraint(
            "clinical_priority IN ('low', 'medium', 'high', 'critical')",
            name="ck_care_tasks_clinical_priority",
        ),
        sa.CheckConstraint("sla_target_minutes > 0", name="ck_care_tasks_sla_positive"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_care_tasks_id"), "care_tasks", ["id"], unique=False)
    op.create_index(op.f("ix_care_tasks_title"), "care_tasks", ["title"], unique=False)
    op.create_index(
        op.f("ix_care_tasks_clinical_priority"),
        "care_tasks",
        ["clinical_priority"],
        unique=False,
    )
    op.create_index(op.f("ix_care_tasks_specialty"), "care_tasks", ["specialty"], unique=False)
    op.create_index(op.f("ix_care_tasks_completed"), "care_tasks", ["completed"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_care_tasks_completed"), table_name="care_tasks")
    op.drop_index(op.f("ix_care_tasks_specialty"), table_name="care_tasks")
    op.drop_index(op.f("ix_care_tasks_clinical_priority"), table_name="care_tasks")
    op.drop_index(op.f("ix_care_tasks_title"), table_name="care_tasks")
    op.drop_index(op.f("ix_care_tasks_id"), table_name="care_tasks")
    op.drop_table("care_tasks")
