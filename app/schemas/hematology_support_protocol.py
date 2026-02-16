"""
Schemas para soporte operativo de hematologia en urgencias.

No sustituye protocolos institucionales ni criterio clinico especializado.
"""
from pydantic import BaseModel, Field


class HematologySupportProtocolRequest(BaseModel):
    """Entrada clinico-operativa para decision hematologica temprana en urgencias."""

    mah_anemia_present: bool = False
    thrombocytopenia_present: bool = False
    organ_damage_present: bool = False

    cold_exposure_trigger: bool = False
    intravascular_hemolysis_sudden: bool = False
    hemoglobinuria_present: bool = False
    free_plasma_hemoglobin_high: bool = False
    hypotension_present: bool = False
    acral_cyanosis_present: bool = False
    hemophagocytosis_in_smear: bool = False

    bloody_diarrhea_prodrome: bool = False
    shiga_toxin_suspected: bool = False
    direct_coombs_negative: bool = False
    schistocytes_percent: float | None = Field(default=None, ge=0, le=100)
    creatinine_elevated: bool = False
    neurological_involvement: bool = False

    heparin_exposure_active: bool = False
    days_since_heparin_start: int | None = Field(default=None, ge=0, le=60)
    platelet_drop_percent: float | None = Field(default=None, ge=0, le=100)
    major_orthopedic_postop_context: bool = False
    renal_failure_present: bool = False
    hepatic_failure_present: bool = False

    hemophilia_a_severe: bool = False
    high_titer_factor_viii_inhibitors: bool = False
    acute_hemarthrosis: bool = False
    on_emicizumab_prophylaxis: bool = False
    prothrombin_complex_planned: bool = False

    biopsy_histology_available: bool = False
    fine_needle_aspirate_only: bool = False
    cd20_positive: bool = False
    cd3_positive: bool = False
    cd15_positive: bool = False
    cd30_positive: bool = False
    cd19_positive: bool = False
    cd5_positive: bool = False
    cd23_positive: bool = False
    cd20_weak: bool = False
    cyclin_d1_positive: bool = False
    sox11_positive: bool = False
    hhv8_positive: bool = False
    ebv_positive: bool = False
    htlv1_positive: bool = False

    pediatric_patient: bool = False
    short_stature: bool = False
    cafe_au_lait_spots: bool = False
    thumb_or_radius_hypoplasia: bool = False
    renal_anomaly_present: bool = False
    micrognathia_present: bool = False
    macrocytosis_present: bool = False
    pancytopenia_present: bool = False

    planned_splenectomy: bool = False
    encapsulated_vaccines_completed_preop: bool = False
    days_vaccines_before_splenectomy: int | None = Field(default=None, ge=0, le=365)
    postsplenectomy_status: bool = False
    active_bleeding: bool = False
    thromboprophylaxis_started: bool = False

    hsct_recipient: bool = False
    recipient_male: bool = False
    donor_karyotype_47xxy_detected: bool = False

    notes: str | None = Field(default=None, max_length=2000)


class HematologySupportProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo de hematologia."""

    severity_level: str
    critical_alerts: list[str]
    diagnostic_actions: list[str]
    therapeutic_actions: list[str]
    pharmacologic_safety_alerts: list[str]
    oncology_immunophenotype_notes: list[str]
    inherited_bone_marrow_failure_flags: list[str]
    postsplenectomy_checklist: list[str]
    transplant_flags: list[str]
    interpretability_trace: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskHematologySupportResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: HematologySupportProtocolRecommendation
