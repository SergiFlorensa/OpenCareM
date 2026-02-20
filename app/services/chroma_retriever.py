"""
Retriever opcional con Chroma para consultas RAG locales.

Modo fail-safe: si `chromadb` no esta instalado o falla, devuelve vacio
para permitir fallback al retriever legacy.
"""
from __future__ import annotations

import logging
import time
from array import array
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import OllamaEmbeddingService

logger = logging.getLogger(__name__)


class ChromaRetriever:
    """Recuperador semantico opcional con Chroma (local, OSS)."""

    def __init__(self, embedding_service: Optional[OllamaEmbeddingService] = None):
        self.embedding_service = embedding_service or OllamaEmbeddingService()

    @staticmethod
    def _load_dependency() -> tuple[Any | None, str | None]:
        try:
            import chromadb
        except Exception as exc:  # pragma: no cover - depende de extras opcionales
            return None, exc.__class__.__name__
        return chromadb, None

    def search(
        self,
        query: str,
        db: Session,
        *,
        k: int = 5,
        specialty_filter: Optional[str] = None,
    ) -> tuple[list[DocumentChunk], dict[str, str]]:
        started_at = time.perf_counter()
        trace: dict[str, str] = {"chroma_enabled": "1"}

        chromadb, import_error = self._load_dependency()
        if import_error:
            trace["chroma_available"] = "0"
            trace["chroma_error"] = import_error
            return [], trace
        trace["chroma_available"] = "1"

        try:
            candidate_pool = max(20, settings.CLINICAL_CHAT_RAG_CHROMA_CANDIDATE_POOL)
            query_builder = db.query(DocumentChunk)
            if specialty_filter:
                query_builder = query_builder.filter(DocumentChunk.specialty == specialty_filter)
            candidates = (
                query_builder.order_by(DocumentChunk.id.desc()).limit(candidate_pool).all()
            )
            trace["chroma_candidates"] = str(len(candidates))
            if not candidates:
                trace["chroma_chunks_found"] = "0"
                return [], trace

            chunks_by_id: dict[str, DocumentChunk] = {}
            ids: list[str] = []
            embeddings: list[list[float]] = []
            documents: list[str] = []
            metadatas: list[dict[str, str]] = []

            for chunk in candidates:
                try:
                    embedding_array = array("f")
                    embedding_array.frombytes(chunk.chunk_embedding)
                    if len(embedding_array) == 0:
                        continue
                    chunk_id = str(chunk.id)
                    ids.append(chunk_id)
                    embeddings.append([float(value) for value in embedding_array])
                    documents.append(str(chunk.chunk_text or ""))
                    metadatas.append(
                        {
                            "chunk_id": chunk_id,
                            "specialty": str(chunk.specialty or ""),
                            "section_path": str(chunk.section_path or ""),
                        }
                    )
                    chunks_by_id[chunk_id] = chunk
                except (TypeError, ValueError):
                    continue

            if not ids:
                trace["chroma_chunks_found"] = "0"
                trace["chroma_error"] = "empty_candidate_embeddings"
                return [], trace

            query_vector, embedding_trace = self.embedding_service.embed_text(query)
            trace.update(embedding_trace)
            if not query_vector:
                trace["chroma_error"] = "empty_query_embedding"
                return [], trace

            client = chromadb.Client()
            collection = client.create_collection(
                name=f"clinical_chat_runtime_{int(time.time_ns())}",
                metadata={"hnsw:space": "cosine"},
            )
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
            n_results = max(1, min(k, len(ids)))
            query_result = collection.query(
                query_embeddings=[query_vector],
                n_results=n_results,
                include=["distances", "metadatas"],
            )

            result_ids = []
            if isinstance(query_result.get("ids"), list) and query_result["ids"]:
                result_ids = query_result["ids"][0]
            distances = []
            if isinstance(query_result.get("distances"), list) and query_result["distances"]:
                distances = query_result["distances"][0]

            result: list[DocumentChunk] = []
            for idx, raw_id in enumerate(result_ids):
                chunk = chunks_by_id.get(str(raw_id))
                if chunk is None:
                    continue
                distance = 1.0
                if idx < len(distances):
                    try:
                        distance = float(distances[idx])
                    except (TypeError, ValueError):
                        distance = 1.0
                score = 1.0 / (1.0 + max(0.0, distance))
                setattr(chunk, "_rag_score", score)
                result.append(chunk)

            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            trace.update(
                {
                    "chroma_chunks_found": str(len(result)),
                    "chroma_latency_ms": str(latency_ms),
                    "chroma_metric": "cosine",
                }
            )
            return result, trace
        except Exception as exc:  # pragma: no cover - defensivo
            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            logger.warning("Chroma retriever fallo y caera a legacy: %s", exc)
            trace.update(
                {
                    "chroma_error": exc.__class__.__name__,
                    "chroma_latency_ms": str(latency_ms),
                }
            )
            return [], trace
