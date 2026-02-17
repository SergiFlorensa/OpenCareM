"""
Servicio de gestion de fuentes de conocimiento clinico confiables.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.clinical_knowledge_source import ClinicalKnowledgeSource
from app.models.clinical_knowledge_source_validation import ClinicalKnowledgeSourceValidation
from app.models.user import User
from app.schemas.knowledge_source import KnowledgeSourceCreateRequest, KnowledgeSourceSealRequest


class KnowledgeSourceService:
    """Gestiona alta, listado y sellado profesional de fuentes clinicas."""

    @staticmethod
    def _normalize_specialty(value: str | None, fallback: str = "general") -> str:
        if not value:
            return fallback
        normalized = value.strip().lower().replace(" ", "_")
        return normalized or fallback

    @staticmethod
    def _normalize_tags(tags: list[str]) -> list[str]:
        normalized: list[str] = []
        for tag in tags:
            cleaned = tag.strip().lower().replace(" ", "_")
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned[:40])
        return normalized[:20]

    @staticmethod
    def get_allowed_domains() -> list[str]:
        raw = settings.CLINICAL_CHAT_WEB_ALLOWED_DOMAINS
        return [item.strip().lower() for item in raw.split(",") if item.strip()]

    @classmethod
    def _extract_domain(cls, source_url: str | None) -> str | None:
        if not source_url:
            return None
        parsed = urlparse(source_url)
        domain = (parsed.hostname or "").strip().lower()
        return domain or None

    @classmethod
    def is_allowed_domain(cls, domain: str | None) -> bool:
        if not domain:
            return False
        if not settings.CLINICAL_CHAT_WEB_STRICT_WHITELIST:
            return True
        allowed_domains = cls.get_allowed_domains()
        for allowed in allowed_domains:
            if domain == allowed or domain.endswith(f".{allowed}"):
                return True
        return False

    @classmethod
    def create_source(
        cls,
        db: Session,
        *,
        payload: KnowledgeSourceCreateRequest,
        current_user: User,
    ) -> ClinicalKnowledgeSource:
        if not payload.content and not payload.source_url and not payload.source_path:
            raise ValueError("Debe indicar contenido, URL o ruta de fuente.")
        source_domain = cls._extract_domain(payload.source_url)
        if payload.source_url and not cls.is_allowed_domain(source_domain):
            raise ValueError(
                "Dominio no permitido por politica de seguridad. "
                "Solo se aceptan dominios de la whitelist clinica."
            )
        source = ClinicalKnowledgeSource(
            specialty=cls._normalize_specialty(
                payload.specialty,
                current_user.specialty or "general",
            ),
            title=payload.title.strip(),
            summary=payload.summary.strip() if payload.summary else None,
            content=payload.content.strip() if payload.content else None,
            source_type=payload.source_type,
            source_url=payload.source_url.strip() if payload.source_url else None,
            source_domain=source_domain,
            source_path=payload.source_path.strip() if payload.source_path else None,
            tags=cls._normalize_tags(payload.tags),
            status="pending_review",
            created_by_user_id=current_user.id,
            expires_at=payload.expires_at,
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        return source

    @staticmethod
    def get_source(db: Session, *, source_id: int) -> Optional[ClinicalKnowledgeSource]:
        return (
            db.query(ClinicalKnowledgeSource)
            .filter(ClinicalKnowledgeSource.id == source_id)
            .first()
        )

    @staticmethod
    def list_sources(
        db: Session,
        *,
        specialty: str | None,
        status: str | None,
        validated_only: bool,
        limit: int,
    ) -> list[ClinicalKnowledgeSource]:
        safe_limit = max(1, min(limit, 200))
        query = db.query(ClinicalKnowledgeSource)
        if specialty:
            query = query.filter(
                ClinicalKnowledgeSource.specialty == specialty.strip().lower().replace(" ", "_")
            )
        if validated_only:
            query = query.filter(ClinicalKnowledgeSource.status == "validated")
        elif status:
            query = query.filter(ClinicalKnowledgeSource.status == status)
        return (
            query.order_by(
                ClinicalKnowledgeSource.updated_at.desc(),
                ClinicalKnowledgeSource.id.desc(),
            )
            .limit(safe_limit)
            .all()
        )

    @classmethod
    def seal_source(
        cls,
        db: Session,
        *,
        source: ClinicalKnowledgeSource,
        payload: KnowledgeSourceSealRequest,
        reviewer: User,
    ) -> ClinicalKnowledgeSourceValidation:
        if payload.decision == "approve" and source.source_url:
            source_domain = cls._extract_domain(source.source_url)
            if not cls.is_allowed_domain(source_domain):
                raise ValueError("No se puede sellar una fuente con dominio fuera de whitelist.")
            source.source_domain = source_domain
        now = datetime.now(timezone.utc)
        status_map = {
            "approve": "validated",
            "reject": "rejected",
            "expire": "expired",
        }
        source.status = status_map[payload.decision]
        source.validated_by_user_id = reviewer.id
        source.validation_note = payload.note.strip() if payload.note else None
        source.validated_at = now
        source.expires_at = payload.expires_at if payload.expires_at else source.expires_at
        event = ClinicalKnowledgeSourceValidation(
            source_id=source.id,
            reviewer_user_id=reviewer.id,
            decision=payload.decision,
            note=payload.note.strip() if payload.note else None,
        )
        db.add(event)
        db.add(source)
        db.commit()
        db.refresh(source)
        return event

    @staticmethod
    def list_validations(
        db: Session,
        *,
        source_id: int,
        limit: int,
    ) -> list[ClinicalKnowledgeSourceValidation]:
        safe_limit = max(1, min(limit, 100))
        return (
            db.query(ClinicalKnowledgeSourceValidation)
            .filter(ClinicalKnowledgeSourceValidation.source_id == source_id)
            .order_by(
                ClinicalKnowledgeSourceValidation.created_at.desc(),
                ClinicalKnowledgeSourceValidation.id.desc(),
            )
            .limit(safe_limit)
            .all()
        )
