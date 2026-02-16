"""
Schemas para soporte operativo de endocrinologia y metabolismo en urgencias.

No sustituye protocolos institucionales ni criterio clinico especializado.
"""
from pydantic import BaseModel, Field


class EndocrinologySupportProtocolRequest(BaseModel):
    """Entrada clinico-operativa para priorizacion endocrino-metabolica en urgencias."""

    suspected_hypoglycemia: bool = False
    fasting_context: bool = False
    ketosis_present: bool = False
    lactic_acidosis_present: bool = False
    hyperammonemia_present: bool = False
    dicarboxylic_acids_elevated: bool = False

    insulin_resistance_suspected: bool = False
    hexokinase2_downregulation_reported: bool = False
    hepatic_foxo1_activation_reported: bool = False

    pediatric_patient: bool = False
    pediatric_growth_deceleration: bool = False
    tsh_elevated: bool = False
    free_t4_low: bool = False
    anti_tpo_positive: bool = False
    anti_thyroglobulin_positive: bool = False
    diffuse_firm_painless_goiter: bool = False

    medullary_thyroid_carcinoma_suspected: bool = False
    preop_urinary_metanephrines_completed: bool = False
    ret_genetic_study_completed: bool = False
    calcitonin_available: bool = False
    cea_available: bool = False
    thyroglobulin_followup_planned: bool = False
    central_or_lateral_nodes_suspected: bool = False

    hyponatremia_present: bool = False
    plasma_hypoosmolarity_present: bool = False
    inappropriately_concentrated_urine: bool = False
    serum_sodium_mmol_l: float | None = Field(default=None, ge=90, le=170)
    neurologic_symptoms_present: bool = False
    siadh_course_chronic: bool = False
    tolvaptan_planned: bool = False
    water_restriction_planned: bool = False

    hyperprolactinemia_present: bool = False
    prolactin_ng_ml: float | None = Field(default=None, ge=0, le=10000)
    pregnancy_ruled_out: bool = False
    dopamine_antagonist_exposure: bool = False
    primary_hypothyroidism_present: bool = False
    pituitary_mri_planned: bool = False

    refractory_hypotension_present: bool = False
    abdominal_pain_or_vomiting_present: bool = False
    skin_mucosal_hyperpigmentation_present: bool = False

    adrenal_incidentaloma_present: bool = False
    isolated_serum_cortisol_screening_planned: bool = False
    aldosterone_renin_ratio_completed: bool = False
    overnight_dexamethasone_1mg_test_completed: bool = False
    urinary_metanephrines_24h_completed: bool = False
    hypertension_present: bool = False

    t1d_autoimmunity_positive: bool = False
    glucose_normal: bool = False
    prediabetes_range: bool = False
    diabetes_criteria_present: bool = False

    obesity_present: bool = False
    high_cardiovascular_risk: bool = False
    weight_loss_priority: bool = False
    glp1_ra_planned: bool = False
    pioglitazone_planned: bool = False
    sulfonylurea_planned: bool = False
    insulin_planned: bool = False

    hypercalcemia_present: bool = False
    thiazide_exposure: bool = False
    chronic_alcohol_use: bool = False
    hypertriglyceridemia_present: bool = False
    hdl_low_present: bool = False

    notes: str | None = Field(default=None, max_length=2000)


class EndocrinologySupportProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo endocrino-metabolico."""

    severity_level: str
    critical_alerts: list[str]
    diagnostic_actions: list[str]
    therapeutic_actions: list[str]
    pharmacologic_safety_alerts: list[str]
    screening_checklist: list[str]
    diabetes_staging_support: list[str]
    metabolic_context_flags: list[str]
    interpretability_trace: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskEndocrinologySupportResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: EndocrinologySupportProtocolRecommendation
