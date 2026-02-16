"""
Schemas del protocolo operativo de sepsis para urgencias.

El objetivo es acelerar deteccion, bundle inicial y escalado, sin
sustituir criterio clinico humano.
"""
from pydantic import BaseModel, Field


class SepsisProtocolRequest(BaseModel):
    """Entrada clinico-operativa para evaluar riesgo de sepsis/shock septico."""

    suspected_infection: bool = True
    respiratory_rate_rpm: int | None = Field(default=None, ge=0)
    systolic_bp: int | None = Field(default=None, ge=20)
    altered_mental_status: bool = False
    lactate_mmol_l: float | None = Field(default=None, ge=0)
    map_mmhg: int | None = Field(default=None, ge=0)
    blood_cultures_collected: bool = False
    antibiotics_started: bool = False
    fluid_bolus_ml_per_kg: int | None = Field(default=None, ge=0)
    vasopressor_started: bool = False
    time_since_detection_minutes: int | None = Field(default=None, ge=0)
    probable_focus: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=2000)


class SepsisProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo de sepsis."""

    qsofa_score: int
    high_sepsis_risk: bool
    septic_shock_suspected: bool
    one_hour_bundle_actions: list[str]
    escalation_actions: list[str]
    alerts: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskSepsisProtocolResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: SepsisProtocolRecommendation
