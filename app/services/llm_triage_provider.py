from app.schemas.ai import TaskTriageResponse


class LLMTriageProvider:
    @staticmethod
    def suggest_task_metadata(
        title: str, description: str | None = None
    ) -> TaskTriageResponse | None:
        """
        Devuelve una recomendacion simulada de LLM cuando hay senal clara de IA.

        Este proveedor es intencionadamente determinista para practicar arquitectura
        hibrida sin introducir aun dependencias de red o proveedor.
        """
        text = f"{title} {description or ''}".lower()

        ml_keywords = ("ml", "model", "llm", "vector", "rag", "embedding", "prompt")
        if not any(keyword in text for keyword in ml_keywords):
            return None

        return TaskTriageResponse(
            priority="medium",
            category="analysis",
            confidence=0.78,
            reason="El proveedor LLM detecto contexto orientado a IA/ML en la solicitud.",
            source="llm",
        )
