"""
Schemas para soporte operativo neurologico en urgencias.

No sustituye protocolos de neurologia/neurocirugia ni juicio clinico presencial.
"""
from pydantic import BaseModel, Field


class NeurologySupportProtocolRequest(BaseModel):
    """Entrada clinico-operativa para decision neurologica temprana."""

    sudden_severe_headache: bool = False
    cranial_ct_subarachnoid_hyperdensity: bool = False
    perimesencephalic_bleeding_pattern: bool = False
    cerebral_angiography_result: str = Field(
        default="no_realizada",
        pattern="^(normal|aneurisma_o_malformacion|no_realizada)$",
    )

    suspected_stroke: bool = False
    symptom_onset_known: bool = True
    wake_up_stroke: bool = False
    hours_since_symptom_onset: float | None = Field(default=None, ge=0, le=240)
    ct_perfusion_performed: bool = False
    salvageable_penumbra_present: bool | None = None
    aspects_score: int | None = Field(default=None, ge=0, le=10)

    parkinsonism_suspected: bool = False
    levodopa_response: str = Field(default="desconocida", pattern="^(excelente|pobre|desconocida)$")
    early_falls: bool = False
    severe_early_dysautonomia: bool = False
    ocular_movement_limitation: bool = False
    mibg_cardiac_denervation: bool | None = None
    datscan_presynaptic_deficit: bool | None = None

    facial_weakness_pattern: str = Field(
        default="ninguno",
        pattern="^(ninguno|mitad_inferior|hemicara_completa)$",
    )

    bilateral_pressing_headache: bool = False
    pulsatile_unilateral_headache: bool = False
    headache_activity_limitation: bool = False
    nausea_or_vomiting: bool = False
    photophobia: bool = False

    rapidly_progressive_weakness: bool = False
    areflexia_or_hyporeflexia: bool = False
    csf_albuminocytologic_dissociation: bool = False
    corticosteroids_planned: bool = False

    fluctuating_weakness: bool = False
    ocular_ptosis_or_diplopia: bool = False
    pupils_spared: bool = True
    myasthenia_seronegative: bool = False

    young_woman: bool = False
    acute_psychiatric_symptoms: bool = False
    seizures_present: bool = False
    orofacial_dyskinesias: bool = False
    ovarian_teratoma_screening_done: bool = False

    csf_tau_elevated: bool | None = None
    csf_beta_amyloid_42_decreased: bool | None = None
    apoe_e4_present: bool | None = None
    aneurysm_or_malformation_suspected: bool = False

    progressive_paraparesis: bool = False
    upper_motor_neuron_signs: bool = False
    sphincter_dysfunction: bool = False
    worsens_with_cervical_flexion_extension: bool = False
    cervical_mri_compressive_pattern_t2: bool | None = None

    dbs_candidate_considered: bool = False
    parkinson_symptoms_levodopa_responsive: bool = False
    severe_cognitive_decline: bool = False

    notes: str | None = Field(default=None, max_length=2000)


class NeurologySupportProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo neurologico."""

    severity_level: str
    vascular_life_threat_alerts: list[str]
    immediate_actions: list[str]
    stroke_reperfusion_pathway: list[str]
    differential_clues: list[str]
    autoimmune_neuromuscular_pathway: list[str]
    biomarker_guidance: list[str]
    advanced_decision_support: list[str]
    contraindication_alerts: list[str]
    interpretability_trace: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskNeurologySupportResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: NeurologySupportProtocolRecommendation
