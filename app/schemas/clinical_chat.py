"""
Schemas para chat clinico-operativo sobre CareTask.

El chat no diagnostica. Solo organiza recomendaciones operativas y memoria de
consulta para apoyar la toma de decisiones con validacion humana.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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
    conversation_mode: Literal["auto", "general", "clinical"] = "auto"
    tool_mode: Literal[
        "chat",
        "medication",
        "cases",
        "treatment",
        "deep_search",
        "images",
    ] = "chat"
    use_authenticated_specialty_mode: bool = True
    use_patient_history: bool = True
    max_patient_history_messages: int = Field(default=40, ge=0, le=200)
    use_web_sources: bool = False
    max_web_sources: int = Field(default=3, ge=1, le=10)
    max_internal_sources: int = Field(default=4, ge=1, le=12)
    max_history_messages: int = Field(default=10, ge=0, le=50)
    include_protocol_catalog: bool = True
    persist_extracted_facts: bool = True


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
    interpretability_trace: list[str]
    non_diagnostic_warning: str


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
