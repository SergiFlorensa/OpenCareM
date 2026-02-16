"""
Auditoria de calidad de triaje para comparar IA vs validacion humana.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class CareTaskTriageAuditLog(Base):
    """
    Registra si el triaje recomendado por IA fue adecuado o desviado.

    `classification`:
    - `match`: coincide con validacion humana
    - `under_triage`: IA menos urgente que humano (riesgo de infrapriorizar)
    - `over_triage`: IA mas urgente que humano (riesgo de sobredemanda)
    """

    __tablename__ = "care_task_triage_audit_logs"

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
    ai_recommended_level = Column(Integer, nullable=False)
    human_validated_level = Column(Integer, nullable=False)
    classification = Column(String(32), nullable=False, index=True)
    reviewer_note = Column(Text, nullable=True)
    reviewed_by = Column(String(80), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
