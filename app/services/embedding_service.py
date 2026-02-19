"""
Servicio de embeddings usando Ollama localmente.

Genera vectores de 384 dimensiones y permite fallback deterministico
cuando Ollama no esta disponible.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import time
from pathlib import Path
from typing import Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaEmbeddingService:
    """Servicio de embeddings usando modelo Ollama local."""

    EMBEDDING_DIM = 384
    CACHE_DIR = Path(".ollama_cache/embeddings")

    def __init__(self, model: Optional[str] = None, cache_enabled: bool = True):
        self.model = model or settings.CLINICAL_CHAT_RAG_EMBEDDING_MODEL
        self.cache_enabled = cache_enabled
        self.base_url = settings.CLINICAL_CHAT_LLM_BASE_URL
        if cache_enabled:
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def embed_text(self, text: str) -> tuple[list[float], dict[str, str]]:
        """
        Genera embedding para un texto.

        Devuelve `(vector, trace_info)`.
        """
        if not text or not text.strip():
            raise ValueError("Texto vacio")

        text_normalized = text.strip()

        if self.cache_enabled:
            vector, cache_hit = self._load_from_cache(text_normalized)
            if cache_hit and vector:
                return vector, {
                    "embedding_source": "cache",
                    "embedding_model": self.model,
                    "cache_hit": "true",
                }

        started_at = time.perf_counter()
        try:
            vector = self._call_ollama(text_normalized)
            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            if self.cache_enabled:
                self._save_to_cache(text_normalized, vector)
            return vector, {
                "embedding_source": "ollama",
                "embedding_model": self.model,
                "embedding_latency_ms": str(latency_ms),
                "cache_hit": "false",
            }
        except (URLError, TimeoutError, ValueError, OSError, json.JSONDecodeError) as exc:
            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            logger.warning("Error en embeddings Ollama: %s", exc.__class__.__name__)
            vector = self._fallback_vector(text_normalized)
            return vector, {
                "embedding_source": "fallback_hash",
                "embedding_model": self.model,
                "embedding_error": exc.__class__.__name__,
                "embedding_latency_ms": str(latency_ms),
                "cache_hit": "false",
            }

    def embed_batch(
        self,
        texts: list[str],
    ) -> tuple[list[list[float]], dict[str, str]]:
        vectors: list[list[float]] = []
        started_at = time.perf_counter()
        cache_hits = 0
        errors = 0

        for text in texts:
            try:
                vector, trace = self.embed_text(text)
                vectors.append(vector)
                if trace.get("cache_hit") == "true":
                    cache_hits += 1
                if trace.get("embedding_error"):
                    errors += 1
            except ValueError:
                errors += 1
                vectors.append(self._fallback_vector(text))

        latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
        return vectors, {
            "embedding_batch_size": str(len(texts)),
            "embedding_vectors": str(len(vectors)),
            "embedding_cache_hits": str(cache_hits),
            "embedding_errors": str(errors),
            "embedding_batch_latency_ms": str(latency_ms),
            "embedding_avg_latency_ms": f"{latency_ms / len(texts):.2f}" if texts else "0",
        }

    def _call_ollama(self, text: str) -> list[float]:
        payload = {
            "model": self.model,
            "input": text,
        }
        url = f"{self.base_url.rstrip('/')}/api/embed"
        request = Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=settings.CLINICAL_CHAT_LLM_TIMEOUT_SECONDS) as response:
            raw_response = response.read().decode("utf-8", errors="ignore")

        response_data = json.loads(raw_response)
        embedding = response_data.get("embedding")
        if not embedding:
            embeddings = response_data.get("embeddings")
            if isinstance(embeddings, list) and embeddings:
                embedding = embeddings[0]
        if not embedding:
            raise ValueError("No embedding en respuesta de Ollama")
        return [float(item) for item in embedding]

    def _fallback_vector(self, text: str) -> list[float]:
        """
        Vector fallback deterministico basado en hash del texto.
        """
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        raw = (digest * ((self.EMBEDDING_DIM // len(digest)) + 1))[: self.EMBEDDING_DIM]
        return [((value - 127.5) / 127.5) for value in raw]

    def _cache_key(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _load_from_cache(self, text: str) -> tuple[Optional[list[float]], bool]:
        cache_file = self.CACHE_DIR / f"{self._cache_key(text)}.json"
        if not cache_file.exists():
            return None, False
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            embedding = data.get("embedding")
            if isinstance(embedding, list):
                return [float(item) for item in embedding], True
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.debug("Error cargando cache de embeddings: %s", exc)
        return None, False

    def _save_to_cache(self, text: str, vector: list[float]) -> None:
        cache_file = self.CACHE_DIR / f"{self._cache_key(text)}.json"
        payload = {"text_sample": text[:100], "embedding": vector}
        try:
            cache_file.write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.debug("Error guardando cache de embeddings: %s", exc)

    @staticmethod
    def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        norm_a = math.sqrt(sum(value * value for value in vec1))
        norm_b = math.sqrt(sum(value * value for value in vec2))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        dot = sum(a * b for a, b in zip(vec1, vec2, strict=False))
        similarity = dot / (norm_a * norm_b)
        return max(0.0, min(1.0, float(similarity)))

    @staticmethod
    def batch_cosine_similarity(
        query_vec: list[float],
        candidate_vecs: list[list[float]],
    ) -> list[float]:
        if not candidate_vecs:
            return []
        query_norm = math.sqrt(sum(value * value for value in query_vec))
        if query_norm == 0:
            return [0.0 for _ in candidate_vecs]

        similarities: list[float] = []
        for candidate in candidate_vecs:
            candidate_norm = math.sqrt(sum(value * value for value in candidate))
            if candidate_norm == 0:
                similarities.append(0.0)
                continue
            dot = sum(a * b for a, b in zip(candidate, query_vec, strict=False))
            score = dot / (candidate_norm * query_norm)
            similarities.append(max(0.0, min(1.0, float(score))))
        return similarities
