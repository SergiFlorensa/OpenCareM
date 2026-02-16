"""
Schemas para soporte operativo reuma-inmuno en urgencias.

No sustituye protocolos institucionales ni criterio clinico especializado.
"""
from pydantic import BaseModel, Field


class RheumImmunoSupportProtocolRequest(BaseModel):
    """Entrada clinico-operativa para decision reumatologica/inmunologica temprana."""

    lupus_known: bool = False
    new_unexplained_dyspnea: bool = False
    prior_aptt_prolonged: bool = False

    systemic_sclerosis_known: bool = False
    raynaud_phenomenon_active: bool = False
    active_digital_ischemic_ulcers: bool = False

    giant_cell_arteritis_suspected: bool = False
    esr_mm_h: float | None = Field(default=None, ge=0, le=200)

    proximal_symmetric_weakness: bool = False
    myalgia_prominent: bool = False
    anti_mda5_positive: bool = False
    interstitial_lung_disease_signs: bool = False

    recurrent_oral_aphthae: bool = False
    ocular_inflammation_or_uveitis: bool = False
    erythema_nodosum_present: bool = False
    cerebral_parenchymal_involvement: bool = False
    cyclosporine_planned: bool = False

    elderly_male_with_acute_monoarthritis: bool = False
    intercurrent_trigger_present: bool = False
    wrist_xray_chondrocalcinosis: bool = False
    knee_xray_chondrocalcinosis: bool = False
    pubic_symphysis_xray_chondrocalcinosis: bool = False

    young_male_with_inflammatory_back_pain: bool = False
    sacroiliitis_on_imaging: bool = False
    peripheral_joint_involvement: bool = False

    pregnancy_ongoing: bool = False
    anti_ro_positive: bool = False
    anti_la_positive: bool = False
    fetal_conduction_or_myocardial_risk: bool = False
    fluorinated_corticosteroids_started: bool = False
    anti_desmoglein3_positive: bool = False
    anti_acetylcholine_receptor_positive: bool = False

    igg4_related_disease_suspected: bool = False
    igg4_lymphoplasmacytic_infiltrate: bool = False
    igg4_obliterative_phlebitis: bool = False
    igg4_storiform_fibrosis: bool = False

    aps_clinical_event_present: bool = False
    aps_laboratory_criterion_present: bool = False
    thrombocytopenia_present: bool = False

    notes: str | None = Field(default=None, max_length=2000)


class RheumImmunoSupportProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo reuma-inmuno."""

    severity_level: str
    critical_alerts: list[str]
    diagnostic_actions: list[str]
    therapeutic_actions: list[str]
    safety_alerts: list[str]
    imaging_screening_actions: list[str]
    maternal_fetal_actions: list[str]
    data_model_flags: list[str]
    interpretability_trace: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskRheumImmunoSupportResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: RheumImmunoSupportProtocolRecommendation
