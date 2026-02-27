"""
Schemas para chat clinico-operativo sobre CareTask.

El chat no diagnostica. Solo organiza recomendaciones operativas y memoria de
consulta para apoyar la toma de decisiones con validacion humana.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ClinicalLocalEvidenceItem(BaseModel):
    """Evidencia local adjunta por el profesional para enriquecer el contexto."""

    title: str = Field(..., min_length=2, max_length=120)
    modality: Literal["note", "report", "pdf", "image", "ehr_structured", "lab_panel"] = "note"
    source: str | None = Field(default=None, max_length=260)
    content: str | None = Field(default=None, max_length=4000)
    metadata: dict[str, str] = Field(default_factory=dict)


class CareTaskClinicalChatMessageRequest(BaseModel):
    """Entrada para crear un turno de chat clinico en un CareTask."""

    query: str = Field(..., min_length=3, max_length=4000)
    session_id: str | None = Field(
        default=None,
        min_length=3,
        max_length=64,
        pattern=r"^[A-Za-z0-9._:-]+$",
    )
    clinician_id: str | None = Field(default=None, max_length=80)
    specialty_hint: str | None = Field(default=None, max_length=80)
    # Campo legado para compatibilidad de clientes antiguos.
    # El backend actual enruta de forma automatica por intencion y no depende de este valor.
    conversation_mode: Literal["auto", "general", "clinical"] = "auto"
    tool_mode: Literal[
        "chat",
        "medication",
        "cases",
        "treatment",
        "deep_search",
        "images",
    ] = "chat"
    use_authenticated_specialty_mode: bool = False
    use_patient_history: bool = True
    max_patient_history_messages: int = Field(default=20, ge=0, le=200)
    use_web_sources: bool = False
    max_web_sources: int = Field(default=2, ge=1, le=10)
    max_internal_sources: int = Field(default=3, ge=1, le=12)
    max_history_messages: int = Field(default=6, ge=0, le=50)
    include_protocol_catalog: bool = True
    persist_extracted_facts: bool = True
    enable_active_interrogation: bool = False
    interrogation_max_turns: int = Field(default=3, ge=1, le=10)
    interrogation_confidence_threshold: float = Field(default=0.93, ge=0.5, le=0.99)
    local_evidence: list[ClinicalLocalEvidenceItem] = Field(default_factory=list, max_length=5)


class CareTaskClinicalChatHistoryItemResponse(BaseModel):
    """Mensaje de chat persistido para historial operativo."""

    id: int
    care_task_id: int
    session_id: str
    clinician_id: str | None
    effective_specialty: str
    user_query: str
    assistant_answer: str
    matched_domains: list[str]
    matched_endpoints: list[str]
    knowledge_sources: list[dict[str, str]]
    web_sources: list[dict[str, str]]
    memory_facts_used: list[str]
    patient_history_facts_used: list[str]
    extracted_facts: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CareTaskClinicalChatQualityMetrics(BaseModel):
    """Metricas automaticas locales para control de calidad por turno."""

    answer_relevance: float = Field(..., ge=0, le=1)
    context_relevance: float = Field(..., ge=0, le=1)
    groundedness: float = Field(..., ge=0, le=1)
    quality_status: Literal["ok", "attention", "degraded"]


class CareTaskClinicalChatMessageResponse(BaseModel):
    """Respuesta de creacion de mensaje con trazabilidad de workflow."""

    care_task_id: int
    message_id: int
    session_id: str
    agent_run_id: int
    workflow_name: str
    response_mode: Literal["general", "clinical"]
    tool_mode: Literal[
        "chat",
        "medication",
        "cases",
        "treatment",
        "deep_search",
        "images",
    ]
    answer: str
    matched_domains: list[str]
    matched_endpoints: list[str]
    effective_specialty: str
    knowledge_sources: list[dict[str, str]]
    web_sources: list[dict[str, str]]
    memory_facts_used: list[str]
    patient_history_facts_used: list[str]
    extracted_facts: list[str]
    quality_metrics: CareTaskClinicalChatQualityMetrics
    interpretability_trace: list[str]
    non_diagnostic_warning: str


class CareTaskClinicalChatPublicResponse(BaseModel):
    """Respuesta publica de chat para frontend, sin trazas internas de backend."""

    care_task_id: int
    message_id: int
    session_id: str
    response_mode: Literal["general", "clinical"]
    tool_mode: Literal[
        "chat",
        "medication",
        "cases",
        "treatment",
        "deep_search",
        "images",
    ]
    answer: str
    effective_specialty: str
    matched_domains: list[str]
    knowledge_sources: list[dict[str, str]]
    quality_metrics: CareTaskClinicalChatQualityMetrics
    non_diagnostic_warning: str


class CareTaskClinicalChatAsyncCreateResponse(BaseModel):
    """Confirmacion de encolado para procesamiento asincrono."""

    care_task_id: int
    job_id: str
    session_id: str
    status: Literal["queued", "running", "completed", "failed"]
    poll_after_ms: int = Field(default=1200, ge=250, le=10000)


class CareTaskClinicalChatAsyncStatusResponse(BaseModel):
    """Estado de ejecucion asincrona de un turno de chat."""

    care_task_id: int
    job_id: str
    session_id: str
    status: Literal["queued", "running", "completed", "failed"]
    created_at: datetime
    updated_at: datetime
    message_id: int | None = None
    agent_run_id: int | None = None
    workflow_name: str | None = None
    response_mode: Literal["general", "clinical"] | None = None
    tool_mode: Literal[
        "chat",
        "medication",
        "cases",
        "treatment",
        "deep_search",
        "images",
    ] | None = None
    quality_status: Literal["ok", "attention", "degraded"] | None = None
    llm_used: bool | None = None
    error: str | None = None


class CareTaskClinicalChatMemoryResponse(BaseModel):
    """Resumen agregado de memoria reutilizable del chat clinico."""

    care_task_id: int
    session_id: str | None
    interactions_count: int
    top_domains: list[str]
    top_extracted_facts: list[str]
    patient_reference: str | None
    patient_interactions_count: int
    patient_top_domains: list[str]
    patient_top_extracted_facts: list[str]
