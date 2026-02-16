"""
Schemas del protocolo operativo de SCASEST para urgencias.

No sustituye diagnostico cardiologico; organiza acciones iniciales y escalado.
"""
from pydantic import BaseModel, Field


class ScasestProtocolRequest(BaseModel):
    """Entrada clinico-operativa para sospecha de SCASEST."""

    chest_pain_typical: bool = False
    dyspnea: bool = False
    syncope: bool = False
    ecg_st_depression: bool = False
    ecg_t_inversion: bool = False
    troponin_positive: bool = False
    hemodynamic_instability: bool = False
    ventricular_arrhythmias: bool = False
    refractory_angina: bool = False
    contraindication_antiplatelet: bool = False
    contraindication_anticoagulation: bool = False
    heart_rate_bpm: int | None = Field(default=None, ge=0)
    systolic_bp: int | None = Field(default=None, ge=20)
    oxygen_saturation_percent: int | None = Field(default=None, ge=40, le=100)
    grace_score: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=2000)


class ScasestProtocolRecommendation(BaseModel):
    """Salida estructurada para manejo operativo inicial de SCASEST."""

    scasest_suspected: bool
    high_risk_scasest: bool
    diagnostic_actions: list[str]
    initial_treatment_actions: list[str]
    escalation_actions: list[str]
    alerts: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskScasestProtocolResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: ScasestProtocolRecommendation
