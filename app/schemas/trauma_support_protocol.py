"""
Schemas para soporte operativo de trauma en urgencias.

No sustituye diagnostico definitivo ni decisiones medico-quirurgicas expertas.
"""
from typing import Literal

from pydantic import BaseModel, Field


class TraumaSupportRequest(BaseModel):
    """Entrada estructurada para priorizacion operativa de trauma."""

    minutes_since_trauma: int = Field(ge=0, le=10080)
    prehospital_delay_minutes: int | None = Field(default=None, ge=0, le=720)

    suspected_major_brain_injury: bool = False
    suspected_major_vascular_injury: bool = False
    epidural_hematoma_suspected: bool = False
    massive_hemothorax_suspected: bool = False
    splenic_rupture_suspected: bool = False
    sepsis_signs_post_stabilization: bool = False
    persistent_organ_dysfunction: bool = False

    laryngeal_fracture_palpable: bool = False
    hoarseness_present: bool = False
    subcutaneous_emphysema_present: bool = False
    agitation_present: bool = False
    stupor_present: bool = False
    intercostal_retractions_present: bool = False
    accessory_muscle_use_present: bool = False

    hyperthermia_present: bool = False
    hypercapnia_present: bool = False
    acidosis_present: bool = False

    motor_loss_arms_more_than_legs: bool = False
    motor_loss_global: bool = False
    sensory_loss_global: bool = False
    preserved_vibration_proprioception: bool = False
    ipsilateral_motor_vibration_loss: bool = False
    contralateral_pain_temperature_loss: bool = False

    crush_injury_suspected: bool = False
    hyperkalemia_risk: bool = False
    hyperphosphatemia_present: bool = False
    ecg_series_started: bool = False

    patient_profile: Literal["adulto", "geriatrico", "pediatrico", "embarazada"] = "adulto"
    pregnancy_weeks: int | None = Field(default=None, ge=0, le=45)
    left_lateral_decubitus_applied: bool = False
    broselow_tape_used: bool = False
    sniffing_position_applied: bool = False

    core_temperature_celsius: float | None = Field(default=None, ge=20, le=45)
    osborn_j_wave_present: bool = False

    open_fracture_wound_cm: float | None = Field(default=None, ge=0, le=80)
    high_energy_open_fracture: bool = False

    heart_rate_bpm: int | None = Field(default=None, ge=0, le=260)
    systolic_bp_mm_hg: int | None = Field(default=None, ge=20, le=300)
    respiratory_rate_rpm: int | None = Field(default=None, ge=0, le=80)
    urine_output_ml_h: int | None = Field(default=None, ge=0, le=1000)
    estimated_blood_loss_ml: int | None = Field(default=None, ge=0, le=10000)

    chest_pain_present: bool = False
    dyspnea_present: bool = False
    cyanosis_present: bool = False
    percussion_hyperresonance_present: bool = False
    tracheal_deviation_present: bool = False

    beck_hypotension_present: bool = False
    beck_muffled_heart_sounds_present: bool = False
    beck_jvd_present: bool = False

    glasgow_coma_scale: int | None = Field(default=None, ge=3, le=15)
    vomiting_present: bool = False
    amnesia_present: bool = False
    focal_neurologic_deficit_present: bool = False

    compartment_pressure_mm_hg: int | None = Field(default=None, ge=0, le=150)
    compartment_pain_out_of_proportion: bool = False
    compartment_paresthesias: bool = False
    compartment_pallor: bool = False
    compartment_pulselessness: bool = False
    compartment_paralysis: bool = False

    burn_tbsa_percent: float | None = Field(default=None, ge=0, le=100)
    burn_airway_injury_suspected: bool = False

    notes: str | None = Field(default=None, max_length=2000)


class TraumaConditionCard(BaseModel):
    """Tarjeta de condicion/patologia para salida tabular operativa."""

    condition: str
    classification_category: str
    key_signs_symptoms: list[str]
    diagnostic_method: list[str]
    initial_immediate_treatment: list[str]
    definitive_surgical_treatment: list[str]
    technical_observations: list[str]
    source: str


class TraumaSupportRecommendation(BaseModel):
    """Salida operativa interpretable para trauma en urgencias."""

    mortality_phase_risk: Literal["immediate", "early", "late", "mixed"]
    tecla_ticla_priority: Literal["nivel_i", "nivel_ii", "monitorizacion_estrecha"]

    laryngeal_trauma_triad_present: bool
    airway_priority_level: Literal["nivel_i", "alto", "moderado"]
    airway_red_flags: list[str]
    oxygen_curve_shift_right_risk: bool

    suspected_spinal_syndrome: Literal[
        "central_cord",
        "anterior_cord",
        "brown_sequard",
        "indeterminado",
    ]

    crush_syndrome_alert: bool
    renal_failure_risk_high: bool
    serial_ecg_required: bool
    crush_complications: list[str]

    hypothermia_stage: Literal["none", "mild", "moderate", "severe"]
    hypothermia_alerts: list[str]

    open_fracture_gustilo_grade: Literal["grado_i", "grado_ii", "grado_iii", "no_aplica"]
    antibiotic_coverage_recommendation: str

    condition_matrix: list[TraumaConditionCard]
    special_population_actions: list[str]
    primary_actions: list[str]
    alerts: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskTraumaSupportResponse(BaseModel):
    """Respuesta trazable del endpoint de soporte de trauma."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: TraumaSupportRecommendation
