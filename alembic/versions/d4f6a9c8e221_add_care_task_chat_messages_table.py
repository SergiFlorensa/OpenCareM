"""add care_task_chat_messages table

Revision ID: d4f6a9c8e221
Revises: c5e8a2f1d440
Create Date: 2026-02-15 11:40:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4f6a9c8e221"
down_revision: Union[str, None] = "c5e8a2f1d440"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "care_task_chat_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("care_task_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("clinician_id", sa.String(length=80), nullable=True),
        sa.Column("user_query", sa.Text(), nullable=False),
        sa.Column("assistant_answer", sa.Text(), nullable=False),
        sa.Column("matched_domains", sa.JSON(), nullable=False),
        sa.Column("matched_endpoints", sa.JSON(), nullable=False),
        sa.Column("memory_facts_used", sa.JSON(), nullable=False),
        sa.Column("extracted_facts", sa.JSON(), nullable=False),
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
        sa.ForeignKeyConstraint(["care_task_id"], ["care_tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_care_task_chat_messages_id"),
        "care_task_chat_messages",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_care_task_chat_messages_care_task_id"),
        "care_task_chat_messages",
        ["care_task_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_care_task_chat_messages_session_id"),
        "care_task_chat_messages",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        "ix_care_task_chat_messages_care_task_session",
        "care_task_chat_messages",
        ["care_task_id", "session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_care_task_chat_messages_care_task_session",
        table_name="care_task_chat_messages",
    )
    op.drop_index(
        op.f("ix_care_task_chat_messages_session_id"),
        table_name="care_task_chat_messages",
    )
    op.drop_index(
        op.f("ix_care_task_chat_messages_care_task_id"),
        table_name="care_task_chat_messages",
    )
    op.drop_index(
        op.f("ix_care_task_chat_messages_id"),
        table_name="care_task_chat_messages",
    )
    op.drop_table("care_task_chat_messages")
