"""
Servicio de chat clinico-operativo.
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.care_task import CareTask
from app.models.care_task_chat_message import CareTaskChatMessage
from app.models.clinical_knowledge_source import ClinicalKnowledgeSource
from app.models.user import User
from app.schemas.clinical_chat import CareTaskClinicalChatMessageRequest
from app.schemas.critical_ops_protocol import CriticalOpsProtocolRequest
from app.schemas.scasest_protocol import ScasestProtocolRequest
from app.schemas.sepsis_protocol import SepsisProtocolRequest
from app.services.agent_run_service import AgentRunService
from app.services.critical_ops_protocol_service import CriticalOpsProtocolService
from app.services.knowledge_source_service import KnowledgeSourceService
from app.services.llm_chat_provider import LLMChatProvider
from app.services.scasest_protocol_service import ScasestProtocolService
from app.services.sepsis_protocol_service import SepsisProtocolService


class ClinicalChatService:
    """Motor de chat operativo con memoria incremental y trazabilidad."""

    _DOMAIN_CATALOG: list[dict[str, object]] = [
        {
            "key": "critical_ops",
            "label": "Operativa critica transversal",
            "endpoint": "/api/v1/care-tasks/{task_id}/critical-ops/recommendation",
            "summary": "SLA criticos, oxigenoterapia y red flags.",
            "keywords": ["sla", "ecg", "triaje", "shock", "bipap", "cpap"],
        },
        {
            "key": "sepsis",
            "label": "Sepsis",
            "endpoint": "/api/v1/care-tasks/{task_id}/sepsis/recommendation",
            "summary": "Bundle de sepsis y escalado hemodinamico.",
            "keywords": ["sepsis", "lactato", "qsofa", "noradrenalina"],
        },
        {
            "key": "scasest",
            "label": "SCASEST",
            "endpoint": "/api/v1/care-tasks/{task_id}/scasest/recommendation",
            "summary": "Riesgo SCASEST y escalado cardiologico.",
            "keywords": ["scasest", "troponina", "grace", "angina"],
        },
        {
            "key": "resuscitation",
            "label": "Reanimacion y soporte vital",
            "endpoint": "/api/v1/care-tasks/{task_id}/resuscitation/recommendation",
            "summary": "BLS/ACLS, via aerea y ritmos.",
            "keywords": ["rcp", "acls", "desfibrilacion", "cardioversion", "rosc"],
        },
        {
            "key": "medicolegal",
            "label": "Medico-legal",
            "endpoint": "/api/v1/care-tasks/{task_id}/medicolegal/recommendation",
            "summary": "Consentimiento, custodia y bioetica.",
            "keywords": ["consentimiento", "custodia", "bioetica", "menor", "transfusion"],
        },
        {
            "key": "neurology",
            "label": "Neurologia",
            "endpoint": "/api/v1/care-tasks/{task_id}/neurology/recommendation",
            "summary": "Codigo ictus y diferenciales neurocriticos.",
            "keywords": ["ictus", "hsa", "aspects", "trombectomia", "miastenia"],
        },
    ]
    _SPECIALTY_FALLBACK = {
        "emergency": "critical_ops",
        "emergencias": "critical_ops",
        "icu": "resuscitation",
        "cardiology": "scasest",
        "cardiologia": "scasest",
        "neurology": "neurology",
    }
    _DOMAIN_KNOWLEDGE_INDEX: dict[str, list[dict[str, str]]] = {
        "critical_ops": [
            {
                "source": "docs/66_motor_operativo_critico_transversal_urgencias.md",
                "title": "Motor critico transversal",
            }
        ],
        "sepsis": [
            {"source": "docs/47_motor_sepsis_urgencias.md", "title": "Bundle de sepsis"}
        ],
        "scasest": [
            {"source": "docs/49_motor_scasest_urgencias.md", "title": "Soporte SCASEST"}
        ],
        "resuscitation": [
            {
                "source": "docs/58_motor_reanimacion_soporte_vital_urgencias.md",
                "title": "Reanimacion avanzada",
            }
        ],
        "medicolegal": [
            {
                "source": "docs/45_motor_medico_legal_urgencias.md",
                "title": "Soporte medico-legal",
            }
        ],
        "neurology": [
            {"source": "docs/67_motor_operativo_neurologia_urgencias.md", "title": "Neurologia"}
        ],
    }
    _FACT_UNITS_PATTERN = re.compile(
        r"\b\d+(?:[.,]\d+)?\s*(?:mmhg|mg/dl|mmol/l|lpm|%|h|horas|min|ml/kg|cmh2o|ng/ml)\b",
        flags=re.IGNORECASE,
    )
    _FACT_COMPARATOR_PATTERN = re.compile(r"(?:>=|<=|>|<)\s*\d+(?:[.,]\d+)?", flags=re.IGNORECASE)
    _TOKEN_PATTERN = re.compile(r"[a-z0-9]{3,}", flags=re.IGNORECASE)
    _CLINICAL_TERMS = [
        "sepsis",
        "shock",
        "scasest",
        "ictus",
        "hsa",
        "cpap",
        "bipap",
        "consentimiento",
        "rechaza",
        "alergia",
    ]
    _CLINICAL_TOOL_MODES = {"medication", "cases", "treatment", "images"}
    _NON_CLINICAL_MEMORY_PREFIXES = ("modo_respuesta:", "herramienta:")
    _FOLLOW_UP_HINTS = (
        "y ahora",
        "y si",
        "si empeora",
        "resume",
        "reformula",
        "amplia",
        "detalla",
        "que hago",
        "siguiente",
        "continuamos",
    )
    _DOC_CHUNK_CACHE: dict[str, list[str]] = {}

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        return normalized.lower().strip()

    @classmethod
    def _tokenize(cls, text: str) -> set[str]:
        return {token for token in cls._TOKEN_PATTERN.findall(cls._normalize(text))}

    @staticmethod
    def _safe_session_id(raw_session_id: str | None) -> str:
        return raw_session_id or f"chat-{uuid4().hex[:12]}"

    @classmethod
    def _domain_by_key(cls) -> dict[str, dict[str, object]]:
        return {str(item["key"]): item for item in cls._DOMAIN_CATALOG}

    @classmethod
    def _resolve_effective_specialty(
        cls,
        *,
        payload: CareTaskClinicalChatMessageRequest,
        care_task: CareTask,
        authenticated_user: User | None,
    ) -> str:
        if payload.use_authenticated_specialty_mode and authenticated_user is not None:
            specialty = cls._normalize(authenticated_user.specialty or "")
            if specialty:
                return specialty
        if payload.specialty_hint:
            return cls._normalize(payload.specialty_hint)
        return cls._normalize(care_task.specialty or "general")

    @classmethod
    def _match_domains(
        cls,
        *,
        query: str,
        effective_specialty: str,
        max_domains: int = 3,
    ) -> list[dict[str, object]]:
        normalized_query = cls._normalize(query)
        scored: list[tuple[int, dict[str, object]]] = []
        for domain in cls._DOMAIN_CATALOG:
            score = sum(
                1
                for keyword in domain.get("keywords", [])
                if cls._normalize(str(keyword)) in normalized_query
            )
            if score > 0:
                scored.append((score, domain))
        fallback_key = cls._SPECIALTY_FALLBACK.get(effective_specialty, "critical_ops")
        fallback_domain = cls._domain_by_key().get(fallback_key)
        if scored:
            scored.sort(key=lambda item: item[0], reverse=True)
            domains = [item[1] for item in scored]
            if fallback_domain is not None and fallback_domain not in domains:
                domains.insert(0, fallback_domain)
            return domains[:max_domains]
        return [fallback_domain] if fallback_domain is not None else []

    @classmethod
    def _count_domain_keyword_hits(cls, query: str) -> int:
        normalized_query = cls._normalize(query)
        hits = 0
        for domain in cls._DOMAIN_CATALOG:
            for keyword in domain.get("keywords", []):
                if cls._normalize(str(keyword)) in normalized_query:
                    hits += 1
        return hits

    @classmethod
    def _has_clinical_signal(
        cls,
        *,
        query: str,
        extracted_facts: list[str],
        keyword_hits: int,
    ) -> bool:
        if keyword_hits > 0:
            return True
        if any(
            fact.startswith("umbral:") or fact.startswith("comparador:")
            for fact in extracted_facts
        ):
            return True
        if any(fact.startswith("termino:") for fact in extracted_facts):
            return True
        normalized_query = cls._normalize(query)
        return any(term in normalized_query for term in cls._CLINICAL_TERMS)

    @classmethod
    def _resolve_response_mode(
        cls,
        *,
        payload: CareTaskClinicalChatMessageRequest,
        query: str,
        extracted_facts: list[str],
        keyword_hits: int,
    ) -> str:
        if payload.conversation_mode == "general":
            return "general"
        if payload.conversation_mode == "clinical":
            return "clinical"
        if payload.tool_mode == "deep_search":
            return "general"
        if payload.tool_mode in cls._CLINICAL_TOOL_MODES:
            return "clinical"
        if cls._has_clinical_signal(
            query=query,
            extracted_facts=extracted_facts,
            keyword_hits=keyword_hits,
        ):
            return "clinical"
        return "general"

    @classmethod
    def _extract_facts(cls, query: str) -> list[str]:
        normalized_query = cls._normalize(query)
        facts: list[str] = []
        for match in cls._FACT_UNITS_PATTERN.findall(query):
            facts.append(f"umbral:{cls._normalize(match).replace(' ', '')}")
        for match in cls._FACT_COMPARATOR_PATTERN.findall(query):
            facts.append(f"comparador:{cls._normalize(match).replace(' ', '')}")
        if "rechaza" in normalized_query:
            facts.append("decision:rechazo_tratamiento")
        if "familiar" in normalized_query or "acompan" in normalized_query:
            facts.append("contexto:acompanante_presente")
        if "consentimiento" in normalized_query:
            facts.append("legal:consentimiento_mencionado")
        if "alerg" in normalized_query:
            facts.append("seguridad:alergia_reportada")
        for term in cls._CLINICAL_TERMS:
            if term in normalized_query:
                facts.append(f"termino:{term}")
        unique_facts: list[str] = []
        for fact in facts:
            if fact not in unique_facts:
                unique_facts.append(fact)
        return unique_facts[:16]

    @classmethod
    def _filter_memory_fact(cls, fact: str) -> bool:
        normalized = cls._normalize(fact)
        return not normalized.startswith(cls._NON_CLINICAL_MEMORY_PREFIXES)

    @classmethod
    def _compose_effective_query(
        cls,
        *,
        query: str,
        recent_dialogue: list[dict[str, str]],
    ) -> tuple[str, bool]:
        normalized_query = cls._normalize(query)
        query_tokens = cls._tokenize(query)
        if not recent_dialogue:
            return query, False
        is_follow_up = len(query_tokens) <= 8 or any(
            hint in normalized_query for hint in cls._FOLLOW_UP_HINTS
        )
        if not is_follow_up:
            return query, False
        last_user_query = (recent_dialogue[-1].get("user_query") or "").strip()
        if not last_user_query:
            return query, False
        effective_query = f"{last_user_query}. Seguimiento: {query}"
        return effective_query, True

    @staticmethod
    def _list_recent_messages(
        db: Session,
        *,
        care_task_id: int,
        session_id: str | None,
        limit: int,
    ) -> list[CareTaskChatMessage]:
        safe_limit = max(0, min(limit, 100))
        if safe_limit == 0:
            return []
        query = db.query(CareTaskChatMessage).filter(
            CareTaskChatMessage.care_task_id == care_task_id
        )
        if session_id is not None:
            query = query.filter(CareTaskChatMessage.session_id == session_id)
        return (
            query.order_by(CareTaskChatMessage.created_at.desc(), CareTaskChatMessage.id.desc())
            .limit(safe_limit)
            .all()
        )

    @staticmethod
    def _list_patient_messages(
        db: Session,
        *,
        patient_reference: str,
        limit: int,
    ) -> list[CareTaskChatMessage]:
        safe_limit = max(0, min(limit, 300))
        if safe_limit == 0:
            return []
        return (
            db.query(CareTaskChatMessage)
            .join(CareTask, CareTask.id == CareTaskChatMessage.care_task_id)
            .filter(CareTask.patient_reference == patient_reference)
            .order_by(CareTaskChatMessage.created_at.desc(), CareTaskChatMessage.id.desc())
            .limit(safe_limit)
            .all()
        )

    @staticmethod
    def list_messages(
        db: Session,
        *,
        care_task_id: int,
        session_id: str | None,
        limit: int,
    ) -> list[CareTaskChatMessage]:
        safe_limit = max(1, min(limit, 200))
        query = db.query(CareTaskChatMessage).filter(
            CareTaskChatMessage.care_task_id == care_task_id
        )
        if session_id is not None:
            query = query.filter(CareTaskChatMessage.session_id == session_id)
        return (
            query.order_by(CareTaskChatMessage.created_at.desc(), CareTaskChatMessage.id.desc())
            .limit(safe_limit)
            .all()
        )

    @classmethod
    def _build_patient_summary(
        cls,
        db: Session,
        *,
        patient_reference: str | None,
        max_messages: int,
    ) -> dict[str, Any] | None:
        if not patient_reference:
            return None
        messages = cls._list_patient_messages(
            db,
            patient_reference=patient_reference,
            limit=max_messages,
        )
        domain_counter: Counter[str] = Counter()
        fact_counter: Counter[str] = Counter()
        encounter_counter: Counter[int] = Counter()
        for message in messages:
            domain_counter.update(message.matched_domains or [])
            fact_counter.update(message.extracted_facts or [])
            encounter_counter.update([message.care_task_id])
        return {
            "patient_reference": patient_reference,
            "patient_interactions_count": len(messages),
            "patient_encounters_count": len(encounter_counter),
            "patient_top_domains": [item for item, _ in domain_counter.most_common(5)],
            "patient_top_extracted_facts": [item for item, _ in fact_counter.most_common(10)],
        }

    @classmethod
    def summarize_memory(
        cls,
        db: Session,
        *,
        care_task_id: int,
        session_id: str | None,
        limit: int = 200,
    ) -> dict[str, object]:
        messages = cls.list_messages(
            db,
            care_task_id=care_task_id,
            session_id=session_id,
            limit=limit,
        )
        domain_counter: Counter[str] = Counter()
        fact_counter: Counter[str] = Counter()
        for message in messages:
            domain_counter.update(message.matched_domains or [])
            fact_counter.update(message.extracted_facts or [])
        summary: dict[str, object] = {
            "interactions_count": len(messages),
            "top_domains": [domain for domain, _ in domain_counter.most_common(5)],
            "top_extracted_facts": [fact for fact, _ in fact_counter.most_common(10)],
            "patient_reference": None,
            "patient_interactions_count": 0,
            "patient_top_domains": [],
            "patient_top_extracted_facts": [],
        }
        care_task = db.query(CareTask).filter(CareTask.id == care_task_id).first()
        if care_task is None:
            return summary
        patient_summary = cls._build_patient_summary(
            db,
            patient_reference=care_task.patient_reference,
            max_messages=min(limit, 300),
        )
        if patient_summary is None:
            return summary
        summary["patient_reference"] = patient_summary["patient_reference"]
        summary["patient_interactions_count"] = patient_summary["patient_interactions_count"]
        summary["patient_top_domains"] = patient_summary["patient_top_domains"]
        summary["patient_top_extracted_facts"] = patient_summary["patient_top_extracted_facts"]
        return summary

    @classmethod
    def _load_doc_chunks(cls, source_path: str) -> list[str]:
        if source_path in cls._DOC_CHUNK_CACHE:
            return cls._DOC_CHUNK_CACHE[source_path]
        root = Path(__file__).resolve().parents[2]
        full_path = root / source_path
        if not full_path.exists():
            cls._DOC_CHUNK_CACHE[source_path] = []
            return []
        raw_text = full_path.read_text(encoding="utf-8", errors="ignore")
        paragraphs = re.split(r"\n\s*\n", raw_text)
        chunks: list[str] = []
        for paragraph in paragraphs:
            compact = " ".join(paragraph.split())
            if len(compact) < 40:
                continue
            chunks.append(compact[:620])
        cls._DOC_CHUNK_CACHE[source_path] = chunks[:250]
        return cls._DOC_CHUNK_CACHE[source_path]

    @classmethod
    def _build_catalog_knowledge_sources(
        cls,
        *,
        query: str,
        matched_domains: list[dict[str, object]],
        max_internal_sources: int,
    ) -> list[dict[str, str]]:
        query_tokens = cls._tokenize(query)
        ranked: list[tuple[int, dict[str, str]]] = []
        for domain in matched_domains:
            domain_key = str(domain["key"])
            for reference in cls._DOMAIN_KNOWLEDGE_INDEX.get(domain_key, []):
                source_path = reference["source"]
                best_score = 0
                best_chunk = ""
                for chunk in cls._load_doc_chunks(source_path):
                    score = len(query_tokens.intersection(cls._tokenize(chunk)))
                    if score > best_score:
                        best_score = score
                        best_chunk = chunk
                if best_score == 0:
                    continue
                ranked.append(
                    (
                        best_score,
                        {
                            "type": "internal_catalog",
                            "domain": domain_key,
                            "title": reference["title"],
                            "source": source_path,
                            "snippet": best_chunk[:280],
                        },
                    )
                )
        ranked.sort(key=lambda item: item[0], reverse=True)
        unique: list[dict[str, str]] = []
        seen_keys: set[str] = set()
        for _, source in ranked:
            key = f"{source['domain']}::{source['source']}"
            if key in seen_keys:
                continue
            seen_keys.add(key)
            unique.append(source)
            if len(unique) >= max_internal_sources:
                break
        if unique:
            return unique
        return [
            {
                "type": "internal_catalog",
                "domain": str(domain["key"]),
                "title": str(domain["label"]),
                "source": "domain_catalog",
                "snippet": str(domain["summary"])[:280],
            }
            for domain in matched_domains[:max_internal_sources]
        ]

    @staticmethod
    def _source_is_active(source: ClinicalKnowledgeSource) -> bool:
        if source.expires_at is None:
            return True
        return source.expires_at >= datetime.now(timezone.utc)

    @classmethod
    def _build_validated_knowledge_sources(
        cls,
        db: Session,
        *,
        query: str,
        effective_specialty: str,
        matched_domains: list[dict[str, object]],
        max_internal_sources: int,
    ) -> list[dict[str, str]]:
        safe_limit = max(1, min(max_internal_sources * 20, 400))
        candidate_specialties = [effective_specialty, "general"]
        query_tokens = cls._tokenize(query)
        domain_tokens = {cls._normalize(str(domain["key"])) for domain in matched_domains}
        sources = (
            db.query(ClinicalKnowledgeSource)
            .filter(ClinicalKnowledgeSource.status == "validated")
            .filter(ClinicalKnowledgeSource.specialty.in_(candidate_specialties))
            .order_by(
                ClinicalKnowledgeSource.updated_at.desc(),
                ClinicalKnowledgeSource.id.desc(),
            )
            .limit(safe_limit)
            .all()
        )
        ranked: list[tuple[int, dict[str, str]]] = []
        for source in sources:
            if not cls._source_is_active(source):
                continue
            corpus = " ".join(
                part
                for part in [
                    source.title or "",
                    source.summary or "",
                    source.content or "",
                    " ".join(source.tags or []),
                    source.specialty or "",
                ]
                if part
            )
            source_tokens = cls._tokenize(corpus)
            score = len(query_tokens.intersection(source_tokens))
            if source.specialty == effective_specialty:
                score += 2
            for token in domain_tokens:
                if token and token in source_tokens:
                    score += 1
            if score <= 0:
                continue
            ranked.append(
                (
                    score,
                    {
                        "type": "internal_validated",
                        "domain": source.specialty,
                        "title": source.title,
                        "source": (
                            source.source_url
                            or source.source_path
                            or f"knowledge:{source.id}"
                        ),
                        "snippet": (source.summary or source.content or "")[:280],
                    },
                )
            )
        ranked.sort(key=lambda item: item[0], reverse=True)
        unique: list[dict[str, str]] = []
        seen: set[str] = set()
        for _, source in ranked:
            key = f"{source['domain']}::{source['source']}"
            if key in seen:
                continue
            seen.add(key)
            unique.append(source)
            if len(unique) >= max_internal_sources:
                break
        return unique

    @staticmethod
    def _extract_duckduckgo_topics(raw_topics: list[dict[str, Any]]) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        for topic in raw_topics:
            nested_topics = topic.get("Topics")
            if isinstance(nested_topics, list):
                results.extend(ClinicalChatService._extract_duckduckgo_topics(nested_topics))
                continue
            title = str(topic.get("Text") or "").strip()
            url = str(topic.get("FirstURL") or "").strip()
            if title and url:
                domain = (urlparse(url).hostname or "").lower()
                results.append(
                    {
                        "type": "web",
                        "title": title[:180],
                        "source": "duckduckgo",
                        "url": url,
                        "domain": domain,
                        "snippet": title[:280],
                    }
                )
        return results

    @staticmethod
    def _fetch_web_sources(query: str, max_web_sources: int) -> list[dict[str, str]]:
        if not settings.CLINICAL_CHAT_WEB_ENABLED:
            return []
        try:
            encoded_query = quote_plus(query)
            url = (
                "https://duckduckgo.com/?q="
                f"{encoded_query}&format=json&no_html=1&no_redirect=1&skip_disambig=1"
            )
            request = Request(url=url, headers={"User-Agent": "clinical-chat/1.0"})
            with urlopen(
                request,
                timeout=max(1, int(settings.CLINICAL_CHAT_WEB_TIMEOUT_SECONDS)),
            ) as response:
                payload = json.loads(response.read().decode("utf-8", errors="ignore"))
        except (URLError, ValueError, TimeoutError):
            return []

        collected: list[dict[str, str]] = []
        abstract_text = str(payload.get("AbstractText") or "").strip()
        abstract_url = str(payload.get("AbstractURL") or "").strip()
        heading = str(payload.get("Heading") or "DuckDuckGo result").strip()
        if abstract_text and abstract_url:
            abstract_domain = (urlparse(abstract_url).hostname or "").lower()
            collected.append(
                {
                    "type": "web",
                    "title": heading[:180],
                    "source": "duckduckgo",
                    "url": abstract_url,
                    "domain": abstract_domain,
                    "snippet": abstract_text[:280],
                }
            )
        related_topics = payload.get("RelatedTopics", [])
        if isinstance(related_topics, list):
            collected.extend(ClinicalChatService._extract_duckduckgo_topics(related_topics))
        unique: list[dict[str, str]] = []
        seen_urls: set[str] = set()
        for item in collected:
            domain = item.get("domain", "")
            if not KnowledgeSourceService.is_allowed_domain(domain):
                continue
            if item["url"] in seen_urls:
                continue
            seen_urls.add(item["url"])
            unique.append(item)
            if len(unique) >= max_web_sources:
                break
        return unique

    @staticmethod
    def _fetch_recommendations(
        *,
        query: str,
        matched_endpoints: list[str],
    ) -> list[dict[str, Any]]:
        normalized_query = ClinicalChatService._normalize(query)
        results: list[dict[str, Any]] = []
        for endpoint in matched_endpoints:
            recommendation: dict[str, Any] | None = None
            if endpoint.endswith('/critical-ops/recommendation'):
                recommendation = CriticalOpsProtocolService.build_recommendation(
                    CriticalOpsProtocolRequest(
                        suspected_septic_shock='sepsis' in normalized_query,
                        non_traumatic_chest_pain='torac' in normalized_query,
                        triage_level='rojo' if 'shock' in normalized_query else 'amarillo',
                    )
                ).model_dump()
            elif endpoint.endswith('/sepsis/recommendation'):
                recommendation = SepsisProtocolService.build_recommendation(
                    SepsisProtocolRequest(
                        suspected_infection=True,
                        lactate_mmol_l=4.0 if 'lactato' in normalized_query else None,
                        systolic_bp=(
                            85
                            if 'tas' in normalized_query or 'shock' in normalized_query
                            else None
                        ),
                    )
                ).model_dump()
            elif endpoint.endswith('/scasest/recommendation'):
                recommendation = ScasestProtocolService.build_recommendation(
                    ScasestProtocolRequest(
                        chest_pain_typical='torac' in normalized_query,
                        troponin_positive='troponina' in normalized_query,
                        hemodynamic_instability='shock' in normalized_query,
                    )
                ).model_dump()
            if recommendation is None:
                continue
            results.append(
                {
                    'type': 'internal_recommendation',
                    'endpoint': endpoint,
                    'title': f"Recomendacion sintetizada {endpoint.split('/')[-2]}",
                    'source': endpoint,
                    'snippet': json.dumps(recommendation, ensure_ascii=False)[:300],
                    'recommendation': recommendation,
                }
            )
        return results

    @staticmethod
    def _render_clinical_answer(
        *,
        care_task: CareTask,
        query: str,
        matched_domains: list[dict[str, object]],
        matched_endpoints: list[str],
        effective_specialty: str,
        memory_facts_used: list[str],
        patient_summary: dict[str, Any] | None,
        patient_history_facts_used: list[str],
        extracted_facts: list[str],
        knowledge_sources: list[dict[str, str]],
        web_sources: list[dict[str, str]],
        include_protocol_catalog: bool,
        tool_mode: str,
        recent_dialogue: list[dict[str, str]],
        endpoint_recommendations: list[dict[str, Any]],
    ) -> str:
        lines: list[str] = [
            "Plan operativo inicial (no diagnostico).",
            (
                f"Caso: {care_task.title}. "
                f"Especialidad: {effective_specialty}. "
                f"Herramienta: {tool_mode}."
            ),
        ]
        if recent_dialogue:
            last_turn = recent_dialogue[-1]
            lines.append(
                "Continuidad: tomo como referencia el ultimo turno sobre "
                f"'{last_turn.get('user_query', '')[:120]}'."
            )
        if matched_domains:
            lines.append("1) Priorizacion inmediata (0-10 min)")
            for idx, domain in enumerate(matched_domains):
                label = str(domain["label"])
                summary = str(domain["summary"])
                if include_protocol_catalog and idx < len(matched_endpoints):
                    lines.append(
                        f"- Activar ruta {label}: {summary}. "
                        f"Endpoint: {matched_endpoints[idx]}"
                    )
                else:
                    lines.append(f"- Activar ruta {label}: {summary}.")
        if memory_facts_used:
            lines.append("2) Contexto clinico reutilizado")
            lines.append("- Memoria de sesion: " + ", ".join(memory_facts_used[:5]) + ".")
        if patient_summary and patient_summary.get("patient_interactions_count", 0) > 0:
            lines.append("3) Contexto longitudinal")
            lines.append(
                "- Historial paciente: "
                f"{patient_summary['patient_interactions_count']} interacciones, "
                f"{patient_summary['patient_encounters_count']} episodios."
            )
        if patient_history_facts_used:
            lines.append(
                "- Hechos longitudinales: "
                + ", ".join(patient_history_facts_used[:5])
                + "."
            )
        if extracted_facts:
            lines.append("4) Hechos detectados")
            lines.append("- " + ", ".join(extracted_facts[:6]) + ".")
        if endpoint_recommendations:
            lines.append("5) Recomendaciones operativas internas")
            for recommendation in endpoint_recommendations[:4]:
                lines.append(f"- {recommendation['endpoint']}: {recommendation['snippet']}")
        if knowledge_sources:
            lines.append("6) Evidencia usada")
            lines.append("- Fuentes internas indexadas:")
            for source in knowledge_sources[:4]:
                lines.append(f"  - {source['title']} ({source['source']})")
        elif settings.CLINICAL_CHAT_REQUIRE_VALIDATED_INTERNAL_SOURCES:
            lines.append(
                "6) Evidencia usada\n- Sin fuentes internas validadas para esta consulta. "
                "Escalar revision profesional antes de tomar decision."
            )
        if web_sources:
            lines.append("- Fuentes web consultadas (dominios en whitelist):")
            for source in web_sources[:3]:
                lines.append(f"  - {source['title']}: {source['url']}")
        lines.append("7) Cierre operativo")
        lines.append(
            "- Validar decisiones con protocolo local, "
            "responsable clinico y estado dinamico del paciente."
        )
        lines.append(
            "- Este fallback operativo no constituye diagnostico final; "
            "requiere verificacion clinica presencial."
        )
        return "\n".join(lines)

    @staticmethod
    def _is_social_or_discovery_query(query: str) -> bool:
        normalized = ClinicalChatService._normalize(query)
        if normalized.startswith(("hola", "buenas", "hey", "que tal")):
            return True
        discovery_tokens = {"caso", "casos", "informacion", "info", "resumen"}
        return len(normalized.split()) <= 8 and any(
            token in normalized for token in discovery_tokens
        )

    @staticmethod
    def _safe_source_snippet(source: dict[str, str]) -> str:
        snippet = str(source.get("snippet") or "").strip()
        if not snippet:
            return ""
        if snippet.startswith("{") or snippet.startswith("["):
            return ""
        return snippet

    @staticmethod
    def _describe_available_domains(matched_domains: list[dict[str, object]]) -> list[str]:
        labels: list[str] = []
        for domain in matched_domains[:4]:
            label = str(domain.get("label") or domain.get("key") or "ruta clinica")
            if label not in labels:
                labels.append(label)
        return labels

    @staticmethod
    def _render_general_answer(
        *,
        query: str,
        memory_facts_used: list[str],
        knowledge_sources: list[dict[str, str]],
        web_sources: list[dict[str, str]],
        tool_mode: str,
        recent_dialogue: list[dict[str, str]],
        matched_domains: list[dict[str, object]],
    ) -> str:
        lines: list[str] = [
            "Modo conversacional general activo.",
            f"Herramienta seleccionada: {tool_mode}.",
        ]
        if ClinicalChatService._is_social_or_discovery_query(query):
            lines.append(
                "Hola. Si, puedo ayudarte con casos y rutas operativas validadas. "
                "Antes de responder en detalle sigo hilos de contexto, evidencia y accion."
            )
            available_domains = ClinicalChatService._describe_available_domains(matched_domains)
            if available_domains:
                lines.append("Ahora mismo puedo orientarte en:")
                for label in available_domains:
                    lines.append(f"- {label}")
            if knowledge_sources:
                lines.append("Fuentes internas disponibles:")
                for source in knowledge_sources[:3]:
                    lines.append(f"- {source.get('title', 'Fuente interna')}")
            lines.append(
                "Si me das un caso concreto (edad, sintomas clave, prioridad), te devuelvo "
                "un resumen accionable y fuentes usadas."
            )
        else:
            lines.append("Entendido. Respondo en formato conversacional y operativo.")
            if web_sources:
                first_source = web_sources[0]
                snippet = ClinicalChatService._safe_source_snippet(first_source)
                if snippet:
                    lines.append("Resumen inicial:")
                    lines.append(f"- {snippet}")
                lines.append("Fuente principal:")
                lines.append(
                    f"- {first_source.get('title', 'Referencia web')}: "
                    f"{first_source.get('url', '')}"
                )
            elif knowledge_sources:
                first_source = knowledge_sources[0]
                snippet = ClinicalChatService._safe_source_snippet(first_source)
                if snippet:
                    lines.append("Contexto disponible en base interna:")
                    lines.append(f"- {snippet}")
                lines.append(
                    f"Referencia interna: {first_source.get('title', 'Fuente interna')} "
                    f"({first_source.get('source', 'catalogo')})"
                )
            else:
                lines.append(
                    "No hay contexto documental adicional para esta consulta. "
                    "Si quieres, activa busqueda profunda para ampliar evidencia."
                )
        if memory_facts_used:
            lines.append("Contexto reutilizado: " + ", ".join(memory_facts_used[:4]) + ".")
        if recent_dialogue:
            last_turn = recent_dialogue[-1]
            lines.append(
                "Sigo el hilo desde tu turno anterior: "
                f"'{last_turn.get('user_query', '')[:120]}'."
            )
        lines.append("Si quieres, te doy una version mas breve o una checklist accionable.")
        return "\n".join(lines)

    @staticmethod
    def create_message(
        db: Session,
        *,
        care_task: CareTask,
        payload: CareTaskClinicalChatMessageRequest,
        authenticated_user: User | None,
    ) -> tuple[CareTaskChatMessage, int, str, list[str], str, str]:
        session_id = ClinicalChatService._safe_session_id(payload.session_id)
        effective_specialty = ClinicalChatService._resolve_effective_specialty(
            payload=payload,
            care_task=care_task,
            authenticated_user=authenticated_user,
        )
        recent_messages = ClinicalChatService._list_recent_messages(
            db,
            care_task_id=care_task.id,
            session_id=session_id,
            limit=payload.max_history_messages,
        )
        recent_dialogue = [
            {
                "user_query": message.user_query,
                "assistant_answer": message.assistant_answer,
            }
            for message in reversed(recent_messages[:8])
        ]
        effective_query, query_expanded = ClinicalChatService._compose_effective_query(
            query=payload.query,
            recent_dialogue=recent_dialogue,
        )
        fact_counter: Counter[str] = Counter()
        for history_message in recent_messages:
            filtered_facts = [
                fact
                for fact in (history_message.extracted_facts or [])
                if ClinicalChatService._filter_memory_fact(fact)
            ]
            fact_counter.update(filtered_facts)
        session_memory_facts = [fact for fact, _ in fact_counter.most_common(5)]

        patient_summary = None
        patient_history_facts_used: list[str] = []
        if payload.use_patient_history:
            patient_summary = ClinicalChatService._build_patient_summary(
                db,
                patient_reference=care_task.patient_reference,
                max_messages=payload.max_patient_history_messages,
            )
            if patient_summary is not None:
                patient_history_facts_used = [
                    fact
                    for fact in patient_summary["patient_top_extracted_facts"]
                    if ClinicalChatService._filter_memory_fact(fact)
                ][:5]
        memory_facts_used: list[str] = []
        for fact in session_memory_facts + patient_history_facts_used:
            if fact not in memory_facts_used:
                memory_facts_used.append(fact)

        keyword_hits = ClinicalChatService._count_domain_keyword_hits(effective_query)
        matched_domain_records = ClinicalChatService._match_domains(
            query=effective_query,
            effective_specialty=effective_specialty,
            max_domains=3,
        )
        matched_domains = [str(domain["key"]) for domain in matched_domain_records]
        matched_endpoints = [
            str(domain["endpoint"]).format(task_id=care_task.id)
            for domain in matched_domain_records
        ]
        extracted_facts = (
            ClinicalChatService._extract_facts(payload.query)
            if payload.persist_extracted_facts
            else []
        )
        response_mode = ClinicalChatService._resolve_response_mode(
            payload=payload,
            query=payload.query,
            extracted_facts=extracted_facts,
            keyword_hits=keyword_hits,
        )
        tool_mode = payload.tool_mode
        extracted_facts.append(f"modo_respuesta:{response_mode}")
        extracted_facts.append(f"herramienta:{tool_mode}")
        unique_facts: list[str] = []
        for fact in extracted_facts:
            if fact not in unique_facts:
                unique_facts.append(fact)
        extracted_facts = unique_facts[:20]
        endpoint_recommendations: list[dict[str, Any]] = []
        if response_mode == "clinical":
            endpoint_recommendations = ClinicalChatService._fetch_recommendations(
                query=effective_query,
                matched_endpoints=matched_endpoints,
            )
        if tool_mode in {"medication", "treatment", "cases"}:
            extracted_facts.append(f"tool_focus:{tool_mode}")
        knowledge_sources = ClinicalChatService._build_validated_knowledge_sources(
            db,
            query=effective_query,
            effective_specialty=effective_specialty,
            matched_domains=matched_domain_records,
            max_internal_sources=payload.max_internal_sources,
        )
        if not knowledge_sources and not settings.CLINICAL_CHAT_REQUIRE_VALIDATED_INTERNAL_SOURCES:
            knowledge_sources = ClinicalChatService._build_catalog_knowledge_sources(
                query=effective_query,
                matched_domains=matched_domain_records,
                max_internal_sources=payload.max_internal_sources,
            )
        web_limit = payload.max_web_sources
        use_web_sources = payload.use_web_sources
        if tool_mode == "deep_search":
            use_web_sources = True
            web_limit = max(payload.max_web_sources, 6)
        web_sources = (
            ClinicalChatService._fetch_web_sources(effective_query, web_limit)
            if use_web_sources
            else []
        )
        endpoint_sources = [
            {
                "type": "internal_recommendation",
                "title": str(item.get("title") or "Recomendacion interna"),
                "source": str(item.get("source") or "internal"),
                "snippet": str(item.get("snippet") or "")[:280],
            }
            for item in endpoint_recommendations
        ]
        if response_mode == "clinical":
            knowledge_sources = [*knowledge_sources, *endpoint_sources][
                : max(payload.max_internal_sources, 6)
            ]
        interpretability_trace = [
            f"query_length={len(payload.query)}",
            f"effective_specialty={effective_specialty}",
            f"conversation_mode={payload.conversation_mode}",
            f"response_mode={response_mode}",
            f"tool_mode={tool_mode}",
            f"query_expanded={1 if query_expanded else 0}",
            f"keyword_hits={keyword_hits}",
            f"history_messages_used={len(recent_messages)}",
            f"patient_history_used={1 if patient_summary else 0}",
            f"matched_domains={','.join(matched_domains) if matched_domains else 'none'}",
            f"matched_endpoints={','.join(matched_endpoints) if matched_endpoints else 'none'}",
            f"internal_sources={len(knowledge_sources)}",
            f"web_sources={len(web_sources)}",
            f"endpoint_recommendations={len(endpoint_recommendations)}",
            "reasoning_threads=intent>context>sources>actions",
            "source_policy=internal_first_web_whitelist",
            f"memory_facts_used={len(memory_facts_used)}",
            f"extracted_facts={len(extracted_facts)}",
        ]
        llm_answer, llm_trace = LLMChatProvider.generate_answer(
            query=payload.query,
            response_mode=response_mode,
            effective_specialty=effective_specialty,
            tool_mode=tool_mode,
            matched_domains=matched_domains,
            matched_endpoints=matched_endpoints,
            memory_facts_used=memory_facts_used,
            patient_summary=patient_summary,
            patient_history_facts_used=patient_history_facts_used,
            knowledge_sources=knowledge_sources,
            web_sources=web_sources,
            recent_dialogue=recent_dialogue,
            endpoint_results=endpoint_recommendations,
        )
        if llm_answer:
            answer = llm_answer
        elif response_mode == "clinical":
            answer = ClinicalChatService._render_clinical_answer(
                care_task=care_task,
                query=payload.query,
                matched_domains=matched_domain_records,
                matched_endpoints=matched_endpoints,
                effective_specialty=effective_specialty,
                memory_facts_used=memory_facts_used,
                patient_summary=patient_summary,
                patient_history_facts_used=patient_history_facts_used,
                extracted_facts=extracted_facts,
                knowledge_sources=knowledge_sources,
                web_sources=web_sources,
                include_protocol_catalog=payload.include_protocol_catalog,
                tool_mode=tool_mode,
                recent_dialogue=recent_dialogue,
                endpoint_recommendations=endpoint_recommendations,
            )
        else:
            answer = ClinicalChatService._render_general_answer(
                query=payload.query,
                memory_facts_used=memory_facts_used,
                knowledge_sources=knowledge_sources,
                web_sources=web_sources,
                tool_mode=tool_mode,
                recent_dialogue=recent_dialogue,
                matched_domains=matched_domain_records,
            )
        if llm_trace:
            interpretability_trace.extend(
                [f"{key}={value}" for key, value in llm_trace.items()]
            )
        run = AgentRunService.run_care_task_clinical_chat_workflow(
            db=db,
            care_task=care_task,
            chat_input={
                "query": payload.query,
                "session_id": session_id,
                "clinician_id": payload.clinician_id,
                "specialty_hint": payload.specialty_hint,
                "effective_specialty": effective_specialty,
                "conversation_mode": payload.conversation_mode,
                "tool_mode": tool_mode,
                "response_mode": response_mode,
                "use_patient_history": payload.use_patient_history,
                "use_web_sources": use_web_sources,
                "max_web_sources": web_limit,
                "max_history_messages": payload.max_history_messages,
                "max_patient_history_messages": payload.max_patient_history_messages,
            },
            chat_output={
                "answer": answer,
                "response_mode": response_mode,
                "tool_mode": tool_mode,
                "matched_domains": matched_domains,
                "matched_endpoints": matched_endpoints,
                "knowledge_sources": knowledge_sources,
                "web_sources": web_sources,
                "endpoint_recommendations": endpoint_recommendations,
                "memory_facts_used": memory_facts_used,
                "patient_history_facts_used": patient_history_facts_used,
                "extracted_facts": extracted_facts,
                "patient_summary": patient_summary,
                "interpretability_trace": interpretability_trace,
            },
        )
        message = CareTaskChatMessage(
            care_task_id=care_task.id,
            session_id=session_id,
            clinician_id=payload.clinician_id,
            effective_specialty=effective_specialty,
            user_query=payload.query,
            assistant_answer=answer,
            matched_domains=matched_domains,
            matched_endpoints=matched_endpoints,
            knowledge_sources=knowledge_sources,
            web_sources=web_sources,
            memory_facts_used=memory_facts_used,
            patient_history_facts_used=patient_history_facts_used,
            extracted_facts=extracted_facts,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message, run.id, run.workflow_name, interpretability_trace, response_mode, tool_mode
