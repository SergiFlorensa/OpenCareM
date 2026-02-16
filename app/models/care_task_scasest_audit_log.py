"""
Auditoria de calidad para soporte operativo de SCASEST.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class CareTaskScasestAuditLog(Base):
    """
    Compara recomendacion SCASEST de IA con validacion humana.

    `classification`:
    - `match`: mismo nivel global de riesgo
    - `under_scasest_risk`: IA menos severa que humano
    - `over_scasest_risk`: IA mas severa que humano
    """

    __tablename__ = "care_task_scasest_audit_logs"

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
    ai_high_risk_scasest = Column(Boolean, nullable=False, default=False)
    human_validated_high_risk_scasest = Column(Boolean, nullable=False, default=False)
    classification = Column(String(32), nullable=False, index=True)
    ai_escalation_required = Column(Boolean, nullable=False, default=False)
    human_escalation_required = Column(Boolean, nullable=False, default=False)
    ai_immediate_antiischemic_strategy = Column(Boolean, nullable=False, default=False)
    human_immediate_antiischemic_strategy = Column(Boolean, nullable=False, default=False)
    reviewer_note = Column(Text, nullable=True)
    reviewed_by = Column(String(80), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
