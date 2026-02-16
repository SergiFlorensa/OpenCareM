"""
Schemas para soporte operativo de nefrologia en urgencias.

No sustituye protocolos institucionales ni criterio clinico especializado.
"""
from pydantic import BaseModel, Field


class NephrologySupportProtocolRequest(BaseModel):
    """Entrada clinico-operativa para priorizacion nefrologica en urgencias."""

    acute_kidney_injury_present: bool = False
    urine_sodium_mmol_l: float | None = Field(default=None, ge=0, le=300)
    abrupt_anuria_present: bool = False
    hydronephrosis_ultrasound_present: bool = False

    proteinuria_present: bool = False
    microhematuria_present: bool = False
    dysmorphic_rbc_present: bool = False
    bilateral_ground_glass_ct_present: bool = False
    pulmonary_hemorrhage_present: bool = False
    acute_anemization_present: bool = False
    anti_gbm_positive: bool = False
    rapidly_progressive_gn_requires_dialysis: bool = False
    platelet_count_typo_suspected: bool = False

    ph: float | None = Field(default=None, ge=6.5, le=7.8)
    hco3_mmol_l: float | None = Field(default=None, ge=0, le=60)
    pco2_mm_hg: float | None = Field(default=None, ge=0, le=120)

    refractory_metabolic_acidosis: bool = False
    refractory_hyperkalemia_with_ecg_changes: bool = False
    severe_tumor_hypercalcemia_neurologic: bool = False
    dialyzable_intoxication_lithium: bool = False
    dialyzable_intoxication_salicylates: bool = False
    refractory_volume_overload_pulmonary_edema: bool = False
    uremic_encephalopathy: bool = False
    uremic_pericarditis: bool = False

    diabetic_nephropathy_suspected: bool = False
    proteinuric_ckd_present: bool = False
    sglt2_planned: bool = False
    acei_active: bool = False
    arb_active: bool = False
    diabetic_retinopathy_present: bool = False

    iga_mesangial_deposits_biopsy: bool = False
    c3_mesangial_deposits_biopsy: bool = False
    proteinuria_g_24h: float | None = Field(default=None, ge=0, le=30)
    months_conservative_therapy: int | None = Field(default=None, ge=0, le=60)

    recent_drug_trigger_present: bool = False
    suspected_drug_name: str | None = Field(default=None, max_length=120)
    fever_present: bool = False
    rash_present: bool = False
    eosinophilia_present: bool = False
    no_improvement_after_48_72h: bool = False

    anca_positive: bool = False
    crescents_percent_glomeruli: float | None = Field(default=None, ge=0, le=100)
    pauci_immune_if_negative: bool = False

    notes: str | None = Field(default=None, max_length=2000)


class NephrologySupportProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo de nefrologia."""

    severity_level: str
    critical_alerts: list[str]
    aki_classification: str
    acid_base_assessment: list[str]
    diagnostic_actions: list[str]
    therapeutic_actions: list[str]
    dialysis_alerts: list[str]
    nephroprotection_actions: list[str]
    pharmacologic_safety_alerts: list[str]
    glomerular_interstitial_flags: list[str]
    interpretability_trace: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskNephrologySupportResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: NephrologySupportProtocolRecommendation
