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
import math
import re
import time
from array import array
from typing import Any, Optional

from sqlalchemy import Text, cast, func, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document_chunk import DocumentChunk
from app.services.chroma_retriever import ChromaRetriever
from app.services.clinical_svm_domain_service import ClinicalSVMDomainService
from app.services.elastic_retriever import ElasticRetriever
from app.services.llamaindex_retriever import LlamaIndexRetriever
from app.services.llm_chat_provider import LLMChatProvider
from app.services.rag_gatekeeper import BasicGatekeeper
from app.services.rag_prompt_builder import RAGContextAssembler
from app.services.rag_retriever import HybridRetriever

logger = logging.getLogger(__name__)


class RAGOrchestrator:
    """Orquestador principal del pipeline RAG."""

    _MULTI_INTENT_DOMAIN_CATALOG: list[dict[str, object]] = [
        {
            "key": "oncology",
            "label": "Oncologia",
            "summary": "Neutropenia febril, toxicidad y complicaciones de tratamiento.",
            "keywords": ["oncologia", "oncologico", "cancer", "quimioterapia", "neutropenia"],
        },
        {
            "key": "sepsis",
            "label": "Sepsis",
            "summary": "Bundle inicial y escalado hemodinamico.",
            "keywords": ["sepsis", "lactato", "qsofa", "hipotension", "noradrenalina"],
        },
        {
            "key": "pediatrics_neonatology",
            "label": "Pediatria y neonatologia",
            "summary": "Urgencias pediatricas y neonatales.",
            "keywords": ["pediatria", "neonato", "lactante", "nino", "nina", "vacunacion"],
        },
        {
            "key": "gynecology_obstetrics",
            "label": "Ginecologia y obstetricia",
            "summary": "Sangrado, embarazo y riesgo materno fetal.",
            "keywords": [
                "obstetricia",
                "ginecologia",
                "gestante",
                "embarazo",
                "preeclampsia",
                "ectopico",
            ],
        },
        {
            "key": "scasest",
            "label": "SCASEST",
            "summary": "Sindromes coronarios agudos sin elevacion ST.",
            "keywords": ["scasest", "troponina", "angina", "grace", "isquemia"],
        },
        {
            "key": "critical_ops",
            "label": "Operativa critica",
            "summary": "ABC, monitorizacion y escalado inmediato.",
            "keywords": ["shock", "abc", "via aerea", "inestabilidad", "monitorizacion"],
        },
    ]
    _SEGMENT_SPLIT_PATTERN = re.compile(
        r"(?:[;\n]+|\s(?:ademas|adem[aá]s|junto\s+con|asociado\s+a|concomitante\s+con)\s+)",
        flags=re.IGNORECASE,
    )
    _SOFT_CONNECTOR_PATTERN = re.compile(
        r"\s(?:y|e|mas|m[aá]s)\s+",
        flags=re.IGNORECASE,
    )
    _ACTION_STOPWORDS = {
        "paciente",
        "caso",
        "general",
        "situacion",
        "valoracion",
        "manejo",
        "clinico",
        "clinica",
        "tiempo",
        "urgencias",
    }
    _AUXILIARY_TOKENS = {
        "ser",
        "estar",
        "haber",
        "hay",
        "ha",
        "han",
        "fue",
        "es",
        "son",
        "era",
        "eran",
        "esta",
        "estan",
        "debe",
        "deben",
        "puede",
        "pueden",
        "podria",
        "podrian",
    }
    _ACTION_TOKENS = {
        "activar",
        "administrar",
        "ajustar",
        "aislar",
        "confirmar",
        "escalar",
        "iniciar",
        "monitorizar",
        "reevaluar",
        "solicitar",
        "titular",
        "valorar",
        "vigilar",
        "derivar",
        "priorizar",
    }

    def __init__(self, db: Session):
        self.db = db
        self.legacy_retriever = HybridRetriever()
        self.llamaindex_retriever = LlamaIndexRetriever()
        self.chroma_retriever = ChromaRetriever()
        self.elastic_retriever = ElasticRetriever()
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
            k, adaptive_trace = self._resolve_adaptive_k(query)
            trace.update(adaptive_trace)
            retrieved_chunks = []
            retrieval_strategy = "hybrid"
            token_count = len([token for token in query.split() if token.strip()])
            query_complexity, query_complexity_reason = self._classify_query_complexity(
                query=query,
                token_count=token_count,
            )
            trace["rag_query_complexity"] = query_complexity
            trace["rag_query_complexity_reason"] = query_complexity_reason
            force_extractive_only = bool(settings.CLINICAL_CHAT_RAG_FORCE_EXTRACTIVE_ONLY)
            configured_llm_min_remaining_budget_ms = int(
                settings.CLINICAL_CHAT_RAG_LLM_MIN_REMAINING_BUDGET_MS
            )
            retrieval_keyword_only = (
                settings.CLINICAL_CHAT_RAG_DETERMINISTIC_ROUTING_ENABLED
                and (
                    force_extractive_only
                    or configured_llm_min_remaining_budget_ms >= 2000
                )
                and query_complexity == "complex"
            )
            trace["rag_retrieval_keyword_only"] = "1" if retrieval_keyword_only else "0"
            retrieval_query, compact_trace = self._build_retrieval_query(
                query=query,
                query_complexity=query_complexity,
            )
            trace.update(compact_trace)
            if (
                settings.CLINICAL_CHAT_RAG_DETERMINISTIC_ROUTING_ENABLED
                and query_complexity == "simple"
            ):
                previous_k = k
                k = max(1, min(k, settings.CLINICAL_CHAT_RAG_SIMPLE_ROUTE_MAX_CHUNKS))
                trace["rag_deterministic_k_override"] = f"{previous_k}->{k}"
            skip_domain_search_tokens_over = int(
                settings.CLINICAL_CHAT_RAG_SKIP_DOMAIN_SEARCH_TOKENS_OVER
            )
            skip_domain_search = token_count > skip_domain_search_tokens_over
            if (
                settings.CLINICAL_CHAT_RAG_DETERMINISTIC_ROUTING_ENABLED
                and settings.CLINICAL_CHAT_RAG_COMPLEX_ROUTE_FORCE_SKIP_DOMAIN_SEARCH
                and query_complexity == "complex"
            ):
                skip_domain_search = True
                trace["rag_domain_search_skip_reason"] = "deterministic_complex_route"
            elif skip_domain_search:
                trace["rag_domain_search_skip_reason"] = "token_threshold"
            else:
                trace["rag_domain_search_skip_reason"] = "none"
            if (
                not skip_domain_search
                and self._is_generic_domain_fallback(
                    matched_domains=matched_domains,
                    effective_specialty=effective_specialty,
                )
            ):
                skip_domain_search = True
                trace["rag_domain_search_skip_reason"] = "generic_domain_fallback_bypass"
            trace["rag_domain_search_skipped"] = "1" if skip_domain_search else "0"
            trace["rag_domain_search_skip_threshold_tokens"] = str(
                skip_domain_search_tokens_over
            )

            if settings.CLINICAL_CHAT_RAG_QA_SHORTCUT_ENABLED and hasattr(self.db, "query"):
                qa_chunks, qa_trace = self._match_precomputed_qa_chunks(
                    query=retrieval_query,
                    specialty_filter=effective_specialty,
                    k=k,
                )
                trace.update(qa_trace)
                if qa_chunks:
                    retrieved_chunks = qa_chunks
                    retrieval_strategy = "qa_shortcut"
            elif settings.CLINICAL_CHAT_RAG_QA_SHORTCUT_ENABLED:
                trace["rag_qa_shortcut_enabled"] = "1"
                trace["rag_qa_shortcut_hit"] = "0"
                trace["rag_qa_shortcut_reason"] = "db_query_unavailable"

            if matched_domains and not skip_domain_search and not retrieved_chunks:
                domain_chunks, domain_trace = self.legacy_retriever.search_by_domain(
                    matched_domains,
                    self.db,
                    query=retrieval_query,
                    k=k,
                )
                trace.update(domain_trace)
                if domain_chunks:
                    filtered_domain_chunks = self._filter_chunks_for_specialty(
                        domain_chunks,
                        specialty_filter=effective_specialty,
                    )
                    if filtered_domain_chunks:
                        retrieved_chunks = filtered_domain_chunks
                    else:
                        trace["domain_search_filtered_out"] = str(len(domain_chunks))
                if retrieved_chunks:
                    retrieval_strategy = "domain"

            if not retrieved_chunks:
                segment_plan, segment_trace = self._build_multi_intent_segment_plan(
                    query=retrieval_query,
                    effective_specialty=effective_specialty,
                    matched_domains=matched_domains,
                )
                trace.update(segment_trace)
                if segment_plan:
                    segment_chunks, segment_backend_trace = self._search_multi_intent_segments(
                        segment_plan=segment_plan,
                        k=k,
                        keyword_only=retrieval_keyword_only,
                    )
                    trace.update(segment_backend_trace)
                    if segment_chunks:
                        retrieved_chunks = segment_chunks
                        retrieval_strategy = "multi_intent_hybrid"

            if not retrieved_chunks:
                if retrieval_keyword_only:
                    try:
                        chunks, backend_trace, retrieval_strategy = (
                            self._search_with_configured_backend(
                                query=retrieval_query,
                                k=k,
                                specialty_filter=effective_specialty,
                                keyword_only=True,
                            )
                        )
                    except TypeError:
                        chunks, backend_trace, retrieval_strategy = (
                            self._search_with_configured_backend(
                                query=retrieval_query,
                                k=k,
                                specialty_filter=effective_specialty,
                            )
                        )
                else:
                    chunks, backend_trace, retrieval_strategy = (
                        self._search_with_configured_backend(
                            query=retrieval_query,
                            k=k,
                            specialty_filter=effective_specialty,
                        )
                    )
                trace.update(backend_trace)
                retrieved_chunks = chunks

            retrieved_chunks, noise_trace = self._drop_noisy_chunks(retrieved_chunks)
            trace.update(noise_trace)

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

            if settings.CLINICAL_CHAT_RAG_MMR_ENABLED:
                retrieved_chunks, mmr_trace = self._apply_mmr_rerank(
                    query=retrieval_query,
                    chunks=retrieved_chunks,
                    top_k=k,
                )
                trace.update(mmr_trace)

            chunk_dicts, assembly_trace = RAGContextAssembler.assemble_rag_context(
                retrieved_chunks,
                retrieval_trace=trace,
            )
            trace.update(assembly_trace)

            if settings.CLINICAL_CHAT_RAG_COMPRESS_CONTEXT_ENABLED:
                chunk_dicts, compression_trace = RAGContextAssembler.compress_rag_context(
                    query=query,
                    chunks=chunk_dicts,
                    max_chars_per_chunk=settings.CLINICAL_CHAT_RAG_COMPRESS_MAX_CHARS,
                )
                trace.update(compression_trace)
            else:
                trace["rag_context_compressed"] = "0"

            rag_sources = self._build_rag_knowledge_sources(chunk_dicts)
            augmented_sources = self._merge_sources(knowledge_sources, rag_sources)
            pre_context_relevance = self.gatekeeper.compute_context_relevance(
                query=query,
                retrieved_chunks=chunk_dicts,
            )
            safe_wrapper_context_min = float(
                settings.CLINICAL_CHAT_RAG_SAFE_WRAPPER_MIN_CONTEXT_RATIO
            )
            trace["rag_context_relevance_pre"] = f"{pre_context_relevance:.3f}"
            trace["rag_safe_wrapper_min_context_ratio"] = f"{safe_wrapper_context_min:.3f}"
            if (
                settings.CLINICAL_CHAT_RAG_SAFE_WRAPPER_ENABLED
                and pre_context_relevance < safe_wrapper_context_min
            ):
                safe_wrapper_answer = self._build_safe_wrapper_answer(
                    query=query,
                    chunks=chunk_dicts,
                    matched_domains=matched_domains,
                    reason=(
                        "context_relevance_below_threshold"
                        f" ({pre_context_relevance:.3f}<{safe_wrapper_context_min:.3f})"
                    ),
                )
                elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
                trace.update(
                    {
                        "rag_status": "success",
                        "rag_retrieval_strategy": retrieval_strategy,
                        "rag_generation_mode": "safe_wrapper_abstain",
                        "rag_chunks_retrieved": str(len(retrieved_chunks)),
                        "rag_total_latency_ms": str(elapsed_ms),
                        "rag_validation_status": "warning",
                        "rag_validation_issues": [
                            "safe_wrapper activado por evidencia insuficiente antes de LLM"
                        ],
                        "rag_safe_wrapper_triggered": "1",
                        "rag_safe_wrapper_reason": "low_context_relevance_pre_generation",
                        "rag_sources": rag_sources,
                        "llm_enabled": "true" if settings.CLINICAL_CHAT_LLM_ENABLED else "false",
                        "llm_used": "false",
                        "llm_error": "SafeWrapperAbstain",
                    }
                )
                return safe_wrapper_answer, trace
            answer: str | None = None
            llm_trace: dict[str, Any] = {}
            rag_generation_mode = "extractive_only"
            trace["rag_force_extractive_only"] = "1" if force_extractive_only else "0"
            budget_total_ms = int(settings.CLINICAL_CHAT_RAG_MAX_TOTAL_LATENCY_MS)
            min_remaining_for_llm_ms = self._resolve_dynamic_llm_min_remaining_budget_ms(
                configured_budget_ms=configured_llm_min_remaining_budget_ms,
                query_complexity=query_complexity,
                pre_context_relevance=pre_context_relevance,
            )
            elapsed_pre_llm_ms = round((time.perf_counter() - started_at) * 1000, 2)
            remaining_pre_llm_ms = max(0.0, float(budget_total_ms) - elapsed_pre_llm_ms)
            trace.update(
                {
                    "rag_latency_budget_total_ms": str(budget_total_ms),
                    "rag_latency_budget_remaining_pre_llm_ms": str(round(remaining_pre_llm_ms, 2)),
                    "rag_llm_min_remaining_budget_config_ms": str(
                        configured_llm_min_remaining_budget_ms
                    ),
                    "rag_llm_min_remaining_budget_dynamic_ms": str(min_remaining_for_llm_ms),
                }
            )
            if force_extractive_only:
                llm_trace = {
                    "llm_enabled": "true" if settings.CLINICAL_CHAT_LLM_ENABLED else "false",
                    "llm_used": "false",
                    "llm_model": settings.CLINICAL_CHAT_LLM_MODEL,
                    "llm_error": "ForcedExtractiveMode",
                }
                trace.update(llm_trace)
                trace["rag_llm_skipped_reason"] = "force_extractive_only"
            elif settings.CLINICAL_CHAT_LLM_ENABLED:
                if remaining_pre_llm_ms < float(min_remaining_for_llm_ms):
                    llm_trace = {
                        "llm_enabled": "true",
                        "llm_used": "false",
                        "llm_model": settings.CLINICAL_CHAT_LLM_MODEL,
                        "llm_error": "BudgetExhausted",
                    }
                    trace.update(llm_trace)
                    trace["rag_llm_skipped_reason"] = "latency_budget_exhausted_pre_llm"
                else:
                    llm_timeout_override_seconds = max(
                        2.0,
                        min(
                            float(settings.CLINICAL_CHAT_LLM_TIMEOUT_SECONDS),
                            max(0.0, remaining_pre_llm_ms - 250.0) / 1000.0,
                        ),
                    )
                    trace["rag_llm_timeout_override_seconds"] = (
                        f"{llm_timeout_override_seconds:.2f}"
                    )
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
                        timeout_budget_seconds_override=llm_timeout_override_seconds,
                    )
                    trace.update(llm_trace)
                    rag_generation_mode = "llm"
            else:
                trace.update(
                    {
                        "llm_enabled": "false",
                        "llm_used": "false",
                        "llm_model": settings.CLINICAL_CHAT_LLM_MODEL,
                    }
                )

            if not answer and settings.CLINICAL_CHAT_RAG_EXTRACTIVE_FALLBACK_ENABLED:
                answer = self._build_extractive_answer(
                    query=query,
                    chunks=chunk_dicts,
                    matched_domains=matched_domains,
                )
                if force_extractive_only:
                    rag_generation_mode = "extractive_forced_mode"
                else:
                    rag_generation_mode = (
                        "extractive_fallback_llm_error"
                        if settings.CLINICAL_CHAT_LLM_ENABLED and llm_trace
                        else "extractive_no_llm"
                    )
                if (
                    settings.CLINICAL_CHAT_LLM_ENABLED
                    and llm_trace.get("llm_error")
                    and not force_extractive_only
                ):
                    trace["rag_generation_fallback_reason"] = str(llm_trace.get("llm_error"))

            if not answer:
                elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
                trace.update(
                    {
                        "rag_status": "failed_generation",
                        "rag_fallback_reason": llm_trace.get("llm_error", "llm_empty"),
                        "rag_retrieval_strategy": retrieval_strategy,
                        "rag_chunks_retrieved": str(len(retrieved_chunks)),
                        "rag_sources": rag_sources,
                        "rag_total_latency_ms": str(elapsed_ms),
                    }
                )
                return None, trace

            is_valid = True
            issues: list[str] = []
            post_context_relevance = self.gatekeeper.compute_context_relevance(
                query=query,
                retrieved_chunks=chunk_dicts,
            )
            post_faithfulness = self.gatekeeper.compute_faithfulness(
                response=answer,
                retrieved_chunks=chunk_dicts,
            )
            if settings.CLINICAL_CHAT_RAG_ENABLE_GATEKEEPER:
                is_valid, issues = self.gatekeeper.validate_response(
                    query=query,
                    response=answer,
                    retrieved_chunks=chunk_dicts,
                )
            trace["rag_context_relevance_post"] = f"{post_context_relevance:.3f}"
            trace["rag_faithfulness_post"] = f"{post_faithfulness:.3f}"

            safe_wrapper_triggered_post = (
                settings.CLINICAL_CHAT_RAG_SAFE_WRAPPER_ENABLED
                and settings.CLINICAL_CHAT_RAG_EXTRACTIVE_FALLBACK_ENABLED
                and rag_generation_mode == "llm"
                and (
                    post_context_relevance
                    < float(settings.CLINICAL_CHAT_RAG_SAFE_WRAPPER_MIN_CONTEXT_RATIO)
                    or post_faithfulness < float(settings.CLINICAL_CHAT_RAG_FAITHFULNESS_MIN_RATIO)
                )
            )
            if safe_wrapper_triggered_post:
                safe_wrapper_answer = self._build_safe_wrapper_answer(
                    query=query,
                    chunks=chunk_dicts,
                    matched_domains=matched_domains,
                    reason=(
                        "post_validation_context="
                        f"{post_context_relevance:.3f},faithfulness={post_faithfulness:.3f}"
                    ),
                )
                if safe_wrapper_answer:
                    answer = safe_wrapper_answer
                    rag_generation_mode = "safe_wrapper_post_validation"
                    trace["rag_safe_wrapper_triggered"] = "1"
                    trace["rag_safe_wrapper_reason"] = "post_validation_low_alignment"
                    issues.append("ADVERTENCIA: safe_wrapper activado tras validacion")
                    is_valid = False

            elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
            trace.update(
                {
                    "rag_status": "success",
                    "rag_retrieval_strategy": retrieval_strategy,
                    "rag_generation_mode": rag_generation_mode,
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

    @staticmethod
    def _resolve_adaptive_k(query: str) -> tuple[int, dict[str, str]]:
        base_k = settings.CLINICAL_CHAT_RAG_MAX_CHUNKS
        min_k = settings.CLINICAL_CHAT_RAG_MIN_CHUNKS
        max_k = settings.CLINICAL_CHAT_RAG_MAX_CHUNKS_HARD
        if not settings.CLINICAL_CHAT_RAG_ADAPTIVE_K_ENABLED:
            k = max(min_k, min(base_k, max_k))
            return k, {
                "rag_adaptive_k_enabled": "0",
                "rag_adaptive_k_value": str(k),
                "rag_adaptive_k_reason": "disabled",
            }

        token_count = len([token for token in query.split() if token.strip()])
        k = base_k
        reason = "base"
        if token_count <= 5:
            k = max(min_k, base_k - 1)
            reason = "short_query"
        elif token_count >= 18:
            k = min(max_k, base_k + 1)
            reason = "long_query"

        high_risk_markers = (
            "shock",
            "hiperkalemia",
            "qrs",
            "anuria",
            "oliguria",
            "neutropenia",
            "preeclampsia",
            "sepsis",
        )
        query_lower = query.lower()
        if any(marker in query_lower for marker in high_risk_markers):
            if k < base_k:
                k = min(max_k, base_k)
                reason = f"{reason}+high_risk_raise_to_base"
            else:
                reason = f"{reason}+high_risk"

        # Mantiene estabilidad de latencia: evita saltos grandes de fan-out por consulta.
        soft_cap = min(max_k, base_k + 1)
        k = min(k, soft_cap)
        k = max(min_k, min(k, max_k))
        return k, {
            "rag_adaptive_k_enabled": "1",
            "rag_adaptive_k_value": str(k),
            "rag_adaptive_k_reason": reason,
            "rag_adaptive_k_tokens": str(token_count),
        }

    @staticmethod
    def _classify_query_complexity(*, query: str, token_count: int) -> tuple[str, str]:
        normalized = query.lower()
        separators = sum(normalized.count(char) for char in (":", ";", "(", ")", ","))
        connectors = sum(
            normalized.count(fragment) for fragment in (" y ", " con ", " sin ", " o ")
        )
        procedural_markers = (
            "pasos",
            "criterios",
            "bundle",
            "ruta",
            "algoritmo",
            "priorizar",
        )
        marker_hits = sum(1 for marker in procedural_markers if marker in normalized)
        complex_signals = 0
        reasons: list[str] = []
        if token_count >= int(settings.CLINICAL_CHAT_RAG_DETERMINISTIC_COMPLEX_MIN_TOKENS):
            complex_signals += 1
            reasons.append("tokens")
        if separators >= 2:
            complex_signals += 1
            reasons.append("separators")
        if connectors >= 2:
            complex_signals += 1
            reasons.append("connectors")
        if marker_hits >= 1:
            complex_signals += 1
            reasons.append("procedural_markers")

        if complex_signals >= 2:
            return "complex", "+".join(reasons) if reasons else "signals"
        if token_count <= 6 and separators == 0 and connectors <= 1:
            return "simple", "short_compact"
        return "medium", "default"

    @staticmethod
    def _build_retrieval_query(
        *,
        query: str,
        query_complexity: str,
    ) -> tuple[str, dict[str, str]]:
        trace: dict[str, str] = {
            "rag_retrieval_query_compacted": "0",
            "rag_retrieval_query_compact_reason": "not_required",
        }
        if not settings.CLINICAL_CHAT_RAG_DETERMINISTIC_ROUTING_ENABLED:
            return query, trace
        if query_complexity != "complex":
            return query, trace

        stopwords = {
            "con",
            "sin",
            "para",
            "por",
            "del",
            "las",
            "los",
            "que",
            "como",
            "and",
            "the",
            "with",
            "from",
            "hasta",
            "entre",
            "sobre",
        }
        tokens = re.findall(r"[a-zA-Z0-9\-/\+]+", str(query or "").lower())
        prioritized = [
            token
            for token in tokens
            if len(token) >= 4
            and token not in stopwords
            and token not in {"pasos", "criterios", "acciones", "inicial", "iniciales"}
        ]
        selected: list[str] = []
        for token in prioritized:
            if token in selected:
                continue
            selected.append(token)
            if len(selected) >= 8:
                break
        if len(selected) < 4:
            return query, trace
        compact_query = " ".join(selected)
        trace["rag_retrieval_query_compacted"] = "1"
        trace["rag_retrieval_query_compact_reason"] = "complex_query_fast_path"
        trace["rag_retrieval_query_terms"] = ",".join(selected)
        return compact_query, trace

    @staticmethod
    def _resolve_dynamic_llm_min_remaining_budget_ms(
        *,
        configured_budget_ms: int,
        query_complexity: str,
        pre_context_relevance: float,
    ) -> int:
        dynamic_budget = max(200, int(configured_budget_ms))
        if query_complexity == "simple":
            dynamic_budget = min(dynamic_budget, 900)
        elif query_complexity == "medium":
            dynamic_budget = min(dynamic_budget, 1400)

        if pre_context_relevance < 0.16:
            dynamic_budget = max(dynamic_budget, 1800)
        elif pre_context_relevance < 0.22:
            dynamic_budget = max(dynamic_budget, 1500)
        return dynamic_budget

    def _apply_mmr_rerank(
        self,
        *,
        query: str,
        chunks: list[Any],
        top_k: int,
    ) -> tuple[list[Any], dict[str, str]]:
        if len(chunks) <= 1:
            return chunks, {
                "rag_mmr_enabled": "1",
                "rag_mmr_selected": str(len(chunks)),
                "rag_mmr_reason": "single_chunk",
                "rag_mmr_lambda": f"{settings.CLINICAL_CHAT_RAG_MMR_LAMBDA:.2f}",
            }

        query_vec, embedding_trace = self.legacy_retriever.embedding_service.embed_text(query)
        candidate_vectors: dict[int, list[float]] = {}
        for chunk in chunks:
            vector = self._extract_chunk_vector(chunk)
            if vector:
                candidate_vectors[int(getattr(chunk, "id"))] = vector

        if not query_vec or not candidate_vectors:
            trace = {
                "rag_mmr_enabled": "1",
                "rag_mmr_selected": str(min(top_k, len(chunks))),
                "rag_mmr_reason": "missing_vectors",
                "rag_mmr_lambda": f"{settings.CLINICAL_CHAT_RAG_MMR_LAMBDA:.2f}",
            }
            for key, value in embedding_trace.items():
                trace[f"rag_mmr_{key}"] = str(value)
            return chunks[:top_k], trace

        lambda_value = settings.CLINICAL_CHAT_RAG_MMR_LAMBDA
        original_scores = [float(getattr(chunk, "_rag_score", 0.0) or 0.0) for chunk in chunks]
        min_score = min(original_scores) if original_scores else 0.0
        max_score = max(original_scores) if original_scores else 0.0
        score_span = max(1e-6, max_score - min_score)

        relevance: dict[int, float] = {}
        for chunk in chunks:
            chunk_id = int(getattr(chunk, "id"))
            vector = candidate_vectors.get(chunk_id)
            if not vector:
                relevance[chunk_id] = 0.0
                continue
            semantic = self._cosine_similarity(query_vec, vector)
            lexical = (float(getattr(chunk, "_rag_score", 0.0) or 0.0) - min_score) / score_span
            relevance[chunk_id] = (0.7 * semantic) + (0.3 * lexical)

        selected: list[Any] = []
        selected_ids: set[int] = set()
        limit = min(top_k, len(chunks))

        while len(selected) < limit:
            best_chunk = None
            best_mmr = None
            for candidate in chunks:
                candidate_id = int(getattr(candidate, "id"))
                if candidate_id in selected_ids:
                    continue
                candidate_vector = candidate_vectors.get(candidate_id)
                diversity_penalty = 0.0
                if candidate_vector and selected:
                    diversity_penalty = max(
                        self._cosine_similarity(
                            candidate_vector,
                            candidate_vectors.get(int(getattr(chosen, "id")), []),
                        )
                        for chosen in selected
                    )
                mmr_score = (lambda_value * relevance.get(candidate_id, 0.0)) - (
                    (1 - lambda_value) * diversity_penalty
                )
                if best_mmr is None or mmr_score > best_mmr:
                    best_mmr = mmr_score
                    best_chunk = candidate

            if best_chunk is None:
                break
            selected.append(best_chunk)
            selected_ids.add(int(getattr(best_chunk, "id")))

        trace = {
            "rag_mmr_enabled": "1",
            "rag_mmr_lambda": f"{lambda_value:.2f}",
            "rag_mmr_selected": str(len(selected)),
            "rag_mmr_candidates": str(len(chunks)),
        }
        for key, value in embedding_trace.items():
            trace[f"rag_mmr_{key}"] = str(value)
        return selected or chunks[:top_k], trace

    @staticmethod
    def _extract_chunk_vector(chunk: Any) -> list[float]:
        raw = getattr(chunk, "chunk_embedding", None)
        if not raw:
            return []
        try:
            values = array("f")
            values.frombytes(raw)
            return [float(value) for value in values]
        except (TypeError, ValueError):
            return []

    @staticmethod
    def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
        if not vec_a or not vec_b:
            return 0.0
        dot = 0.0
        norm_a = 0.0
        norm_b = 0.0
        for a, b in zip(vec_a, vec_b, strict=False):
            dot += a * b
            norm_a += a * a
            norm_b += b * b
        if norm_a <= 0 or norm_b <= 0:
            return 0.0
        return float(dot / ((norm_a ** 0.5) * (norm_b ** 0.5)))

    @staticmethod
    def _filter_chunks_for_specialty(
        chunks: list[Any],
        *,
        specialty_filter: str,
    ) -> list[Any]:
        normalized_filter = str(specialty_filter or "").strip().lower()
        if not normalized_filter or normalized_filter == "general":
            return chunks
        filtered: list[Any] = []
        for chunk in chunks:
            chunk_specialty = str(getattr(chunk, "specialty", "") or "").strip().lower()
            if chunk_specialty == normalized_filter:
                filtered.append(chunk)
        return filtered

    @staticmethod
    def _is_generic_domain_fallback(
        *,
        matched_domains: list[str],
        effective_specialty: str,
    ) -> bool:
        normalized_domains = [str(item).strip().lower() for item in (matched_domains or []) if item]
        normalized_specialty = str(effective_specialty or "").strip().lower()
        return (
            len(normalized_domains) == 1
            and normalized_domains[0] == "critical_ops"
            and normalized_specialty in {"", "general", "*"}
        )

    @classmethod
    def _drop_noisy_chunks(cls, chunks: list[Any]) -> tuple[list[Any], dict[str, str]]:
        if not chunks:
            return [], {"rag_chunks_noise_filtered": "0"}
        filtered: list[Any] = []
        removed = 0
        for chunk in chunks:
            text = str(getattr(chunk, "chunk_text", "") or "")
            lines = [line for line in text.splitlines() if line.strip()]
            candidate_lines = lines[:8] if lines else [text]
            if candidate_lines and all(
                cls._looks_like_non_clinical_noise(line) for line in candidate_lines
            ):
                removed += 1
                continue
            source_file = ""
            chunk_document = getattr(chunk, "document", None)
            if chunk_document is not None:
                source_file = str(getattr(chunk_document, "source_file", "") or "")
            normalized_source = source_file.replace("\\", "/").lower()
            if normalized_source and "docs/decisions/" in normalized_source:
                removed += 1
                continue
            filtered.append(chunk)
        if not filtered:
            return chunks, {
                "rag_chunks_noise_filtered": str(removed),
                "rag_chunks_noise_filter_fallback": "1",
            }
        return filtered, {
            "rag_chunks_noise_filtered": str(removed),
            "rag_chunks_noise_filter_fallback": "0",
        }

    def _search_with_configured_backend(
        self,
        *,
        query: str,
        k: int,
        specialty_filter: str,
        keyword_only: bool = False,
    ) -> tuple[list[Any], dict[str, str], str]:
        configured_backend = (
            settings.CLINICAL_CHAT_RAG_RETRIEVER_BACKEND.strip().lower() or "legacy"
        )
        backend, router_reason = self._select_retriever_backend(
            query=query,
            specialty_filter=specialty_filter,
            configured_backend=configured_backend,
        )
        can_relax_specialty = self._should_relax_specialty_filter(specialty_filter)
        normalized_specialty = str(specialty_filter or "").strip().lower()
        router_trace = {
            "rag_router_configured_backend": configured_backend,
            "rag_router_selected_backend": backend,
            "rag_router_reason": router_reason,
            "rag_router_candidate_backends": "elastic,chroma,llamaindex,legacy",
            "rag_retriever_specialty_relaxation_allowed": "1" if can_relax_specialty else "0",
        }

        def _call_legacy_hybrid(
            *,
            search_query: str,
            specialty: str | None,
        ) -> tuple[list[Any], dict[str, str]]:
            if keyword_only:
                try:
                    return self.legacy_retriever.search_hybrid(
                        search_query,
                        self.db,
                        k=k,
                        specialty_filter=specialty,
                        keyword_only=True,
                    )
                except TypeError:
                    # Compatibilidad con stubs/tests que no aceptan keyword_only.
                    return self.legacy_retriever.search_hybrid(
                        search_query,
                        self.db,
                        k=k,
                        specialty_filter=specialty,
                    )
            return self.legacy_retriever.search_hybrid(
                search_query,
                self.db,
                k=k,
                specialty_filter=specialty,
            )

        def _retry_without_specialty(
            *,
            trace: dict[str, str],
            reason: str,
        ) -> tuple[list[Any], dict[str, str], str]:
            if not can_relax_specialty:
                trace["rag_retriever_specialty_relaxation"] = "0"
                return [], trace, "hybrid_empty"
            relaxed_chunks, relaxed_trace = _call_legacy_hybrid(
                search_query=query,
                specialty=None,
            )
            trace["rag_retriever_specialty_relaxation"] = "1"
            trace["rag_retriever_specialty_relaxation_reason"] = reason
            trace["rag_retriever_specialty_original"] = normalized_specialty
            for key, value in relaxed_trace.items():
                trace[f"relaxed_{key}"] = value
            strategy = "hybrid_specialty_relaxation" if relaxed_chunks else "hybrid_empty"
            return relaxed_chunks, trace, strategy

        if backend == "llamaindex":
            llama_chunks, llama_trace = self.llamaindex_retriever.search(
                query,
                self.db,
                k=k,
                specialty_filter=specialty_filter,
            )
            trace = {"rag_retriever_backend": "llamaindex", **router_trace}
            trace.update(llama_trace)
            if llama_chunks:
                trace["rag_retriever_specialty_relaxation"] = "0"
                return llama_chunks, trace, "llamaindex"

            legacy_chunks, legacy_trace = _call_legacy_hybrid(
                search_query=query,
                specialty=specialty_filter,
            )
            trace["rag_retriever_fallback"] = "legacy_hybrid"
            for key, value in legacy_trace.items():
                trace[f"legacy_{key}"] = value
            if legacy_chunks:
                trace["rag_retriever_specialty_relaxation"] = "0"
                return legacy_chunks, trace, "hybrid_fallback"
            return _retry_without_specialty(
                trace=trace,
                reason="llamaindex_and_legacy_empty_with_specialty",
            )

        if backend == "chroma":
            chroma_chunks, chroma_trace = self.chroma_retriever.search(
                query,
                self.db,
                k=k,
                specialty_filter=specialty_filter,
            )
            trace = {"rag_retriever_backend": "chroma", **router_trace}
            trace.update(chroma_trace)
            if chroma_chunks:
                trace["rag_retriever_specialty_relaxation"] = "0"
                return chroma_chunks, trace, "chroma"

            legacy_chunks, legacy_trace = _call_legacy_hybrid(
                search_query=query,
                specialty=specialty_filter,
            )
            trace["rag_retriever_fallback"] = "legacy_hybrid"
            for key, value in legacy_trace.items():
                trace[f"legacy_{key}"] = value
            if legacy_chunks:
                trace["rag_retriever_specialty_relaxation"] = "0"
                return legacy_chunks, trace, "hybrid_fallback"
            return _retry_without_specialty(
                trace=trace,
                reason="chroma_and_legacy_empty_with_specialty",
            )

        if backend == "elastic":
            elastic_chunks, elastic_trace = self.elastic_retriever.search(
                query,
                self.db,
                k=k,
                specialty_filter=specialty_filter,
            )
            trace = {"rag_retriever_backend": "elastic", **router_trace}
            trace.update(elastic_trace)
            if elastic_chunks:
                trace["rag_retriever_specialty_relaxation"] = "0"
                return elastic_chunks, trace, "elastic"

            legacy_chunks, legacy_trace = _call_legacy_hybrid(
                search_query=query,
                specialty=specialty_filter,
            )
            trace["rag_retriever_fallback"] = "legacy_hybrid"
            for key, value in legacy_trace.items():
                trace[f"legacy_{key}"] = value
            if legacy_chunks:
                trace["rag_retriever_specialty_relaxation"] = "0"
                return legacy_chunks, trace, "hybrid_fallback"
            return _retry_without_specialty(
                trace=trace,
                reason="elastic_and_legacy_empty_with_specialty",
            )

        legacy_chunks, legacy_trace = _call_legacy_hybrid(
            search_query=query,
            specialty=specialty_filter,
        )
        trace = {"rag_retriever_backend": "legacy", **router_trace}
        trace.update(legacy_trace)
        if legacy_chunks:
            trace["rag_retriever_specialty_relaxation"] = "0"
            return legacy_chunks, trace, "hybrid"
        return _retry_without_specialty(
            trace=trace,
            reason="legacy_empty_with_specialty",
        )

    @classmethod
    def _normalize_segment_text(cls, text: str) -> str:
        compact = re.sub(r"\s+", " ", str(text or "")).strip()
        compact = compact.strip(" ,.;:-")
        return compact

    @classmethod
    def _detect_domain_markers(cls, text: str) -> set[str]:
        normalized = str(text or "").lower()
        hits: set[str] = set()
        for item in cls._MULTI_INTENT_DOMAIN_CATALOG:
            key = str(item.get("key") or "").strip()
            if not key:
                continue
            for keyword in item.get("keywords", []) or []:
                marker = str(keyword or "").strip().lower()
                if marker and marker in normalized:
                    hits.add(key)
                    break
        return hits

    @classmethod
    def _segment_multi_intent_query(cls, query: str) -> list[str]:
        normalized_query = cls._normalize_segment_text(query)
        if not normalized_query:
            return []

        max_segments = int(settings.CLINICAL_CHAT_RAG_MULTI_INTENT_MAX_SEGMENTS)
        min_chars = int(settings.CLINICAL_CHAT_RAG_MULTI_INTENT_MIN_SEGMENT_CHARS)
        initial = [
            cls._normalize_segment_text(item)
            for item in cls._SEGMENT_SPLIT_PATTERN.split(normalized_query)
        ]
        initial = [item for item in initial if len(item) >= min_chars]
        if len(initial) > 1:
            return initial[:max_segments]

        marker_domains = cls._detect_domain_markers(normalized_query)
        if len(marker_domains) < 2:
            return [normalized_query]

        soft_segments = [
            cls._normalize_segment_text(item)
            for item in cls._SOFT_CONNECTOR_PATTERN.split(normalized_query)
        ]
        soft_segments = [item for item in soft_segments if len(item) >= min_chars]
        if len(soft_segments) <= 1:
            return [normalized_query]
        return soft_segments[:max_segments]

    @classmethod
    def _build_multi_intent_segment_plan(
        cls,
        *,
        query: str,
        effective_specialty: str,
        matched_domains: list[str],
    ) -> tuple[list[dict[str, Any]], dict[str, str]]:
        trace: dict[str, str] = {
            "rag_multi_intent_enabled": (
                "1" if settings.CLINICAL_CHAT_RAG_MULTI_INTENT_ENABLED else "0"
            )
        }
        if not settings.CLINICAL_CHAT_RAG_MULTI_INTENT_ENABLED:
            trace["rag_multi_intent_plan_size"] = "0"
            return [], trace

        segments = cls._segment_multi_intent_query(query)
        trace["rag_multi_intent_segments_detected"] = str(len(segments))
        if len(segments) <= 1:
            trace["rag_multi_intent_plan_size"] = "0"
            return [], trace

        min_probability = float(settings.CLINICAL_CHAT_RAG_MULTI_INTENT_MIN_DOMAIN_PROBABILITY)
        plan: list[dict[str, Any]] = []
        for segment in segments:
            svm_assessment = ClinicalSVMDomainService.analyze_query(
                query=segment,
                domain_catalog=cls._MULTI_INTENT_DOMAIN_CATALOG,
                matched_domains=matched_domains,
                effective_specialty=effective_specialty,
            )
            top_domain = str(svm_assessment.get("top_domain") or "").strip().lower()
            top_probability = float(svm_assessment.get("top_probability") or 0.0)
            specialty_filter = str(effective_specialty or "").strip().lower()
            if top_domain and top_probability >= min_probability:
                specialty_filter = top_domain
            plan.append(
                {
                    "segment": segment,
                    "top_domain": top_domain or "none",
                    "top_probability": top_probability,
                    "specialty_filter": specialty_filter or effective_specialty,
                }
            )

        domain_votes = {
            item["specialty_filter"]
            for item in plan
            if str(item.get("specialty_filter") or "").strip().lower() not in {"", "general", "*"}
        }
        if len(plan) <= 1 or len(domain_votes) <= 1:
            trace["rag_multi_intent_plan_size"] = "0"
            trace["rag_multi_intent_domain_votes"] = str(len(domain_votes))
            return [], trace

        trace["rag_multi_intent_plan_size"] = str(len(plan))
        trace["rag_multi_intent_domain_votes"] = str(len(domain_votes))
        trace["rag_multi_intent_domains"] = ",".join(
            sorted(
                {
                    str(item.get("top_domain") or "none")
                    for item in plan
                    if str(item.get("top_domain") or "none") != "none"
                }
            )[:6]
        ) or "none"
        return plan, trace

    def _search_multi_intent_segments(
        self,
        *,
        segment_plan: list[dict[str, Any]],
        k: int,
        keyword_only: bool,
    ) -> tuple[list[Any], dict[str, str]]:
        trace: dict[str, str] = {"rag_multi_intent_search_used": "1"}
        if not segment_plan:
            trace["rag_multi_intent_chunks"] = "0"
            return [], trace

        per_segment_k = max(1, min(k, 2))
        collected_chunks: list[Any] = []
        segment_strategies: list[str] = []
        for index, segment_item in enumerate(segment_plan, start=1):
            query = str(segment_item.get("segment") or "").strip()
            if not query:
                continue
            specialty_filter = str(segment_item.get("specialty_filter") or "").strip()
            top_probability = float(segment_item.get("top_probability") or 0.0)
            try:
                chunks, backend_trace, strategy = self._search_with_configured_backend(
                    query=query,
                    k=per_segment_k,
                    specialty_filter=specialty_filter,
                    keyword_only=keyword_only,
                )
            except TypeError:
                chunks, backend_trace, strategy = self._search_with_configured_backend(
                    query=query,
                    k=per_segment_k,
                    specialty_filter=specialty_filter,
                )
            segment_strategies.append(strategy)
            trace[f"rag_multi_intent_segment_{index}_strategy"] = strategy
            trace[f"rag_multi_intent_segment_{index}_specialty"] = specialty_filter or "general"
            trace[f"rag_multi_intent_segment_{index}_hits"] = str(len(chunks))
            for key, value in backend_trace.items():
                if key in {"rag_sources"}:
                    continue
                trace[f"rag_multi_intent_segment_{index}_{key}"] = str(value)
            boost = min(0.08, top_probability * 0.10)
            for chunk in chunks:
                base_score = float(getattr(chunk, "_rag_score", 0.0) or 0.0)
                setattr(chunk, "_rag_score", base_score + boost)
                collected_chunks.append(chunk)

        if not collected_chunks:
            trace["rag_multi_intent_chunks"] = "0"
            return [], trace

        deduped_by_id: dict[str, Any] = {}
        for chunk in collected_chunks:
            chunk_id = str(getattr(chunk, "id", "") or "")
            if not chunk_id:
                chunk_id = str(id(chunk))
            existing = deduped_by_id.get(chunk_id)
            if existing is None:
                deduped_by_id[chunk_id] = chunk
                continue
            existing_score = float(getattr(existing, "_rag_score", 0.0) or 0.0)
            new_score = float(getattr(chunk, "_rag_score", 0.0) or 0.0)
            if new_score > existing_score:
                deduped_by_id[chunk_id] = chunk

        ranked_chunks = sorted(
            deduped_by_id.values(),
            key=lambda item: float(getattr(item, "_rag_score", 0.0) or 0.0),
            reverse=True,
        )
        max_return = max(1, min(int(settings.CLINICAL_CHAT_RAG_MAX_CHUNKS_HARD), max(k, 4)))
        selected = ranked_chunks[:max_return]
        trace["rag_multi_intent_chunks"] = str(len(selected))
        trace["rag_multi_intent_strategies"] = ",".join(segment_strategies[:6]) or "none"
        return selected, trace

    @staticmethod
    def _tokenize_qa_text(value: str) -> list[str]:
        return re.findall(r"[a-z0-9#\-\+/]+", str(value or "").lower())

    def _match_precomputed_qa_chunks(
        self,
        *,
        query: str,
        specialty_filter: str,
        k: int,
    ) -> tuple[list[Any], dict[str, str]]:
        trace: dict[str, str] = {"rag_qa_shortcut_enabled": "1"}
        stopwords = {
            "de",
            "la",
            "el",
            "los",
            "las",
            "con",
            "sin",
            "para",
            "por",
            "del",
            "que",
            "como",
            "en",
            "y",
            "o",
        }
        raw_tokens = self._tokenize_qa_text(query)
        query_tokens = [
            token
            for token in raw_tokens
            if len(token) >= 3 and token not in stopwords
        ]
        query_terms = list(dict.fromkeys(query_tokens))[:16]
        query_set = set(query_terms)
        trace["rag_qa_shortcut_query_terms"] = (
            ",".join(query_terms[:10]) if query_terms else "none"
        )

        if len(query_set) < 2:
            trace["rag_qa_shortcut_hit"] = "0"
            trace["rag_qa_shortcut_reason"] = "insufficient_query_terms"
            return [], trace

        normalized_specialty = str(specialty_filter or "").strip().lower()
        has_specific_specialty = normalized_specialty not in {"", "general", "*"}
        max_candidates = int(settings.CLINICAL_CHAT_RAG_QA_SHORTCUT_MAX_CANDIDATES)
        min_score = float(settings.CLINICAL_CHAT_RAG_QA_SHORTCUT_MIN_SCORE)
        top_k = max(1, min(int(settings.CLINICAL_CHAT_RAG_QA_SHORTCUT_TOP_K), max(1, k)))
        trace["rag_qa_shortcut_min_score"] = f"{min_score:.2f}"
        trace["rag_qa_shortcut_top_k"] = str(top_k)
        trace["rag_qa_shortcut_max_candidates"] = str(max_candidates)

        query_builder = self.db.query(DocumentChunk).filter(
            DocumentChunk.custom_questions.isnot(None),
        )
        if has_specific_specialty:
            query_builder = query_builder.filter(
                func.lower(DocumentChunk.specialty) == normalized_specialty
            )

        question_blob = func.lower(cast(DocumentChunk.custom_questions, Text))
        keyword_blob = func.lower(cast(DocumentChunk.keywords, Text))
        section_blob = func.lower(func.coalesce(DocumentChunk.section_path, ""))
        filters = []
        for term in query_terms[:10]:
            like_term = f"%{term}%"
            filters.append(question_blob.ilike(like_term))
            filters.append(keyword_blob.ilike(like_term))
            filters.append(section_blob.ilike(like_term))
        if filters:
            query_builder = query_builder.filter(or_(*filters))

        candidates = query_builder.limit(max_candidates).all()
        if not candidates and has_specific_specialty:
            retry_builder = self.db.query(DocumentChunk).filter(
                DocumentChunk.custom_questions.isnot(None),
            )
            if filters:
                retry_builder = retry_builder.filter(or_(*filters))
            candidates = retry_builder.limit(max_candidates).all()
            trace["rag_qa_shortcut_specialty_relaxation"] = "1"
        else:
            trace["rag_qa_shortcut_specialty_relaxation"] = "0"

        candidates, noise_trace = self._drop_noisy_chunks(candidates)
        trace["rag_qa_shortcut_candidates"] = str(len(candidates))
        trace["rag_qa_shortcut_noise_filtered"] = str(
            int(noise_trace.get("rag_chunks_noise_filtered", "0"))
        )
        if not candidates:
            trace["rag_qa_shortcut_hit"] = "0"
            trace["rag_qa_shortcut_reason"] = "no_candidates"
            return [], trace

        ranked: list[tuple[Any, float]] = []
        best_global_score = 0.0
        for chunk in candidates:
            question_bank = [
                str(question).strip()
                for question in (getattr(chunk, "custom_questions", None) or [])
                if str(question).strip()
            ]
            section_hint = str(getattr(chunk, "section_path", "") or "").strip()
            if section_hint:
                question_bank.append(section_hint)
            keyword_hint_items = [
                str(item).strip()
                for item in (getattr(chunk, "keywords", None) or [])
                if str(item).strip()
            ]
            if keyword_hint_items:
                question_bank.append(" ".join(keyword_hint_items[:10]))
            chunk_text_tokens = self._tokenize_qa_text(str(getattr(chunk, "chunk_text", "") or ""))
            if chunk_text_tokens:
                question_bank.append(" ".join(chunk_text_tokens[:32]))
            question_bank = list(dict.fromkeys(question_bank))
            if not question_bank:
                continue
            section_tokens = set(
                token
                for token in self._tokenize_qa_text(str(getattr(chunk, "section_path", "") or ""))
                if len(token) >= 3 and token not in stopwords
            )
            best_score = 0.0
            for question in question_bank[:8]:
                question_tokens = [
                    token
                    for token in self._tokenize_qa_text(question)
                    if len(token) >= 3 and token not in stopwords
                ]
                if not question_tokens:
                    continue
                question_set = set(question_tokens)
                overlap = len(query_set.intersection(question_set))
                if overlap < 2:
                    continue
                precision = overlap / max(1, len(question_set))
                recall = overlap / max(1, len(query_set))
                contains_bonus = 0.0
                normalized_question = " ".join(question_tokens)
                normalized_query = " ".join(query_terms)
                if normalized_query and normalized_query in normalized_question:
                    contains_bonus += 0.10
                elif normalized_question and normalized_question in normalized_query:
                    contains_bonus += 0.06
                section_overlap = len(query_set.intersection(section_tokens))
                section_bonus = min(0.08, 0.02 * section_overlap)
                specialty_bonus = (
                    0.03
                    if (
                        has_specific_specialty
                        and str(getattr(chunk, "specialty", "") or "").strip().lower()
                        == normalized_specialty
                    )
                    else 0.0
                )
                score = (
                    (0.75 * recall)
                    + (0.15 * precision)
                    + contains_bonus
                    + section_bonus
                    + specialty_bonus
                )
                if score > best_score:
                    best_score = score
                if score > best_global_score:
                    best_global_score = score
            if best_score >= min_score:
                setattr(chunk, "_rag_score", float(best_score))
                ranked.append((chunk, float(best_score)))

        if not ranked:
            trace["rag_qa_shortcut_hit"] = "0"
            trace["rag_qa_shortcut_reason"] = "below_threshold"
            trace["rag_qa_shortcut_top_score"] = f"{best_global_score:.3f}"
            return [], trace

        ranked.sort(key=lambda item: item[1], reverse=True)
        selected_chunks = [chunk for chunk, _score in ranked[:top_k]]
        trace["rag_qa_shortcut_hit"] = "1"
        trace["rag_qa_shortcut_hits"] = str(len(selected_chunks))
        trace["rag_qa_shortcut_top_score"] = f"{ranked[0][1]:.3f}"
        return selected_chunks, trace

    @staticmethod
    def _should_relax_specialty_filter(specialty_filter: str) -> bool:
        normalized_specialty = str(specialty_filter or "").strip().lower()
        return normalized_specialty not in {"", "general", "*"}

    @staticmethod
    def _select_retriever_backend(
        *,
        query: str,
        specialty_filter: str,
        configured_backend: str,
    ) -> tuple[str, str]:
        """
        Selector ligero de backend para balancear latencia y relevancia.
        """
        backend = (
            configured_backend
            if configured_backend in {"legacy", "llamaindex", "chroma", "elastic"}
            else "legacy"
        )
        tokens = len([token for token in query.split() if token.strip()])
        normalized_specialty = (specialty_filter or "").strip().lower()

        if backend == "legacy":
            return "legacy", "configured_legacy"

        if tokens <= 4:
            return "legacy", "short_query_keyword_priority"

        if normalized_specialty and normalized_specialty != "general":
            return backend, "specialty_semantic_priority"

        if tokens <= 7 and backend != "legacy":
            return "legacy", "medium_short_query_latency_priority"

        return backend, "configured_default"

    @staticmethod
    def _looks_like_non_clinical_noise(line: str) -> bool:
        normalized = line.lower().strip()
        if not normalized:
            return True
        blocked_markers = (
            ".py",
            "python.exe",
            "pytest",
            "uvicorn",
            "curl ",
            "/api/v1/",
            "http://",
            "https://",
            "select ",
            "insert ",
            "git ",
            "npm ",
            "pip ",
            "endpoint",
            "workflow",
            "agent_run",
            "tool_mode",
            "py_compile",
            "venv\\",
            "venv/",
            "app/",
            "app\\",
            "{",
            "}",
            "`",
            "motor operativo",
            "sistema no tenia",
            "sistema no tenía",
            "logica operativa cubierta",
            "lógica operativa cubierta",
            "validacion -",
            "validación -",
            "documento >",
        )
        if any(marker in normalized for marker in blocked_markers):
            return True
        alpha_chars = sum(1 for char in normalized if char.isalpha())
        return alpha_chars < 18

    @staticmethod
    def _tokenize_for_relevance(text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9]{3,}", str(text or "").lower())
            if token not in {"para", "con", "sin", "por", "del", "las", "los", "una", "uno"}
        }

    @classmethod
    def _tokenize_for_actions(cls, text: str) -> list[str]:
        return re.findall(r"[a-z0-9]{2,}", str(text or "").lower())

    @classmethod
    def _clinical_actionability_score(
        cls,
        *,
        text: str,
        overlap_score: float,
        retrieval_score: float,
        evidence_score: float,
    ) -> tuple[float, float]:
        tokens = cls._tokenize_for_actions(text)
        if not tokens:
            return 0.0, 1.0
        filtered = [token for token in tokens if token not in cls._ACTION_STOPWORDS]
        if not filtered:
            return 0.0, 1.0

        aux_hits = sum(1 for token in filtered if token in cls._AUXILIARY_TOKENS)
        action_hits = sum(1 for token in filtered if token in cls._ACTION_TOKENS)
        aux_ratio = float(aux_hits) / float(max(1, len(filtered)))
        action_density = min(1.0, float(action_hits) / 3.0)
        lexical_density = min(1.0, float(len(set(filtered))) / float(len(filtered)))

        score = (
            (0.35 * float(overlap_score))
            + (0.25 * float(evidence_score))
            + (0.20 * float(retrieval_score))
            + (0.12 * float(action_density))
            + (0.08 * float(lexical_density))
            - (0.18 * max(0.0, aux_ratio - 0.35))
        )
        return max(0.0, min(1.0, round(score, 4))), round(aux_ratio, 4)

    @classmethod
    def _query_overlap_score(cls, *, query_tokens: set[str], text: str) -> float:
        if not query_tokens:
            return 0.0
        text_tokens = cls._tokenize_for_relevance(text)
        if not text_tokens:
            return 0.0
        shared = query_tokens.intersection(text_tokens)
        if not shared:
            return 0.0
        # Penalizacion logaritmica suave para queries largas.
        denom = max(1.0, math.log2(2 + len(query_tokens)))
        return round(min(1.0, len(shared) / denom), 4)

    @staticmethod
    def _split_sentences(text: str, *, max_sentences: int = 5) -> list[str]:
        raw = [segment.strip() for segment in re.split(r"(?<=[\.\!\?\;])\s+", str(text or ""))]
        sentences: list[str] = []
        for segment in raw:
            compact = re.sub(r"\s+", " ", segment).strip()
            if len(compact) < 35:
                continue
            sentences.append(compact)
            if len(sentences) >= max_sentences:
                break
        return sentences

    @classmethod
    def _evidence_score(cls, text: str) -> float:
        normalized = text.lower()
        evidence_terms = (
            "priorizar",
            "iniciar",
            "monitor",
            "escalar",
            "bundle",
            "control",
            "reevalu",
            "antibiot",
            "troponina",
            "ecg",
            "lactato",
            "hipotension",
            "hipotensión",
            "qrs",
            "sepsis",
            "scasest",
            "dialisis",
            "diálisis",
        )
        term_hits = sum(1 for term in evidence_terms if term in normalized)
        numeric_hits = len(
            re.findall(
                r"(?:>=|<=|>|<)?\s*\d+(?:[.,]\d+)?\s*(?:mmhg|mmol/l|mg/dl|%)?",
                normalized,
            )
        )
        score = min(1.0, (term_hits * 0.12) + (numeric_hits * 0.06))
        return round(score, 4)

    @classmethod
    def _generative_proxy_score(cls, *, query_tokens: set[str], text: str) -> float:
        """Proxy de fluidez/coherencia (sin LLM) para ranking hibrido."""
        normalized = str(text or "").strip()
        if not normalized:
            return 0.0
        has_terminal_punct = 1.0 if normalized[-1] in ".;:!?" else 0.4
        length_score = min(1.0, len(normalized) / 180.0)
        coverage = cls._query_overlap_score(query_tokens=query_tokens, text=normalized)
        # Hibrido proxy generativo: fluidez + cobertura.
        return round((0.40 * has_terminal_punct) + (0.30 * length_score) + (0.30 * coverage), 4)

    @staticmethod
    def _jaccard_similarity(left_tokens: set[str], right_tokens: set[str]) -> float:
        if not left_tokens or not right_tokens:
            return 0.0
        union = left_tokens.union(right_tokens)
        if not union:
            return 0.0
        return round(len(left_tokens.intersection(right_tokens)) / len(union), 4)

    @classmethod
    def _clean_snippet_text(cls, text: str, *, max_chars: int) -> str:
        lines = [segment.strip() for segment in str(text or "").splitlines() if segment.strip()]
        kept: list[str] = []
        for line in lines:
            if cls._looks_like_non_clinical_noise(line):
                continue
            compact = re.sub(r"\s+", " ", line).strip()
            if compact:
                kept.append(compact)
            if sum(len(item) for item in kept) >= max_chars:
                break
        if not kept:
            compact_text = re.sub(r"\s+", " ", str(text or "")).strip()
            return compact_text[:max_chars]
        merged = " ".join(kept).strip()
        return merged[:max_chars]

    @classmethod
    def _build_extractive_answer(
        cls,
        *,
        query: str,
        chunks: list[dict[str, Any]],
        matched_domains: list[str],
    ) -> str | None:
        if not chunks:
            return None
        max_items = max(1, int(settings.CLINICAL_CHAT_RAG_EXTRACTIVE_FALLBACK_MAX_ITEMS))
        lines: list[str] = ["Resumen operativo basado en evidencia interna (RAG extractivo)."]
        lines.append("Prioridades 0-10 minutos:")

        query_tokens = cls._tokenize_for_relevance(query)
        action_focus_enabled = bool(settings.CLINICAL_CHAT_RAG_ACTION_FOCUS_ENABLED)
        action_min_score = float(settings.CLINICAL_CHAT_RAG_ACTION_MIN_SCORE)
        action_max_aux_ratio = float(settings.CLINICAL_CHAT_RAG_ACTION_MAX_AUX_RATIO)
        sentence_candidates: list[dict[str, Any]] = []
        for chunk in chunks[: max_items * 4]:
            cleaned = cls._clean_snippet_text(str(chunk.get("text") or ""), max_chars=260)
            retrieval_score = float(chunk.get("score") or 0.0)
            retrieval_score = max(0.0, min(1.0, retrieval_score))
            for sentence in cls._split_sentences(cleaned):
                sentence = re.sub(r"^\s*(?:\d+[\).\-\s]+|[-*]+\s*)", "", sentence).strip()
                if len(sentence) < 40 or cls._looks_like_non_clinical_noise(sentence):
                    continue
                overlap = cls._query_overlap_score(query_tokens=query_tokens, text=sentence)
                if query_tokens and overlap <= 0.0:
                    continue
                extractive_relevance = (0.72 * overlap) + (0.28 * retrieval_score)
                evidence = cls._evidence_score(sentence)
                generative_proxy = cls._generative_proxy_score(
                    query_tokens=query_tokens,
                    text=sentence,
                )
                # Ensemble hibrido estilo united-reader: tau extractivo, delta generativo.
                tau = 0.60
                delta = 0.40
                relevance = (tau * extractive_relevance) + (delta * generative_proxy)
                actionability, aux_ratio = cls._clinical_actionability_score(
                    text=sentence,
                    overlap_score=overlap,
                    retrieval_score=retrieval_score,
                    evidence_score=evidence,
                )
                if action_focus_enabled:
                    if actionability < action_min_score:
                        continue
                    if (
                        aux_ratio > action_max_aux_ratio
                        and actionability < (action_min_score + 0.12)
                    ):
                        continue
                sentence_candidates.append(
                    {
                        "text": sentence.rstrip(" .") + ".",
                        "tokens": cls._tokenize_for_relevance(sentence),
                        "retrieval": retrieval_score,
                        "overlap": overlap,
                        "extractive_relevance": round(extractive_relevance, 4),
                        "generative_proxy": generative_proxy,
                        "relevance": round(relevance, 4),
                        "evidence": evidence,
                        "actionability": actionability,
                        "aux_ratio": aux_ratio,
                    }
                )

        if not sentence_candidates:
            return None

        # Stage 1: relevancia (consulta -> evidencia candidata)
        stage1 = sorted(
            sentence_candidates,
            key=lambda item: float(item["relevance"]),
            reverse=True,
        )[: max_items * 4]

        # Stage 2: evidencia util (accionabilidad)
        for item in stage1:
            item["evidence_rank_score"] = round(
                (0.55 * float(item["relevance"]))
                + (0.25 * float(item["evidence"]))
                + (0.20 * float(item.get("actionability", 0.0))),
                4,
            )
        stage2 = sorted(stage1, key=lambda item: float(item["evidence_rank_score"]), reverse=True)[
            : max_items * 3
        ]

        # Stage 3: centralidad (coherencia entre frases) + MMR ligero para no repetir.
        for idx, item in enumerate(stage2):
            similarities: list[float] = []
            for jdx, other in enumerate(stage2):
                if idx == jdx:
                    continue
                similarities.append(
                    cls._jaccard_similarity(
                        set(item.get("tokens") or set()),
                        set(other.get("tokens") or set()),
                    )
                )
            centrality = sum(similarities) / len(similarities) if similarities else 0.0
            item["centrality"] = round(centrality, 4)
            item["final_score"] = round(
                (0.65 * float(item["evidence_rank_score"]))
                + (0.20 * float(item["centrality"]))
                + (0.10 * float(item["retrieval"]))
                + (0.05 * float(item.get("actionability", 0.0))),
                4,
            )

        lambda_mmr = 0.72
        selected: list[dict[str, Any]] = []
        remaining = list(stage2)
        while remaining and len(selected) < max_items:
            best_item = None
            best_score = float("-inf")
            for candidate in remaining:
                redundancy = 0.0
                if selected:
                    redundancy = max(
                        cls._jaccard_similarity(
                            set(candidate.get("tokens") or set()),
                            set(chosen.get("tokens") or set()),
                        )
                        for chosen in selected
                    )
                mmr_score = (lambda_mmr * float(candidate["final_score"])) - (
                    (1.0 - lambda_mmr) * redundancy
                )
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_item = candidate
            if best_item is None:
                break
            selected.append(best_item)
            remaining = [item for item in remaining if item is not best_item]

        extracted_actions: list[str] = []
        seen_actions: set[str] = set()
        for candidate in selected:
            action = str(candidate.get("text") or "").strip()
            norm_action = action.lower()
            if norm_action in seen_actions:
                continue
            seen_actions.add(norm_action)
            extracted_actions.append(action)
            if len(extracted_actions) >= max_items:
                break
        if not extracted_actions:
            return None

        for action in extracted_actions[:2]:
            lines.append(f"- {action}")
        if not extracted_actions[:2]:
            lines.append(
                "- Estabilizar ABC, monitorizacion continua y reevaluacion clinica seriada."
            )

        lines.append("Prioridades 10-60 minutos:")
        for action in extracted_actions[2:5]:
            lines.append(f"- {action}")
        if not extracted_actions[2:5]:
            lines.append(
                "- Completar pruebas objetivo y ajustar plan segun respuesta clinica inicial."
            )

        lines.append("Escalado y seguridad:")
        lines.append(
            "- Escalar de forma inmediata si hay inestabilidad hemodinamica, "
            "respiratoria o neurologica."
        )
        lines.append(
            "- Mantener trazabilidad de decisiones y validar cada paso con protocolo local."
        )
        normalized_query = query.lower()
        dose_intent = ("dosis" in normalized_query) or ("posologia" in normalized_query)
        has_dose_evidence = any(
            re.search(r"\b\d+(?:[.,]\d+)?\s*(?:mg|mcg|g|ui|ml)\b", action.lower())
            for action in extracted_actions
        )
        if dose_intent and not has_dose_evidence:
            lines.append(
                "- No se identifica dosis explicita en la evidencia recuperada; "
                "confirmar pauta farmacologica en protocolo local antes de administrar."
            )

        lines.append("Fuentes internas utilizadas:")
        seen_sources: set[str] = set()
        cited = 0
        for chunk in chunks[: max_items * 3]:
            source = str(chunk.get("source") or "").strip()
            section = str(chunk.get("section") or "fragmento interno").strip()
            if not source or source in seen_sources:
                continue
            source_norm = source.lower().replace("\\", "/")
            if "/api/" in source_norm or source_norm.startswith("app/"):
                continue
            seen_sources.add(source)
            source_leaf = source_norm.split("/")[-1] if "/" in source_norm else source_norm
            if source_leaf and source_leaf != section.lower():
                lines.append(f"- {section} ({source_leaf})")
            else:
                lines.append(f"- {section}")
            cited += 1
            if cited >= max_items:
                break
        lines.append(
            "Validar con protocolo local, estado dinamico del paciente y juicio clinico humano."
        )
        return "\n".join(lines)

    @classmethod
    def _build_safe_wrapper_answer(
        cls,
        *,
        query: str,
        chunks: list[dict[str, Any]],
        matched_domains: list[str],
        reason: str,
    ) -> str:
        lines = [
            (
                "No hay evidencia interna suficiente para una recomendacion clinica "
                "confiable en este turno."
            ),
            f"Motivo de seguridad: {reason}.",
            "Siguiente paso seguro:",
            "1) Verificar protocolo local vigente con responsable clinico.",
            "2) Completar datos criticos faltantes (constantes, analitica y hallazgos objetivo).",
            "3) Reintentar con datos objetivos para emitir plan operativo trazable.",
        ]
        if chunks:
            lines.append("Evidencia interna revisada:")
            for chunk in chunks[:2]:
                section = str(chunk.get("section") or "fragmento interno")
                source = str(chunk.get("source") or "")
                source_norm = source.lower().replace("\\", "/")
                if source and ("/api/" in source_norm or source_norm.startswith("app/")):
                    continue
                snippet = cls._clean_snippet_text(str(chunk.get("text") or ""), max_chars=180)
                if snippet:
                    lines.append(f"- {section}: {snippet}")
                else:
                    lines.append(f"- {section}")
        lines.append(
            (
                "Esta salida aplica safe-wrapper: prioriza seguridad sobre completitud "
                "cuando baja la confianza."
            )
        )
        return "\n".join(lines)

    def _build_rag_knowledge_sources(self, chunks: list[dict[str, Any]]) -> list[dict[str, str]]:
        def source_priority(chunk: dict[str, Any]) -> tuple[int, int]:
            locator = str(chunk.get("source") or "").lower().replace("\\", "/")
            title = str(chunk.get("section") or "")
            if "docs/pdf_raw/" in locator:
                return (0, -len(title))
            if locator.startswith("docs/"):
                return (1, -len(title))
            return (2, -len(title))

        def ranking_key(chunk: dict[str, Any]) -> tuple[float, int, int]:
            score = float(chunk.get("score") or 0.0)
            source_rank, title_rank = source_priority(chunk)
            # Prioriza relevancia de retrieval y usa tipo de fuente como desempate.
            return (-score, source_rank, title_rank)

        prioritized_chunks = sorted(chunks, key=ranking_key)
        sources: list[dict[str, str]] = []
        for chunk in prioritized_chunks[: settings.CLINICAL_CHAT_RAG_MAX_CHUNKS]:
            snippet = self._clean_snippet_text(str(chunk.get("text", "")), max_chars=320)
            if len(snippet) < 20:
                continue
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
