"""
Historial de validaciones/sellado profesional de fuentes clinicas.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class ClinicalKnowledgeSourceValidation(Base):
    """Evento de validacion de una fuente clinica."""

    __tablename__ = "clinical_knowledge_source_validations"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(
        Integer,
        ForeignKey("clinical_knowledge_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decision = Column(String(32), nullable=False, index=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self) -> str:
        return (
            "ClinicalKnowledgeSourceValidation("
            f"id={self.id}, source_id={self.source_id}, decision='{self.decision}')"
        )
