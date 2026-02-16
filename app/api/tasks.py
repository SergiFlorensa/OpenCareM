"""
Endpoints de tareas - Rutas HTTP para gestion de tareas.

Arquitectura:
Cliente (peticion HTTP) -> Endpoint -> Servicio -> Modelo -> BD
Cliente <- Endpoint (respuesta HTTP) <- Servicio <- Modelo <- BD
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva tarea",
    description="Crea una tarea nueva en el sistema",
)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Crea una tarea nueva."""
    return TaskService.create_task(db, task)


@router.get(
    "/",
    response_model=List[TaskResponse],
    summary="Listar todas las tareas",
    description="Obtiene una lista de tareas con filtros opcionales",
)
def get_tasks(
    skip: int = Query(0, ge=0, description="Numero de registros a saltar"),
    limit: int = Query(100, ge=1, le=100, description="Numero maximo de resultados"),
    completed: Optional[bool] = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db),
):
    """Lista tareas con paginacion y filtros."""
    return TaskService.get_all_tasks(db, skip=skip, limit=limit, completed=completed)


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Obtener una tarea especifica",
    description="Obtiene los detalles de una tarea por su ID",
)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Obtiene una tarea por ID."""
    task = TaskService.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarea con ID {task_id} no encontrada",
        )
    return task


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Actualizar una tarea",
    description="Actualiza los datos de una tarea existente",
)
def update_task(task_id: int, task_data: TaskUpdate, db: Session = Depends(get_db)):
    """Actualiza una tarea."""
    updated_task = TaskService.update_task(db, task_id, task_data)
    if not updated_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarea con ID {task_id} no encontrada",
        )
    return updated_task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una tarea",
    description="Elimina una tarea del sistema",
)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Elimina una tarea."""
    deleted = TaskService.delete_task(db, task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarea con ID {task_id} no encontrada",
        )
    return None


@router.get(
    "/stats/count",
    summary="Estadisticas de tareas",
    description="Obtiene contadores de tareas",
)
def get_tasks_stats(db: Session = Depends(get_db)):
    """Devuelve estadisticas de tareas."""
    total = TaskService.get_tasks_count(db)
    completed = TaskService.get_tasks_count(db, completed=True)
    pending = TaskService.get_tasks_count(db, completed=False)
    return {"total": total, "completed": completed, "pending": pending}
