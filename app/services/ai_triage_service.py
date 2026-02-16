from typing import Literal

from app.core.config import settings
from app.schemas.ai import TaskTriageResponse
from app.services.llm_triage_provider import LLMTriageProvider


class AITriageService:
    @staticmethod
    def _rules_suggest_task_metadata(
        title: str, description: str | None = None
    ) -> TaskTriageResponse:
        """Triaje basado en reglas, explicable y determinista."""
        text = f"{title} {description or ''}".lower()

        bug_keywords = ("bug", "error", "fix", "exception", "crash", "incident")
        ops_keywords = ("deploy", "docker", "infra", "monitor", "prometheus", "grafana")
        docs_keywords = ("docs", "readme", "document", "guide", "tutorial")
        analysis_keywords = ("analyze", "investigate", "research", "spike", "poc")
        urgent_keywords = ("urgent", "asap", "critical", "blocker", "production")

        category: Literal["dev", "ops", "bug", "docs", "analysis", "general"] = "general"
        reason_parts: list[str] = []
        confidence = 0.55

        if any(keyword in text for keyword in bug_keywords):
            category = "bug"
            confidence = max(confidence, 0.8)
            reason_parts.append("Se detectaron palabras clave de errores.")
        elif any(keyword in text for keyword in docs_keywords):
            category = "docs"
            confidence = max(confidence, 0.76)
            reason_parts.append("Se detectaron palabras clave de documentacion.")
        elif any(keyword in text for keyword in ops_keywords):
            category = "ops"
            confidence = max(confidence, 0.78)
            reason_parts.append("Se detectaron palabras clave de operaciones/infraestructura.")
        elif any(keyword in text for keyword in analysis_keywords):
            category = "analysis"
            confidence = max(confidence, 0.74)
            reason_parts.append("Se detectaron palabras clave de analisis/investigacion.")
        elif "api" in text or "feature" in text or "endpoint" in text:
            category = "dev"
            confidence = max(confidence, 0.72)
            reason_parts.append("Se detectaron palabras clave de desarrollo/producto.")

        priority: Literal["low", "medium", "high"] = "medium"
        if any(keyword in text for keyword in urgent_keywords):
            priority = "high"
            confidence = max(confidence, 0.85)
            reason_parts.append("Las palabras de urgencia indican prioridad alta.")
        elif category in {"bug", "ops"}:
            priority = "high"
            confidence = max(confidence, 0.8)
            reason_parts.append("La categoria suele impactar la fiabilidad del sistema.")
        elif category in {"docs", "analysis"}:
            priority = "low"
            reason_parts.append("La tarea parece no bloqueante para la operacion en ejecucion.")

        if not reason_parts:
            reason_parts.append("No se detectaron senales fuertes; se aplican valores conservadores.")

        return TaskTriageResponse(
            priority=priority,
            category=category,
            confidence=round(confidence, 2),
            reason=" ".join(reason_parts),
            source="rules",
        )

    @staticmethod
    def suggest_task_metadata(title: str, description: str | None = None) -> TaskTriageResponse:
        """
        Selecciona estrategia de triaje segun `AI_TRIAGE_MODE` y mantiene fallback seguro.

        - `rules`: siempre reglas deterministas.
        - `hybrid`: intenta proveedor LLM primero; si no esta disponible, usa reglas.
        """
        if settings.AI_TRIAGE_MODE == "rules":
            return AITriageService._rules_suggest_task_metadata(title, description)

        llm_result = LLMTriageProvider.suggest_task_metadata(title, description)
        if llm_result is not None and llm_result.confidence >= 0.7:
            return llm_result

        fallback_result = AITriageService._rules_suggest_task_metadata(title, description)
        fallback_result.source = "rules_fallback"
        fallback_result.reason = (
            f"{fallback_result.reason} "
            "Fallback de modo hibrido: salida LLM no disponible."
        )
        return fallback_result
