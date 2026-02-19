"""add RAG tables: clinical_documents, document_chunks, rag_queries_audit

Revision ID: d8c3f2e1a445
Revises: c2f4a9e1b771
Create Date: 2026-02-17 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d8c3f2e1a445"
down_revision: Union[str, None] = "c2f4a9e1b771"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea tablas para RAG: documentos, chunks, auditoría."""

    # Tabla de documentos clínicos
    op.create_table(
        "clinical_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_file", sa.String(length=500), nullable=True),
        sa.Column("specialty", sa.String(length=80), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("content_hash", sa.String(length=64), nullable=False, unique=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_hash", name="uq_clinical_document_hash"),
    )

    op.create_index(
        "ix_clinical_documents_id",
        "clinical_documents",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_clinical_documents_title",
        "clinical_documents",
        ["title"],
        unique=False,
    )
    op.create_index(
        "ix_clinical_documents_specialty",
        "clinical_documents",
        ["specialty"],
        unique=False,
    )
    op.create_index(
        "ix_clinical_documents_content_hash",
        "clinical_documents",
        ["content_hash"],
        unique=True,
    )

    # Tabla de fragmentos de documentos con embeddings
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "document_id",
            sa.Integer(),
            sa.ForeignKey("clinical_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("section_path", sa.String(length=500), nullable=True),
        sa.Column("tokens_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunk_embedding", sa.LargeBinary(), nullable=False),  # vector embedding
        sa.Column("keywords", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("custom_questions", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("specialty", sa.String(length=80), nullable=True),
        sa.Column("content_type", sa.String(length=32), nullable=False, server_default="paragraph"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_document_chunks_doc_id",
        "document_chunks",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        "ix_document_chunks_specialty",
        "document_chunks",
        ["specialty"],
        unique=False,
    )
    op.create_index(
        "ix_document_chunks_section",
        "document_chunks",
        ["section_path"],
        unique=False,
    )

    # Tabla de auditoría de consultas RAG
    op.create_table(
        "rag_queries_audit",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "care_task_id",
            sa.Integer(),
            sa.ForeignKey("care_tasks.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("search_method", sa.String(length=32), nullable=False),
        sa.Column("chunks_retrieved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("vector_search_latency_ms", sa.Float(), nullable=True),
        sa.Column("keyword_search_latency_ms", sa.Float(), nullable=True),
        sa.Column("total_latency_ms", sa.Float(), nullable=True),
        sa.Column("model_used", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_rag_queries_audit_care_task_id",
        "rag_queries_audit",
        ["care_task_id"],
        unique=False,
    )
    op.create_index(
        "ix_rag_queries_audit_created_at",
        "rag_queries_audit",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Elimina tablas RAG."""
    op.drop_table("rag_queries_audit")
    op.drop_table("document_chunks")
    op.drop_table("clinical_documents")
