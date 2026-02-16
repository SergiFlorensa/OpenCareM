"""
Auditoria de calidad para screening operativo avanzado.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class CareTaskScreeningAuditLog(Base):
    """
    Compara recomendacion IA de screening con validacion humana.

    `classification`:
    - `match`: mismo nivel de riesgo global
    - `under_screening`: IA menos severa que humano
    - `over_screening`: IA mas severa que humano
    """

    __tablename__ = "care_task_screening_audit_logs"

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
    ai_geriatric_risk_level = Column(String(16), nullable=False)
    human_validated_risk_level = Column(String(16), nullable=False)
    classification = Column(String(32), nullable=False, index=True)
    ai_hiv_screening_suggested = Column(Boolean, nullable=False, default=False)
    human_hiv_screening_suggested = Column(Boolean, nullable=False, default=False)
    ai_sepsis_route_suggested = Column(Boolean, nullable=False, default=False)
    human_sepsis_route_suggested = Column(Boolean, nullable=False, default=False)
    ai_persistent_covid_suspected = Column(Boolean, nullable=False, default=False)
    human_persistent_covid_suspected = Column(Boolean, nullable=False, default=False)
    ai_long_acting_candidate = Column(Boolean, nullable=False, default=False)
    human_long_acting_candidate = Column(Boolean, nullable=False, default=False)
    reviewer_note = Column(Text, nullable=True)
    reviewed_by = Column(String(80), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
