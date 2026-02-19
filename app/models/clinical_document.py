"""
Modelo para documentos clinicos fuente.
"""
from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ClinicalDocument(Base):
    """Representa un documento clinico (protocolo, guia, articulo)."""

    __tablename__ = "clinical_documents"
    __table_args__ = (
        UniqueConstraint("content_hash", name="uq_clinical_document_hash"),
    )

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    source_file = Column(String(500), nullable=True)
    specialty = Column(String(80), nullable=True, index=True)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    content_hash = Column(String(64), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"ClinicalDocument(id={self.id}, title='{self.title}', "
            f"specialty='{self.specialty}')"
        )
