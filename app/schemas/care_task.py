"""
CareTask Schemas - Contratos de datos para operaciones clinico-operativas.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.ai import TaskTriageResponse


class CareTaskBase(BaseModel):
    """
    Campos base del recurso CareTask.

    Se mantienen simples para que la transicion desde Task sea gradual.
    """

    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    clinical_priority: str = Field(default="medium")
    specialty: str = Field(default="general", max_length=80)
    patient_reference: str | None = Field(default=None, max_length=120)
    sla_target_minutes: int = Field(default=240, gt=0)
    human_review_required: bool = Field(default=True)
    completed: bool = Field(default=False)


class CareTaskCreate(CareTaskBase):
    """Payload de creacion de CareTask."""


class CareTaskUpdate(BaseModel):
    """
    Payload de actualizacion parcial.

    Todos los campos son opcionales para poder editar solo lo necesario.
    """

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    clinical_priority: Optional[str] = None
    specialty: Optional[str] = Field(None, max_length=80)
    patient_reference: Optional[str] = Field(None, max_length=120)
    sla_target_minutes: Optional[int] = Field(None, gt=0)
    human_review_required: Optional[bool] = None
    completed: Optional[bool] = None


class CareTaskResponse(CareTaskBase):
    """Respuesta completa del recurso CareTask."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CareTaskTriageResponse(BaseModel):
    """
    Resultado de triaje para un CareTask existente.

    Devuelve tanto la recomendacion como el enlace directo a la corrida
    de agente para inspeccion operativa.
    """

    care_task_id: int
    agent_run_id: int
    workflow_name: str
    triage: TaskTriageResponse


class CareTaskTriageApprovalRequest(BaseModel):
    """
    Solicitud de aprobacion/rechazo humano de una corrida de triaje.
    """

    agent_run_id: int = Field(..., gt=0)
    approved: bool
    reviewer_note: Optional[str] = Field(default=None, max_length=2000)
    reviewed_by: Optional[str] = Field(default=None, max_length=80)


class CareTaskTriageApprovalResponse(BaseModel):
    """
    Resultado persistido de una revision humana.
    """

    review_id: int
    care_task_id: int
    agent_run_id: int
    approved: bool
    reviewer_note: Optional[str]
    reviewed_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class CareTaskTriageAuditRequest(BaseModel):
    """
    Registro de calidad de triaje comparando recomendacion IA vs validacion humana.
    """

    agent_run_id: int = Field(..., gt=0)
    human_validated_level: int = Field(..., ge=1, le=5)
    reviewer_note: Optional[str] = Field(default=None, max_length=2000)
    reviewed_by: Optional[str] = Field(default=None, max_length=80)


class CareTaskTriageAuditResponse(BaseModel):
    """
    Salida de auditoria de desviacion de triaje.
    """

    audit_id: int
    care_task_id: int
    agent_run_id: int
    ai_recommended_level: int
    human_validated_level: int
    classification: str
    reviewer_note: Optional[str]
    reviewed_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class CareTaskTriageAuditSummaryResponse(BaseModel):
    """
    Agregado de auditoria para observabilidad de calidad de triaje.
    """

    total_audits: int
    matches: int
    under_triage: int
    over_triage: int
    under_triage_rate_percent: float
    over_triage_rate_percent: float


class CareTaskScreeningAuditRequest(BaseModel):
    """
    Registro de calidad del screening avanzado comparando IA vs validacion humana.
    """

    agent_run_id: int = Field(..., gt=0)
    human_validated_risk_level: str = Field(..., pattern="^(low|medium|high)$")
    human_hiv_screening_suggested: bool = False
    human_sepsis_route_suggested: bool = False
    human_persistent_covid_suspected: bool = False
    human_long_acting_candidate: bool = False
    reviewer_note: Optional[str] = Field(default=None, max_length=2000)
    reviewed_by: Optional[str] = Field(default=None, max_length=80)


class CareTaskScreeningAuditResponse(BaseModel):
    """
    Salida de auditoria de calidad para screening avanzado.
    """

    audit_id: int
    care_task_id: int
    agent_run_id: int
    ai_geriatric_risk_level: str
    human_validated_risk_level: str
    classification: str
    ai_hiv_screening_suggested: bool
    human_hiv_screening_suggested: bool
    ai_sepsis_route_suggested: bool
    human_sepsis_route_suggested: bool
    ai_persistent_covid_suspected: bool
    human_persistent_covid_suspected: bool
    ai_long_acting_candidate: bool
    human_long_acting_candidate: bool
    reviewer_note: Optional[str]
    reviewed_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class CareTaskScreeningAuditSummaryResponse(BaseModel):
    """
    Agregado de calidad de screening para observabilidad operativa.
    """

    total_audits: int
    matches: int
    under_screening: int
    over_screening: int
    under_screening_rate_percent: float
    over_screening_rate_percent: float
    hiv_screening_match_rate_percent: float
    sepsis_route_match_rate_percent: float
    persistent_covid_match_rate_percent: float
    long_acting_match_rate_percent: float


class CareTaskMedicolegalAuditRequest(BaseModel):
    """
    Registro de calidad del soporte medico-legal comparando IA vs validacion humana.
    """

    agent_run_id: int = Field(..., gt=0)
    human_validated_legal_risk_level: str = Field(..., pattern="^(low|medium|high)$")
    human_consent_required: bool = False
    human_judicial_notification_required: bool = False
    human_chain_of_custody_required: bool = False
    reviewer_note: Optional[str] = Field(default=None, max_length=2000)
    reviewed_by: Optional[str] = Field(default=None, max_length=80)


class CareTaskMedicolegalAuditResponse(BaseModel):
    """
    Salida de auditoria de calidad para soporte medico-legal.
    """

    audit_id: int
    care_task_id: int
    agent_run_id: int
    ai_legal_risk_level: str
    human_validated_legal_risk_level: str
    classification: str
    ai_consent_required: bool
    human_consent_required: bool
    ai_judicial_notification_required: bool
    human_judicial_notification_required: bool
    ai_chain_of_custody_required: bool
    human_chain_of_custody_required: bool
    reviewer_note: Optional[str]
    reviewed_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class CareTaskMedicolegalAuditSummaryResponse(BaseModel):
    """
    Agregado de calidad medico-legal para observabilidad operativa.
    """

    total_audits: int
    matches: int
    under_legal_risk: int
    over_legal_risk: int
    under_legal_risk_rate_percent: float
    over_legal_risk_rate_percent: float
    consent_required_match_rate_percent: float
    judicial_notification_match_rate_percent: float
    chain_of_custody_match_rate_percent: float


class CareTaskScasestAuditRequest(BaseModel):
    """
    Registro de calidad del soporte SCASEST comparando IA vs validacion humana.
    """

    agent_run_id: int = Field(..., gt=0)
    human_validated_high_risk_scasest: bool
    human_escalation_required: bool = False
    human_immediate_antiischemic_strategy: bool = False
    reviewer_note: Optional[str] = Field(default=None, max_length=2000)
    reviewed_by: Optional[str] = Field(default=None, max_length=80)


class CareTaskScasestAuditResponse(BaseModel):
    """
    Salida de auditoria de calidad para soporte SCASEST.
    """

    audit_id: int
    care_task_id: int
    agent_run_id: int
    ai_high_risk_scasest: bool
    human_validated_high_risk_scasest: bool
    classification: str
    ai_escalation_required: bool
    human_escalation_required: bool
    ai_immediate_antiischemic_strategy: bool
    human_immediate_antiischemic_strategy: bool
    reviewer_note: Optional[str]
    reviewed_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class CareTaskScasestAuditSummaryResponse(BaseModel):
    """
    Agregado de calidad SCASEST para observabilidad operativa.
    """

    total_audits: int
    matches: int
    under_scasest_risk: int
    over_scasest_risk: int
    under_scasest_risk_rate_percent: float
    over_scasest_risk_rate_percent: float
    escalation_required_match_rate_percent: float
    immediate_antiischemic_strategy_match_rate_percent: float


class CareTaskCardioRiskAuditRequest(BaseModel):
    """
    Registro de calidad del soporte cardiovascular comparando IA vs validacion humana.
    """

    agent_run_id: int = Field(..., gt=0)
    human_validated_risk_level: str = Field(..., pattern="^(low|moderate|high|very_high)$")
    human_non_hdl_target_required: bool = False
    human_pharmacologic_strategy_suggested: bool = False
    human_intensive_lifestyle_required: bool = False
    reviewer_note: Optional[str] = Field(default=None, max_length=2000)
    reviewed_by: Optional[str] = Field(default=None, max_length=80)


class CareTaskCardioRiskAuditResponse(BaseModel):
    """
    Salida de auditoria de calidad para soporte cardiovascular.
    """

    audit_id: int
    care_task_id: int
    agent_run_id: int
    ai_risk_level: str
    human_validated_risk_level: str
    classification: str
    ai_non_hdl_target_required: bool
    human_non_hdl_target_required: bool
    ai_pharmacologic_strategy_suggested: bool
    human_pharmacologic_strategy_suggested: bool
    ai_intensive_lifestyle_required: bool
    human_intensive_lifestyle_required: bool
    reviewer_note: Optional[str]
    reviewed_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class CareTaskCardioRiskAuditSummaryResponse(BaseModel):
    """
    Agregado de calidad cardiovascular para observabilidad operativa.
    """

    total_audits: int
    matches: int
    under_cardio_risk: int
    over_cardio_risk: int
    under_cardio_risk_rate_percent: float
    over_cardio_risk_rate_percent: float
    non_hdl_target_required_match_rate_percent: float
    pharmacologic_strategy_match_rate_percent: float
    intensive_lifestyle_match_rate_percent: float


class CareTaskResuscitationAuditRequest(BaseModel):
    """
    Registro de calidad del soporte de reanimacion comparando IA vs validacion humana.
    """

    agent_run_id: int = Field(..., gt=0)
    human_validated_severity_level: str = Field(..., pattern="^(medium|high|critical)$")
    human_shock_recommended: bool = False
    human_reversible_causes_completed: bool = False
    human_airway_plan_adequate: bool = False
    reviewer_note: Optional[str] = Field(default=None, max_length=2000)
    reviewed_by: Optional[str] = Field(default=None, max_length=80)


class CareTaskResuscitationAuditResponse(BaseModel):
    """
    Salida de auditoria de calidad para soporte de reanimacion.
    """

    audit_id: int
    care_task_id: int
    agent_run_id: int
    ai_severity_level: str
    human_validated_severity_level: str
    classification: str
    ai_shock_recommended: bool
    human_shock_recommended: bool
    ai_reversible_causes_required: bool
    human_reversible_causes_completed: bool
    ai_airway_plan_adequate: bool
    human_airway_plan_adequate: bool
    reviewer_note: Optional[str]
    reviewed_by: Optional[str]
    created_at: datetime
    updated_at: datetime


class CareTaskResuscitationAuditSummaryResponse(BaseModel):
    """
    Agregado de calidad de reanimacion para observabilidad operativa.
    """

    total_audits: int
    matches: int
    under_resuscitation_risk: int
    over_resuscitation_risk: int
    under_resuscitation_risk_rate_percent: float
    over_resuscitation_risk_rate_percent: float
    shock_recommended_match_rate_percent: float
    reversible_causes_match_rate_percent: float
    airway_plan_match_rate_percent: float


class CareTaskQualityDomainSummaryResponse(BaseModel):
    """
    Resumen normalizado de calidad para un dominio operativo.
    """

    total_audits: int
    matches: int
    under_events: int
    over_events: int
    under_rate_percent: float
    over_rate_percent: float
    match_rate_percent: float


class CareTaskQualityScorecardResponse(BaseModel):
    """
    Scorecard global de calidad IA para lectura operativa rapida.
    """

    total_audits: int
    matches: int
    under_events: int
    over_events: int
    under_rate_percent: float
    over_rate_percent: float
    match_rate_percent: float
    quality_status: str
    domains: dict[str, CareTaskQualityDomainSummaryResponse]
