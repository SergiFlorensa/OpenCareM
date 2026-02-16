from typing import Literal

from pydantic import BaseModel, Field


class TaskTriageRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200, description="Titulo de tarea a clasificar")
    description: str | None = Field(
        default=None, max_length=2000, description="Detalles opcionales de la tarea"
    )


class TaskTriageResponse(BaseModel):
    priority: Literal["low", "medium", "high"] = Field(
        ..., description="Prioridad de ejecucion sugerida"
    )
    category: Literal["dev", "ops", "bug", "docs", "analysis", "general"] = Field(
        ..., description="Categoria sugerida"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confianza del modelo de 0 a 1")
    reason: str = Field(..., description="Motivo legible de la recomendacion")
    source: Literal["rules", "llm", "rules_fallback"] = Field(
        ..., description="Origen de decision usado para generar la recomendacion"
    )
