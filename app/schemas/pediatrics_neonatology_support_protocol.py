"""
Schemas para soporte operativo de pediatria y neonatologia en urgencias.

No sustituye protocolos institucionales ni criterio clinico especializado.
"""
from pydantic import BaseModel, Field


class PediatricsNeonatologySupportProtocolRequest(BaseModel):
    """Entrada clinico-operativa para priorizacion pediatrica/neonatal."""

    patient_age_months: int | None = Field(default=None, ge=0, le=216)
    patient_age_years: int | None = Field(default=None, ge=0, le=18)

    high_fever_present: bool = False
    photophobia_present: bool = False
    cough_present: bool = False
    koplik_spots_present: bool = False
    confluent_maculopapular_rash_present: bool = False
    cephalocaudal_rash_progression_present: bool = False
    red_eye_present: bool = False
    kawasaki_features_present: bool = False
    mmr_doses_received: int | None = Field(default=None, ge=0, le=2)
    respiratory_isolation_started: bool = False

    apgar_minute_1: int | None = Field(default=None, ge=0, le=10)
    apgar_minute_5: int | None = Field(default=None, ge=0, le=10)
    apgar_only_minute_0_recorded: bool = False
    neonatal_heart_rate_bpm: int | None = Field(default=None, ge=0, le=300)
    spontaneous_breathing_present: bool = False
    neonatal_respiratory_distress_present: bool = False
    neonatal_cyanosis_present: bool = False
    minute_of_life: int | None = Field(default=None, ge=0, le=60)
    oxygen_saturation_percent: float | None = Field(default=None, ge=0, le=100)
    gestational_age_weeks: int | None = Field(default=None, ge=22, le=44)
    fio2_percent: float | None = Field(default=None, ge=21, le=100)
    oxygen_increase_requested: bool = False
    cpap_started: bool = False

    confirmed_pertussis_case: bool = False
    household_contact: bool = False
    face_to_face_secretions_contact: bool = False
    newborn_of_infectious_mother_at_delivery: bool = False
    healthcare_airway_exposure_without_mask: bool = False
    macrolide_prophylaxis_started: bool = False
    days_since_effective_pertussis_treatment: int | None = Field(
        default=None,
        ge=0,
        le=30,
    )
    days_since_pertussis_symptom_onset: int | None = Field(default=None, ge=0, le=60)

    intermittent_colicky_abdominal_pain: bool = False
    asymptomatic_intervals_between_pain: bool = False
    vomiting_present: bool = False
    currant_jelly_stool_present: bool = False
    peritonitis_signs_present: bool = False
    recent_respiratory_infection_adenovirus_suspected: bool = False
    days_since_rotavirus_vaccine: int | None = Field(default=None, ge=0, le=90)

    hutchinson_teeth_present: bool = False
    interstitial_keratitis_present: bool = False
    sensorineural_deafness_present: bool = False
    saddle_nose_present: bool = False
    mulberry_molars_present: bool = False
    saber_shins_present: bool = False
    frontal_bossing_present: bool = False
    clutton_joints_present: bool = False
    congenital_heart_disease_present: bool = False

    notes: str | None = Field(default=None, max_length=2000)


class PediatricsNeonatologySupportProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo pediatria/neonatologia."""

    severity_level: str
    critical_alerts: list[str]
    infectious_exanthem_actions: list[str]
    neonatal_resuscitation_actions: list[str]
    pertussis_contact_actions: list[str]
    surgical_pediatric_actions: list[str]
    congenital_syphilis_actions: list[str]
    safety_blocks: list[str]
    interpretability_trace: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskPediatricsNeonatologySupportResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: PediatricsNeonatologySupportProtocolRecommendation
