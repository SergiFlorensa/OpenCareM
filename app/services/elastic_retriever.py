"""
Retriever opcional con Elasticsearch para consultas RAG locales.

Modo fail-safe:
- Si Elastic no esta disponible o devuelve error, retorna vacio.
- La orquestacion aplica fallback al retriever legacy sin romper el flujo.
"""
from __future__ import annotations

import base64
import json
import logging
import ssl
import time
from types import SimpleNamespace
from typing import Any, Optional
from urllib import error, request

from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)


class ElasticRetriever:
    """Recuperador hibrido basado en Elasticsearch."""

    @staticmethod
    def _parse_text_fields() -> list[str]:
        raw = str(settings.CLINICAL_CHAT_RAG_ELASTIC_TEXT_FIELDS or "").strip()
        if not raw:
            return ["chunk_text^3", "section_path^2", "source_file"]
        return [field.strip() for field in raw.split(",") if field.strip()]

    @staticmethod
    def _build_headers() -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        api_key = str(settings.CLINICAL_CHAT_RAG_ELASTIC_API_KEY or "").strip()
        username = str(settings.CLINICAL_CHAT_RAG_ELASTIC_USERNAME or "").strip()
        password = str(settings.CLINICAL_CHAT_RAG_ELASTIC_PASSWORD or "").strip()
        if api_key:
            headers["Authorization"] = f"ApiKey {api_key}"
        elif username:
            token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
            headers["Authorization"] = f"Basic {token}"
        return headers

    @staticmethod
    def _build_query_payload(
        *,
        query: str,
        size: int,
        specialty_filter: Optional[str],
        use_semantic: bool,
    ) -> dict[str, Any]:
        normalized_specialty = str(specialty_filter or "").strip().lower()
        filter_clauses: list[dict[str, Any]] = []
        if normalized_specialty and normalized_specialty not in {"general", "*"}:
            filter_clauses.append({"term": {"specialty.keyword": normalized_specialty}})

        should_clauses: list[dict[str, Any]] = [
            {
                "multi_match": {
                    "query": query,
                    "fields": ElasticRetriever._parse_text_fields(),
                    "type": "best_fields",
                    "operator": "or",
                    "fuzziness": "AUTO",
                }
            }
        ]
        if use_semantic:
            should_clauses.append(
                {
                    "semantic": {
                        "field": str(settings.CLINICAL_CHAT_RAG_ELASTIC_SEMANTIC_FIELD),
                        "query": query,
                    }
                }
            )

        return {
            "size": size,
            "track_total_hits": False,
            "_source": [
                "id",
                "chunk_id",
                "chunk_text",
                "text",
                "content",
                "section_path",
                "section",
                "title",
                "source_file",
                "source",
                "document_source",
                "keywords",
                "custom_questions",
                "specialty",
            ],
            "query": {
                "bool": {
                    "should": should_clauses,
                    "minimum_should_match": 1,
                    "filter": filter_clauses,
                }
            },
            "highlight": {
                "pre_tags": [""],
                "post_tags": [""],
                "number_of_fragments": 1,
                "fragment_size": 320,
                "fields": {
                    "chunk_text": {},
                    "text": {},
                    "content": {},
                },
            },
        }

    @staticmethod
    def _extract_keywords(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            items = [part.strip() for part in value.split(",")]
            return [item for item in items if item]
        return []

    @staticmethod
    def _extract_questions(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    def _execute_search(
        self,
        *,
        payload: dict[str, Any],
        timeout_seconds: int,
    ) -> tuple[dict[str, Any] | None, str | None]:
        base_url = str(settings.CLINICAL_CHAT_RAG_ELASTIC_URL or "").rstrip("/")
        index_name = str(settings.CLINICAL_CHAT_RAG_ELASTIC_INDEX or "").strip()
        if not base_url or not index_name:
            return None, "invalid_config"
        url = f"{base_url}/{index_name}/_search"
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(url=url, data=body, headers=self._build_headers(), method="POST")
        context = None
        if not settings.CLINICAL_CHAT_RAG_ELASTIC_VERIFY_TLS:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        try:
            with request.urlopen(req, timeout=timeout_seconds, context=context) as response:
                data = response.read().decode("utf-8")
                return json.loads(data), None
        except error.HTTPError as exc:
            reason = "http_error"
            try:
                payload = exc.read().decode("utf-8")
                if "unknown query [semantic]" in payload.lower():
                    reason = "semantic_query_unsupported"
                elif "no mapping found for [specialty.keyword]" in payload.lower():
                    reason = "specialty_keyword_mapping_missing"
            except Exception:
                pass
            return None, reason
        except Exception as exc:  # pragma: no cover - defensivo de red
            return None, exc.__class__.__name__

    def search(
        self,
        query: str,
        db: Session,  # noqa: ARG002 - mantiene firma uniforme con otros retrievers
        *,
        k: int = 5,
        specialty_filter: Optional[str] = None,
    ) -> tuple[list[Any], dict[str, str]]:
        started_at = time.perf_counter()
        trace: dict[str, str] = {"elastic_enabled": "1"}

        candidate_pool = max(20, int(settings.CLINICAL_CHAT_RAG_ELASTIC_CANDIDATE_POOL))
        size = max(k, min(candidate_pool, max(k * 3, k)))
        timeout_seconds = int(settings.CLINICAL_CHAT_RAG_ELASTIC_TIMEOUT_SECONDS)
        trace["elastic_candidate_pool"] = str(candidate_pool)
        trace["elastic_requested_size"] = str(size)
        trace["elastic_specialty_filter"] = str(specialty_filter or "none")

        payload = self._build_query_payload(
            query=query,
            size=size,
            specialty_filter=specialty_filter,
            use_semantic=True,
        )
        response, error_reason = self._execute_search(
            payload=payload,
            timeout_seconds=timeout_seconds,
        )
        if response is None and error_reason in {
            "semantic_query_unsupported",
            "specialty_keyword_mapping_missing",
        }:
            trace["elastic_retry_mode"] = error_reason
            payload = self._build_query_payload(
                query=query,
                size=size,
                specialty_filter=specialty_filter,
                use_semantic=False,
            )
            if error_reason == "specialty_keyword_mapping_missing":
                payload = self._build_query_payload(
                    query=query,
                    size=size,
                    specialty_filter=None,
                    use_semantic=False,
                )
                trace["elastic_specialty_filter_relaxed"] = "1"
            response, error_reason = self._execute_search(
                payload=payload,
                timeout_seconds=timeout_seconds,
            )
        else:
            trace["elastic_specialty_filter_relaxed"] = "0"

        if response is None:
            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            trace.update(
                {
                    "elastic_available": "0",
                    "elastic_error": str(error_reason or "unknown"),
                    "elastic_latency_ms": str(latency_ms),
                }
            )
            return [], trace

        hits = (
            response.get("hits", {}).get("hits", [])
            if isinstance(response, dict)
            else []
        )
        trace["elastic_available"] = "1"
        trace["elastic_hits"] = str(len(hits))

        result: list[Any] = []
        seen_ids: set[str] = set()
        for idx, hit in enumerate(hits):
            source = hit.get("_source", {}) if isinstance(hit, dict) else {}
            highlight = hit.get("highlight", {}) if isinstance(hit, dict) else {}
            raw_id = (
                source.get("id")
                or source.get("chunk_id")
                or hit.get("_id")
                or f"elastic-{idx}"
            )
            chunk_key = str(raw_id)
            if chunk_key in seen_ids:
                continue
            seen_ids.add(chunk_key)

            text = (
                (highlight.get("chunk_text") or [None])[0]
                or (highlight.get("text") or [None])[0]
                or (highlight.get("content") or [None])[0]
                or source.get("chunk_text")
                or source.get("text")
                or source.get("content")
                or ""
            )
            section = (
                source.get("section_path")
                or source.get("section")
                or source.get("title")
                or "sin seccion"
            )
            source_file = (
                source.get("source_file")
                or source.get("source")
                or source.get("document_source")
                or "catalogo interno"
            )
            specialty = source.get("specialty") or specialty_filter or "general"
            keywords = self._extract_keywords(source.get("keywords"))
            questions = self._extract_questions(source.get("custom_questions"))
            score = float(hit.get("_score") or 0.0)
            chunk_id = idx + 1
            try:
                chunk_id = int(str(raw_id))
            except (TypeError, ValueError):
                pass
            chunk = SimpleNamespace(
                id=chunk_id,
                chunk_text=str(text),
                section_path=str(section),
                keywords=keywords,
                custom_questions=questions,
                specialty=str(specialty),
                tokens_count=max(1, len(str(text).split())),
                document=SimpleNamespace(source_file=str(source_file)),
            )
            setattr(chunk, "_rag_score", score)
            result.append(chunk)
            if len(result) >= k:
                break

        latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
        trace.update(
            {
                "elastic_chunks_found": str(len(result)),
                "elastic_latency_ms": str(latency_ms),
            }
        )
        return result, trace
