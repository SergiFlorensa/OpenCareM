"""
Schemas para soporte operativo de sospecha de reaccion por Anisakis.

No sustituye protocolos institucionales ni criterio clinico especializado.
"""
from pydantic import BaseModel, Field


class AnisakisSupportProtocolRequest(BaseModel):
    """Entrada clinico-operativa para priorizacion de sospecha por anisakis."""

    fish_ingestion_last_hours: float | None = Field(default=None, ge=0, le=168)
    raw_or_undercooked_fish_exposure: bool = False
    preparation_risk_present: bool = False
    insufficient_cooking_suspected: bool = False

    digestive_symptoms_present: bool = False
    urticaria_present: bool = False
    angioedema_present: bool = False
    respiratory_compromise_present: bool = False
    hypotension_present: bool = False
    anaphylaxis_present: bool = False

    specific_ige_requested: bool = False
    anisakis_specific_ige_positive: bool = False
    prick_test_positive: bool = False

    cooking_temperature_c: float | None = Field(default=None, ge=-30, le=300)
    freezing_temperature_c: float | None = Field(default=None, ge=-80, le=40)
    freezing_duration_hours: float | None = Field(default=None, ge=0, le=720)
    deep_sea_eviscerated_or_ultrafrozen_fish_consumed: bool = False
    tail_cut_preferred_consumption: bool = False

    notes: str | None = Field(default=None, max_length=2000)


class AnisakisSupportProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo anisakis."""

    severity_level: str
    critical_alerts: list[str]
    diagnostic_actions: list[str]
    acute_management_actions: list[str]
    discharge_prevention_actions: list[str]
    safety_blocks: list[str]
    interpretability_trace: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskAnisakisSupportResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: AnisakisSupportProtocolRecommendation
