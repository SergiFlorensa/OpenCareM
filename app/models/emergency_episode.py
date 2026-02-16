"""
Modelo de episodio de urgencias para representar el flujo extremo-a-extremo.
"""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class EmergencyEpisode(Base):
    """
    Representa un episodio operativo de urgencias desde llegada hasta cierre.

    Se alinea al flujo:
    llegada -> triaje -> evaluacion -> pruebas/tratamiento -> decision -> cierre.
    """

    __tablename__ = "emergency_episodes"

    id = Column(Integer, primary_key=True, index=True)
    care_task_id = Column(
        Integer,
        ForeignKey("care_tasks.id", ondelete="SET NULL"),
        nullable=True,
    )

    # walk_in | ambulance_prealert
    origin = Column(String(32), nullable=False, index=True)
    current_stage = Column(String(64), nullable=False, index=True)
    # time_dependent | non_critical
    priority_risk = Column(String(32), nullable=True, index=True)
    # discharge | admission | transfer | ap_referral
    disposition = Column(String(32), nullable=True, index=True)
    notes = Column(Text, nullable=True)

    arrived_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    triaged_at = Column(DateTime(timezone=True), nullable=True)
    medical_evaluation_at = Column(DateTime(timezone=True), nullable=True)
    diagnostics_completed_at = Column(DateTime(timezone=True), nullable=True)
    disposition_decided_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
