"""init tasks table

Revision ID: f1b3f75c533d
Revises:
Create Date: 2026-02-07 11:27:15.950977

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1b3f75c533d"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crea la tabla principal de tareas para la API.
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "completed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
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
    op.create_index("ix_tasks_id", "tasks", ["id"], unique=False)
    op.create_index("ix_tasks_title", "tasks", ["title"], unique=False)
    op.create_index("ix_tasks_completed", "tasks", ["completed"], unique=False)


def downgrade() -> None:
    # Revierte la estructura de tareas para volver al estado previo.
    op.drop_index("ix_tasks_completed", table_name="tasks")
    op.drop_index("ix_tasks_title", table_name="tasks")
    op.drop_index("ix_tasks_id", table_name="tasks")
    op.drop_table("tasks")
