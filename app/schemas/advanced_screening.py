"""
Schemas del motor de screening operativo avanzado.

El objetivo es priorizar riesgos y sugerir acciones de cribado en urgencias,
manteniendo interpretabilidad y validacion humana obligatoria.
"""
from typing import Literal

from pydantic import BaseModel, Field


class AdvancedScreeningRequest(BaseModel):
    """Entrada operativa para reglas de riesgo y cribado temprano."""

    age_years: int = Field(..., ge=0)
    sex: Literal["f", "m", "otro"] | None = None
    systolic_bp: int | None = Field(default=None, ge=40)
    can_walk_independently: bool | None = None
    sodium_mmol_l: float | None = None
    glucose_mg_dl: float | None = None
    heart_rate_bpm: int | None = Field(default=None, ge=20)
    oxygen_saturation_percent: int | None = Field(default=None, ge=40, le=100)
    chief_complaints: list[str] = Field(default_factory=list)
    known_conditions: list[str] = Field(default_factory=list)
    immunosuppressed: bool = False
    persistent_positive_days: int | None = Field(default=None, ge=0)
    persistent_symptoms: bool = False
    imaging_compatible_with_persistent_infection: bool = False
    stable_after_acute_phase: bool = False
    infection_context: Literal[
        "endocarditis",
        "osteomielitis",
        "infeccion_piel_tejidos_blandos",
        "otra",
        "no_aplica",
    ] = "no_aplica"


class AdvancedScreeningRecommendation(BaseModel):
    """Salida estructurada de recomendaciones de screening y riesgo."""

    geriatric_risk_level: Literal["low", "medium", "high"]
    screening_actions: list[str]
    alerts: list[str]
    alerts_generated_total: int
    alerts_suppressed_total: int
    long_acting_candidate: bool
    long_acting_rationale: str | None
    persistent_covid_suspected: bool
    persistent_covid_actions: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskAdvancedScreeningResponse(BaseModel):
    """Respuesta final trazable del endpoint de screening avanzado."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: AdvancedScreeningRecommendation
