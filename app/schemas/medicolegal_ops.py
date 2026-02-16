"""
Schemas del motor de soporte medico-legal para urgencias.

No sustituye criterio juridico ni medico forense; organiza alertas y
acciones operativas para validacion humana.
"""
from pydantic import BaseModel, Field


class MedicolegalOpsRequest(BaseModel):
    """Entrada estructurada para evaluar riesgo medico-legal operativo."""

    triage_wait_minutes: int | None = Field(default=None, ge=0)
    first_medical_contact_minutes: int | None = Field(default=None, ge=0)
    patient_age_years: int = Field(..., ge=0)
    patient_has_decision_capacity: bool = True
    informed_consent_documented: bool = False
    invasive_procedure_planned: bool = False
    legal_representative_present: bool = False
    legal_representatives_deceased: bool = False
    refuses_care: bool = False
    parental_religious_refusal_life_saving_treatment: bool = False
    life_threatening_condition: bool = False
    blood_transfusion_indicated: bool = False
    immediate_judicial_authorization_available: bool = False
    public_health_risk: bool = False
    involuntary_psychiatric_admission: bool = False
    patient_escape_risk: bool = False
    intoxication_forensic_context: bool = False
    chain_of_custody_started: bool = False
    suspected_crime_injuries: bool = False
    non_natural_death_suspected: bool = False
    context_notes: str | None = Field(default=None, max_length=2000)


class MedicolegalOpsRecommendation(BaseModel):
    """Salida de soporte operativo para cumplimiento medico-legal."""

    legal_risk_level: str
    life_preserving_override_recommended: bool
    ethical_legal_basis: list[str]
    urgency_summary: str
    critical_legal_alerts: list[str]
    required_documents: list[str]
    operational_actions: list[str]
    compliance_checklist: list[str]
    human_validation_required: bool
    non_diagnostic_warning: str


class CareTaskMedicolegalOpsResponse(BaseModel):
    """Respuesta trazable del endpoint medico-legal por CareTask."""

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    recommendation: MedicolegalOpsRecommendation
