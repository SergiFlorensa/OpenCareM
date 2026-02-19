"""
Modelo para fragmentos de documentos con vectores de embeddings.
"""
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DocumentChunk(Base):
    """Almacena fragmentos de documentos indexables con embeddings."""

    __tablename__ = "document_chunks"
    __table_args__ = (
        Index("ix_document_chunks_doc_id", "document_id"),
        Index("ix_document_chunks_specialty", "specialty"),
        Index("ix_document_chunks_section", "section_path"),
    )

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        Integer,
        ForeignKey("clinical_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    section_path = Column(String(500), nullable=True)
    tokens_count = Column(Integer, nullable=False, default=0)
    chunk_embedding = Column(LargeBinary, nullable=False)
    keywords = Column(JSON, nullable=False, default=list)
    custom_questions = Column(JSON, nullable=False, default=list)
    specialty = Column(String(80), nullable=True)
    content_type = Column(String(32), nullable=False, default="paragraph")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    document = relationship(
        "ClinicalDocument",
        back_populates="chunks",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return (
            f"DocumentChunk(id={self.id}, doc_id={self.document_id}, "
            f"section='{self.section_path}', tokens={self.tokens_count})"
        )
