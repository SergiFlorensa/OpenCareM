"""
Schemas para soporte operativo de epidemiologia clinica.

No sustituye protocolos institucionales ni criterio clinico especializado.
"""
from pydantic import BaseModel, Field


class EpidemiologySupportProtocolRequest(BaseModel):
    """Entrada clinico-operativa para analitica epidemiologica aplicada."""

    requested_individual_risk_estimation: bool = False
    requested_population_status_snapshot: bool = False

    new_cases_count: int | None = Field(default=None, ge=0)
    population_at_risk_count: int | None = Field(default=None, ge=1)
    person_time_at_risk: float | None = Field(default=None, ge=0)
    existing_cases_count: int | None = Field(default=None, ge=0)
    population_total_count: int | None = Field(default=None, ge=1)

    exposed_risk: float | None = Field(default=None, ge=0, le=1)
    unexposed_risk: float | None = Field(default=None, ge=0, le=1)

    control_event_risk: float | None = Field(default=None, ge=0, le=1)
    intervention_event_risk: float | None = Field(default=None, ge=0, le=1)

    hill_strength_of_association: bool = False
    hill_consistency: bool = False
    hill_specificity: bool = False
    hill_temporality: bool = False
    hill_biological_gradient: bool = False
    hill_plausibility: bool = False
    hill_coherence: bool = False
    hill_experiment: bool = False
    hill_analogy: bool = False

    economic_study_type: str | None = Field(default=None, max_length=40)
    qaly_or_utility_outcomes_used: bool = False

    notes: str | None = Field(default=None, max_length=2000)


class EpidemiologySupportProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo epidemiologico."""

    severity_level: str
    critical_alerts: list[str]
    frequency_actions: list[str]
    nnt_actions: list[str]
    causal_inference_actions: list[str]
    economic_evaluation_actions: list[str]
    safety_blocks: list[str]
    interpretability_trace: list[str]
    incidence_accumulated: float | None
    incidence_density: float | None
    prevalence: float | None
    risk_relative: float | None
    absolute_risk_reduction: float | None
    number_needed_to_treat: float | None
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskEpidemiologySupportResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: EpidemiologySupportProtocolRecommendation
