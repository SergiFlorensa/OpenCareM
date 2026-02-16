"""
Schemas para soporte operativo de reanimacion y soporte vital.

No sustituye ACLS/BLS ni juicio clinico experto.
"""
from pydantic import BaseModel, Field


class ResuscitationProtocolRequest(BaseModel):
    """Entrada clinico-operativa para escenarios de reanimacion."""

    context_type: str = Field(
        ...,
        pattern="^(cardiac_arrest|tachyarrhythmia_with_pulse|bradyarrhythmia_with_pulse|post_rosc)$",
    )
    rhythm: str = Field(
        ...,
        pattern=(
            "^(vf|pulseless_vt|asystole|pea|svt_flutter|af|vt_monomorphic|"
            "vt_polymorphic|brady_advanced)$"
        ),
    )
    has_pulse: bool
    compression_depth_cm: float | None = Field(default=None, ge=0, le=10)
    compression_rate_per_min: int | None = Field(default=None, ge=0, le=200)
    interruption_seconds: int | None = Field(default=None, ge=0, le=60)
    etco2_mm_hg: float | None = Field(default=None, ge=0, le=120)
    hypotension: bool = False
    altered_mental_status: bool = False
    shock_signs: bool = False
    ischemic_chest_pain: bool = False
    acute_heart_failure: bool = False
    systolic_bp_mm_hg: float | None = Field(default=None, ge=40, le=260)
    diastolic_bp_mm_hg: float | None = Field(default=None, ge=20, le=200)
    map_mm_hg: float | None = Field(default=None, ge=20, le=180)
    oxygen_saturation_percent: int | None = Field(default=None, ge=40, le=100)
    comatose_post_rosc: bool = False
    pregnant: bool = False
    gestational_weeks: int | None = Field(default=None, ge=0, le=45)
    uterine_fundus_at_or_above_umbilicus: bool = False
    minutes_since_arrest: int | None = Field(default=None, ge=0, le=240)
    access_above_diaphragm_secured: bool | None = None
    fetal_monitor_connected: bool | None = None
    magnesium_infusion_active: bool = False
    magnesium_toxicity_suspected: bool = False
    opioid_suspected: bool = False
    door_ecg_minutes: int | None = Field(default=None, ge=0, le=240)
    symptom_onset_minutes: int | None = Field(default=None, ge=0, le=10080)
    notes: str | None = Field(default=None, max_length=2000)


class ResuscitationProtocolRecommendation(BaseModel):
    """Salida estructurada para soporte operativo de reanimacion."""

    severity_level: str
    rhythm_classification: str
    shock_recommended: bool
    cpr_quality_ok: bool | None
    primary_actions: list[str]
    medication_actions: list[str]
    electrical_therapy_plan: list[str]
    sedoanalgesia_plan: list[str]
    pre_shock_safety_checklist: list[str]
    ventilation_actions: list[str]
    reversible_causes_checklist: list[str]
    special_situation_actions: list[str]
    sla_alerts: list[str]
    alerts: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskResuscitationProtocolResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: ResuscitationProtocolRecommendation
