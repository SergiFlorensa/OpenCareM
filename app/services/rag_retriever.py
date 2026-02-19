"""
Motor de recuperacion hibrido para RAG.

Combina similitud semantica (embeddings) con coincidencia lexical.
"""
from __future__ import annotations

import logging
import time
from array import array
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import OllamaEmbeddingService

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Recuperador hibrido de fragmentos clinicos."""

    def __init__(
        self,
        embedding_service: Optional[OllamaEmbeddingService] = None,
        vector_weight: Optional[float] = None,
        keyword_weight: Optional[float] = None,
    ):
        self.embedding_service = embedding_service or OllamaEmbeddingService()
        vector = (
            settings.CLINICAL_CHAT_RAG_VECTOR_WEIGHT
            if vector_weight is None
            else vector_weight
        )
        keyword = (
            settings.CLINICAL_CHAT_RAG_KEYWORD_WEIGHT
            if keyword_weight is None
            else keyword_weight
        )
        total = vector + keyword
        if total <= 0:
            vector = 0.5
            keyword = 0.5
            total = 1.0
        self.vector_weight = vector / total
        self.keyword_weight = keyword / total

    def search_vector(
        self,
        query: str,
        db: Session,
        *,
        k: int = 5,
        specialty_filter: Optional[str] = None,
    ) -> tuple[list[DocumentChunk], dict[str, str]]:
        started_at = time.perf_counter()
        trace_info: dict[str, str] = {}

        try:
            query_vec, embedding_trace = self.embedding_service.embed_text(query)
            trace_info.update(embedding_trace)
            if not query_vec:
                trace_info["vector_search_error"] = "empty_query_embedding"
                return [], trace_info

            query_builder = db.query(DocumentChunk)
            if specialty_filter:
                query_builder = query_builder.filter_by(specialty=specialty_filter)
            all_chunks = query_builder.all()
            if not all_chunks:
                trace_info["vector_search_chunks_found"] = "0"
                return [], trace_info

            candidate_chunks: list[DocumentChunk] = []
            candidate_vectors: list[list[float]] = []
            for chunk in all_chunks:
                try:
                    embedding_array = array("f")
                    embedding_array.frombytes(chunk.chunk_embedding)
                    if len(embedding_array) == 0:
                        continue
                    candidate_chunks.append(chunk)
                    candidate_vectors.append(list(embedding_array))
                except ValueError:
                    continue

            if not candidate_vectors:
                trace_info["vector_search_chunks_found"] = "0"
                trace_info["vector_search_error"] = "empty_candidate_embeddings"
                return [], trace_info

            similarities = self.embedding_service.batch_cosine_similarity(
                query_vec,
                candidate_vectors,
            )
            chunk_scores = list(zip(candidate_chunks, similarities, strict=False))
            chunk_scores.sort(key=lambda item: item[1], reverse=True)

            top_scores = chunk_scores[:k]
            results: list[DocumentChunk] = []
            for chunk, score in top_scores:
                setattr(chunk, "_rag_score", float(score))
                results.append(chunk)

            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            avg_score = (
                sum(float(score) for _, score in top_scores) / len(top_scores)
                if top_scores
                else 0.0
            )
            trace_info.update(
                {
                    "vector_search_chunks_found": str(len(results)),
                    "vector_search_avg_score": f"{avg_score:.3f}",
                    "vector_search_latency_ms": str(latency_ms),
                    "vector_search_method": "cosine_similarity",
                }
            )
            return results, trace_info
        except Exception as exc:  # pragma: no cover - defensivo
            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            trace_info["vector_search_error"] = exc.__class__.__name__
            trace_info["vector_search_latency_ms"] = str(latency_ms)
            logger.error("Error en busqueda vectorial: %s", exc)
            return [], trace_info

    def search_keyword(
        self,
        query: str,
        db: Session,
        *,
        k: int = 5,
        specialty_filter: Optional[str] = None,
    ) -> tuple[list[DocumentChunk], dict[str, str]]:
        started_at = time.perf_counter()
        query_terms = {term for term in query.lower().split() if term}
        trace_info: dict[str, str] = {}

        query_builder = db.query(DocumentChunk)
        if specialty_filter:
            query_builder = query_builder.filter_by(specialty=specialty_filter)
        all_chunks = query_builder.all()
        if not all_chunks:
            trace_info["keyword_search_chunks_found"] = "0"
            return [], trace_info

        scored: list[tuple[DocumentChunk, float]] = []
        for chunk in all_chunks:
            chunk_text = (chunk.chunk_text or "").lower()
            text_hits = sum(1 for term in query_terms if term in chunk_text)
            keywords_hits = 0
            for keyword in chunk.keywords or []:
                keyword_text = str(keyword).lower()
                if keyword_text and keyword_text in query.lower():
                    keywords_hits += 1
            question_hits = 0
            for question in chunk.custom_questions or []:
                if query.lower() in str(question).lower():
                    question_hits += 1
            score = float(text_hits + (keywords_hits * 1.5) + (question_hits * 1.2))
            if score > 0:
                scored.append((chunk, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        top_scores = scored[:k]
        results: list[DocumentChunk] = []
        for chunk, score in top_scores:
            setattr(chunk, "_rag_score", float(score))
            results.append(chunk)

        latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
        avg_score = (
            sum(float(score) for _, score in top_scores) / len(top_scores)
            if top_scores
            else 0.0
        )
        trace_info.update(
            {
                "keyword_search_chunks_found": str(len(results)),
                "keyword_search_avg_score": f"{avg_score:.2f}",
                "keyword_search_latency_ms": str(latency_ms),
                "keyword_search_method": "text_and_keywords",
            }
        )
        return results, trace_info

    def search_hybrid(
        self,
        query: str,
        db: Session,
        *,
        k: int = 5,
        specialty_filter: Optional[str] = None,
    ) -> tuple[list[DocumentChunk], dict[str, str]]:
        started_at = time.perf_counter()
        trace: dict[str, str] = {}

        vector_chunks, vector_trace = self.search_vector(
            query,
            db,
            k=max(k * 2, 8),
            specialty_filter=specialty_filter,
        )
        keyword_chunks, keyword_trace = self.search_keyword(
            query,
            db,
            k=max(k * 2, 8),
            specialty_filter=specialty_filter,
        )
        trace.update(vector_trace)
        trace.update(keyword_trace)

        combined_scores: dict[int, float] = {}
        chunks_by_id: dict[int, DocumentChunk] = {}

        if vector_chunks:
            for idx, chunk in enumerate(vector_chunks):
                base_score = 1.0 - (idx / max(1, len(vector_chunks)))
                combined_scores[chunk.id] = combined_scores.get(chunk.id, 0.0) + (
                    base_score * self.vector_weight
                )
                chunks_by_id[chunk.id] = chunk

        if keyword_chunks:
            for idx, chunk in enumerate(keyword_chunks):
                base_score = 1.0 - (idx / max(1, len(keyword_chunks)))
                combined_scores[chunk.id] = combined_scores.get(chunk.id, 0.0) + (
                    base_score * self.keyword_weight
                )
                chunks_by_id[chunk.id] = chunk

        ranked_ids = sorted(combined_scores.items(), key=lambda item: item[1], reverse=True)
        result: list[DocumentChunk] = []
        for chunk_id, score in ranked_ids[:k]:
            chunk = chunks_by_id[chunk_id]
            setattr(chunk, "_rag_score", float(score))
            result.append(chunk)

        latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
        trace.update(
            {
                "hybrid_search_chunks_found": str(len(result)),
                "hybrid_search_latency_ms": str(latency_ms),
                "hybrid_search_method": (
                    f"vector({self.vector_weight:.0%})+keyword({self.keyword_weight:.0%})"
                ),
            }
        )
        return result, trace

    def search_by_domain(
        self,
        detected_domains: list[str],
        db: Session,
        *,
        k: int = 5,
    ) -> tuple[list[DocumentChunk], dict[str, str]]:
        """
        Busqueda lexical por dominios clinicos detectados.
        """
        trace: dict[str, str] = {"domain_search_domains": ",".join(detected_domains)}
        if not detected_domains:
            trace["domain_search_error"] = "no_domains"
            return [], trace

        domain_terms = {
            "scasest": ["scasest", "coronario", "troponina", "grace", "cardio"],
            "sepsis": ["sepsis", "qsofa", "lactato", "bundle"],
            "resuscitation": ["rcp", "reanimacion", "acls", "arritmia"],
            "critical_ops": ["critico", "urgencias", "shock", "estabilizacion"],
            "neurology": ["ictus", "neurologia", "aspects", "hsa"],
            "trauma": ["trauma", "abcde", "hemorragia", "fractura"],
            "medicolegal": ["consentimiento", "medicolegal", "custodia", "bioetica"],
        }

        terms: list[str] = []
        for domain in detected_domains:
            terms.extend(domain_terms.get(domain, [domain]))
        terms = [term for term in terms if term]
        unique_terms = list(dict.fromkeys(terms))

        filters = []
        for term in unique_terms[:12]:
            like_term = f"%{term}%"
            filters.append(DocumentChunk.chunk_text.ilike(like_term))
            filters.append(DocumentChunk.section_path.ilike(like_term))
            filters.append(DocumentChunk.specialty.ilike(like_term))

        query_builder = db.query(DocumentChunk)
        if filters:
            query_builder = query_builder.filter(or_(*filters))
        raw_results = query_builder.limit(max(k * 4, 12)).all()

        scored: list[tuple[DocumentChunk, float]] = []
        for chunk in raw_results:
            text = f"{chunk.section_path or ''} {chunk.chunk_text or ''}".lower()
            score = float(sum(1 for term in unique_terms if term.lower() in text))
            if score > 0:
                scored.append((chunk, score))
        scored.sort(key=lambda item: item[1], reverse=True)

        result: list[DocumentChunk] = []
        for chunk, score in scored[:k]:
            setattr(chunk, "_rag_score", float(score))
            result.append(chunk)

        trace["domain_search_chunks_found"] = str(len(result))
        trace["domain_search_terms"] = ",".join(unique_terms[:8]) if unique_terms else "none"
        return result, trace
