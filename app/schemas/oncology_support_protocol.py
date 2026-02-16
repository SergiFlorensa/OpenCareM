"""
Schemas para soporte operativo de oncologia en urgencias.

No sustituye protocolos institucionales ni criterio clinico especializado.
"""
from pydantic import BaseModel, Field


class OncologySupportProtocolRequest(BaseModel):
    """Entrada clinico-operativa para priorizacion oncológica en urgencias."""

    checkpoint_inhibitor_class: str | None = Field(default=None, max_length=40)
    checkpoint_agent_name: str | None = Field(default=None, max_length=80)

    metastatic_crc_unresectable: bool = False
    first_line_setting: bool = False
    dmmr_present: bool = False
    msi_high_present: bool = False

    immune_hepatotoxicity_suspected: bool = False
    hepatic_toxicity_grade: int | None = Field(default=None, ge=1, le=5)
    transaminases_multiple_uln: float | None = Field(default=None, ge=0, le=50)
    total_bilirubin_mg_dl: float | None = Field(default=None, ge=0, le=60)
    immunotherapy_suspended: bool = False
    prednisone_mg_kg_day: float | None = Field(default=None, ge=0, le=10)
    refractory_to_steroids: bool = False
    infliximab_considered: bool = False
    rechallenge_considered_after_resolution: bool = False

    trastuzumab_planned: bool = False
    anthracycline_planned: bool = False
    baseline_lvef_assessed: bool = False
    baseline_lvef_percent: float | None = Field(default=None, ge=0, le=100)

    temperature_c_single: float | None = Field(default=None, ge=30, le=45)
    fever_over_38_more_than_1h: bool = False
    fever_three_measurements_24h: bool = False
    absolute_neutrophil_count_mm3: int | None = Field(default=None, ge=0, le=50000)
    anc_expected_to_drop_below_500: bool = False
    perioperative_or_adjuvant_context: bool = False
    palliative_later_line_context: bool = False

    bone_sarcoma_post_neoadjuvant_specimen_available: bool = False
    necrosis_rate_percent: float | None = Field(default=None, ge=0, le=100)
    ewing_sarcoma_suspected: bool = False
    ewsr1_rearrangement_documented: bool = False

    notes: str | None = Field(default=None, max_length=2000)


class OncologySupportProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo oncológico."""

    severity_level: str
    critical_alerts: list[str]
    immunotherapy_mechanism_notes: list[str]
    biomarker_strategy: list[str]
    toxicity_management_actions: list[str]
    cardio_oncology_actions: list[str]
    febrile_neutropenia_actions: list[str]
    sarcoma_response_actions: list[str]
    interpretability_trace: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskOncologySupportResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: OncologySupportProtocolRecommendation
