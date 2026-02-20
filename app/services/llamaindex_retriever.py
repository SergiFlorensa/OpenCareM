"""
Retriever opcional con LlamaIndex para consultas RAG locales.

Este modulo es fail-safe: si `llama-index` no esta instalado o falla,
devuelve resultado vacio y permite fallback al retriever legacy.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document_chunk import DocumentChunk

logger = logging.getLogger(__name__)


class LlamaIndexRetriever:
    """Recuperador semantico opcional basado en LlamaIndex + Ollama embeddings."""

    @staticmethod
    def _load_dependencies() -> tuple[Any | None, Any | None, Any | None, str | None]:
        try:
            from llama_index.core import Document, VectorStoreIndex
            from llama_index.embeddings.ollama import OllamaEmbedding
        except Exception as exc:  # pragma: no cover - depende de extras opcionales
            return None, None, None, exc.__class__.__name__
        return Document, VectorStoreIndex, OllamaEmbedding, None

    @staticmethod
    def _build_embed_model(ollama_embedding_cls: Any) -> Any:
        candidates = [
            {
                "model_name": settings.CLINICAL_CHAT_RAG_EMBEDDING_MODEL,
                "base_url": settings.CLINICAL_CHAT_LLM_BASE_URL,
            },
            {
                "model_name": settings.CLINICAL_CHAT_RAG_EMBEDDING_MODEL,
                "ollama_base_url": settings.CLINICAL_CHAT_LLM_BASE_URL,
            },
            {"model_name": settings.CLINICAL_CHAT_RAG_EMBEDDING_MODEL},
        ]
        for kwargs in candidates:
            try:
                return ollama_embedding_cls(**kwargs)
            except TypeError:
                continue
        raise TypeError("No compatible constructor for OllamaEmbedding")

    def search(
        self,
        query: str,
        db: Session,
        *,
        k: int = 5,
        specialty_filter: Optional[str] = None,
    ) -> tuple[list[DocumentChunk], dict[str, str]]:
        started_at = time.perf_counter()
        trace: dict[str, str] = {
            "llamaindex_enabled": "1",
            "llamaindex_embedding_model": settings.CLINICAL_CHAT_RAG_EMBEDDING_MODEL,
        }

        document_cls, index_cls, ollama_embedding_cls, import_error = self._load_dependencies()
        if import_error:
            trace["llamaindex_available"] = "0"
            trace["llamaindex_error"] = import_error
            return [], trace
        trace["llamaindex_available"] = "1"

        try:
            candidate_pool = max(20, settings.CLINICAL_CHAT_RAG_LLAMAINDEX_CANDIDATE_POOL)
            query_builder = db.query(DocumentChunk)
            if specialty_filter:
                query_builder = query_builder.filter(DocumentChunk.specialty == specialty_filter)
            candidates = (
                query_builder.order_by(DocumentChunk.id.desc()).limit(candidate_pool).all()
            )
            trace["llamaindex_candidates"] = str(len(candidates))
            if not candidates:
                trace["llamaindex_nodes_found"] = "0"
                return [], trace

            docs: list[Any] = []
            chunks_by_id: dict[int, DocumentChunk] = {}
            for chunk in candidates:
                chunk_text = (chunk.chunk_text or "").strip()
                if not chunk_text:
                    continue
                source_file = ""
                if chunk.document is not None and chunk.document.source_file:
                    source_file = str(chunk.document.source_file)
                metadata = {
                    "chunk_id": str(chunk.id),
                    "section_path": str(chunk.section_path or ""),
                    "source_file": source_file,
                    "specialty": str(chunk.specialty or ""),
                }
                docs.append(document_cls(text=chunk_text, metadata=metadata))
                chunks_by_id[chunk.id] = chunk

            if not docs:
                trace["llamaindex_nodes_found"] = "0"
                return [], trace

            embed_model = self._build_embed_model(ollama_embedding_cls)
            index = index_cls.from_documents(docs, embed_model=embed_model)
            top_k = max(1, min(k, len(docs)))
            retriever = index.as_retriever(similarity_top_k=top_k)
            nodes = retriever.retrieve(query)

            result: list[DocumentChunk] = []
            seen_ids: set[int] = set()
            for node_with_score in nodes:
                node = getattr(node_with_score, "node", node_with_score)
                metadata = getattr(node, "metadata", {}) or {}
                raw_chunk_id = metadata.get("chunk_id")
                try:
                    chunk_id = int(raw_chunk_id)
                except (TypeError, ValueError):
                    continue
                if chunk_id in seen_ids:
                    continue
                chunk = chunks_by_id.get(chunk_id)
                if chunk is None:
                    continue
                score = float(getattr(node_with_score, "score", 0.0) or 0.0)
                setattr(chunk, "_rag_score", score)
                result.append(chunk)
                seen_ids.add(chunk_id)
                if len(result) >= k:
                    break

            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            trace.update(
                {
                    "llamaindex_nodes_found": str(len(result)),
                    "llamaindex_latency_ms": str(latency_ms),
                }
            )
            return result, trace
        except Exception as exc:  # pragma: no cover - defensivo
            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            logger.warning("LlamaIndex retriever fallo y caera a legacy: %s", exc)
            trace.update(
                {
                    "llamaindex_error": exc.__class__.__name__,
                    "llamaindex_latency_ms": str(latency_ms),
                }
            )
            return [], trace
