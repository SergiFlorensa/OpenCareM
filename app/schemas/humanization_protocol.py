"""
Schemas del protocolo de humanizacion pediatrica para alta complejidad.

Este modulo aporta soporte operativo para comunicacion, familia y
coordinacion multidisciplinar. No realiza diagnostico medico.
"""
from typing import Literal

from pydantic import BaseModel, Field


class HumanizationProtocolRequest(BaseModel):
    """Entrada operativa para construir recomendacion humanizada en pediatria."""

    patient_age_years: int = Field(..., ge=0)
    primary_context: Literal[
        "neuro_oncologia",
        "ensayo_clinico",
        "hospitalizacion_compleja",
        "seguimiento",
    ] = "hospitalizacion_compleja"
    emotional_distress_level: int = Field(..., ge=0, le=10)
    family_understanding_level: int = Field(..., ge=0, le=10)
    family_present: bool = True
    sibling_support_needed: bool = False
    social_risk_flags: list[str] = Field(default_factory=list)
    needs_spiritual_support: bool = False
    multidisciplinary_team: list[str] = Field(default_factory=list)
    has_clinical_trial_option: bool = False
    informed_consent_status: Literal["pendiente", "explicado", "firmado", "rechazado"] = "pendiente"
    professional_burnout_risk: Literal["low", "medium", "high"] = "low"
    notes: str | None = Field(default=None, max_length=3000)


class HumanizationProtocolRecommendation(BaseModel):
    """Salida estructurada de acciones operativas de humanizacion."""

    communication_plan: list[str]
    family_integration_plan: list[str]
    support_plan: list[str]
    innovation_coordination_plan: list[str]
    team_care_plan: list[str]
    alerts: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskHumanizationProtocolResponse(BaseModel):
    """Respuesta final trazable para endpoint de humanizacion pediatrica."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: HumanizationProtocolRecommendation
