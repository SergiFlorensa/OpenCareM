"""
Schemas para soporte operativo gastro-hepato en urgencias.

No sustituye protocolos institucionales ni criterio clinico especializado.
"""
from pydantic import BaseModel, Field


class GastroHepatoSupportProtocolRequest(BaseModel):
    """Entrada clinico-operativa para reglas digestivas/hepatobiliares de urgencias."""

    abdominal_pain: bool = False
    jaundice: bool = False
    ascites: bool = False
    hypotension_present: bool = False

    portal_doppler_no_flow_silence: bool = False
    portal_doppler_heterogeneous: bool = False
    portal_thrombosis_confirmed: bool = False
    initial_oral_anticoagulation_started: bool = False
    failed_initial_anticoagulation: bool = False
    endovascular_therapy_considered: bool = False

    cirrhosis_known: bool = False
    upper_gi_bleeding_suspected: bool = False
    vasoactive_somatostatin_started: bool = False
    endoscopy_performed: bool = False
    hours_to_endoscopy: float | None = Field(default=None, ge=0, le=168)
    variceal_band_ligation_done: bool = False
    early_rebleeding: bool = False
    bleeding_controlled_with_bands: bool | None = None
    tips_considered: bool = False

    portal_venous_gas_on_ct: bool = False
    gastric_pneumatosis_on_ct: bool = False
    aerobilia_central_pattern: bool = False
    prior_biliary_instrumentation: bool = False

    painless_gallbladder_distension: bool = False
    biliary_tree_dilation_intra_extrahepatic: bool = False
    cholestatic_jaundice: bool = False
    recent_amoxicillin_clavulanate: bool = False

    left_lower_quadrant_pain: bool = False
    fever_present: bool = False
    leukocytosis_present: bool = False
    crp_elevated: bool = False
    ct_pericolonic_inflammation_sigmoid_descending: bool = False
    bowel_loop_dilation_present: bool = False

    hernia_below_inguinal_ligament: bool = False
    intestinal_obstruction_signs: bool = False
    incarceration_or_strangulation_signs: bool = False

    porcelain_gallbladder: bool = False
    gallstone_size_cm: float | None = Field(default=None, ge=0, le=10)
    symptomatic_microlithiasis: bool = False
    duodenal_adenocarcinoma_non_metastatic: bool = False
    duodenal_adenocarcinoma_nodal_or_metastatic: bool = False
    inguinal_hernia_repair_planned: bool = False
    wants_non_mesh_technique: bool = False
    planned_hernia_technique: str = Field(
        default="desconocida",
        pattern="^(desconocida|shouldice|lichtenstein|tep|tapp|otra)$",
    )

    ibd_patient: bool = False
    azathioprine_active: bool = False
    infliximab_or_biologic_active: bool = False

    zenker_diverticulum_suspected: bool = False
    open_zenker_surgery_selected: bool = False

    gerd_preop_evaluation: bool = False
    esophageal_manometry_done: bool = False
    fap_suspected: bool = False
    apc_mutation_present: bool | None = None
    mandibular_osteomas: bool = False
    retinal_pigment_epithelium_hypertrophy: bool = False

    notes: str | None = Field(default=None, max_length=2000)


class GastroHepatoSupportProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo gastro-hepato."""

    severity_level: str
    critical_alerts: list[str]
    hemodynamic_actions: list[str]
    imaging_red_flags: list[str]
    differential_clues: list[str]
    surgical_decision_support: list[str]
    pharmacology_safety_alerts: list[str]
    functional_genetic_guidance: list[str]
    interpretability_trace: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskGastroHepatoSupportResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: GastroHepatoSupportProtocolRecommendation
