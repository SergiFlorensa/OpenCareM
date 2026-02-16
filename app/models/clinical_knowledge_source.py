"""
Modelo de fuente de conocimiento clinico validable.
"""
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class ClinicalKnowledgeSource(Base):
    """Fuente de conocimiento usada por el chat clinico."""

    __tablename__ = "clinical_knowledge_sources"

    id = Column(Integer, primary_key=True, index=True)
    specialty = Column(String(80), nullable=False, index=True, default="general")
    title = Column(String(200), nullable=False)
    summary = Column(String(600), nullable=True)
    content = Column(Text, nullable=True)
    source_type = Column(String(40), nullable=False, default="guideline")
    source_url = Column(String(500), nullable=True)
    source_domain = Column(String(255), nullable=True, index=True)
    source_path = Column(String(300), nullable=True)
    tags = Column(JSON, nullable=False, default=list)
    status = Column(
        String(32),
        nullable=False,
        index=True,
        default="pending_review",
        server_default="pending_review",
    )
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    validated_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    validation_note = Column(Text, nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return (
            "ClinicalKnowledgeSource("
            f"id={self.id}, specialty='{self.specialty}', status='{self.status}')"
        )
