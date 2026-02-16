from fastapi import APIRouter

from app.schemas.ai import TaskTriageRequest, TaskTriageResponse
from app.services.ai_triage_service import AITriageService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post(
    "/triage-task",
    response_model=TaskTriageResponse,
    summary="Sugerir prioridad y categoria de tarea",
)
def triage_task(payload: TaskTriageRequest):
    """Devuelve una recomendacion explicable para planificar y priorizar tareas."""
    return AITriageService.suggest_task_metadata(
        title=payload.title,
        description=payload.description,
    )
