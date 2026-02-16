"""
Esquemas de fuentes de conocimiento clinico validables.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class KnowledgeSourceCreateRequest(BaseModel):
    specialty: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=80,
        description="Especialidad operativa. Si no se envia, usa la del usuario autenticado.",
    )
    title: str = Field(..., min_length=6, max_length=200)
    summary: Optional[str] = Field(default=None, max_length=600)
    content: Optional[str] = Field(default=None, max_length=20000)
    source_type: Literal[
        "guideline",
        "pubmed",
        "mir",
        "institutional",
        "internal_note",
    ] = "guideline"
    source_url: Optional[str] = Field(default=None, max_length=500)
    source_path: Optional[str] = Field(default=None, max_length=300)
    tags: list[str] = Field(default_factory=list, max_length=20)
    expires_at: Optional[datetime] = None


class KnowledgeSourceSealRequest(BaseModel):
    decision: Literal["approve", "reject", "expire"] = Field(
        ...,
        description="Decision de sellado profesional.",
    )
    note: Optional[str] = Field(default=None, max_length=2000)
    expires_at: Optional[datetime] = None


class KnowledgeSourceValidationEventResponse(BaseModel):
    id: int
    source_id: int
    reviewer_user_id: Optional[int]
    decision: str
    note: Optional[str]
    created_at: datetime


class KnowledgeSourceResponse(BaseModel):
    id: int
    specialty: str
    title: str
    summary: Optional[str]
    source_type: str
    source_url: Optional[str]
    source_domain: Optional[str]
    source_path: Optional[str]
    tags: list[str]
    status: str
    created_by_user_id: Optional[int]
    validated_by_user_id: Optional[int]
    validation_note: Optional[str]
    validated_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class KnowledgeSourceTrustedDomainsResponse(BaseModel):
    web_whitelist_enforced: bool
    allowed_domains: list[str]
