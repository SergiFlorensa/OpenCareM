"""
Registro de revision humana del triaje ejecutado sobre un CareTask.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class CareTaskTriageReview(Base):
    """
    Guarda la decision humana sobre una corrida de triaje.

    Cada corrida de agente (`agent_run_id`) puede tener una sola revision para
    mantener trazabilidad clara y evitar ambiguedad de estado final.
    """

    __tablename__ = "care_task_triage_reviews"

    id = Column(Integer, primary_key=True, index=True)
    care_task_id = Column(
        Integer,
        ForeignKey("care_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_run_id = Column(
        Integer,
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    approved = Column(Boolean, nullable=False)
    reviewer_note = Column(Text, nullable=True)
    reviewed_by = Column(String(80), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
