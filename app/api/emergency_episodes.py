"""
Endpoints de episodio de urgencias (flujo extremo-a-extremo).
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.emergency_episode import (
    EmergencyEpisodeCreate,
    EmergencyEpisodeKpiSummaryResponse,
    EmergencyEpisodeResponse,
    EmergencyEpisodeTransitionRequest,
)
from app.services.emergency_episode_service import EmergencyEpisodeService

router = APIRouter(prefix="/emergency-episodes", tags=["emergency-episodes"])


@router.post("/", response_model=EmergencyEpisodeResponse, status_code=status.HTTP_201_CREATED)
def create_emergency_episode(payload: EmergencyEpisodeCreate, db: Session = Depends(get_db)):
    """Crea un episodio nuevo de urgencias con su etapa inicial."""
    return EmergencyEpisodeService.create_episode(db=db, payload=payload)


@router.get("/", response_model=list[EmergencyEpisodeResponse])
def list_emergency_episodes(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Lista episodios recientes para seguimiento operativo."""
    return EmergencyEpisodeService.list_episodes(db=db, limit=limit)


@router.get("/{episode_id}", response_model=EmergencyEpisodeResponse)
def get_emergency_episode(episode_id: int, db: Session = Depends(get_db)):
    """Recupera un episodio por id."""
    episode = EmergencyEpisodeService.get_episode_by_id(db=db, episode_id=episode_id)
    if episode is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episodio no encontrado")
    return episode


@router.post("/{episode_id}/transition", response_model=EmergencyEpisodeResponse)
def transition_emergency_episode(
    episode_id: int,
    payload: EmergencyEpisodeTransitionRequest,
    db: Session = Depends(get_db),
):
    """Mueve episodio a la siguiente etapa validando transicion permitida."""
    try:
        return EmergencyEpisodeService.transition_episode(
            db=db,
            episode_id=episode_id,
            payload=payload,
        )
    except ValueError as exc:
        message = str(exc)
        if "no encontrado" in message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc


@router.get("/{episode_id}/kpis", response_model=EmergencyEpisodeKpiSummaryResponse)
def get_emergency_episode_kpis(episode_id: int, db: Session = Depends(get_db)):
    """Devuelve KPIs de tiempo del episodio."""
    episode = EmergencyEpisodeService.get_episode_by_id(db=db, episode_id=episode_id)
    if episode is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episodio no encontrado")
    return EmergencyEpisodeService.build_kpi_summary(episode=episode)
