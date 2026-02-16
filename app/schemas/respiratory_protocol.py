"""
Schemas del protocolo respiratorio para urgencias.

El objetivo es soporte operativo precoz en triaje y tratamiento,
sin sustituir criterio clinico profesional.
"""
from typing import Literal

from pydantic import BaseModel, Field


class RespiratoryProtocolRequest(BaseModel):
    """Entrada clinico-operativa para evaluar riesgo y acciones tempranas."""

    age_years: int = Field(..., ge=0)
    immunosuppressed: bool = False
    comorbidities: list[str] = Field(default_factory=list)
    vaccination_updated_last_12_months: bool | None = None
    symptom_onset_hours: int | None = Field(default=None, ge=0)
    hours_since_er_arrival: int | None = Field(default=None, ge=0)
    current_systolic_bp: int | None = Field(default=None, ge=20)
    baseline_systolic_bp: int | None = Field(default=None, ge=20)
    needs_oxygen: bool = False
    pathogen_suspected: Literal["covid", "gripe", "vrs", "indeterminado"] = "indeterminado"
    antigen_result: Literal["positivo", "negativo", "no_realizado"] = "no_realizado"
    oral_antiviral_contraindicated: bool = False
    notes: str | None = Field(default=None, max_length=2000)


class RespiratoryProtocolRecommendation(BaseModel):
    """Salida estructurada de recomendacion operativa respiratoria."""

    vulnerable_patient: bool
    shock_relative_suspected: bool
    diagnostic_plan: list[str]
    antiviral_plan: list[str]
    isolation_plan: list[str]
    alerts: list[str]
    non_clinical_warning: str


class CareTaskRespiratoryProtocolResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: RespiratoryProtocolRecommendation
