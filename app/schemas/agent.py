from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    workflow_name: Literal["task_triage_v1"] = Field(
        ..., description="Workflow agente a ejecutar"
    )
    title: str = Field(..., min_length=3, max_length=200, description="Titulo base de la tarea")
    description: str | None = Field(
        default=None, max_length=2000, description="Descripcion opcional"
    )


class AgentStepTraceResponse(BaseModel):
    id: int
    step_order: int
    step_name: str
    status: str
    step_input: dict[str, Any]
    step_output: dict[str, Any] | None
    decision: str | None
    fallback_used: bool
    error_message: str | None
    step_cost_usd: float
    step_latency_ms: int
    created_at: datetime


class AgentRunResponse(BaseModel):
    id: int
    workflow_name: str
    status: str
    run_input: dict[str, Any]
    run_output: dict[str, Any] | None
    error_message: str | None
    total_cost_usd: float
    total_latency_ms: int
    created_at: datetime
    updated_at: datetime
    steps: list[AgentStepTraceResponse]


class AgentRunSummaryResponse(BaseModel):
    id: int
    workflow_name: str
    status: str
    total_cost_usd: float
    total_latency_ms: int
    created_at: datetime
    updated_at: datetime


class AgentOpsSummaryResponse(BaseModel):
    total_runs: int
    completed_runs: int
    failed_runs: int
    fallback_steps: int
    fallback_rate_percent: float
