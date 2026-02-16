"""
Schemas para soporte operativo de oftalmologia en urgencias.

No sustituye protocolos institucionales ni criterio clinico especializado.
"""
from pydantic import BaseModel, Field


class OphthalmologySupportProtocolRequest(BaseModel):
    """Entrada clinico-operativa para priorizacion oftalmologica en urgencias."""

    sudden_visual_loss: bool = False
    visual_loss_progressive_over_months: bool = False

    fundus_flame_hemorrhages_present: bool = False
    fundus_papilledema_present: bool = False
    cotton_wool_exudates_present: bool = False
    cherry_red_spot_present: bool = False
    diffuse_retinal_whitening_present: bool = False
    intraocular_pressure_mmhg: float | None = Field(default=None, ge=0, le=80)

    embolic_arrhythmia_suspected: bool = False
    antiarrhythmic_management_planned: bool = False

    anisocoria_present: bool = False
    anisocoria_worse_in_darkness: bool = False
    anisocoria_worse_in_bright_light: bool = False
    relative_afferent_pupillary_defect_present: bool = False
    optic_nerve_disease_suspected: bool = False
    extensive_retinal_disease_suspected: bool = False
    posterior_communicating_aneurysm_suspected: bool = False
    compressive_third_nerve_signs_present: bool = False

    abrupt_conjunctival_reaction_after_exposure: bool = False
    palpebral_edema_or_erythema_present: bool = False
    chemosis_present: bool = False
    intense_itching_present: bool = False
    tearing_present: bool = False
    ocular_pain_present: bool = False
    long_term_diabetes_present: bool = False

    cataract_surgery_planned: bool = False
    tamsulosin_or_alpha_blocker_active: bool = False
    intracameral_phenylephrine_planned: bool = False
    recommendation_to_stop_tamsulosin_preop: bool = False
    index_myopia_shift_present: bool = False
    high_myopia_present: bool = False
    young_patient_for_lens_surgery: bool = False

    drusen_present: bool = False
    retinal_pigment_epithelium_thinning_or_changes: bool = False
    neovascular_membrane_or_exudation_present: bool = False
    anti_vegf_planned: bool = False

    notes: str | None = Field(default=None, max_length=2000)


class OphthalmologySupportProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo oftalmologico."""

    severity_level: str
    critical_alerts: list[str]
    vascular_triage_actions: list[str]
    neuro_ophthalmology_actions: list[str]
    inflammation_actions: list[str]
    cataract_safety_actions: list[str]
    dmae_actions: list[str]
    safety_blocks: list[str]
    interpretability_trace: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskOphthalmologySupportResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: OphthalmologySupportProtocolRecommendation
