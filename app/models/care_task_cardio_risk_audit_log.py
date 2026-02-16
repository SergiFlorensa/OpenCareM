"""
Auditoria de calidad para soporte operativo de riesgo cardiovascular.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class CareTaskCardioRiskAuditLog(Base):
    """
    Compara recomendacion cardiovascular IA con validacion humana.

    `classification`:
    - `match`: mismo nivel global de riesgo
    - `under_cardio_risk`: IA menos severa que humano
    - `over_cardio_risk`: IA mas severa que humano
    """

    __tablename__ = "care_task_cardio_risk_audit_logs"

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
    ai_risk_level = Column(String(16), nullable=False)
    human_validated_risk_level = Column(String(16), nullable=False)
    classification = Column(String(32), nullable=False, index=True)
    ai_non_hdl_target_required = Column(Boolean, nullable=False, default=False)
    human_non_hdl_target_required = Column(Boolean, nullable=False, default=False)
    ai_pharmacologic_strategy_suggested = Column(Boolean, nullable=False, default=False)
    human_pharmacologic_strategy_suggested = Column(Boolean, nullable=False, default=False)
    ai_intensive_lifestyle_required = Column(Boolean, nullable=False, default=False)
    human_intensive_lifestyle_required = Column(Boolean, nullable=False, default=False)
    reviewer_note = Column(Text, nullable=True)
    reviewed_by = Column(String(80), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
