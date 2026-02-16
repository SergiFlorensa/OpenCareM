"""
Schemas para soporte operativo de cuidados paliativos en urgencias.

No sustituye protocolos institucionales ni criterio clinico especializado.
"""
from pydantic import BaseModel, Field


class PalliativeSupportProtocolRequest(BaseModel):
    """Entrada clinico-operativa para priorizacion paliativa en urgencias."""

    patient_rejects_life_prolonging_treatment: bool = False
    informed_consequences_documented: bool = False
    professional_futility_assessment_documented: bool = False
    effort_adequation_planned: bool = False

    aid_in_dying_request_expressed: bool = False
    aid_in_dying_request_reiterated: bool = False
    aid_in_dying_process_formalized_per_lo_3_2021: bool = False

    renal_clearance_ml_min: float | None = Field(default=None, ge=0, le=300)
    renal_failure_present: bool = False
    current_opioid_name: str | None = Field(default=None, max_length=60)
    morphine_active: bool = False
    chronic_pain_baseline_present: bool = False
    long_acting_opioid_active: bool = False
    breakthrough_pain_present: bool = False
    rapid_onset_rescue_opioid_planned: bool = False
    transmucosal_fentanyl_planned: bool = False

    advanced_dementia_present: bool = False
    dysphagia_or_oral_intake_refusal: bool = False
    enteral_tube_sng_or_peg_planned: bool = False
    comfort_feeding_planned: bool = False
    aspiration_infection_terminal_context: bool = False
    shared_advance_care_plan_available: bool = False
    hospital_admission_planned: bool = False

    renal_function_deterioration_present: bool = False
    intense_somnolence_present: bool = False
    tactile_hallucinations_present: bool = False
    delirium_present: bool = False
    reversible_cause_addressed: bool = False
    neuroleptic_planned: bool = False
    persistent_delirium_after_cause_treatment: bool = False
    steroid_psychosis_hyperactive_profile: bool = False

    notes: str | None = Field(default=None, max_length=2000)


class PalliativeSupportProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo paliativo."""

    severity_level: str
    critical_alerts: list[str]
    ethical_legal_actions: list[str]
    opioid_safety_actions: list[str]
    dementia_comfort_actions: list[str]
    delirium_management_actions: list[str]
    safety_blocks: list[str]
    interpretability_trace: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskPalliativeSupportResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: PalliativeSupportProtocolRecommendation
