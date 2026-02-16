"""add clinical knowledge sources tables

Revision ID: c2f4a9e1b771
Revises: e8a1c4b7d552
Create Date: 2026-02-15 19:25:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c2f4a9e1b771"
down_revision: Union[str, None] = "e8a1c4b7d552"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clinical_knowledge_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("specialty", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.String(length=600), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("source_domain", sa.String(length=255), nullable=True),
        sa.Column("source_path", sa.String(length=300), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="pending_review",
        ),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("validated_by_user_id", sa.Integer(), nullable=True),
        sa.Column("validation_note", sa.Text(), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["validated_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_clinical_knowledge_sources_id"),
        "clinical_knowledge_sources",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_clinical_knowledge_sources_source_domain"),
        "clinical_knowledge_sources",
        ["source_domain"],
        unique=False,
    )
    op.create_index(
        op.f("ix_clinical_knowledge_sources_specialty"),
        "clinical_knowledge_sources",
        ["specialty"],
        unique=False,
    )
    op.create_index(
        op.f("ix_clinical_knowledge_sources_status"),
        "clinical_knowledge_sources",
        ["status"],
        unique=False,
    )

    op.create_table(
        "clinical_knowledge_source_validations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("reviewer_user_id", sa.Integer(), nullable=True),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["reviewer_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["clinical_knowledge_sources.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_clinical_knowledge_source_validations_decision"),
        "clinical_knowledge_source_validations",
        ["decision"],
        unique=False,
    )
    op.create_index(
        op.f("ix_clinical_knowledge_source_validations_id"),
        "clinical_knowledge_source_validations",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_clinical_knowledge_source_validations_source_id"),
        "clinical_knowledge_source_validations",
        ["source_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_clinical_knowledge_source_validations_source_id"),
        table_name="clinical_knowledge_source_validations",
    )
    op.drop_index(
        op.f("ix_clinical_knowledge_source_validations_id"),
        table_name="clinical_knowledge_source_validations",
    )
    op.drop_index(
        op.f("ix_clinical_knowledge_source_validations_decision"),
        table_name="clinical_knowledge_source_validations",
    )
    op.drop_table("clinical_knowledge_source_validations")

    op.drop_index(
        op.f("ix_clinical_knowledge_sources_status"),
        table_name="clinical_knowledge_sources",
    )
    op.drop_index(
        op.f("ix_clinical_knowledge_sources_specialty"),
        table_name="clinical_knowledge_sources",
    )
    op.drop_index(
        op.f("ix_clinical_knowledge_sources_source_domain"),
        table_name="clinical_knowledge_sources",
    )
    op.drop_index(
        op.f("ix_clinical_knowledge_sources_id"),
        table_name="clinical_knowledge_sources",
    )
    op.drop_table("clinical_knowledge_sources")
