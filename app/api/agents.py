from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.agent_run import AgentStep
from app.schemas.agent import (
    AgentOpsSummaryResponse,
    AgentRunRequest,
    AgentRunResponse,
    AgentRunSummaryResponse,
    AgentStepTraceResponse,
)
from app.services.agent_run_service import AgentRunService

router = APIRouter(prefix="/agents", tags=["agents"])


def _map_step(step: AgentStep) -> AgentStepTraceResponse:
    return AgentStepTraceResponse(
        id=step.id,
        step_order=step.step_order,
        step_name=step.step_name,
        status=step.status,
        step_input=step.step_input,
        step_output=step.step_output,
        decision=step.decision,
        fallback_used=bool(step.fallback_used),
        error_message=step.error_message,
        step_cost_usd=step.step_cost_usd,
        step_latency_ms=step.step_latency_ms,
        created_at=step.created_at,
    )


@router.get(
    "/ops/summary",
    response_model=AgentOpsSummaryResponse,
    summary="Obtener metricas de resumen operativo de ejecuciones de agente",
)
def get_agent_ops_summary(
    workflow_name: str | None = Query(default=None), db: Session = Depends(get_db)
):
    """Devuelve contadores agregados para monitorizar fiabilidad y fallback."""
    summary = AgentRunService.get_ops_summary(db=db, workflow_name=workflow_name)
    return AgentOpsSummaryResponse(**summary)


@router.get(
    "/runs",
    response_model=list[AgentRunSummaryResponse],
    summary="Listar ejecuciones recientes de workflows de agentes",
)
def list_agent_runs(
    limit: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    workflow_name: str | None = Query(default=None),
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Devuelve historial filtrado para operacion y depuracion de incidencias."""
    runs = AgentRunService.list_recent_runs(
        db=db,
        limit=limit,
        status=status_filter,
        workflow_name=workflow_name,
        created_from=created_from,
        created_to=created_to,
    )
    return [
        AgentRunSummaryResponse(
            id=run.id,
            workflow_name=run.workflow_name,
            status=run.status,
            total_cost_usd=run.total_cost_usd,
            total_latency_ms=run.total_latency_ms,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )
        for run in runs
    ]


@router.get(
    "/runs/{run_id}",
    response_model=AgentRunResponse,
    summary="Obtener una ejecucion de agente con pasos detallados",
)
def get_agent_run(run_id: int, db: Session = Depends(get_db)):
    """Devuelve una ejecucion persistida incluyendo trazas por paso."""
    run, steps = AgentRunService.get_run_with_steps(db=db, run_id=run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ejecucion de agente no encontrada."
        )
    return AgentRunResponse(
        id=run.id,
        workflow_name=run.workflow_name,
        status=run.status,
        run_input=run.run_input,
        run_output=run.run_output,
        error_message=run.error_message,
        total_cost_usd=run.total_cost_usd,
        total_latency_ms=run.total_latency_ms,
        created_at=run.created_at,
        updated_at=run.updated_at,
        steps=[_map_step(step) for step in steps],
    )


@router.post(
    "/run",
    response_model=AgentRunResponse,
    summary="Ejecutar workflow de agente con trazabilidad",
)
def run_agent_workflow(payload: AgentRunRequest, db: Session = Depends(get_db)):
    """Lanza un workflow, persiste trazas por paso y devuelve el resultado completo."""
    if payload.workflow_name != "task_triage_v1":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="workflow_name no soportado.",
        )
    try:
        run = AgentRunService.run_task_triage_workflow(
            db=db,
            title=payload.title,
            description=payload.description,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    steps = AgentRunService.get_run_with_steps(db=db, run_id=run.id)[1]
    return AgentRunResponse(
        id=run.id,
        workflow_name=run.workflow_name,
        status=run.status,
        run_input=run.run_input,
        run_output=run.run_output,
        error_message=run.error_message,
        total_cost_usd=run.total_cost_usd,
        total_latency_ms=run.total_latency_ms,
        created_at=run.created_at,
        updated_at=run.updated_at,
        steps=[_map_step(step) for step in steps],
    )
