"""
Schemas para soporte operativo de inmunologia en urgencias.

No sustituye protocolos institucionales ni criterio clinico especializado.
"""
from pydantic import BaseModel, Field


class ImmunologySupportProtocolRequest(BaseModel):
    """Entrada clinico-operativa para priorizacion inmunologica en urgencias."""

    patient_male: bool = False
    age_months: int | None = Field(default=None, ge=0, le=240)

    btk_mutation_confirmed: bool = False
    x_linked_family_pattern_suspected: bool = False
    b_cell_maturation_block_suspected: bool = False
    peripheral_cd19_cd20_b_cells_absent: bool = False

    igg_low_or_absent: bool = False
    iga_low_or_absent: bool = False
    igm_low_or_absent: bool = False
    igm_elevated: bool = False

    recurrent_sinopulmonary_bacterial_infections: bool = False
    severe_infection_after_6_months: bool = False
    monocyte_function_abnormal_reported: bool = False

    lower_respiratory_infection_active: bool = False
    alveolar_macrophage_dysfunction_suspected: bool = False
    neutrophil_recruitment_failure_suspected: bool = False
    mucociliary_clearance_failure_suspected: bool = False
    complement_support_failure_suspected: bool = False
    antimicrobial_peptide_barrier_failure_suspected: bool = False

    notes: str | None = Field(default=None, max_length=2000)


class ImmunologySupportProtocolRecommendation(BaseModel):
    """Salida estructurada del soporte operativo inmunologico."""

    severity_level: str
    critical_alerts: list[str]
    primary_immunodeficiency_actions: list[str]
    innate_pulmonary_actions: list[str]
    humoral_differential_actions: list[str]
    safety_blocks: list[str]
    interpretability_trace: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskImmunologySupportResponse(BaseModel):
    """Respuesta final del endpoint vinculada a run trazable."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: ImmunologySupportProtocolRecommendation
