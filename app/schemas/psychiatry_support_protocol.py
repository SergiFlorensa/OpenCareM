"""
Schemas para soporte operativo de psiquiatria en urgencias.

No sustituye protocolos institucionales ni criterio clinico especializado.
"""
from pydantic import BaseModel, Field


class PsychiatrySupportProtocolRequest(BaseModel):
    """Entrada clinico-operativa para priorizacion psiquiatrica en urgencias."""

    age_years: int = Field(default=18, ge=0, le=120)

    traumatic_event_exposure: bool = False
    days_since_traumatic_event: int | None = Field(default=None, ge=0, le=3650)
    reexperiencing_symptoms: bool = False
    avoidance_symptoms: bool = False
    hyperarousal_symptoms: bool = False

    psychosocial_stressor_present: bool = False
    days_since_psychosocial_stressor: int | None = Field(default=None, ge=0, le=3650)

    self_harm_present: bool = False
    prior_suicide_attempt: bool = False
    family_history_suicide: bool = False
    social_isolation: bool = False
    male_sex: bool = False

    psychosis_suspected: bool = False
    psychosis_onset_acute: bool = False
    psychosis_early_age_onset: bool = False
    negative_symptoms_predominant: bool = False

    bipolar_disorder_known: bool = False
    pregnancy_ongoing: bool = False
    planned_mood_stabilizer: str | None = Field(default=None, max_length=60)

    insomnia_present: bool = False
    pain_secondary_cause_suspected: bool = False
    hypnotic_planned: bool = False
    benzodiazepine_planned: bool = False

    eating_disorder_suspected: bool = False
    lanugo_present: bool = False
    hypotension_present: bool = False
    sinus_bradycardia_present: bool = False
    tachycardia_present: bool = False
    purging_vomiting_present: bool = False
    hypokalemia_present: bool = False
    hypochloremic_alkalosis_present: bool = False

    delusional_disorder_suspected: bool = False
    defense_projection: bool = False
    defense_denial: bool = False
    defense_reaction_formation: bool = False
    defense_regression: bool = False

    notes: str | None = Field(default=None, max_length=2000)


class PsychiatrySupportProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo de psiquiatria."""

    severity_level: str
    critical_alerts: list[str]
    triage_actions: list[str]
    diagnostic_support: list[str]
    pharmacologic_safety_alerts: list[str]
    prognosis_flags: list[str]
    maternal_fetal_actions: list[str]
    internal_medicine_alerts: list[str]
    psychodynamic_flags: list[str]
    interpretability_trace: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskPsychiatrySupportResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: PsychiatrySupportProtocolRecommendation
