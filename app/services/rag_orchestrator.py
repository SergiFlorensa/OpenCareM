"""
Orquestador RAG para el chat clinico.

Pipeline:
1) retrieval (hibrido o por dominio)
2) ensamblado de contexto RAG
3) augment de fuentes internas para el LLM
4) generacion LLM
5) validacion gatekeeper y auditoria
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.llm_chat_provider import LLMChatProvider
from app.services.rag_gatekeeper import BasicGatekeeper
from app.services.rag_prompt_builder import RAGContextAssembler
from app.services.rag_retriever import HybridRetriever

logger = logging.getLogger(__name__)


class RAGOrchestrator:
    """Orquestador principal del pipeline RAG."""

    def __init__(self, db: Session):
        self.db = db
        self.retriever = HybridRetriever()
        self.gatekeeper = BasicGatekeeper()

    def process_query_with_rag(
        self,
        *,
        query: str,
        response_mode: str = "clinical",
        effective_specialty: Optional[str] = None,
        tool_mode: str = "chat",
        matched_domains: Optional[list[str]] = None,
        matched_endpoints: Optional[list[str]] = None,
        memory_facts_used: Optional[list[str]] = None,
        patient_summary: Optional[dict[str, Any]] = None,
        patient_history_facts_used: Optional[list[str]] = None,
        knowledge_sources: Optional[list[dict[str, str]]] = None,
        web_sources: Optional[list[dict[str, str]]] = None,
        recent_dialogue: Optional[list[dict[str, str]]] = None,
        endpoint_results: Optional[list[dict[str, Any]]] = None,
        care_task_id: Optional[int] = None,
    ) -> tuple[Optional[str], dict[str, Any]]:
        started_at = time.perf_counter()
        trace: dict[str, Any] = {}

        matched_domains = matched_domains or []
        matched_endpoints = matched_endpoints or []
        memory_facts_used = memory_facts_used or []
        patient_history_facts_used = patient_history_facts_used or []
        knowledge_sources = knowledge_sources or []
        web_sources = web_sources or []
        recent_dialogue = recent_dialogue or []
        endpoint_results = endpoint_results or []
        effective_specialty = effective_specialty or "general"

        if response_mode != "clinical":
            return None, {"rag_status": "skipped_non_clinical"}

        try:
            k = settings.CLINICAL_CHAT_RAG_MAX_CHUNKS
            retrieved_chunks = []
            retrieval_strategy = "hybrid"

            if matched_domains:
                domain_chunks, domain_trace = self.retriever.search_by_domain(
                    matched_domains,
                    self.db,
                    k=k,
                )
                trace.update(domain_trace)
                if domain_chunks:
                    retrieved_chunks = domain_chunks
                    retrieval_strategy = "domain"

            if not retrieved_chunks:
                chunks, hybrid_trace = self.retriever.search_hybrid(
                    query,
                    self.db,
                    k=k,
                    specialty_filter=effective_specialty,
                )
                trace.update(hybrid_trace)
                retrieved_chunks = chunks

            if not retrieved_chunks:
                elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
                trace.update(
                    {
                        "rag_status": "failed_retrieval",
                        "rag_fallback_reason": "no_chunks_found",
                        "rag_total_latency_ms": str(elapsed_ms),
                    }
                )
                return None, trace

            chunk_dicts, assembly_trace = RAGContextAssembler.assemble_rag_context(
                retrieved_chunks,
                retrieval_trace=trace,
            )
            trace.update(assembly_trace)
            rag_sources = self._build_rag_knowledge_sources(chunk_dicts)
            augmented_sources = self._merge_sources(knowledge_sources, rag_sources)

            answer, llm_trace = LLMChatProvider.generate_answer(
                query=query,
                response_mode=response_mode,
                effective_specialty=effective_specialty,
                tool_mode=tool_mode,
                matched_domains=matched_domains,
                matched_endpoints=matched_endpoints,
                memory_facts_used=memory_facts_used,
                patient_summary=patient_summary,
                patient_history_facts_used=patient_history_facts_used,
                knowledge_sources=augmented_sources,
                web_sources=web_sources,
                recent_dialogue=recent_dialogue,
                endpoint_results=endpoint_results,
            )
            trace.update(llm_trace)

            if not answer:
                elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
                trace.update(
                    {
                        "rag_status": "failed_generation",
                        "rag_fallback_reason": llm_trace.get("llm_error", "llm_empty"),
                        "rag_total_latency_ms": str(elapsed_ms),
                    }
                )
                return None, trace

            is_valid = True
            issues: list[str] = []
            if settings.CLINICAL_CHAT_RAG_ENABLE_GATEKEEPER:
                is_valid, issues = self.gatekeeper.validate_response(
                    query=query,
                    response=answer,
                    retrieved_chunks=chunk_dicts,
                )

            elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
            trace.update(
                {
                    "rag_status": "success",
                    "rag_retrieval_strategy": retrieval_strategy,
                    "rag_chunks_retrieved": str(len(retrieved_chunks)),
                    "rag_total_latency_ms": str(elapsed_ms),
                    "rag_validation_status": "valid" if is_valid else "warning",
                    "rag_validation_issues": issues,
                    "rag_sources": rag_sources,
                }
            )

            if care_task_id:
                self._log_rag_query_audit(
                    care_task_id=care_task_id,
                    query=query,
                    method=retrieval_strategy,
                    chunks_retrieved=len(retrieved_chunks),
                    trace=trace,
                )

            return answer, trace
        except Exception as exc:  # pragma: no cover - defensivo
            elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
            trace.update(
                {
                    "rag_status": "failed_exception",
                    "rag_error": str(exc),
                    "rag_total_latency_ms": str(elapsed_ms),
                }
            )
            logger.exception("Error no controlado en RAG orchestrator")
            return None, trace

    def _build_rag_knowledge_sources(self, chunks: list[dict[str, Any]]) -> list[dict[str, str]]:
        sources: list[dict[str, str]] = []
        for chunk in chunks[: settings.CLINICAL_CHAT_RAG_MAX_CHUNKS]:
            snippet = str(chunk.get("text", "")).strip().replace("\n", " ")
            if len(snippet) > 320:
                snippet = f"{snippet[:320]}..."
            source = {
                "type": "rag_chunk",
                "title": str(chunk.get("section") or "fragmento interno"),
                "source": str(chunk.get("source") or "catalogo interno"),
                "snippet": snippet,
            }
            sources.append(source)
        return sources

    @staticmethod
    def _merge_sources(
        base_sources: list[dict[str, str]],
        rag_sources: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        merged: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for source in [*base_sources, *rag_sources]:
            key = (
                str(source.get("title") or ""),
                str(source.get("source") or ""),
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(source)
        max_sources = max(settings.CLINICAL_CHAT_RAG_MAX_CHUNKS + 4, 8)
        return merged[:max_sources]

    def _log_rag_query_audit(
        self,
        *,
        care_task_id: int,
        query: str,
        method: str,
        chunks_retrieved: int,
        trace: dict[str, Any],
    ) -> None:
        try:
            from app.models.rag_query_audit import RAGQueryAudit

            audit = RAGQueryAudit(
                care_task_id=care_task_id,
                query=query[:500],
                search_method=method,
                chunks_retrieved=chunks_retrieved,
                vector_search_latency_ms=self._to_float(trace.get("vector_search_latency_ms")),
                keyword_search_latency_ms=self._to_float(trace.get("keyword_search_latency_ms")),
                total_latency_ms=self._to_float(trace.get("rag_total_latency_ms")),
                model_used=str(trace.get("embedding_model") or trace.get("llm_model") or "unknown"),
            )
            self.db.add(audit)
            self.db.commit()
        except Exception as exc:  # pragma: no cover - defensivo
            self.db.rollback()
            logger.warning("No se pudo guardar auditoria RAG: %s", exc)

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
