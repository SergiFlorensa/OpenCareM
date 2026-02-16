"""
Endpoints para gestion de fuentes clinicas confiables.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_superuser
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.knowledge_source import (
    KnowledgeSourceCreateRequest,
    KnowledgeSourceResponse,
    KnowledgeSourceSealRequest,
    KnowledgeSourceTrustedDomainsResponse,
    KnowledgeSourceValidationEventResponse,
)
from app.services.knowledge_source_service import KnowledgeSourceService

router = APIRouter(prefix="/knowledge-sources", tags=["KnowledgeSources"])


@router.get("/", response_model=list[KnowledgeSourceResponse])
def list_knowledge_sources(
    specialty: Optional[str] = Query(default=None, max_length=80),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    validated_only: bool = Query(default=True),
    limit: int = Query(default=100, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[KnowledgeSourceResponse]:
    if not validated_only and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden listar fuentes no validadas.",
        )
    sources = KnowledgeSourceService.list_sources(
        db,
        specialty=specialty,
        status=status_filter,
        validated_only=validated_only,
        limit=limit,
    )
    return [
        KnowledgeSourceResponse.model_validate(source, from_attributes=True)
        for source in sources
    ]


@router.post("/", response_model=KnowledgeSourceResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_source(
    payload: KnowledgeSourceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> KnowledgeSourceResponse:
    try:
        source = KnowledgeSourceService.create_source(
            db,
            payload=payload,
            current_user=current_user,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return KnowledgeSourceResponse.model_validate(source, from_attributes=True)


@router.post(
    "/{source_id}/seal",
    response_model=KnowledgeSourceValidationEventResponse,
)
def seal_knowledge_source(
    source_id: int,
    payload: KnowledgeSourceSealRequest,
    reviewer: User = Depends(require_superuser),
    db: Session = Depends(get_db),
) -> KnowledgeSourceValidationEventResponse:
    source = KnowledgeSourceService.get_source(db, source_id=source_id)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fuente clinica no encontrada.",
        )
    try:
        event = KnowledgeSourceService.seal_source(
            db,
            source=source,
            payload=payload,
            reviewer=reviewer,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return KnowledgeSourceValidationEventResponse.model_validate(event, from_attributes=True)


@router.get(
    "/{source_id}/validations",
    response_model=list[KnowledgeSourceValidationEventResponse],
)
def list_knowledge_source_validations(
    source_id: int,
    limit: int = Query(default=30, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[KnowledgeSourceValidationEventResponse]:
    source = KnowledgeSourceService.get_source(db, source_id=source_id)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fuente clinica no encontrada.",
        )
    events = KnowledgeSourceService.list_validations(db, source_id=source_id, limit=limit)
    return [
        KnowledgeSourceValidationEventResponse.model_validate(
            event,
            from_attributes=True,
        )
        for event in events
    ]


@router.get(
    "/trusted-domains",
    response_model=KnowledgeSourceTrustedDomainsResponse,
)
def get_trusted_domains(
    _: User = Depends(get_current_user),
) -> KnowledgeSourceTrustedDomainsResponse:
    return KnowledgeSourceTrustedDomainsResponse(
        web_whitelist_enforced=settings.CLINICAL_CHAT_WEB_STRICT_WHITELIST,
        allowed_domains=KnowledgeSourceService.get_allowed_domains(),
    )
