"""
Auditoria de calidad para soporte medico-legal operativo.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class CareTaskMedicolegalAuditLog(Base):
    """
    Compara recomendacion medico-legal IA con validacion humana.

    `classification`:
    - `match`: mismo nivel de riesgo legal global
    - `under_legal_risk`: IA menos severa que humano
    - `over_legal_risk`: IA mas severa que humano
    """

    __tablename__ = "care_task_medicolegal_audit_logs"

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
    ai_legal_risk_level = Column(String(16), nullable=False)
    human_validated_legal_risk_level = Column(String(16), nullable=False)
    classification = Column(String(32), nullable=False, index=True)
    ai_consent_required = Column(Boolean, nullable=False, default=False)
    human_consent_required = Column(Boolean, nullable=False, default=False)
    ai_judicial_notification_required = Column(Boolean, nullable=False, default=False)
    human_judicial_notification_required = Column(Boolean, nullable=False, default=False)
    ai_chain_of_custody_required = Column(Boolean, nullable=False, default=False)
    human_chain_of_custody_required = Column(Boolean, nullable=False, default=False)
    reviewer_note = Column(Text, nullable=True)
    reviewed_by = Column(String(80), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
