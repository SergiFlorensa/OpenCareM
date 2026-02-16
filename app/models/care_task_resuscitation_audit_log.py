"""
Auditoria de calidad para soporte operativo de reanimacion.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class CareTaskResuscitationAuditLog(Base):
    """
    Compara recomendacion de reanimacion IA con validacion humana.

    `classification`:
    - `match`: mismo nivel global de severidad
    - `under_resuscitation_risk`: IA menos severa que humano
    - `over_resuscitation_risk`: IA mas severa que humano
    """

    __tablename__ = "care_task_resuscitation_audit_logs"

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
    ai_severity_level = Column(String(16), nullable=False)
    human_validated_severity_level = Column(String(16), nullable=False)
    classification = Column(String(40), nullable=False, index=True)
    ai_shock_recommended = Column(Boolean, nullable=False, default=False)
    human_shock_recommended = Column(Boolean, nullable=False, default=False)
    ai_reversible_causes_required = Column(Boolean, nullable=False, default=False)
    human_reversible_causes_completed = Column(Boolean, nullable=False, default=False)
    ai_airway_plan_adequate = Column(Boolean, nullable=False, default=False)
    human_airway_plan_adequate = Column(Boolean, nullable=False, default=False)
    reviewer_note = Column(Text, nullable=True)
    reviewed_by = Column(String(80), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
