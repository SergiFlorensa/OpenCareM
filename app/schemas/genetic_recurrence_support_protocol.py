"""
Schemas para soporte operativo de recurrencia genetica en osteogenesis imperfecta.

No sustituye consejo genetico ni criterio clinico especializado.
"""
from pydantic import BaseModel, Field


class GeneticRecurrenceSupportProtocolRequest(BaseModel):
    """Entrada clinico-operativa para priorizacion de recurrencia genetica."""

    gestational_age_weeks: int | None = Field(default=None, ge=0, le=45)

    autosomal_dominant_condition_suspected: bool = False
    oi_type_ii_suspected: bool = False
    col1a1_or_col1a2_involved: bool = False

    previous_pregnancy_with_same_condition: bool = False
    recurrent_affected_pregnancies_count: int = Field(default=1, ge=0, le=20)

    parents_phenotypically_unaffected: bool = False
    mother_phenotypically_affected: bool = False
    father_phenotypically_affected: bool = False

    autosomal_recessive_hypothesis_active: bool = False
    de_novo_hypothesis_active: bool = False
    incomplete_penetrance_hypothesis_active: bool = False

    germline_mosaicism_confirmed: bool = False
    somatic_mosaicism_only_confirmed: bool = False
    molecular_confirmation_available: bool = False
    parental_germline_testing_available: bool = False

    estimated_mutated_gamete_fraction_percent: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    notes: str | None = Field(default=None, max_length=2000)


class GeneticRecurrenceSupportProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo de recurrencia genetica."""

    severity_level: str
    mosaicism_alert_active: bool
    prioritized_recurrence_mechanism: str
    estimated_recurrence_risk_percent: float | None
    critical_alerts: list[str]
    recurrence_interpretation_actions: list[str]
    genetic_counseling_actions: list[str]
    differential_mechanisms: list[str]
    safety_blocks: list[str]
    interpretability_trace: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskGeneticRecurrenceSupportResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: GeneticRecurrenceSupportProtocolRecommendation
