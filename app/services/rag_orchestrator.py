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

import copy
import logging
import math
import re
import time
from array import array
from collections import Counter
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
        {
            "key": "anesthesiology",
            "label": "Anestesiologia",
            "summary": "Analgesia, dolor agudo postoperatorio y soporte perioperatorio.",
            "keywords": [
                "anestesia",
                "anestesiologia",
                "analgesia",
                "postoperatorio",
                "dolor postoperatorio",
                "perioperatorio",
                "dap",
            ],
        },
    ]
    _DOMAIN_SPECIALTY_ALIASES: dict[str, tuple[str, ...]] = {
        "critical_ops": ("critical_ops", "emergency", "emergencias"),
        "sepsis": ("sepsis", "infectious_disease", "critical_ops"),
        "scasest": ("scasest", "cardiology", "cardiologia"),
        "resuscitation": ("resuscitation", "critical_ops", "icu"),
        "medicolegal": ("medicolegal",),
        "neurology": ("neurology", "neurologia"),
        "pediatrics_neonatology": ("pediatrics_neonatology", "pediatrics", "neonatology"),
        "oncology": ("oncology", "oncology_urgencies"),
        "pneumology": ("pneumology", "neumologia"),
        "trauma": ("trauma",),
        "gynecology_obstetrics": ("gynecology_obstetrics", "ginecologia", "obstetricia"),
        "gastro_hepato": ("gastro_hepato", "gastroenterologia", "hepatologia"),
        "rheum_immuno": ("rheum_immuno", "reumatologia", "inmunologia"),
        "psychiatry": ("psychiatry", "psiquiatria"),
        "hematology": ("hematology", "hematologia"),
        "endocrinology": ("endocrinology", "endocrinologia"),
        "nephrology": ("nephrology", "nefrologia"),
        "geriatrics": ("geriatrics", "geriatria"),
        "anesthesiology": ("anesthesiology", "anestesiologia"),
        "palliative": ("palliative", "paliativos"),
        "urology": ("urology", "urologia"),
        "ophthalmology": ("ophthalmology", "oftalmologia", "oftamologia"),
        "immunology": ("immunology", "inmunologia"),
        "genetic_recurrence": ("genetic_recurrence", "genetica"),
        "epidemiology": ("epidemiology", "epidemiologia"),
        "anisakis": ("anisakis",),
    }
    _QUERY_INTENT_MARKERS: dict[str, tuple[str, ...]] = {
        "pharmacology": (
            "farmaco",
            "farmacos",
            "farmacologia",
            "medicamento",
            "medicamentos",
            "tratamiento",
            "tratamientos",
            "dosis",
            "posologia",
            "interaccion",
            "interacciones",
            "contraindicacion",
            "contraindicaciones",
            "ajuste de dosis",
        ),
        "steps_actions": (
            "pasos",
            "que hacer",
            "acciones",
            "algoritmo",
            "protocolo",
            "manejo inicial",
            "recomendaciones",
            "recomendacion",
            "recomendar",
            "proponer",
            "prioridades",
        ),
        "referral": (
            "derivar",
            "derivacion",
            "interconsulta",
            "escalar",
            "traslado",
            "otra especialidad",
            "remitir",
        ),
        "follow_up": (
            "seguimiento",
            "reevaluar",
            "monitorizacion",
            "control",
            "revision",
            "plan de control",
        ),
        "similar_cases": (
            "casos parecidos",
            "casos similares",
            "similar",
            "caso comparable",
            "experiencia previa",
            "valorar otros casos",
            "casos de referencia",
        ),
    }
    _INTENT_EXPANSION_TERMS: dict[str, tuple[str, ...]] = {
        "pharmacology": ("dosis", "ajuste", "contraindicaciones", "interacciones", "seguridad"),
        "steps_actions": ("priorizar", "pasos", "acciones", "checklist", "operativo"),
        "referral": ("criterios de derivacion", "interconsulta", "escalado", "coordinacion"),
        "follow_up": ("seguimiento", "reevaluacion", "monitorizacion", "control evolutivo"),
        "similar_cases": ("casos comparables", "patrones similares", "experiencia previa"),
    }
    _SPECIALTY_RETRIEVAL_EXPANSIONS: dict[str, dict[str, tuple[str, ...]]] = {
        "gastro_hepato": {
            "triggers": (
                "abdomen",
                "abdominal",
                "dolor abdominal",
                "estomago",
                "epigastrio",
                "nausea",
                "nauseas",
                "vomito",
                "vomitos",
            ),
            "terms": (
                "abdomen agudo",
                "exploracion abdominal",
                "defensa abdominal",
                "peritonismo",
                "red flags abdominales",
                "reevaluacion seriada",
                "criterios quirurgicos",
                "escalado quirurgico",
            ),
        },
        "ophthalmology": {
            "triggers": (
                "ojo",
                "ocular",
                "oftalmo",
                "oftalmologia",
                "dolor ocular",
                "vision",
                "fotofobia",
            ),
            "terms": (
                "agudeza visual",
                "tincion fluoresceina",
                "presion intraocular",
                "lampara de hendidura",
                "signos de alarma ocular",
                "derivacion oftalmologia urgente",
            ),
        },
        "scasest": {
            "triggers": (
                "dolor toracico",
                "pecho",
                "toracico",
                "torax",
                "opresivo",
            ),
            "terms": (
                "ecg 10 minutos",
                "troponinas seriadas",
                "estratificacion riesgo",
                "monitorizacion cardiaca",
                "sindrome coronario agudo",
                "criterios derivacion hemodinamica",
            ),
        },
        "anesthesiology": {
            "triggers": (
                "anestesia",
                "anestesiologia",
                "analgesia",
                "postoperatorio",
                "postoperatoria",
                "dolor postoperatorio",
                "dolor agudo postoperatorio",
                "perioperatorio",
                "posoperatorio",
                "dap",
            ),
            "terms": (
                "manejo del dolor agudo postoperatorio",
                "analgesia multimodal",
                "evaluacion del dolor",
                "efectos adversos analgesicos",
                "reevaluacion postoperatoria",
                "escalado unidad del dolor agudo",
            ),
        },
    }
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
    _RST_NUCLEUS_HINTS = {
        "protocolo",
        "bundle",
        "algoritmo",
        "manejo inicial",
        "tratamiento",
        "dosis",
        "accion",
        "pasos",
        "recomendacion",
        "criterio",
        "escalar",
        "iniciar",
        "activar",
    }
    _RST_SATELLITE_HINTS = {
        "introduccion",
        "contexto",
        "historia",
        "antecedentes",
        "epidemiologia",
        "discusion",
        "resumen",
        "editorial",
        "marco teorico",
        "definicion",
    }
    _ARGUMENT_ZONE_HINTS: dict[str, set[str]] = {
        "aim": {"objetivo", "aim", "proposito", "meta"},
        "own_method": {
            "metodo",
            "method",
            "procedimiento",
            "protocolo",
            "manejo inicial",
            "algoritmo",
        },
        "own_results": {
            "resultado",
            "results",
            "hallazgo",
            "conclusion",
            "recomendacion",
        },
        "gap_weak": {
            "limitacion",
            "debilidad",
            "gap",
            "insuficiente",
            "no resuelto",
            "falta evidencia",
        },
    }
    _CLAIM_MARKERS = {
        "se recomienda",
        "debe",
        "deben",
        "se sugiere",
        "es prioritario",
    }
    _PREMISE_MARKERS = {
        "porque",
        "debido a",
        "ya que",
        "evidencia",
        "datos",
        "segun",
    }
    _COHERENCE_CONNECTORS = (
        "por ello",
        "por tanto",
        "ademas",
        "despues",
        "luego",
        "debido a",
        "en consecuencia",
        "sin embargo",
    )
    _OPENING_CONNECTOR_HINTS = (
        "por ello",
        "por tanto",
        "ademas",
        "despues",
        "luego",
        "en consecuencia",
        "sin embargo",
    )
    _EDU_SPLIT_PATTERN = re.compile(
        r"(?:[,;]\s+|\s+(?:y|pero|aunque|si|cuando|mientras|porque|debido\s+a|por\s+lo\s+que)\s+)",
        flags=re.IGNORECASE,
    )
    _CENTERING_STOPWORDS = {
        "paciente",
        "caso",
        "manejo",
        "urgencias",
        "clinico",
        "clinica",
        "general",
        "nivel",
    }
    _NON_CLINICAL_SOURCE_MARKERS = (
        "chat_clinico",
        "frontend_chat",
        "adaptacion_blueprint",
        "project_skills",
        "mcp_",
        "prometheus",
        "grafana",
        "roadmap",
        "codex_cli",
        "agent_system",
    )
    _GENERIC_CLINICAL_SPECIFICITY_MARKERS = (
        "diverticul",
        "hernia crural",
        "colecistect",
        "vesicula en porcelana",
        "fenobarbital",
        "colestasis",
        "incarceracion",
        "obstruccion intestinal",
        "perforacion",
    )

    def __init__(self, db: Session):
        self.db = db
        self.legacy_retriever = HybridRetriever()
        self.llamaindex_retriever = LlamaIndexRetriever()
        self.chroma_retriever = ChromaRetriever()
        self.elastic_retriever = ElasticRetriever()
        self.gatekeeper = BasicGatekeeper()
        self._query_cache: dict[str, dict[str, Any]] = {}

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
        pipeline_relaxed_mode: bool = False,
    ) -> tuple[Optional[str], dict[str, Any]]:
        started_at = time.perf_counter()
        trace: dict[str, Any] = {}
        gatekeeper_enabled = bool(
            settings.CLINICAL_CHAT_RAG_ENABLE_GATEKEEPER and not pipeline_relaxed_mode
        )
        safe_wrapper_enabled = bool(
            settings.CLINICAL_CHAT_RAG_SAFE_WRAPPER_ENABLED and not pipeline_relaxed_mode
        )
        trace["rag_pipeline_profile"] = "evaluation" if pipeline_relaxed_mode else "strict"
        trace["rag_gatekeeper_effective_enabled"] = "1" if gatekeeper_enabled else "0"
        trace["rag_safe_wrapper_effective_enabled"] = "1" if safe_wrapper_enabled else "0"

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

        query_tokens_for_cache = set(self._tokenize_for_relevance(query))
        cache_key = self._build_query_cache_key(
            query=query,
            response_mode=response_mode,
            effective_specialty=effective_specialty,
            matched_domains=matched_domains,
        )
        cache_enabled = bool(settings.CLINICAL_CHAT_RAG_QUERY_CACHE_ENABLED)
        trace["rag_query_cache_enabled"] = "1" if cache_enabled else "0"
        if cache_enabled:
            cached_answer, cached_trace, cache_hit_kind = self._lookup_cached_result(
                cache_key=cache_key,
                query_tokens=query_tokens_for_cache,
                response_mode=response_mode,
                effective_specialty=effective_specialty,
            )
            if cached_trace is not None:
                elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
                cached_trace["rag_query_cache_hit"] = "1"
                cached_trace["rag_query_cache_hit_type"] = cache_hit_kind
                cached_trace["rag_belief_state_pruned"] = (
                    "1" if cache_hit_kind == "subset_prune" else "0"
                )
                cached_trace["rag_total_latency_ms"] = str(elapsed_ms)
                return cached_answer, cached_trace
        trace["rag_query_cache_hit"] = "0"
        trace["rag_query_cache_hit_type"] = "miss"
        trace["rag_belief_state_pruned"] = "0"

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
            fact_only_mode_enabled = bool(settings.CLINICAL_CHAT_RAG_FACT_ONLY_MODE_ENABLED)
            force_extractive_only = bool(
                settings.CLINICAL_CHAT_RAG_FORCE_EXTRACTIVE_ONLY
                or fact_only_mode_enabled
            )
            trace["rag_fact_only_mode_enabled"] = "1" if fact_only_mode_enabled else "0"
            native_ollama_style = bool(
                settings.CLINICAL_CHAT_LLM_PROVIDER == "ollama"
                and settings.CLINICAL_CHAT_LLM_NATIVE_STYLE_ENABLED
            )
            configured_llm_min_remaining_budget_ms = int(
                settings.CLINICAL_CHAT_RAG_LLM_MIN_REMAINING_BUDGET_MS
            )
            retrieval_keyword_only = (
                settings.CLINICAL_CHAT_RAG_DETERMINISTIC_ROUTING_ENABLED
                and (
                    force_extractive_only
                    or (
                        configured_llm_min_remaining_budget_ms >= 2000
                        and not native_ollama_style
                    )
                )
                and query_complexity == "complex"
            )
            trace["rag_retrieval_keyword_only"] = "1" if retrieval_keyword_only else "0"
            _, intent_expansion_terms, intent_trace = self._infer_query_intents(
                query=query,
            )
            trace.update(intent_trace)
            retrieval_query, compact_trace = self._build_retrieval_query(
                query=query,
                query_complexity=query_complexity,
                effective_specialty=effective_specialty,
                intent_expansion_terms=intent_expansion_terms,
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

            if settings.CLINICAL_CHAT_RAG_QA_SHORTCUT_ENABLED:
                try:
                    qa_chunks, qa_trace = self._match_precomputed_qa_chunks(
                        query=retrieval_query,
                        specialty_filter=effective_specialty,
                        k=k,
                    )
                    trace.update(qa_trace)
                except Exception:
                    trace["rag_qa_shortcut_enabled"] = "1"
                    trace["rag_qa_shortcut_hit"] = "0"
                    trace["rag_qa_shortcut_reason"] = "db_query_unavailable"
                    qa_chunks = []
                if qa_chunks:
                    qa_alignment_ratio = self._qa_shortcut_domain_alignment_ratio(
                        chunks=qa_chunks,
                        matched_domains=matched_domains,
                        effective_specialty=effective_specialty,
                    )
                    trace["rag_qa_shortcut_domain_alignment_ratio"] = f"{qa_alignment_ratio:.3f}"
                    qa_top_score = float(trace.get("rag_qa_shortcut_top_score", "0.0") or 0.0)
                    # Evita aceptar shortcut QA cuando el dominio de los chunks no coincide
                    # con la intencion clinica de la consulta.
                    if matched_domains and qa_alignment_ratio < 0.55 and qa_top_score < 0.65:
                        trace["rag_qa_shortcut_hit"] = "0"
                        trace["rag_qa_shortcut_reason"] = "domain_misalignment"
                    else:
                        retrieved_chunks = qa_chunks
                        retrieval_strategy = "qa_shortcut"

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
            chunks_before_verifier = list(retrieved_chunks)

            retrieved_chunks, verifier_trace = self._verify_retrieved_chunks(
                query=retrieval_query,
                chunks=retrieved_chunks,
            )
            trace.update(verifier_trace)

            if (
                not retrieved_chunks
                and settings.CLINICAL_CHAT_RAG_VERIFIER_ENABLED
                and settings.CLINICAL_CHAT_RAG_VERIFIER_BM25_FALLBACK_ENABLED
                and not retrieval_keyword_only
            ):
                trace["rag_verifier_recovery_attempted"] = "1"
                try:
                    recovery_chunks, recovery_backend_trace, recovery_strategy = (
                        self._search_with_configured_backend(
                            query=retrieval_query,
                            k=k,
                            specialty_filter=effective_specialty,
                            keyword_only=True,
                        )
                    )
                except TypeError:
                    recovery_chunks, recovery_backend_trace, recovery_strategy = (
                        self._search_with_configured_backend(
                            query=retrieval_query,
                            k=k,
                            specialty_filter=effective_specialty,
                        )
                    )
                trace["rag_verifier_recovery_strategy"] = f"{recovery_strategy}:keyword_only"
                for key, value in recovery_backend_trace.items():
                    trace[f"rag_verifier_recovery_{key}"] = str(value)
                recovery_chunks, recovery_noise_trace = self._drop_noisy_chunks(recovery_chunks)
                for key, value in recovery_noise_trace.items():
                    trace[f"rag_verifier_recovery_{key}"] = str(value)
                recovered_verified, recovered_verify_trace = self._verify_retrieved_chunks(
                    query=retrieval_query,
                    chunks=recovery_chunks,
                )
                for key, value in recovered_verify_trace.items():
                    trace[f"rag_verifier_recovery_{key}"] = str(value)
                if recovered_verified:
                    retrieved_chunks = recovered_verified
                    retrieval_strategy = "verifier_keyword_recovery"
                    trace["rag_verifier_recovery_status"] = "recovered"
                else:
                    trace["rag_verifier_recovery_status"] = "failed"
            elif settings.CLINICAL_CHAT_RAG_VERIFIER_ENABLED:
                trace["rag_verifier_recovery_attempted"] = "0"

            if (
                not retrieved_chunks
                and chunks_before_verifier
                and settings.CLINICAL_CHAT_RAG_VERIFIER_ENABLED
                and not safe_wrapper_enabled
            ):
                retrieved_chunks = chunks_before_verifier
                trace["rag_verifier_override"] = "1"
                trace["rag_verifier_override_reason"] = (
                    "safe_wrapper_disabled_best_effort"
                )

            retrieved_chunks, discourse_trace = self._apply_discourse_coherence_rerank(
                query=retrieval_query,
                chunks=retrieved_chunks,
            )
            trace.update(discourse_trace)

            if not retrieved_chunks:
                if (
                    settings.CLINICAL_CHAT_RAG_VERIFIER_ENABLED
                    and safe_wrapper_enabled
                ):
                    elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
                    safe_wrapper_answer = self._build_safe_wrapper_answer(
                        query=query,
                        chunks=[],
                        matched_domains=matched_domains,
                        reason="insufficient_verified_evidence",
                    )
                    trace.update(
                        {
                            "rag_status": "success",
                            "rag_retrieval_strategy": retrieval_strategy,
                            "rag_generation_mode": "safe_wrapper_abstain",
                            "rag_chunks_retrieved": "0",
                            "rag_total_latency_ms": str(elapsed_ms),
                            "rag_validation_status": "warning",
                            "rag_validation_issues": [
                                "abstencion por evidencia no verificada bajo umbral"
                            ],
                            "rag_safe_wrapper_triggered": "1",
                            "rag_safe_wrapper_reason": "insufficient_verified_evidence",
                            "rag_sources": [],
                            "llm_enabled": (
                                "true"
                                if settings.CLINICAL_CHAT_LLM_ENABLED
                                else "false"
                            ),
                            "llm_used": "false",
                            "llm_error": "VerifierInsufficientEvidence",
                        }
                    )
                    self._store_cached_result(
                        cache_key=cache_key,
                        answer=safe_wrapper_answer,
                        trace=trace,
                        query_tokens=query_tokens_for_cache,
                        response_mode=response_mode,
                        effective_specialty=effective_specialty,
                    )
                    return safe_wrapper_answer, trace
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

            chunk_dicts, ecorag_trace = self._apply_ecorag_evidential_reflection(
                query=query,
                chunks=chunk_dicts,
            )
            trace.update(ecorag_trace)
            chunk_dicts, current_turn_trace = self._filter_chunks_for_current_turn_domain(
                query=query,
                chunks=chunk_dicts,
                matched_domains=matched_domains,
                effective_specialty=effective_specialty,
            )
            trace.update(current_turn_trace)

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
                safe_wrapper_enabled
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
                self._store_cached_result(
                    cache_key=cache_key,
                    answer=safe_wrapper_answer,
                    trace=trace,
                    query_tokens=query_tokens_for_cache,
                    response_mode=response_mode,
                    effective_specialty=effective_specialty,
                )
                return safe_wrapper_answer, trace
            if fact_only_mode_enabled:
                early_goal_answer, early_goal_trace = self._run_early_goal_test(
                    query=query,
                    chunks=chunk_dicts,
                    matched_domains=matched_domains,
                )
                trace.update(early_goal_trace)
                if early_goal_answer:
                    elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
                    trace.update(
                        {
                            "rag_status": "success",
                            "rag_retrieval_strategy": retrieval_strategy,
                            "rag_generation_mode": "early_goal_extractive",
                            "rag_chunks_retrieved": str(len(retrieved_chunks)),
                            "rag_total_latency_ms": str(elapsed_ms),
                            "rag_validation_status": "valid",
                            "rag_validation_issues": [],
                            "rag_sources": rag_sources,
                            "llm_enabled": (
                                "true" if settings.CLINICAL_CHAT_LLM_ENABLED else "false"
                            ),
                            "llm_used": "false",
                            "llm_error": "EarlyGoalExtractivePath",
                        }
                    )
                    self._store_cached_result(
                        cache_key=cache_key,
                        answer=early_goal_answer,
                        trace=trace,
                        query_tokens=query_tokens_for_cache,
                        response_mode=response_mode,
                        effective_specialty=effective_specialty,
                    )
                    return early_goal_answer, trace
            else:
                trace["rag_early_goal_enabled"] = (
                    "1" if settings.CLINICAL_CHAT_RAG_EARLY_GOAL_TEST_ENABLED else "0"
                )
                trace["rag_early_goal_triggered"] = "0"
                trace["rag_early_goal_reason"] = "fact_only_mode_disabled"
            answer: str | None = None
            llm_trace: dict[str, Any] = {}
            rag_generation_mode = "extractive_only"
            trace["rag_force_extractive_only"] = "1" if force_extractive_only else "0"
            budget_total_ms = int(settings.CLINICAL_CHAT_RAG_MAX_TOTAL_LATENCY_MS)
            min_remaining_for_llm_ms = self._resolve_dynamic_llm_min_remaining_budget_ms(
                configured_budget_ms=configured_llm_min_remaining_budget_ms,
                query_complexity=query_complexity,
                pre_context_relevance=pre_context_relevance,
                budget_total_ms=budget_total_ms,
                native_ollama_style=native_ollama_style,
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
                    if native_ollama_style:
                        llm_timeout_override_seconds = max(
                            float(settings.CLINICAL_CHAT_LLM_TIMEOUT_SECONDS),
                            12.0,
                        )
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
            if gatekeeper_enabled:
                is_valid, issues = self.gatekeeper.validate_response(
                    query=query,
                    response=answer,
                    retrieved_chunks=chunk_dicts,
                )
            trace["rag_context_relevance_post"] = f"{post_context_relevance:.3f}"
            trace["rag_faithfulness_post"] = f"{post_faithfulness:.3f}"

            safe_wrapper_triggered_post = (
                safe_wrapper_enabled
                and gatekeeper_enabled
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

            self._store_cached_result(
                cache_key=cache_key,
                answer=answer,
                trace=trace,
                query_tokens=query_tokens_for_cache,
                response_mode=response_mode,
                effective_specialty=effective_specialty,
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
    def _build_query_cache_key(
        *,
        query: str,
        response_mode: str,
        effective_specialty: str,
        matched_domains: list[str],
    ) -> str:
        normalized_query = re.sub(r"\s+", " ", str(query or "").strip().lower())
        normalized_specialty = str(effective_specialty or "general").strip().lower()
        normalized_mode = str(response_mode or "clinical").strip().lower()
        normalized_domains = sorted(
            {
                str(item or "").strip().lower()
                for item in (matched_domains or [])
                if str(item).strip()
            }
        )
        domain_signature = "|".join(normalized_domains)
        return f"{normalized_mode}::{normalized_specialty}::{domain_signature}::{normalized_query}"

    def _prune_query_cache(self) -> None:
        now = time.time()
        expired_keys = [
            key
            for key, item in self._query_cache.items()
            if float(item.get("expires_at", 0.0) or 0.0) <= now
        ]
        for key in expired_keys:
            self._query_cache.pop(key, None)

        max_entries = max(16, int(settings.CLINICAL_CHAT_RAG_QUERY_CACHE_MAX_ENTRIES))
        if len(self._query_cache) <= max_entries:
            return
        overflow = len(self._query_cache) - max_entries
        oldest = sorted(
            self._query_cache.items(),
            key=lambda item: float(item[1].get("created_at", 0.0) or 0.0),
        )[:overflow]
        for key, _ in oldest:
            self._query_cache.pop(key, None)

    def _lookup_cached_result(
        self,
        *,
        cache_key: str,
        query_tokens: set[str],
        response_mode: str,
        effective_specialty: str,
    ) -> tuple[Optional[str], Optional[dict[str, Any]], str]:
        self._prune_query_cache()
        exact = self._query_cache.get(cache_key)
        if exact:
            return (
                str(exact.get("answer") or ""),
                copy.deepcopy(dict(exact.get("trace") or {})),
                "exact",
            )

        if not query_tokens:
            return None, None, "miss"

        normalized_mode = str(response_mode or "clinical").strip().lower()
        normalized_specialty = str(effective_specialty or "general").strip().lower()
        best_subset_hit: Optional[dict[str, Any]] = None
        best_subset_size = 10**9
        for item in self._query_cache.values():
            if str(item.get("response_mode") or "").lower() != normalized_mode:
                continue
            if str(item.get("effective_specialty") or "").lower() != normalized_specialty:
                continue
            item_tokens = set(item.get("query_tokens") or set())
            if not item_tokens or not query_tokens.issubset(item_tokens):
                continue
            if len(item_tokens) < best_subset_size:
                best_subset_hit = item
                best_subset_size = len(item_tokens)

        if best_subset_hit is None:
            return None, None, "miss"

        return (
            str(best_subset_hit.get("answer") or ""),
            copy.deepcopy(dict(best_subset_hit.get("trace") or {})),
            "subset_prune",
        )

    def _store_cached_result(
        self,
        *,
        cache_key: str,
        answer: Optional[str],
        trace: dict[str, Any],
        query_tokens: set[str],
        response_mode: str,
        effective_specialty: str,
    ) -> None:
        if not settings.CLINICAL_CHAT_RAG_QUERY_CACHE_ENABLED:
            return
        if not answer:
            return
        self._prune_query_cache()
        now = time.time()
        ttl = max(30, int(settings.CLINICAL_CHAT_RAG_QUERY_CACHE_TTL_SECONDS))
        self._query_cache[cache_key] = {
            "answer": str(answer),
            "trace": copy.deepcopy(dict(trace)),
            "query_tokens": set(query_tokens),
            "response_mode": str(response_mode or "clinical").strip().lower(),
            "effective_specialty": str(effective_specialty or "general").strip().lower(),
            "created_at": now,
            "expires_at": now + float(ttl),
        }
        self._prune_query_cache()

    @classmethod
    def _run_early_goal_test(
        cls,
        *,
        query: str,
        chunks: list[dict[str, Any]],
        matched_domains: list[str],
    ) -> tuple[Optional[str], dict[str, str]]:
        trace: dict[str, str] = {
            "rag_early_goal_enabled": (
                "1" if settings.CLINICAL_CHAT_RAG_EARLY_GOAL_TEST_ENABLED else "0"
            ),
            "rag_early_goal_triggered": "0",
        }
        if not settings.CLINICAL_CHAT_RAG_EARLY_GOAL_TEST_ENABLED:
            trace["rag_early_goal_reason"] = "disabled"
            return None, trace
        if not chunks:
            trace["rag_early_goal_reason"] = "no_chunks"
            return None, trace

        min_score = float(settings.CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_SCORE)
        min_actionability = float(settings.CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_ACTIONABILITY)
        min_retrieval = float(settings.CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_RETRIEVAL_SCORE)
        query_tokens = cls._tokenize_for_relevance(query)
        best_score = 0.0
        best_actionability = 0.0
        best_retrieval = 0.0
        for chunk in chunks[:6]:
            cleaned = cls._clean_snippet_text(str(chunk.get("text") or ""), max_chars=280)
            retrieval = max(0.0, min(1.0, float(chunk.get("score") or 0.0)))
            for sentence in cls._split_sentences(cleaned, max_sentences=4):
                overlap = cls._query_overlap_score(query_tokens=query_tokens, text=sentence)
                evidence = cls._evidence_score(sentence)
                actionability, _ = cls._clinical_actionability_score(
                    text=sentence,
                    overlap_score=overlap,
                    retrieval_score=retrieval,
                    evidence_score=evidence,
                )
                score = (
                    (0.45 * overlap)
                    + (0.30 * actionability)
                    + (0.15 * evidence)
                    + (0.10 * retrieval)
                )
                if score > best_score:
                    best_score = score
                    best_actionability = actionability
                    best_retrieval = retrieval

        trace["rag_early_goal_best_score"] = f"{best_score:.3f}"
        trace["rag_early_goal_best_actionability"] = f"{best_actionability:.3f}"
        trace["rag_early_goal_best_retrieval"] = f"{best_retrieval:.3f}"
        if (
            best_score < min_score
            or best_actionability < min_actionability
            or best_retrieval < min_retrieval
        ):
            trace["rag_early_goal_reason"] = "threshold_not_met"
            return None, trace

        extractive = cls._build_extractive_answer(
            query=query,
            chunks=chunks,
            matched_domains=matched_domains,
        )
        if not extractive:
            trace["rag_early_goal_reason"] = "extractive_empty"
            return None, trace
        trace["rag_early_goal_triggered"] = "1"
        trace["rag_early_goal_reason"] = "threshold_met"
        return extractive, trace

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

    @classmethod
    def _infer_query_intents(cls, *, query: str) -> tuple[list[str], list[str], dict[str, str]]:
        normalized_query = str(query or "").lower()
        detected: list[str] = []
        expansion_terms: list[str] = []
        for intent, markers in cls._QUERY_INTENT_MARKERS.items():
            if any(marker in normalized_query for marker in markers):
                detected.append(intent)
                expansion_terms.extend(cls._INTENT_EXPANSION_TERMS.get(intent, ()))
        dedup_expansion: list[str] = []
        for token in expansion_terms:
            normalized = str(token).strip().lower()
            if not normalized or normalized in dedup_expansion:
                continue
            dedup_expansion.append(normalized)
        trace = {
            "rag_query_intents_detected": ",".join(detected) if detected else "none",
            "rag_query_intent_expansion_terms": (
                ",".join(dedup_expansion[:10]) if dedup_expansion else "none"
            ),
        }
        return detected, dedup_expansion, trace

    @classmethod
    def _build_retrieval_query(
        cls,
        *,
        query: str,
        query_complexity: str,
        effective_specialty: str | None = None,
        intent_expansion_terms: list[str] | None = None,
    ) -> tuple[str, dict[str, str]]:
        trace: dict[str, str] = {
            "rag_retrieval_query_compacted": "0",
            "rag_retrieval_query_compact_reason": "not_required",
            "rag_retrieval_query_specialty_expanded": "0",
            "rag_retrieval_query_specialty_terms": "none",
        }
        query_tokens = cls._tokenize_for_relevance(query)
        specialty_terms = cls._specialty_retrieval_terms(
            query=query,
            query_tokens=query_tokens,
            effective_specialty=effective_specialty,
        )
        if specialty_terms:
            trace["rag_retrieval_query_specialty_expanded"] = "1"
            trace["rag_retrieval_query_specialty_terms"] = ",".join(specialty_terms[:8])

        if not settings.CLINICAL_CHAT_RAG_DETERMINISTIC_ROUTING_ENABLED:
            if specialty_terms:
                return f"{query} {' '.join(specialty_terms[:4])}".strip(), trace
            return query, trace
        if query_complexity != "complex":
            if specialty_terms:
                trace["rag_retrieval_query_compact_reason"] = "specialty_expansion_only"
                return f"{query} {' '.join(specialty_terms[:4])}".strip(), trace
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
        if intent_expansion_terms:
            tokens.extend(
                [str(item).lower() for item in intent_expansion_terms if str(item).strip()]
            )
        if specialty_terms:
            tokens.extend([str(item).lower() for item in specialty_terms if str(item).strip()])
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

    @classmethod
    def _specialty_retrieval_terms(
        cls,
        *,
        query: str,
        query_tokens: set[str],
        effective_specialty: str | None,
    ) -> list[str]:
        specialty_key = str(effective_specialty or "").strip().lower()
        if not specialty_key:
            return []
        config = cls._SPECIALTY_RETRIEVAL_EXPANSIONS.get(specialty_key)
        if not config:
            return []
        if not cls._is_generic_operational_query(query=query, query_tokens=query_tokens):
            return []
        normalized_query = str(query or "").lower()
        triggers = tuple(str(item).lower() for item in config.get("triggers", ()))
        trigger_hit = any(trigger in normalized_query for trigger in triggers) or any(
            trigger in query_tokens for trigger in triggers
        )
        if not trigger_hit:
            return []
        terms: list[str] = []
        for term in config.get("terms", ()):
            normalized_term = str(term).strip().lower()
            if not normalized_term or normalized_term in terms:
                continue
            terms.append(normalized_term)
        return terms[:6]

    @staticmethod
    def _resolve_dynamic_llm_min_remaining_budget_ms(
        *,
        configured_budget_ms: int,
        query_complexity: str,
        pre_context_relevance: float,
        budget_total_ms: int,
        native_ollama_style: bool,
    ) -> int:
        dynamic_budget = max(200, int(configured_budget_ms))
        if budget_total_ms > 0:
            dynamic_budget = min(dynamic_budget, max(300, int(budget_total_ms * 0.75)))
        if query_complexity == "simple":
            dynamic_budget = min(dynamic_budget, 900)
        elif query_complexity == "medium":
            dynamic_budget = min(dynamic_budget, 1400)

        if pre_context_relevance < 0.16:
            dynamic_budget = max(dynamic_budget, 1800)
        elif pre_context_relevance < 0.22:
            dynamic_budget = max(dynamic_budget, 1500)
        if native_ollama_style:
            native_budget_cap = 350
            if budget_total_ms > 0:
                native_budget_cap = max(250, min(350, int(budget_total_ms * 0.12)))
            dynamic_budget = min(dynamic_budget, native_budget_cap)
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

    @classmethod
    def _resolve_domain_aliases(cls, *, matched_domains: list[str]) -> set[str]:
        aliases: set[str] = set()
        for domain in matched_domains or []:
            normalized = str(domain or "").strip().lower()
            if not normalized:
                continue
            aliases.add(normalized)
            aliases.update(cls._DOMAIN_SPECIALTY_ALIASES.get(normalized, ()))
        return {item for item in aliases if item}

    @classmethod
    def _qa_shortcut_domain_alignment_ratio(
        cls,
        *,
        chunks: list[Any],
        matched_domains: list[str],
        effective_specialty: str,
    ) -> float:
        if not chunks:
            return 0.0
        domain_aliases = cls._resolve_domain_aliases(matched_domains=matched_domains)
        normalized_specialty = str(effective_specialty or "").strip().lower()
        if normalized_specialty and normalized_specialty not in {"general", "*"}:
            domain_aliases.add(normalized_specialty)
        if not domain_aliases:
            return 1.0

        aligned = 0
        for chunk in chunks:
            chunk_specialty = str(getattr(chunk, "specialty", "") or "").strip().lower()
            if chunk_specialty and chunk_specialty in domain_aliases:
                aligned += 1
                continue
            source_tokens = ""
            chunk_document = getattr(chunk, "document", None)
            if chunk_document is not None:
                source_tokens = str(getattr(chunk_document, "source_file", "") or "").lower()
            if not source_tokens:
                source_tokens = str(getattr(chunk, "section_path", "") or "").lower()
            if any(alias in source_tokens for alias in domain_aliases):
                aligned += 1
        return aligned / max(1, len(chunks))

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

    @staticmethod
    def _is_current_turn_generic_operational_query(query: str) -> bool:
        normalized_query = str(query or "").strip().lower()
        return any(
            marker in normalized_query
            for marker in (
                "datos clave",
                "escalado",
                "pasos",
                "que hacer",
                "manejo",
                "acciones",
                "prioridades",
                "recomendaciones",
                "seguimiento",
                "deriv",
            )
        )

    @classmethod
    def _filter_chunks_for_current_turn_domain(
        cls,
        *,
        query: str,
        chunks: list[dict[str, Any]],
        matched_domains: list[str],
        effective_specialty: str,
    ) -> tuple[list[dict[str, Any]], dict[str, str]]:
        if not chunks:
            return chunks, {"rag_current_turn_domain_filter": "0"}
        concrete_domains = [
            str(item).strip().lower()
            for item in (matched_domains or [])
            if str(item).strip().lower() not in {"", "critical_ops", "general", "administrative"}
        ]
        if len(concrete_domains) != 1:
            return chunks, {"rag_current_turn_domain_filter": "0"}

        domain_aliases = cls._resolve_domain_aliases(matched_domains=matched_domains)
        normalized_specialty = str(effective_specialty or "").strip().lower()
        if normalized_specialty and normalized_specialty not in {"general", "*"}:
            domain_aliases.add(normalized_specialty)

        aligned: list[dict[str, Any]] = []
        unknown: list[dict[str, Any]] = []
        for chunk in chunks:
            source_blob = " ".join(
                [
                    str(chunk.get("source") or ""),
                    str(chunk.get("source_title") or ""),
                    str(chunk.get("section") or ""),
                    str(chunk.get("text") or ""),
                ]
            ).lower()
            if any(alias in source_blob for alias in domain_aliases):
                aligned.append(chunk)
            else:
                unknown.append(chunk)

        filtered = aligned or unknown or chunks
        dropped = max(0, len(chunks) - len(filtered))
        if cls._is_current_turn_generic_operational_query(query):
            operational = [
                chunk
                for chunk in filtered
                if str(chunk.get("source") or "").lower().replace("\\", "/").endswith(".md")
            ]
            if operational:
                dropped += max(0, len(filtered) - len(operational))
                filtered = operational
        return filtered, {
            "rag_current_turn_domain_filter": "1",
            "rag_current_turn_domain_filter_dropped": str(dropped),
        }

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
            if cls._looks_like_non_clinical_source(source_file):
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
    def _build_hyde_query_for_segment(
        cls,
        *,
        segment: str,
        top_domain: str,
    ) -> str:
        normalized_segment = cls._normalize_segment_text(segment)
        if not settings.CLINICAL_CHAT_RAG_HYDE_ENABLED:
            return normalized_segment
        if not normalized_segment:
            return normalized_segment
        normalized_domain = str(top_domain or "").strip().lower()
        if not normalized_domain or normalized_domain == "none":
            return normalized_segment
        summary = ""
        for item in cls._MULTI_INTENT_DOMAIN_CATALOG:
            if str(item.get("key") or "").strip().lower() != normalized_domain:
                continue
            summary = str(item.get("summary") or "").strip()
            break
        if not summary:
            return normalized_segment
        return (
            f"{normalized_segment}. "
            f"Hipotesis clinica del subcaso: {summary}"
        )

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
            search_query = cls._build_hyde_query_for_segment(
                segment=segment,
                top_domain=top_domain or "none",
            )
            plan.append(
                {
                    "segment": segment,
                    "search_query": search_query,
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
        trace["rag_multi_intent_hyde_enabled"] = (
            "1" if settings.CLINICAL_CHAT_RAG_HYDE_ENABLED else "0"
        )
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
            query = str(
                segment_item.get("search_query")
                or segment_item.get("segment")
                or ""
            ).strip()
            if not query:
                continue
            original_segment = str(segment_item.get("segment") or "").strip()
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
            trace[f"rag_multi_intent_segment_{index}_query"] = original_segment or query
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

    @classmethod
    def _looks_like_non_clinical_source(cls, source: str) -> bool:
        normalized = str(source or "").replace("\\", "/").lower().strip()
        if not normalized:
            return False
        if "docs/decisions/" in normalized:
            return True
        if any(marker in normalized for marker in cls._NON_CLINICAL_SOURCE_MARKERS):
            return True
        doc_number_match = re.search(r"docs/(\d+)_", normalized)
        if doc_number_match:
            try:
                doc_number = int(doc_number_match.group(1))
            except ValueError:
                doc_number = 0
            # Mantener corpus clinico operativo acotado a motores/especialidades (40-86).
            if doc_number < 40 or doc_number >= 87:
                return True
        return False

    @staticmethod
    def _tokenize_for_relevance(text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9]{3,}", str(text or "").lower())
            if token not in {"para", "con", "sin", "por", "del", "las", "los", "una", "uno"}
        }

    @staticmethod
    def _tokenize_for_cross_encoder(text: str) -> list[str]:
        return [
            token
            for token in re.findall(r"[a-z0-9]{3,}", str(text or "").lower())
            if token not in {"para", "con", "sin", "por", "del", "las", "los", "una", "uno"}
        ]

    @staticmethod
    def _token_ngrams(tokens: list[str], *, n: int = 2) -> set[tuple[str, ...]]:
        if n <= 1 or len(tokens) < n:
            return set()
        return {
            tuple(tokens[index : index + n])
            for index in range(0, len(tokens) - n + 1)
        }

    @classmethod
    def _build_chunk_verifier_text(cls, chunk: Any) -> str:
        if isinstance(chunk, dict):
            chunk_text = str(chunk.get("text") or "").strip()
            section = str(chunk.get("section") or "").strip()
            source_title = str(chunk.get("source_title") or "").strip()
            keyword_items = [
                str(item).strip()
                for item in (chunk.get("keywords") or [])
                if str(item).strip()
            ]
        else:
            chunk_text = str(getattr(chunk, "chunk_text", "") or "").strip()
            section = str(getattr(chunk, "section_path", "") or "").strip()
            document = getattr(chunk, "document", None)
            source_title = ""
            if document is not None:
                source_title = str(getattr(document, "title", "") or "").strip()
            keyword_items = [
                str(item).strip()
                for item in (getattr(chunk, "keywords", None) or [])
                if str(item).strip()
            ]
        parts = [
            item
            for item in [source_title, section, " ".join(keyword_items[:10]), chunk_text]
            if item
        ]
        return " ".join(parts).strip()

    @classmethod
    def _cross_encoder_proxy_score(
        cls,
        *,
        query: str,
        chunk_text: str,
        retrieval_score: float,
    ) -> float:
        query_tokens = cls._tokenize_for_cross_encoder(query)
        text_tokens = cls._tokenize_for_cross_encoder(chunk_text)
        if not query_tokens or not text_tokens:
            return round(max(0.0, min(1.0, retrieval_score * 0.45)), 4)

        query_token_set = set(query_tokens)
        text_token_set = set(text_tokens)
        shared = query_token_set.intersection(text_token_set)
        recall = len(shared) / max(1, len(query_token_set))
        precision = len(shared) / max(1, len(text_token_set))
        soft_shared = 0
        for query_token in query_token_set:
            query_prefix = query_token[:5]
            if len(query_prefix) < 4:
                continue
            if any(
                (
                    text_token.startswith(query_prefix)
                    or query_token.startswith(text_token[:5])
                )
                for text_token in text_token_set
                if len(text_token) >= 4
            ):
                soft_shared += 1
        soft_recall = soft_shared / max(1, len(query_token_set))
        recall = max(recall, soft_recall)
        query_bigrams = cls._token_ngrams(query_tokens, n=2)
        text_bigrams = cls._token_ngrams(text_tokens, n=2)
        bigram_overlap = 0.0
        if query_bigrams and text_bigrams:
            bigram_overlap = len(query_bigrams.intersection(text_bigrams)) / max(
                1,
                len(query_bigrams),
            )
        evidence = cls._evidence_score(chunk_text)
        overlap_score = cls._query_overlap_score(
            query_tokens=query_token_set,
            text=chunk_text,
        )
        actionability, aux_ratio = cls._clinical_actionability_score(
            text=chunk_text,
            overlap_score=overlap_score,
            retrieval_score=retrieval_score,
            evidence_score=evidence,
        )
        score = (
            (0.34 * recall)
            + (0.16 * precision)
            + (0.18 * retrieval_score)
            + (0.12 * bigram_overlap)
            + (0.12 * evidence)
            + (0.08 * actionability)
            - (0.05 * max(0.0, aux_ratio - 0.55))
        )
        return round(max(0.0, min(1.0, score)), 4)

    def _verify_retrieved_chunks(
        self,
        *,
        query: str,
        chunks: list[Any],
    ) -> tuple[list[Any], dict[str, str]]:
        trace: dict[str, str] = {
            "rag_verifier_enabled": "1" if settings.CLINICAL_CHAT_RAG_VERIFIER_ENABLED else "0"
        }
        if not chunks:
            trace["rag_verifier_candidates"] = "0"
            trace["rag_verifier_verified"] = "0"
            trace["rag_verifier_passed"] = "0"
            trace["rag_verifier_reason"] = "empty_candidates"
            return [], trace

        if not settings.CLINICAL_CHAT_RAG_VERIFIER_ENABLED:
            trace["rag_verifier_candidates"] = str(len(chunks))
            trace["rag_verifier_verified"] = str(len(chunks))
            trace["rag_verifier_passed"] = "1"
            trace["rag_verifier_reason"] = "disabled"
            return chunks, trace

        min_score = float(settings.CLINICAL_CHAT_RAG_VERIFIER_MIN_SCORE)
        configured_min_chunks = max(1, int(settings.CLINICAL_CHAT_RAG_VERIFIER_MIN_CHUNKS))
        min_chunks = min(configured_min_chunks, max(1, len(chunks)))
        trace["rag_verifier_min_score"] = f"{min_score:.2f}"
        trace["rag_verifier_min_chunks"] = str(min_chunks)
        trace["rag_verifier_min_chunks_configured"] = str(configured_min_chunks)
        trace["rag_verifier_candidates"] = str(len(chunks))

        verified: list[tuple[Any, float]] = []
        scores: list[float] = []
        for chunk in chunks:
            retrieval_score = float(getattr(chunk, "_rag_score", 0.0) or 0.0)
            retrieval_score = max(0.0, min(1.0, retrieval_score))
            chunk_text = self._build_chunk_verifier_text(chunk)
            if not chunk_text:
                continue
            verify_score = self._cross_encoder_proxy_score(
                query=query,
                chunk_text=chunk_text,
                retrieval_score=retrieval_score,
            )
            setattr(chunk, "_rag_verify_score", float(verify_score))
            scores.append(float(verify_score))
            if verify_score < min_score:
                continue
            blended = max(verify_score, (0.70 * retrieval_score) + (0.30 * verify_score))
            setattr(chunk, "_rag_score", round(float(blended), 4))
            verified.append((chunk, float(verify_score)))

        top_score = max(scores) if scores else 0.0
        avg_score = (sum(scores) / len(scores)) if scores else 0.0
        trace["rag_verifier_top_score"] = f"{top_score:.3f}"
        trace["rag_verifier_mean_score"] = f"{avg_score:.3f}"
        trace["rag_verifier_verified"] = str(len(verified))

        if len(verified) < min_chunks:
            trace["rag_verifier_passed"] = "0"
            trace["rag_verifier_reason"] = "below_min_verified_chunks"
            return [], trace

        verified.sort(key=lambda item: item[1], reverse=True)
        trace["rag_verifier_passed"] = "1"
        trace["rag_verifier_reason"] = "ok"
        return [chunk for chunk, _ in verified], trace

    @classmethod
    def _extract_chunk_text_and_section(cls, chunk: Any) -> tuple[str, str]:
        if isinstance(chunk, dict):
            text = str(chunk.get("text") or chunk.get("chunk_text") or "").strip()
            section = str(chunk.get("section") or chunk.get("section_path") or "").strip()
            return text, section
        text = str(getattr(chunk, "chunk_text", "") or "").strip()
        section = str(getattr(chunk, "section_path", "") or "").strip()
        return text, section

    @classmethod
    def _infer_rst_role(cls, *, section: str, text: str) -> tuple[str, float]:
        payload = f"{section} {text}".lower()
        nucleus_hits = sum(1 for marker in cls._RST_NUCLEUS_HINTS if marker in payload)
        satellite_hits = sum(1 for marker in cls._RST_SATELLITE_HINTS if marker in payload)
        if nucleus_hits == 0 and satellite_hits == 0:
            return "neutral", 0.50
        total_hits = max(1, nucleus_hits + satellite_hits)
        if nucleus_hits >= satellite_hits:
            confidence = max(0.55, float(nucleus_hits) / float(total_hits))
            return "nucleus", round(min(1.0, confidence), 4)
        confidence = max(0.55, float(satellite_hits) / float(total_hits))
        return "satellite", round(min(1.0, confidence), 4)

    @classmethod
    def _infer_argument_zone(cls, *, section: str, text: str) -> str:
        payload = f"{section} {text}".lower()
        zone_scores: dict[str, int] = {}
        for zone, markers in cls._ARGUMENT_ZONE_HINTS.items():
            zone_scores[zone] = sum(1 for marker in markers if marker in payload)
        best_zone, best_score = max(zone_scores.items(), key=lambda item: item[1])
        if best_score <= 0:
            return "none"
        return best_zone

    @classmethod
    def _extract_salient_entities(cls, query: str) -> set[str]:
        tokens = [
            token
            for token in cls._tokenize_for_cross_encoder(query)
            if token not in cls._CENTERING_STOPWORDS
        ]
        if not tokens:
            return set()
        counts = Counter(token for token in tokens if len(token) >= 4)
        ranked = sorted(
            counts.items(),
            key=lambda item: (-int(item[1]), -len(item[0]), item[0]),
        )
        return {token for token, _ in ranked[:6]}

    @classmethod
    def _segment_edus(cls, text: str, *, max_units: int = 14) -> list[str]:
        sentences = cls._split_sentences(text, max_sentences=max_units * 2)
        if not sentences:
            sentences = [
                segment.strip()
                for segment in re.split(r"(?<=[\.\!\?\;])\s+", str(text or ""))
                if segment.strip()
            ]
        units: list[str] = []
        for sentence in sentences:
            parts = cls._EDU_SPLIT_PATTERN.split(sentence)
            for part in parts:
                compact = re.sub(r"\s+", " ", str(part).strip())
                if len(compact) < 18:
                    continue
                units.append(compact)
                if len(units) >= max_units:
                    return units
        return units

    @staticmethod
    def _term_frequency_vector(tokens: list[str]) -> dict[str, float]:
        if not tokens:
            return {}
        counts = Counter(tokens)
        total = float(sum(counts.values()) or 1.0)
        return {token: float(value) / total for token, value in counts.items()}

    @staticmethod
    def _cosine_sparse_vectors(left: dict[str, float], right: dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        shared = set(left).intersection(right)
        if not shared:
            return 0.0
        dot = sum(float(left[token]) * float(right[token]) for token in shared)
        left_norm = math.sqrt(sum(float(value) * float(value) for value in left.values()))
        right_norm = math.sqrt(sum(float(value) * float(value) for value in right.values()))
        denom = left_norm * right_norm
        if denom <= 0:
            return 0.0
        return max(0.0, min(1.0, float(dot) / float(denom)))

    @classmethod
    def _texttiling_topic_score(cls, *, query_tokens: set[str], edus: list[str]) -> float:
        if len(edus) < 2:
            return 0.0
        window_size = 2
        vectors = [
            cls._term_frequency_vector(cls._tokenize_for_cross_encoder(edu))
            for edu in edus
        ]
        boundary_similarities: list[float] = []
        for index in range(0, len(edus) - 1):
            left_start = max(0, index - window_size + 1)
            right_end = min(len(edus), index + 1 + window_size)
            left_window = vectors[left_start : index + 1]
            right_window = vectors[index + 1 : right_end]
            left_agg: Counter[str] = Counter()
            right_agg: Counter[str] = Counter()
            for item in left_window:
                left_agg.update(item)
            for item in right_window:
                right_agg.update(item)
            left_total = float(sum(left_agg.values()) or 1.0)
            right_total = float(sum(right_agg.values()) or 1.0)
            left_norm = {token: float(weight) / left_total for token, weight in left_agg.items()}
            right_norm = {
                token: float(weight) / right_total for token, weight in right_agg.items()
            }
            boundary_similarities.append(cls._cosine_sparse_vectors(left_norm, right_norm))

        if not boundary_similarities:
            return 0.0
        continuity = sum(boundary_similarities) / float(len(boundary_similarities))
        topic_shifts = sum(1 for value in boundary_similarities if value < 0.20)
        shift_penalty = float(topic_shifts) / float(max(1, len(boundary_similarities)))
        alignment_values: list[float] = []
        for edu in edus:
            overlap = cls._query_overlap_score(query_tokens=query_tokens, text=edu)
            alignment_values.append(overlap)
        alignment = max(alignment_values) if alignment_values else 0.0
        score = (0.50 * continuity) + (0.35 * alignment) + (0.15 * (1.0 - shift_penalty))
        return round(max(0.0, min(1.0, score)), 4)

    @classmethod
    def _lexical_chain_cohesion_score(cls, *, query_tokens: set[str], edus: list[str]) -> float:
        tokens: list[str] = []
        for edu in edus:
            tokens.extend(cls._tokenize_for_cross_encoder(edu))
        if not tokens:
            return 0.0
        chain_counter: Counter[str] = Counter()
        for token in tokens:
            if len(token) < 5:
                continue
            root = token[:5]
            chain_counter[root] += 1
        if not chain_counter:
            return 0.0
        repeated = {root: count for root, count in chain_counter.items() if count >= 2}
        density = float(sum(repeated.values())) / float(max(1, len(tokens)))
        query_roots = {token[:5] for token in query_tokens if len(token) >= 5}
        overlap = float(len(query_roots.intersection(repeated.keys()))) / float(
            max(1, len(query_roots))
        )
        diversity = float(len(repeated)) / float(max(1, len(chain_counter)))
        score = (0.55 * density) + (0.30 * overlap) + (0.15 * diversity)
        return round(max(0.0, min(1.0, score)), 4)

    @staticmethod
    def _build_dense_hash_embedding(tokens: list[str], *, dim: int = 24) -> list[float]:
        if not tokens:
            return [0.0] * dim
        counts = Counter(tokens)
        vector = [0.0] * dim
        for token, count in counts.items():
            index = hash(token) % dim
            vector[index] += float(count)
        norm = math.sqrt(sum(value * value for value in vector))
        if norm <= 0:
            return vector
        return [value / norm for value in vector]

    @staticmethod
    def _mean(values: list[float]) -> float:
        if not values:
            return 0.0
        return float(sum(values)) / float(len(values))

    @classmethod
    def _lcd_pair_score_from_embeddings(
        cls,
        left_embedding: list[float],
        right_embedding: list[float],
    ) -> float:
        if not left_embedding or not right_embedding:
            return 0.0
        concat = left_embedding + right_embedding
        diff = [left - right for left, right in zip(left_embedding, right_embedding)]
        abs_diff = [abs(item) for item in diff]
        prod = [left * right for left, right in zip(left_embedding, right_embedding)]
        concat_energy = cls._mean([abs(item) for item in concat])
        diff_energy = cls._mean([abs(item) for item in diff])
        abs_diff_energy = cls._mean(abs_diff)
        prod_energy = cls._mean(prod)
        # LCD ligero: concat + diff + |diff| + producto elemento a elemento.
        score = (
            (0.24 * concat_energy)
            + (0.46 * prod_energy)
            + (0.22 * (1.0 - min(1.0, abs_diff_energy)))
            + (0.08 * (1.0 - min(1.0, diff_energy)))
        )
        return round(max(0.0, min(1.0, score)), 4)

    @classmethod
    def _lsa_coherence_score(cls, *, query_tokens: set[str], edus: list[str]) -> float:
        if not query_tokens or not edus:
            return 0.0
        tokenized_edus = [cls._tokenize_for_cross_encoder(edu) for edu in edus]
        all_tokens = [token for edu_tokens in tokenized_edus for token in edu_tokens]
        if not all_tokens:
            return 0.0
        vocab_counts = Counter(all_tokens + list(query_tokens))
        vocab = [token for token, _ in vocab_counts.most_common(32)]
        if len(vocab) < 4:
            return 0.0
        idf: dict[str, float] = {}
        doc_count = max(1, len(tokenized_edus))
        for token in vocab:
            docs_with_token = sum(1 for edu_tokens in tokenized_edus if token in edu_tokens)
            idf[token] = math.log((1.0 + doc_count) / (1.0 + docs_with_token)) + 1.0

        def _build_tfidf(tokens: list[str]) -> list[float]:
            counts = Counter(tokens)
            total = float(sum(counts.values()) or 1.0)
            return [
                (float(counts.get(term, 0.0)) / total) * float(idf.get(term, 1.0))
                for term in vocab
            ]

        query_vector = _build_tfidf(list(query_tokens))
        sentence_vectors = [_build_tfidf(tokens) for tokens in tokenized_edus]
        query_norm = math.sqrt(sum(value * value for value in query_vector))
        if query_norm <= 0:
            return 0.0
        query_vector = [value / query_norm for value in query_vector]
        similarities: list[float] = []
        for vector in sentence_vectors:
            norm = math.sqrt(sum(value * value for value in vector))
            if norm <= 0:
                continue
            normalized = [value / norm for value in vector]
            dot = sum(left * right for left, right in zip(query_vector, normalized))
            similarities.append(max(0.0, min(1.0, dot)))
        if not similarities:
            return 0.0
        top = max(similarities)
        avg = sum(similarities) / float(len(similarities))
        score = (0.60 * top) + (0.40 * avg)
        return round(max(0.0, min(1.0, score)), 4)

    @classmethod
    def _entity_grid_coherence_score(cls, *, edus: list[str], salient_entities: set[str]) -> float:
        if len(edus) < 2 or not salient_entities:
            return 0.0
        roles_grid: list[dict[str, int]] = []
        for edu in edus:
            tokens = cls._tokenize_for_cross_encoder(edu)
            if not tokens:
                roles_grid.append({entity: 0 for entity in salient_entities})
                continue
            midpoint = max(1, len(tokens) // 2)
            row: dict[str, int] = {}
            for entity in salient_entities:
                if entity in tokens[:midpoint]:
                    row[entity] = 2
                elif entity in tokens[midpoint:]:
                    row[entity] = 1
                else:
                    row[entity] = 0
            roles_grid.append(row)

        transitions_continue = 0
        transitions_shift = 0
        centering_continue = 0
        centering_total = 0
        previous_center: Optional[str] = None
        for index in range(0, len(roles_grid) - 1):
            current_row = roles_grid[index]
            next_row = roles_grid[index + 1]
            current_center = max(current_row.items(), key=lambda item: item[1])[0]
            next_center = max(next_row.items(), key=lambda item: item[1])[0]
            if previous_center is not None:
                centering_total += 1
                if current_center == previous_center:
                    centering_continue += 1
            previous_center = next_center
            for entity in salient_entities:
                current_active = current_row.get(entity, 0) > 0
                next_active = next_row.get(entity, 0) > 0
                if current_active and next_active:
                    transitions_continue += 1
                elif current_active != next_active:
                    transitions_shift += 1

        continue_ratio = float(transitions_continue) / float(
            max(1, transitions_continue + transitions_shift)
        )
        centering_ratio = float(centering_continue) / float(max(1, centering_total))
        score = (0.65 * continue_ratio) + (0.35 * centering_ratio)
        return round(max(0.0, min(1.0, score)), 4)

    @classmethod
    def _entity_centering_score(cls, *, text: str, salient_entities: set[str]) -> float:
        if not salient_entities:
            return 0.0
        tokens = cls._tokenize_for_cross_encoder(text)
        if not tokens:
            return 0.0
        token_set = set(tokens)
        shared = token_set.intersection(salient_entities)
        coverage = float(len(shared)) / float(max(1, len(salient_entities)))
        recurrence = float(
            sum(1 for token in tokens if token in salient_entities)
        ) / float(max(1, len(tokens)))
        score = (0.70 * coverage) + (0.30 * min(1.0, recurrence * 3.0))
        return round(max(0.0, min(1.0, score)), 4)

    @classmethod
    def _lexical_cohesion_score(cls, *, query_tokens: set[str], text: str) -> float:
        tokens = cls._tokenize_for_cross_encoder(text)
        if not tokens:
            return 0.0
        overlap = cls._query_overlap_score(query_tokens=query_tokens, text=text)
        counts = Counter(tokens)
        repeated_ratio = float(sum(1 for value in counts.values() if value >= 2)) / float(
            max(1, len(counts))
        )
        long_repeated = {
            token
            for token, value in counts.items()
            if value >= 2 and len(token) >= 5
        }
        chain_overlap = float(len(long_repeated.intersection(query_tokens))) / float(
            max(1, len(query_tokens))
        )
        score = (0.65 * overlap) + (0.20 * repeated_ratio) + (0.15 * chain_overlap)
        return round(max(0.0, min(1.0, score)), 4)

    @classmethod
    def _sentence_pair_coherence_score(cls, left: str, right: str) -> float:
        left_tokens = cls._tokenize_for_cross_encoder(left)
        right_tokens = cls._tokenize_for_cross_encoder(right)
        if not left_tokens or not right_tokens:
            return 0.0
        left_set = set(left_tokens)
        right_set = set(right_tokens)
        lexical_overlap = cls._jaccard_similarity(left_set, right_set)
        shared_long = {
            token
            for token in left_set.intersection(right_set)
            if len(token) >= 5
        }
        shared_long_ratio = float(len(shared_long)) / float(max(1, len(left_set)))
        right_norm = right.strip().lower()
        connector_bonus = (
            1.0
            if any(right_norm.startswith(prefix) for prefix in cls._COHERENCE_CONNECTORS)
            else 0.0
        )
        left_embedding = cls._build_dense_hash_embedding(left_tokens)
        right_embedding = cls._build_dense_hash_embedding(right_tokens)
        lcd_feature_score = cls._lcd_pair_score_from_embeddings(
            left_embedding,
            right_embedding,
        )
        score = (
            (0.44 * lexical_overlap)
            + (0.20 * shared_long_ratio)
            + (0.24 * lcd_feature_score)
            + (0.12 * connector_bonus)
        )
        return round(max(0.0, min(1.0, score)), 4)

    @classmethod
    def _order_coherence_score(cls, sentences: list[str]) -> float:
        if len(sentences) < 2:
            return 0.0
        pair_scores: list[float] = []
        for index in range(0, len(sentences) - 1):
            pair_scores.append(
                cls._sentence_pair_coherence_score(
                    sentences[index],
                    sentences[index + 1],
                )
            )
        if not pair_scores:
            return 0.0
        return sum(pair_scores) / float(len(pair_scores))

    @classmethod
    def _local_coherence_discriminator_score(cls, text: str) -> float:
        edus = cls._segment_edus(text, max_units=8)
        if len(edus) < 2:
            return 0.0
        natural_order = cls._order_coherence_score(edus)
        reversed_order = cls._order_coherence_score(list(reversed(edus)))
        order_margin = max(0.0, natural_order - reversed_order)
        opening = edus[0].strip().lower()
        opening_penalty = (
            0.12
            if any(opening.startswith(prefix) for prefix in cls._OPENING_CONNECTOR_HINTS)
            else 0.0
        )
        score = ((0.75 * natural_order) + (0.25 * order_margin)) - opening_penalty
        return round(max(0.0, min(1.0, score)), 4)

    @classmethod
    def _claim_premise_score(cls, text: str) -> float:
        normalized = text.lower()
        has_claim = any(marker in normalized for marker in cls._CLAIM_MARKERS)
        has_premise = any(marker in normalized for marker in cls._PREMISE_MARKERS)
        score = 0.0
        if has_claim:
            score += 0.55
        if has_premise:
            score += 0.45
        return round(min(1.0, score), 4)

    def _apply_discourse_coherence_rerank(
        self,
        *,
        query: str,
        chunks: list[Any],
    ) -> tuple[list[Any], dict[str, str]]:
        trace: dict[str, str] = {
            "rag_discourse_enabled": (
                "1" if settings.CLINICAL_CHAT_RAG_DISCOURSE_COHERENCE_ENABLED else "0"
            ),
            "rag_discourse_candidates": str(len(chunks or [])),
        }
        if not chunks:
            trace["rag_discourse_reason"] = "empty_candidates"
            trace["rag_discourse_selected"] = "0"
            return [], trace
        if not settings.CLINICAL_CHAT_RAG_DISCOURSE_COHERENCE_ENABLED:
            trace["rag_discourse_reason"] = "disabled"
            trace["rag_discourse_selected"] = str(len(chunks))
            return chunks, trace

        min_score = float(settings.CLINICAL_CHAT_RAG_DISCOURSE_MIN_SCORE)
        max_satellite_ratio = float(settings.CLINICAL_CHAT_RAG_DISCOURSE_MAX_SATELLITE_RATIO)
        min_lcd_score = float(settings.CLINICAL_CHAT_RAG_DISCOURSE_LCD_MIN_SCORE)
        query_tokens = self._tokenize_for_relevance(query)
        salient_entities = self._extract_salient_entities(query)

        scored_chunks: list[dict[str, Any]] = []
        for chunk in chunks:
            text, section = self._extract_chunk_text_and_section(chunk)
            if not text:
                continue
            edus = self._segment_edus(text, max_units=10)
            retrieval_score = float(getattr(chunk, "_rag_score", 0.0) or 0.0)
            retrieval_score = max(0.0, min(1.0, retrieval_score))
            overlap = self._query_overlap_score(query_tokens=query_tokens, text=text)
            evidence = self._evidence_score(text)
            actionability, _ = self._clinical_actionability_score(
                text=text,
                overlap_score=overlap,
                retrieval_score=retrieval_score,
                evidence_score=evidence,
            )
            rst_role, rst_confidence = self._infer_rst_role(section=section, text=text)
            argument_zone = self._infer_argument_zone(section=section, text=text)
            argument_zone_score = {
                "own_results": 1.00,
                "own_method": 0.88,
                "aim": 0.60,
                "gap_weak": 0.40,
                "none": 0.45,
            }.get(argument_zone, 0.45)
            centering_score = self._entity_centering_score(
                text=text,
                salient_entities=salient_entities,
            )
            lexical_cohesion = self._lexical_cohesion_score(
                query_tokens=query_tokens,
                text=text,
            )
            texttiling_score = self._texttiling_topic_score(
                query_tokens=query_tokens,
                edus=edus,
            )
            lexical_chain_score = self._lexical_chain_cohesion_score(
                query_tokens=query_tokens,
                edus=edus,
            )
            lsa_score = self._lsa_coherence_score(
                query_tokens=query_tokens,
                edus=edus,
            )
            lcd_score = self._local_coherence_discriminator_score(text)
            entity_grid_score = self._entity_grid_coherence_score(
                edus=edus,
                salient_entities=salient_entities,
            )
            claim_premise = self._claim_premise_score(text)
            coherence_score = (
                (0.12 * overlap)
                + (0.12 * evidence)
                + (0.12 * actionability)
                + (0.10 * centering_score)
                + (0.08 * lexical_cohesion)
                + (0.10 * texttiling_score)
                + (0.09 * lexical_chain_score)
                + (0.09 * lsa_score)
                + (0.08 * entity_grid_score)
                + (0.08 * lcd_score)
                + (0.07 * rst_confidence)
                + (0.08 * argument_zone_score)
                + (0.07 * claim_premise)
            )
            coherence_score = round(max(0.0, min(1.0, coherence_score)), 4)
            blended_score = (0.45 * retrieval_score) + (0.55 * coherence_score)
            if rst_role == "satellite":
                blended_score -= 0.10
            if lcd_score < min_lcd_score:
                blended_score -= 0.08
            blended_score = round(max(0.0, min(1.0, blended_score)), 4)
            setattr(chunk, "_rag_discourse_score", float(coherence_score))
            setattr(chunk, "_rag_rst_role", rst_role)
            setattr(chunk, "_rag_argument_zone", argument_zone)
            setattr(chunk, "_rag_lcd_score", float(lcd_score))
            setattr(chunk, "_rag_texttiling_score", float(texttiling_score))
            setattr(chunk, "_rag_lexical_chain_score", float(lexical_chain_score))
            setattr(chunk, "_rag_lsa_score", float(lsa_score))
            setattr(chunk, "_rag_entity_grid_score", float(entity_grid_score))
            setattr(chunk, "_rag_score", float(blended_score))
            scored_chunks.append(
                {
                    "chunk": chunk,
                    "role": rst_role,
                    "coherence": float(coherence_score),
                    "score": float(blended_score),
                    "texttiling": float(texttiling_score),
                    "lexical_chain": float(lexical_chain_score),
                    "lsa": float(lsa_score),
                    "entity_grid": float(entity_grid_score),
                }
            )

        if not scored_chunks:
            trace["rag_discourse_reason"] = "empty_after_scoring"
            trace["rag_discourse_selected"] = "0"
            return [], trace

        scored_chunks.sort(key=lambda item: float(item["score"]), reverse=True)
        satellite_limit = max(1, int(math.ceil(len(scored_chunks) * max_satellite_ratio)))
        filtered: list[Any] = []
        satellite_kept = 0
        satellite_filtered = 0
        low_score_filtered = 0
        for item in scored_chunks:
            role = str(item["role"])
            coherence_score = float(item["coherence"])
            if coherence_score < min_score and filtered:
                low_score_filtered += 1
                continue
            if role == "satellite" and satellite_kept >= satellite_limit and filtered:
                satellite_filtered += 1
                continue
            filtered.append(item["chunk"])
            if role == "satellite":
                satellite_kept += 1

        if not filtered:
            filtered = [scored_chunks[0]["chunk"]]
            trace["rag_discourse_reason"] = "fallback_top1"
        else:
            trace["rag_discourse_reason"] = "ok"

        top_role = str(getattr(filtered[0], "_rag_rst_role", "neutral"))
        top_score = float(getattr(filtered[0], "_rag_discourse_score", 0.0) or 0.0)
        top_texttiling = float(getattr(filtered[0], "_rag_texttiling_score", 0.0) or 0.0)
        top_lexical_chain = float(
            getattr(filtered[0], "_rag_lexical_chain_score", 0.0) or 0.0
        )
        top_lsa = float(getattr(filtered[0], "_rag_lsa_score", 0.0) or 0.0)
        top_entity_grid = float(getattr(filtered[0], "_rag_entity_grid_score", 0.0) or 0.0)
        top_zone = str(getattr(filtered[0], "_rag_argument_zone", "none"))
        trace.update(
            {
                "rag_discourse_selected": str(len(filtered)),
                "rag_discourse_min_score": f"{min_score:.2f}",
                "rag_discourse_lcd_min_score": f"{min_lcd_score:.2f}",
                "rag_discourse_max_satellite_ratio": f"{max_satellite_ratio:.2f}",
                "rag_discourse_satellite_limit": str(satellite_limit),
                "rag_discourse_satellite_kept": str(satellite_kept),
                "rag_discourse_satellite_filtered": str(satellite_filtered),
                "rag_discourse_low_score_filtered": str(low_score_filtered),
                "rag_discourse_top_role": top_role,
                "rag_discourse_top_score": f"{top_score:.3f}",
                "rag_discourse_top_zone": top_zone,
                "rag_discourse_top_texttiling": f"{top_texttiling:.3f}",
                "rag_discourse_top_lexical_chain": f"{top_lexical_chain:.3f}",
                "rag_discourse_top_lsa": f"{top_lsa:.3f}",
                "rag_discourse_top_entity_grid": f"{top_entity_grid:.3f}",
                "rag_discourse_salient_entities": str(len(salient_entities)),
            }
        )
        return filtered, trace

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
        text_token_set = set(text_tokens)
        shared = query_tokens.intersection(text_token_set)
        soft_overlap_excluded = {
            "paciente",
            "pacientes",
            "caso",
            "casos",
            "urgencia",
            "urgencias",
            "accion",
            "acciones",
            "inicial",
            "iniciales",
            "manejo",
            "tratamiento",
        }
        soft_shared = 0
        for query_token in query_tokens:
            if (
                query_token in text_token_set
                or len(query_token) < 5
                or query_token in soft_overlap_excluded
            ):
                continue
            query_prefix = query_token[:5]
            if any(
                len(text_token) >= 5
                and (text_token.startswith(query_prefix) or query_token.startswith(text_token[:5]))
                for text_token in text_token_set
            ):
                soft_shared += 1
                continue
            if any(
                len(text_token) >= 8
                and len(query_token) >= 8
                and text_token[:3] == query_token[:3]
                for text_token in text_token_set
            ):
                soft_shared += 0.5
        if not shared and soft_shared <= 0:
            return 0.0
        # Penalizacion logaritmica suave para queries largas.
        denom = max(1.0, math.log2(2 + len(query_tokens)))
        effective_overlap = len(shared) + (0.7 * soft_shared)
        return round(min(1.0, effective_overlap / denom), 4)

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

    @classmethod
    def _is_generic_operational_query(cls, *, query: str, query_tokens: set[str]) -> bool:
        normalized = str(query or "").lower()
        operational_markers = (
            "pasos",
            "manejo",
            "datos clave",
            "escalado",
            "recomend",
            "que hacer",
            "que podemos hacer",
            "prioridades",
            "valorar",
            "seguimiento",
            "monitorizacion",
            "derivar",
            "urgencias",
        )
        generic_tokens = {
            "paciente",
            "pacientes",
            "dolor",
            "abdominal",
            "abdomen",
            "pecho",
            "ocular",
            "ojo",
            "rodilla",
            "molestias",
            "fiebre",
            "vomitos",
            "nauseas",
            "caso",
            "casos",
            "urgencias",
            "datos",
            "clave",
            "escalado",
            "pasos",
            "manejo",
        }
        marker_hits = sum(1 for marker in operational_markers if marker in normalized)
        specific_tokens = [
            token for token in query_tokens if len(token) >= 6 and token not in generic_tokens
        ]
        return marker_hits >= 1 and len(specific_tokens) <= 2

    @classmethod
    def _operational_source_bias(
        cls,
        *,
        query: str,
        query_tokens: set[str],
        chunk: dict[str, Any],
    ) -> float:
        locator = str(chunk.get("source") or "").lower().replace("\\", "/")
        section = str(chunk.get("section") or "").lower()
        source_title = str(chunk.get("source_title") or "").lower()
        payload = " ".join(item for item in [locator, section, source_title] if item)
        operational_markers = (
            "motor operativo",
            "urgencias",
            "prioridad",
            "prioridades",
            "pasos",
            "algoritmo",
            "manejo",
            "escalado",
            "bundle",
            "ruta",
            "monitor",
            "evaluacion",
            "reevalu",
            "red flags",
        )
        source_focus = cls._query_overlap_score(
            query_tokens=query_tokens,
            text=f"{source_title} {section}",
        )
        generic_operational_query = cls._is_generic_operational_query(
            query=query,
            query_tokens=query_tokens,
        )

        bias = 0.0
        if locator.startswith("docs/") and "docs/pdf_raw/" not in locator:
            bias += 0.12
        if any(marker in payload for marker in operational_markers):
            bias += 0.12
        bias += min(0.08, source_focus * 0.10)
        if "docs/pdf_raw/" in locator:
            bias -= 0.04
            if generic_operational_query and not any(
                marker in payload for marker in operational_markers
            ):
                bias -= 0.18
            if generic_operational_query and source_focus < 0.18:
                bias -= 0.08
        return round(max(-0.28, min(0.28, bias)), 4)

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
            compact_text = re.sub(
                r"\bdocs[\\/][^\s)]+",
                "",
                compact_text,
                flags=re.IGNORECASE,
            )
            compact_text = re.sub(
                r"(?:[A-Za-z]:)?[\\/](?:[^\\/\s]+[\\/])+[^\\/\s]+(?:\.(?:md|txt|pdf))?",
                "",
                compact_text,
                flags=re.IGNORECASE,
            )
            compact_text = re.sub(r"\s{2,}", " ", compact_text).strip()
            return compact_text[:max_chars]
        merged = " ".join(kept).strip()
        merged = re.sub(
            r"\bdocs[\\/][^\s)]+",
            "",
            merged,
            flags=re.IGNORECASE,
        )
        merged = re.sub(
            r"(?:[A-Za-z]:)?[\\/](?:[^\\/\s]+[\\/])+[^\\/\s]+(?:\.(?:md|txt|pdf))?",
            "",
            merged,
            flags=re.IGNORECASE,
        )
        merged = re.sub(r"\s{2,}", " ", merged).strip()
        return merged[:max_chars]

    @classmethod
    def _apply_ecorag_evidential_reflection(
        cls,
        *,
        query: str,
        chunks: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], dict[str, str]]:
        trace: dict[str, str] = {
            "rag_ecorag_enabled": "1" if settings.CLINICAL_CHAT_RAG_ECORAG_ENABLED else "0"
        }
        if not chunks:
            trace["rag_ecorag_selected"] = "0"
            trace["rag_ecorag_resolved"] = "0"
            trace["rag_ecorag_reason"] = "empty_chunks"
            return [], trace

        if not settings.CLINICAL_CHAT_RAG_ECORAG_ENABLED:
            trace["rag_ecorag_selected"] = str(len(chunks))
            trace["rag_ecorag_resolved"] = "1"
            trace["rag_ecorag_reason"] = "disabled"
            return chunks, trace

        threshold = float(settings.CLINICAL_CHAT_RAG_ECORAG_MIN_EVIDENTIALITY)
        min_chunks = max(1, int(settings.CLINICAL_CHAT_RAG_ECORAG_MIN_CHUNKS))
        min_chunks = min(min_chunks, len(chunks))
        trace["rag_ecorag_threshold"] = f"{threshold:.2f}"
        trace["rag_ecorag_min_chunks"] = str(min_chunks)
        trace["rag_ecorag_candidates"] = str(len(chunks))

        query_tokens = cls._tokenize_for_relevance(query)
        ranked: list[dict[str, Any]] = []
        for chunk in chunks:
            text = cls._clean_snippet_text(str(chunk.get("text") or ""), max_chars=320)
            if not text:
                continue
            retrieval = max(0.0, min(1.0, float(chunk.get("score") or 0.0)))
            overlap = cls._query_overlap_score(query_tokens=query_tokens, text=text)
            evidence = cls._evidence_score(text)
            actionability, _aux_ratio = cls._clinical_actionability_score(
                text=text,
                overlap_score=overlap,
                retrieval_score=retrieval,
                evidence_score=evidence,
            )
            tokens = cls._tokenize_for_relevance(text)
            base_score = (
                (0.35 * overlap)
                + (0.25 * evidence)
                + (0.20 * retrieval)
                + (0.20 * actionability)
            )
            ranked.append(
                {
                    "chunk": chunk,
                    "tokens": tokens,
                    "base_score": round(base_score, 4),
                }
            )

        if not ranked:
            trace["rag_ecorag_selected"] = "0"
            trace["rag_ecorag_resolved"] = "0"
            trace["rag_ecorag_reason"] = "no_ranked_candidates"
            return [], trace

        ranked.sort(key=lambda item: float(item["base_score"]), reverse=True)
        selected: list[dict[str, Any]] = []
        selected_token_union: set[str] = set()
        evidentiality = 0.0

        for candidate in ranked:
            candidate_tokens = set(candidate.get("tokens") or set())
            redundancy = 0.0
            if selected:
                redundancy = max(
                    cls._jaccard_similarity(
                        candidate_tokens,
                        set(item.get("tokens") or set()),
                    )
                    for item in selected
                )
            marginal_score = float(candidate["base_score"]) - (0.20 * redundancy)
            if marginal_score <= 0.04 and len(selected) >= min_chunks:
                continue
            selected.append(candidate)
            selected_token_union.update(candidate_tokens)
            avg_base = sum(float(item["base_score"]) for item in selected) / max(1, len(selected))
            query_coverage = 0.0
            if query_tokens:
                query_coverage = len(selected_token_union.intersection(query_tokens)) / max(
                    1,
                    len(query_tokens),
                )
            evidentiality = (0.75 * avg_base) + (0.25 * query_coverage)
            if len(selected) >= min_chunks and evidentiality >= threshold:
                break

        if len(selected) < min_chunks:
            selected_ids = {id(item["chunk"]) for item in selected}
            for candidate in ranked:
                if id(candidate["chunk"]) in selected_ids:
                    continue
                selected.append(candidate)
                if len(selected) >= min_chunks:
                    break

        selected_chunks = [dict(item["chunk"]) for item in selected]
        if not selected_chunks:
            selected_chunks = chunks[:min_chunks]
        trace["rag_ecorag_selected"] = str(len(selected_chunks))
        trace["rag_ecorag_evidentiality_score"] = f"{evidentiality:.3f}"
        trace["rag_ecorag_resolved"] = (
            "1"
            if len(selected_chunks) >= min_chunks and evidentiality >= threshold
            else "0"
        )
        trace["rag_ecorag_reason"] = (
            "threshold_met"
            if trace["rag_ecorag_resolved"] == "1"
            else "min_chunks_backfill"
        )
        return selected_chunks, trace

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
        normalized_query = str(query or "").strip().lower()
        generic_operational_query = cls._is_generic_operational_query(
            query=query,
            query_tokens=query_tokens,
        )
        action_focus_enabled = bool(settings.CLINICAL_CHAT_RAG_ACTION_FOCUS_ENABLED)
        action_min_score = float(settings.CLINICAL_CHAT_RAG_ACTION_MIN_SCORE)
        action_max_aux_ratio = float(settings.CLINICAL_CHAT_RAG_ACTION_MAX_AUX_RATIO)
        sentence_candidates: list[dict[str, Any]] = []
        sentence_candidates_relaxed: list[dict[str, Any]] = []
        for chunk in chunks[: max_items * 4]:
            cleaned = cls._clean_snippet_text(str(chunk.get("text") or ""), max_chars=260)
            retrieval_score = float(chunk.get("score") or 0.0)
            retrieval_score = max(0.0, min(1.0, retrieval_score))
            source_bias = cls._operational_source_bias(
                query=query,
                query_tokens=query_tokens,
                chunk=chunk,
            )
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
                if generic_operational_query and not any(
                    marker in normalized_query
                    for marker in cls._GENERIC_CLINICAL_SPECIFICITY_MARKERS
                ):
                    normalized_sentence = str(sentence or "").strip().lower()
                    specificity_penalty = sum(
                        0.08
                        for marker in cls._GENERIC_CLINICAL_SPECIFICITY_MARKERS
                        if marker in normalized_sentence
                    )
                    neutral_bonus = sum(
                        0.05
                        for marker in (
                            "constantes",
                            "signos de alarma",
                            "exploracion abdominal",
                            "signos peritoneales",
                            "analitica",
                            "imagen",
                            "reevaluacion",
                            "escalado",
                        )
                        if marker in normalized_sentence
                    )
                    relevance = max(0.0, relevance - specificity_penalty + neutral_bonus)
                actionability, aux_ratio = cls._clinical_actionability_score(
                    text=sentence,
                    overlap_score=overlap,
                    retrieval_score=retrieval_score,
                    evidence_score=evidence,
                )
                source_adjusted_relevance = round(
                    max(0.0, min(1.0, relevance + source_bias)),
                    4,
                )
                candidate = {
                    "text": sentence.rstrip(" .") + ".",
                    "tokens": cls._tokenize_for_relevance(sentence),
                    "retrieval": retrieval_score,
                    "overlap": overlap,
                    "extractive_relevance": round(extractive_relevance, 4),
                    "generative_proxy": generative_proxy,
                    "relevance": round(relevance, 4),
                    "source_adjusted_relevance": source_adjusted_relevance,
                    "source_bias": source_bias,
                    "evidence": evidence,
                    "actionability": actionability,
                    "aux_ratio": aux_ratio,
                }
                sentence_candidates_relaxed.append(candidate)
                if action_focus_enabled:
                    if actionability < action_min_score:
                        continue
                    if (
                        aux_ratio > action_max_aux_ratio
                        and actionability < (action_min_score + 0.12)
                    ):
                        continue
                if generic_operational_query and source_bias < -0.18 and overlap < 0.34:
                    continue
                sentence_candidates.append(candidate)

        if not sentence_candidates:
            if sentence_candidates_relaxed:
                sentence_candidates = sentence_candidates_relaxed[:]
            else:
                return None
        if not sentence_candidates:
            return None

        # Stage 1: relevancia (consulta -> evidencia candidata)
        stage1 = sorted(
            sentence_candidates,
            key=lambda item: float(item.get("source_adjusted_relevance", item["relevance"])),
            reverse=True,
        )[: max_items * 4]

        # Stage 2: evidencia util (accionabilidad)
        for item in stage1:
            item["evidence_rank_score"] = round(
                (0.47 * float(item.get("source_adjusted_relevance", item["relevance"])))
                + (0.25 * float(item["evidence"]))
                + (0.18 * float(item.get("actionability", 0.0)))
                + (0.10 * max(0.0, float(item.get("source_bias", 0.0)))),
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
                + (0.05 * float(item.get("actionability", 0.0)))
                + (0.04 * float(item.get("source_bias", 0.0))),
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
            source_title = str(chunk.get("source_title") or "").strip()
            source_page = str(chunk.get("source_page") or "").strip()
            if not source or source in seen_sources:
                continue
            source_norm = source.lower().replace("\\", "/")
            if "/api/" in source_norm or source_norm.startswith("app/"):
                continue
            if cls._looks_like_non_clinical_source(source):
                continue
            seen_sources.add(source)
            anchor = source_title or section
            if section and anchor.lower() != section.lower():
                anchor = f"{anchor} > {section}"
            if source_page:
                anchor = f"{anchor} [p.{source_page}]"
            lines.append(f"- {anchor}")
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
            if locator.startswith("docs/"):
                if "docs/pdf_raw/" in locator:
                    return (1, -len(title))
                return (0, -len(title))
            return (2, -len(title))

        def ranking_key(chunk: dict[str, Any]) -> tuple[float, int, int]:
            score = float(chunk.get("score") or 0.0)
            source_rank, title_rank = source_priority(chunk)
            # Prioriza relevancia de retrieval y usa tipo de fuente como desempate.
            return (-score, source_rank, title_rank)

        prioritized_chunks = sorted(chunks, key=ranking_key)
        sources: list[dict[str, str]] = []
        for chunk in prioritized_chunks[: settings.CLINICAL_CHAT_RAG_MAX_CHUNKS]:
            source_locator = str(chunk.get("source") or "catalogo interno")
            if self._looks_like_non_clinical_source(source_locator):
                continue
            snippet = self._clean_snippet_text(str(chunk.get("text", "")), max_chars=320)
            if len(snippet) < 20:
                continue
            if len(snippet) > 320:
                snippet = f"{snippet[:320]}..."
            section = str(chunk.get("section") or "fragmento interno").strip()
            source_title = str(chunk.get("source_title") or "").strip()
            page_hint = str(chunk.get("source_page") or "").strip()
            title = source_title or section
            if section and title.lower() != section.lower():
                title = f"{title} > {section}"
            if page_hint:
                title = f"{title} [p.{page_hint}]"
            source = {
                "type": "rag_chunk",
                "title": title or "fragmento interno",
                "source": source_locator,
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
