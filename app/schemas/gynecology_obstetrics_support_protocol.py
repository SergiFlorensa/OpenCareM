"""
Schemas para soporte operativo de ginecologia y obstetricia en urgencias.

No sustituye protocolos institucionales ni criterio clinico especializado.
"""
from typing import Literal

from pydantic import BaseModel, Field


class GynecologyObstetricsSupportProtocolRequest(BaseModel):
    """Entrada clinico-operativa para priorizacion gineco-obstetrica."""

    patient_age_years: int | None = Field(default=None, ge=10, le=65)

    endometrial_cancer_diagnosed: bool = False
    age_at_endometrial_cancer_diagnosis: int | None = Field(default=None, ge=10, le=100)
    family_lynch_related_cancers_count: int = Field(default=0, ge=0, le=30)
    family_generations_affected_count: int = Field(default=0, ge=0, le=10)
    family_lynch_related_cancers_under_50_count: int = Field(default=0, ge=0, le=20)
    known_mismatch_repair_mutation: bool = False

    endometrial_tumor_molecular_profile: Literal[
        "unknown",
        "pole_ultramutated",
        "p53_mutated_serous_like",
        "mismatch_repair_deficient",
        "no_specific_profile",
    ] = "unknown"
    breast_cancer_subtype: Literal[
        "unknown",
        "triple_negative",
        "luminal_a",
        "other",
    ] = "unknown"

    reproductive_age_with_abdominal_pain_or_bleeding: bool = False
    pregnancy_test_positive: bool = False
    severe_abdominal_pain: bool = False
    vaginal_spotting_present: bool = False
    free_intraperitoneal_fluid_on_ultrasound: bool = False
    dilated_or_violaceous_tube_on_ultrasound: bool = False

    cyclic_pelvic_pain_with_menses: bool = False
    deep_endometriosis_digestive_implants_suspected: bool = False

    gestational_age_weeks: int | None = Field(default=None, ge=0, le=45)
    first_trimester_crl_available: bool = False
    lmp_vs_first_trimester_ultrasound_difference_days: int | None = Field(
        default=None,
        ge=-40,
        le=40,
    )
    fetal_percentile: float | None = Field(default=None, ge=0, le=100)

    monochorionic_pregnancy: bool = False
    recipient_amniotic_vertical_pocket_cm: float | None = Field(default=None, ge=0, le=30)
    donor_amniotic_vertical_pocket_cm: float | None = Field(default=None, ge=0, le=30)
    donor_bladder_visible: bool | None = None
    recipient_bladder_distended: bool = False

    varicella_exposure_in_pregnancy: bool = False
    varicella_igg_positive: bool | None = None
    hours_since_varicella_exposure: int | None = Field(default=None, ge=0, le=24 * 30)
    maternal_varicella_confirmed: bool = False
    days_from_maternal_varicella_to_delivery: int | None = Field(default=None, ge=-30, le=30)
    live_attenuated_vaccine_requested_during_pregnancy: bool = False

    postpartum_preeclampsia_suspected: bool = False
    systolic_bp_mm_hg: int | None = Field(default=None, ge=50, le=300)
    target_organ_damage_present: bool = False
    proteinuria_present: bool | None = None
    severe_features_present: bool = False
    iv_antihypertensive_started: bool = False
    magnesium_sulfate_started: bool = False
    preeclampsia_labeled_as_moderate: bool = False

    oral_contraception_planned: bool = False
    baseline_history_completed: bool = False
    baseline_bp_recorded: bool = False
    baseline_bmi_recorded: bool = False
    routine_cytology_required_before_ocp: bool = False
    routine_thrombophilia_panel_required_before_ocp: bool = False
    progestin_generation: Literal[
        "unknown",
        "second_levonorgestrel",
        "third",
        "fourth",
    ] = "unknown"

    gestational_diabetes_one_step_75g_performed: bool = False
    fasting_glucose_mg_dl: float | None = Field(default=None, ge=20, le=400)
    glucose_1h_mg_dl: float | None = Field(default=None, ge=20, le=500)
    glucose_2h_mg_dl: float | None = Field(default=None, ge=20, le=500)

    fetal_neuroprotection_magnesium_requested: bool = False
    risk_of_imminent_preterm_birth: bool = False
    ruptured_membranes_present: bool = False
    cervix_long_without_contractions: bool = False

    chronic_lymphedema_post_oncologic_surgery: bool = False
    diuretic_prescription_requested: bool = False

    notes: str | None = Field(default=None, max_length=2000)


class GynecologyObstetricsSupportProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo gineco-obstetrico."""

    severity_level: str
    critical_alerts: list[str]
    hereditary_oncology_actions: list[str]
    urgent_gynecology_actions: list[str]
    obstetric_monitoring_actions: list[str]
    infectious_risk_actions: list[str]
    preeclampsia_actions: list[str]
    pharmacology_prevention_actions: list[str]
    safety_blocks: list[str]
    interpretability_trace: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskGynecologyObstetricsSupportResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: GynecologyObstetricsSupportProtocolRecommendation
