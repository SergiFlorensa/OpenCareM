"""
Schemas para soporte operativo critico transversal en urgencias.

No sustituye protocolos institucionales ni juicio clinico presencial.
"""
from pydantic import BaseModel, Field


class CriticalOpsProtocolRequest(BaseModel):
    """Entrada clinico-operativa para reglas transversales de urgencias."""

    non_traumatic_chest_pain: bool = False
    door_to_ecg_minutes: int | None = Field(default=None, ge=0, le=720)
    suspected_septic_shock: bool = False
    sepsis_antibiotic_minutes: int | None = Field(default=None, ge=0, le=1440)
    triage_level: str = Field(default="amarillo", pattern="^(rojo|naranja|amarillo|verde|azul)$")
    triage_to_first_assessment_minutes: int | None = Field(default=None, ge=0, le=720)

    oxygen_saturation_percent: int | None = Field(default=None, ge=40, le=100)
    respiratory_failure_severity: str = Field(
        default="ninguna",
        pattern="^(ninguna|leve|moderada|grave)$",
    )
    hypercapnia_risk: bool = False
    respiratory_acidosis_present: bool = False
    pulmonary_edema_suspected: bool = False
    shock_or_severe_arrhythmia_present: bool = False
    good_respiratory_mechanics: bool = True

    suspected_pe: bool = False
    wells_score: float | None = Field(default=None, ge=0, le=20)
    d_dimer_ng_ml: float | None = Field(default=None, ge=0, le=20000)
    chest_xray_performed: bool = False
    hiatal_hernia_on_xray: bool = False

    rapid_cutaneous_mucosal_symptoms: bool = False
    respiratory_compromise: bool = False
    cardiovascular_compromise: bool = False
    on_beta_blocker: bool = False
    anaphylaxis_refractory_to_im_adrenaline: bool = False

    svr_dyn_s_cm5: int | None = Field(default=None, ge=100, le=5000)
    cvp_mm_hg: float | None = Field(default=None, ge=0, le=40)
    cardiac_output_l_min: float | None = Field(default=None, ge=0, le=20)
    pulmonary_capillary_wedge_pressure_mm_hg: float | None = Field(default=None, ge=0, le=40)
    lactate_mmol_l: float | None = Field(default=None, ge=0, le=30)
    previous_lactate_mmol_l: float | None = Field(default=None, ge=0, le=30)
    lactate_interval_minutes: int | None = Field(default=None, ge=0, le=600)

    unknown_origin_coma: bool = False
    capillary_glucose_mg_dl: float | None = Field(default=None, ge=0, le=1000)
    opioid_intoxication_suspected: bool = False
    benzodiazepine_intoxication_suspected: bool = False
    malnutrition_or_chronic_alcohol_use: bool = False
    smoke_inhalation_suspected: bool = False
    cyanide_suspected: bool = False
    paracetamol_overdose_suspected: bool = False
    hours_since_paracetamol_ingestion: float | None = Field(default=None, ge=0, le=200)
    paracetamol_level_mcg_ml: float | None = Field(default=None, ge=0, le=1000)
    core_temperature_celsius: float | None = Field(default=None, ge=20, le=45)
    persistent_asystole: bool = False

    systemic_sclerosis_or_raynaud: bool = False
    digital_necrosis_present: bool = False
    abrupt_anuria_present: bool = False
    woman_childbearing_age: bool = False
    lower_abdominal_pain: bool = False
    vaginal_bleeding: bool = False
    free_fluid_ultrasound: bool = False
    chest_tube_output_immediate_ml: int | None = Field(default=None, ge=0, le=10000)

    notes: str | None = Field(default=None, max_length=2000)


class CriticalOpsProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo critico transversal."""

    severity_level: str
    sla_alerts: list[str]
    sla_breaches: list[str]
    respiratory_device_recommended: str
    respiratory_target_saturation: str
    respiratory_support_plan: list[str]
    chest_pain_pe_pathway: list[str]
    anaphylaxis_pathway: list[str]
    hemodynamic_profile: str
    hemodynamic_actions: list[str]
    toxicology_reversal_actions: list[str]
    toxicology_alerts: list[str]
    operational_red_flags: list[str]
    radiology_actions: list[str]
    critical_alerts: list[str]
    interpretability_trace: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskCriticalOpsProtocolResponse(BaseModel):
    """Respuesta final del endpoint vinculada a traza de agente."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: CriticalOpsProtocolRecommendation
