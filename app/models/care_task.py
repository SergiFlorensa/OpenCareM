"""
CareTask Model - Unidad de trabajo clinico-operativa (no diagnostica).

Este modelo convive con `Task` durante la transicion de dominio.
La idea es mantener compatibilidad mientras introducimos estructura
mas cercana a operaciones reales del sector salud.
"""
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class CareTask(Base):
    """
    Representa una tarea operativa del contexto clinico.

    Importante:
    - No guarda diagnosticos.
    - No reemplaza decision humana.
    - Solo organiza y prioriza operacion.
    """

    __tablename__ = "care_tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Prioridad operativa para flujo clinico.
    clinical_priority = Column(String(20), nullable=False, index=True, default="medium")

    # Especialidad responsable del caso (ej: cardiology, emergency, lab).
    specialty = Column(String(80), nullable=False, index=True, default="general")

    # Referencia funcional de paciente para continuidad longitudinal de visitas.
    patient_reference = Column(String(120), nullable=True, index=True)

    # Tiempo objetivo de atencion en minutos.
    sla_target_minutes = Column(Integer, nullable=False, default=240)

    # Si el caso exige validacion humana explicita antes de cerrar.
    human_review_required = Column(Boolean, nullable=False, default=True)

    # Estado equivalente al flujo de tareas actual.
    completed = Column(Boolean, nullable=False, default=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"CareTask(id={self.id}, title='{self.title}', "
            f"clinical_priority='{self.clinical_priority}', completed={self.completed})"
        )
