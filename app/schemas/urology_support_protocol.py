"""
Schemas para soporte operativo de urologia en urgencias.

No sustituye protocolos institucionales ni criterio clinico especializado.
"""
from pydantic import BaseModel, Field


class UrologySupportProtocolRequest(BaseModel):
    """Entrada clinico-operativa para priorizacion urologica en urgencias."""

    diabetes_mellitus_poor_control: bool = False
    hypertension_present: bool = False
    urinary_tract_gas_on_imaging: bool = False
    urinary_obstruction_lithiasis_suspected: bool = False
    suspected_pathogen_e_coli: bool = False
    xanthogranulomatous_chronic_pattern_suspected: bool = False

    colicky_flank_pain_present: bool = False
    vomiting_present: bool = False
    anuria_present: bool = False
    creatinine_mg_dl: float | None = Field(default=None, ge=0, le=30)
    egfr_ml_min: float | None = Field(default=None, ge=0, le=200)
    bilateral_pyelocaliceal_dilation_on_ultrasound: bool = False
    urgent_urinary_diversion_planned: bool = False
    urgent_ct_planned_before_diversion: bool = False

    genital_trauma_during_erection: bool = False
    penile_edema_or_expansive_hematoma_present: bool = False
    flaccid_penis_after_trauma: bool = False
    urethral_injury_suspected: bool = False
    bladder_catheterization_planned: bool = False
    urgent_surgical_review_planned: bool = False
    cavernosal_blood_gas_planned: bool = False

    localized_renal_tumor_suspected: bool = False
    renal_mass_cm: float | None = Field(default=None, ge=0, le=30)
    solitary_functional_kidney: bool = False
    contralateral_kidney_atrophy_present: bool = False
    planned_partial_nephrectomy: bool = False
    planned_radical_nephrectomy: bool = False

    prostate_mri_anterior_lesion_present: bool = False
    transrectal_biopsy_planned: bool = False
    transperineal_fusion_biopsy_planned: bool = False

    prostate_metastatic_high_volume: bool = False
    gleason_score: int | None = Field(default=None, ge=2, le=10)
    psa_ng_ml: float | None = Field(default=None, ge=0, le=10000)
    bone_metastases_present: bool = False
    liver_metastases_present: bool = False
    lhrh_analog_planned: bool = False
    docetaxel_planned: bool = False
    novel_antiandrogen_name: str | None = Field(default=None, max_length=80)
    local_curative_treatment_planned: bool = False
    radiotherapy_planned: bool = False
    low_volume_metastatic_profile: bool = False

    notes: str | None = Field(default=None, max_length=2000)


class UrologySupportProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo urologico."""

    severity_level: str
    critical_alerts: list[str]
    infection_actions: list[str]
    obstruction_actions: list[str]
    trauma_actions: list[str]
    oncologic_actions: list[str]
    safety_blocks: list[str]
    interpretability_trace: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskUrologySupportResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: UrologySupportProtocolRecommendation
