"""
Modelo de mensajes de chat clinico por CareTask.

Permite guardar consultas del profesional y la respuesta operativa generada
para reutilizar contexto en futuras interacciones.
"""
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class CareTaskChatMessage(Base):
    """Representa una interaccion de chat clinico asociada a un CareTask."""

    __tablename__ = "care_task_chat_messages"
    __table_args__ = (
        Index(
            "ix_care_task_chat_messages_care_task_session",
            "care_task_id",
            "session_id",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    care_task_id = Column(
        Integer,
        ForeignKey("care_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(String(64), nullable=False, index=True)
    clinician_id = Column(String(80), nullable=True)
    effective_specialty = Column(
        String(80),
        nullable=False,
        default="general",
        server_default="general",
    )
    user_query = Column(Text, nullable=False)
    assistant_answer = Column(Text, nullable=False)
    matched_domains = Column(JSON, nullable=False, default=list)
    matched_endpoints = Column(JSON, nullable=False, default=list)
    knowledge_sources = Column(JSON, nullable=False, default=list)
    web_sources = Column(JSON, nullable=False, default=list)
    memory_facts_used = Column(JSON, nullable=False, default=list)
    patient_history_facts_used = Column(JSON, nullable=False, default=list)
    extracted_facts = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return (
            "CareTaskChatMessage("
            f"id={self.id}, care_task_id={self.care_task_id}, "
            f"session_id='{self.session_id}')"
        )
