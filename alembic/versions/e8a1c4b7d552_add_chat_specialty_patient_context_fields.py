"""add chat specialty and patient context fields

Revision ID: e8a1c4b7d552
Revises: d4f6a9c8e221
Create Date: 2026-02-15 18:10:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e8a1c4b7d552"
down_revision: Union[str, None] = "d4f6a9c8e221"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "specialty",
            sa.String(length=80),
            nullable=False,
            server_default="general",
        ),
    )
    op.create_index(op.f("ix_users_specialty"), "users", ["specialty"], unique=False)

    op.add_column(
        "care_tasks",
        sa.Column("patient_reference", sa.String(length=120), nullable=True),
    )
    op.create_index(
        op.f("ix_care_tasks_patient_reference"),
        "care_tasks",
        ["patient_reference"],
        unique=False,
    )

    op.add_column(
        "care_task_chat_messages",
        sa.Column(
            "effective_specialty",
            sa.String(length=80),
            nullable=False,
            server_default="general",
        ),
    )
    op.add_column(
        "care_task_chat_messages",
        sa.Column(
            "knowledge_sources",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )
    op.add_column(
        "care_task_chat_messages",
        sa.Column(
            "web_sources",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )
    op.add_column(
        "care_task_chat_messages",
        sa.Column(
            "patient_history_facts_used",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )
    op.create_index(
        op.f("ix_care_task_chat_messages_effective_specialty"),
        "care_task_chat_messages",
        ["effective_specialty"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_care_task_chat_messages_effective_specialty"),
        table_name="care_task_chat_messages",
    )
    op.drop_column("care_task_chat_messages", "patient_history_facts_used")
    op.drop_column("care_task_chat_messages", "web_sources")
    op.drop_column("care_task_chat_messages", "knowledge_sources")
    op.drop_column("care_task_chat_messages", "effective_specialty")

    op.drop_index(op.f("ix_care_tasks_patient_reference"), table_name="care_tasks")
    op.drop_column("care_tasks", "patient_reference")

    op.drop_index(op.f("ix_users_specialty"), table_name="users")
    op.drop_column("users", "specialty")
