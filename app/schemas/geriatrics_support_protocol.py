"""
Schemas para soporte operativo de geriatria y fragilidad en urgencias.

No sustituye protocolos institucionales ni criterio clinico especializado.
"""
from pydantic import BaseModel, Field


class GeriatricsSupportProtocolRequest(BaseModel):
    """Entrada clinico-operativa para priorizacion geriatrica en urgencias."""

    patient_age_years: int | None = Field(default=None, ge=0, le=130)

    mesangial_matrix_expansion_present: bool = False
    glomerular_basement_membrane_thickening_present: bool = False
    glomerulosclerosis_present: bool = False
    nephrology_red_flags_present: bool = False

    cerebral_volume_loss_age_expected: bool = False
    widened_sulci_or_ventricles_present: bool = False
    sinus_node_pacemaker_cell_loss_suspected: bool = False
    tracheal_costal_cartilage_calcification_present: bool = False

    prolonged_immobility_present: bool = False
    nitrogen_balance_negative: bool = False
    high_protein_support_plan_active: bool = False
    insulin_resistance_signs_present: bool = False
    resting_tachycardia_present: bool = False
    psychomotor_slowing_present: bool = False

    delirium_suspected: bool = False
    infectious_trigger_suspected: bool = False
    severe_behavioral_disturbance_present: bool = False
    risperidone_active: bool = False
    behavioral_stabilization_after_causal_treatment: bool = False
    insomnia_present: bool = False
    benzodiazepine_planned: bool = False
    dementia_progression_assessment_planned_during_acute_event: bool = False

    symptomatic_atrophic_vaginitis: bool = False
    topical_vaginal_estrogen_active: bool = False
    lidocaine_patch_planned_for_general_joint_pain: bool = False
    localized_neuropathic_pain_present: bool = False
    copd_gold_stage: int | None = Field(default=None, ge=1, le=4)
    inhaled_corticosteroid_planned: bool = False
    open_wound_present: bool = False
    tetanus_booster_planned: bool = False
    tetanus_doses_completed: bool | None = None
    years_since_last_tetanus_dose: int | None = Field(default=None, ge=0, le=80)

    notes: str | None = Field(default=None, max_length=2000)


class GeriatricsSupportProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo geriatrico."""

    severity_level: str
    critical_alerts: list[str]
    aging_context_interpretation: list[str]
    diagnostic_actions: list[str]
    therapeutic_actions: list[str]
    pharmacologic_optimization_actions: list[str]
    safety_blocks: list[str]
    interpretability_trace: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskGeriatricsSupportResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: GeriatricsSupportProtocolRecommendation
