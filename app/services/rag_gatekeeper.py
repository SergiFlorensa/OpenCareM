"""
Gatekeeper basico para validar respuestas RAG.
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class BasicGatekeeper:
    """Validador de respuestas RAG basado en reglas ligeras."""

    def compute_context_relevance(
        self,
        *,
        query: str,
        retrieved_chunks: list[dict[str, Any]],
    ) -> float:
        """Calcula alineacion entre consulta y evidencia recuperada."""
        return self._context_relevance_score(query, retrieved_chunks)

    def compute_faithfulness(
        self,
        *,
        response: str,
        retrieved_chunks: list[dict[str, Any]],
    ) -> float:
        """Calcula soporte lexical de la respuesta sobre evidencia recuperada."""
        return self._faithfulness_score(response, retrieved_chunks)

    def validate_response(
        self,
        *,
        query: str,
        response: str,
        retrieved_chunks: list[dict[str, Any]],
    ) -> tuple[bool, list[str]]:
        issues: list[str] = []
        if not self._is_specific_response(response):
            issues.append("RIESGO: respuesta demasiado generica o demasiado corta")
        if retrieved_chunks and not self._has_chunk_citations(response, retrieved_chunks):
            issues.append("ADVERTENCIA: la respuesta no referencia evidencia recuperada")
        context_relevance = self.compute_context_relevance(
            query=query,
            retrieved_chunks=retrieved_chunks,
        )
        if retrieved_chunks and context_relevance < settings.CLINICAL_CHAT_RAG_CONTEXT_MIN_RATIO:
            issues.append(
                "ADVERTENCIA: evidencia recuperada poco alineada con la consulta "
                f"(context_relevance={context_relevance:.3f})"
            )
        faithfulness = self.compute_faithfulness(
            response=response,
            retrieved_chunks=retrieved_chunks,
        )
        if retrieved_chunks and faithfulness < settings.CLINICAL_CHAT_RAG_FAITHFULNESS_MIN_RATIO:
            issues.append(
                "RIESGO: veracidad insuficiente respecto a evidencia recuperada "
                f"(faithfulness={faithfulness:.3f})"
            )
        contradictions = self._detect_contradictions(response, retrieved_chunks)
        issues.extend(contradictions)
        if not self._answers_question(query, response):
            issues.append("RIESGO: la respuesta no aborda la pregunta principal")
        if not self._has_clinical_markers(response):
            issues.append("ADVERTENCIA: lenguaje clinico insuficiente para contexto operativo")

        is_valid = not any(item.startswith("RIESGO") for item in issues)
        if issues:
            logger.warning("Gatekeeper issues: %s", issues)
        return is_valid, issues

    @staticmethod
    def _is_specific_response(response: str) -> bool:
        text = (response or "").strip().lower()
        if len(text) < 80:
            return False
        generic_phrases = (
            "no tengo informacion suficiente",
            "necesito mas contexto",
            "es dificil decir",
            "depende de muchos factores",
        )
        return not any(phrase in text for phrase in generic_phrases)

    @staticmethod
    def _has_chunk_citations(response: str, chunks: list[dict[str, Any]]) -> bool:
        response_lower = response.lower()
        for chunk in chunks[:4]:
            for keyword in chunk.get("keywords", [])[:6]:
                token = str(keyword).lower().strip()
                if token and token in response_lower:
                    return True
        for chunk in chunks[:2]:
            chunk_tokens = [
                token
                for token in str(chunk.get("text", "")).lower().split()
                if len(token) > 6
            ]
            if any(token in response_lower for token in chunk_tokens[:6]):
                return True
        return False

    @staticmethod
    def _detect_contradictions(response: str, chunks: list[dict[str, Any]]) -> list[str]:
        issues: list[str] = []
        response_lower = response.lower()
        for chunk in chunks[:2]:
            chunk_text = str(chunk.get("text", "")).lower()
            if "no recomendado" in chunk_text and "se recomienda" in response_lower:
                issues.append("RIESGO: posible contradiccion con documento recuperado")
            if "contraindicado" in chunk_text and "indicado" in response_lower:
                issues.append("RIESGO: posible contradiccion con protocolo recuperado")
        return issues

    @staticmethod
    def _answers_question(query: str, response: str) -> bool:
        query_tokens = {token for token in query.lower().split() if len(token) > 4}
        if len(query_tokens) <= 2:
            return True
        response_tokens = {token for token in response.lower().split() if len(token) > 4}
        return bool(query_tokens & response_tokens)

    @staticmethod
    def _has_clinical_markers(response: str) -> bool:
        clinical_keywords = (
            "paciente",
            "protocolo",
            "tratamiento",
            "evaluacion",
            "manejo",
            "recomendacion",
            "criterio",
            "seguimiento",
        )
        response_lower = response.lower()
        hits = sum(1 for marker in clinical_keywords if marker in response_lower)
        return hits >= 2

    @staticmethod
    def _context_relevance_score(query: str, chunks: list[dict[str, Any]]) -> float:
        query_tokens = {
            token.strip(".,;:()[]{}")
            for token in (query or "").lower().split()
            if len(token.strip(".,;:()[]{}")) > 3
        }
        if not query_tokens or not chunks:
            return 0.0

        best_overlap = 0.0
        for chunk in chunks[:6]:
            evidence_tokens = {
                token.strip(".,;:()[]{}")
                for token in str(chunk.get("text", "")).lower().split()
                if len(token.strip(".,;:()[]{}")) > 3
            }
            if not evidence_tokens:
                continue
            overlap = len(query_tokens & evidence_tokens) / max(1, len(query_tokens))
            if overlap > best_overlap:
                best_overlap = overlap
        return best_overlap

    @staticmethod
    def _faithfulness_score(response: str, chunks: list[dict[str, Any]]) -> float:
        response_tokens = {
            token.strip(".,;:()[]{}")
            for token in (response or "").lower().split()
            if len(token.strip(".,;:()[]{}")) > 4
        }
        if not response_tokens:
            return 0.0

        evidence_tokens: set[str] = set()
        for chunk in chunks[:5]:
            text = str(chunk.get("text", "")).lower()
            for token in text.split():
                clean = token.strip(".,;:()[]{}")
                if len(clean) > 4:
                    evidence_tokens.add(clean)

        if not evidence_tokens:
            return 0.0
        supported = sum(1 for token in response_tokens if token in evidence_tokens)
        return supported / max(1, len(response_tokens))
