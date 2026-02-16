"""
Schemas para soporte operativo de anestesiologia y reanimacion en urgencias.

No sustituye protocolos institucionales ni criterio clinico especializado.
"""
from pydantic import BaseModel, Field


class AnesthesiologySupportProtocolRequest(BaseModel):
    """Entrada clinico-operativa para priorizacion anestesiologica en urgencias."""

    emergency_airway_needed: bool = False
    no_preop_fasting: bool = False
    intestinal_obstruction_present: bool = False
    acute_hematemesis_present: bool = False
    full_stomach_risk_other: bool = False

    preoxygenation_minutes_planned: float | None = Field(default=None, ge=0, le=20)
    bag_mask_manual_ventilation_planned: bool = False
    expected_intubation_seconds_after_iv: int | None = Field(default=None, ge=0, le=600)
    iv_route_confirmed: bool = False
    inhaled_halogenated_induction_planned: bool = False
    hypnotic_agent: str | None = Field(default=None, max_length=60)
    neuromuscular_blocker_agent: str | None = Field(default=None, max_length=60)
    sellick_maneuver_planned: bool = False
    tube_position_verified: bool = False
    cuff_inflated: bool = False

    severe_perineal_or_pelvic_internal_pain: bool = False
    presacral_mass_present: bool = False
    neuropathic_pain_component: bool = False
    visceral_pain_component: bool = False
    vascular_pain_component: bool = False
    opioid_response_insufficient: bool = False
    opioid_escalation_not_tolerated: bool = False

    upper_abdominal_visceral_pain: bool = False
    pelvic_genital_autonomic_pain: bool = False
    perineal_external_genital_pain: bool = False
    perineal_pelvic_internal_pain: bool = False

    notes: str | None = Field(default=None, max_length=2000)


class AnesthesiologySupportProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo anestesiologico."""

    severity_level: str
    critical_alerts: list[str]
    rapid_sequence_induction_actions: list[str]
    airway_safety_blocks: list[str]
    sympathetic_block_recommendations: list[str]
    differential_block_recommendations: list[str]
    interpretability_trace: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskAnesthesiologySupportResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: AnesthesiologySupportProtocolRecommendation
