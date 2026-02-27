"""
Utilities para ensamblar contexto RAG.
"""
from __future__ import annotations

import re
from typing import Any, Optional

from app.services.llm_chat_provider import LLMChatProvider


class RAGPromptBuilder:
    """Construye prompts enriquecidos para escenarios RAG."""

    @staticmethod
    def build_rag_prompt(
        *,
        query: str,
        retrieved_chunks: list[dict[str, Any]],
        response_mode: str = "clinical",
        effective_specialty: str = "general",
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
    ) -> tuple[str, dict[str, Any]]:
        matched_domains = matched_domains or []
        matched_endpoints = matched_endpoints or []
        memory_facts_used = memory_facts_used or []
        patient_history_facts_used = patient_history_facts_used or []
        knowledge_sources = knowledge_sources or []
        web_sources = web_sources or []
        recent_dialogue = recent_dialogue or []
        endpoint_results = endpoint_results or []

        base_prompt = LLMChatProvider._build_user_prompt(
            query=query,
            response_mode=response_mode,
            matched_domains=matched_domains,
            matched_endpoints=matched_endpoints,
            memory_facts_used=memory_facts_used,
            patient_summary=patient_summary,
            patient_history_facts_used=patient_history_facts_used,
            knowledge_sources=knowledge_sources,
            web_sources=web_sources,
            recent_dialogue=recent_dialogue,
            endpoint_results=endpoint_results,
        )
        rag_context = RAGPromptBuilder._build_rag_context(retrieved_chunks)
        final_prompt = "\n".join(
            [
                "=== CONSULTA CLINICA CON CONTEXTO RAG ===",
                base_prompt,
                "",
                "=== FRAGMENTOS RECUPERADOS ===",
                rag_context,
                "",
                "Responde apoyandote en los fragmentos y en la politica de fuentes.",
            ]
        )

        token_budget = LLMChatProvider._compute_input_token_budget()
        truncated_prompt = LLMChatProvider._truncate_text_to_token_budget(
            final_prompt,
            token_budget,
        )
        trace = {
            "rag_chunks_injected": str(len(retrieved_chunks)),
            "rag_prompt_truncated": "1" if truncated_prompt != final_prompt else "0",
        }
        return truncated_prompt, trace

    @staticmethod
    def _build_rag_context(retrieved_chunks: list[dict[str, Any]]) -> str:
        if not retrieved_chunks:
            return "No se encontraron documentos relevantes."
        lines: list[str] = []
        for idx, chunk in enumerate(retrieved_chunks[:5], start=1):
            title = str(chunk.get("section") or "sin seccion")
            source = str(chunk.get("source") or "catalogo interno")
            score = float(chunk.get("score") or 0.0)
            content = str(chunk.get("text") or "").strip()
            if len(content) > 260:
                content = f"{content[:260]}..."
            lines.extend(
                [
                    f"Documento {idx} (score={score:.2f})",
                    f"- Seccion: {title}",
                    f"- Fuente: {source}",
                    f"- Contenido: {content}",
                ]
            )
        return "\n".join(lines)

    @staticmethod
    def build_system_prompt_rag_aware(
        *,
        response_mode: str = "clinical",
        effective_specialty: str = "general",
        tool_mode: str = "chat",
        rag_enabled: bool = True,
    ) -> str:
        base_prompt = LLMChatProvider._build_system_prompt(
            response_mode=response_mode,
            effective_specialty=effective_specialty,
            tool_mode=tool_mode,
        )
        if not rag_enabled:
            return base_prompt
        return (
            f"{base_prompt}\n\n"
            "Modo RAG activo: fundamenta la respuesta en los fragmentos recuperados. "
            "Si hay incertidumbre o contradiccion, explicitala de forma explicita."
        )


class RAGContextAssembler:
    """Convierte chunks ORM a estructuras serializables para prompts/traza."""

    @staticmethod
    def assemble_rag_context(
        retrieved_chunks: list[Any],
        *,
        embedding_trace: Optional[dict[str, str]] = None,
        retrieval_trace: Optional[dict[str, str]] = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        chunks_dicts: list[dict[str, Any]] = []
        for chunk in retrieved_chunks:
            document = getattr(chunk, "document", None)
            source = None
            if document is not None:
                source = getattr(document, "source_file", None)
            chunk_dict = {
                "id": int(getattr(chunk, "id")),
                "text": str(getattr(chunk, "chunk_text", "")),
                "section": str(getattr(chunk, "section_path", "") or "sin seccion"),
                "score": float(getattr(chunk, "_rag_score", 0.0) or 0.0),
                "keywords": list(getattr(chunk, "keywords", []) or []),
                "questions": list(getattr(chunk, "custom_questions", []) or []),
                "source": str(source or "catalogo interno"),
                "specialty": str(getattr(chunk, "specialty", "") or "general"),
                "token_count": int(getattr(chunk, "tokens_count", 0) or 0),
            }
            chunks_dicts.append(chunk_dict)

        combined_trace: dict[str, Any] = {}
        if embedding_trace:
            combined_trace.update(embedding_trace)
        if retrieval_trace:
            combined_trace.update(retrieval_trace)
        combined_trace["rag_assembled_chunks"] = str(len(chunks_dicts))
        return chunks_dicts, combined_trace

    @staticmethod
    def compress_rag_context(
        *,
        query: str,
        chunks: list[dict[str, Any]],
        max_chars_per_chunk: int,
    ) -> tuple[list[dict[str, Any]], dict[str, str]]:
        """
        Comprime contexto para reducir ruido/token budget:
        conserva frases con mayor solape lexical con la consulta.
        """
        if not chunks:
            return chunks, {
                "rag_context_compressed": "0",
                "rag_context_original_chars": "0",
                "rag_context_compressed_chars": "0",
            }

        query_tokens = {
            token
            for token in re.findall(r"[a-z0-9áéíóúñ]+", (query or "").lower())
            if len(token) > 3
        }
        compressed_chunks: list[dict[str, Any]] = []
        original_chars = 0
        compressed_chars = 0

        for chunk in chunks:
            original_text = str(chunk.get("text") or "")
            original_chars += len(original_text)
            compressed_text = RAGContextAssembler._compress_text_by_query_overlap(
                original_text,
                query_tokens=query_tokens,
                max_chars=max_chars_per_chunk,
            )
            compressed_chars += len(compressed_text)
            compact_chunk = dict(chunk)
            compact_chunk["text"] = compressed_text
            compressed_chunks.append(compact_chunk)

        trace = {
            "rag_context_compressed": "1",
            "rag_context_original_chars": str(original_chars),
            "rag_context_compressed_chars": str(compressed_chars),
            "rag_context_compression_ratio": (
                f"{(compressed_chars / max(1, original_chars)):.3f}"
            ),
        }
        return compressed_chunks, trace

    @staticmethod
    def _compress_text_by_query_overlap(
        text: str,
        *,
        query_tokens: set[str],
        max_chars: int,
    ) -> str:
        if len(text) <= max_chars:
            return text

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[\.\!\?\:\;])\s+", text)
            if sentence and sentence.strip()
        ]
        if not sentences:
            return text[:max_chars]

        scored: list[tuple[float, int, str]] = []
        for idx, sentence in enumerate(sentences):
            tokens = {
                token
                for token in re.findall(r"[a-z0-9áéíóúñ]+", sentence.lower())
                if len(token) > 3
            }
            overlap = 0.0
            if query_tokens and tokens:
                overlap = len(query_tokens.intersection(tokens)) / max(1, len(query_tokens))
            length_bonus = min(0.15, len(sentence) / 1200.0)
            score = overlap + length_bonus
            scored.append((score, idx, sentence))

        scored.sort(key=lambda item: item[0], reverse=True)
        selected: list[tuple[int, str]] = []
        char_budget = 0
        for _score, idx, sentence in scored:
            extra_len = len(sentence) + (1 if selected else 0)
            if char_budget + extra_len > max_chars and selected:
                continue
            selected.append((idx, sentence))
            char_budget += extra_len
            if char_budget >= max_chars:
                break

        if not selected:
            return text[:max_chars]
        selected.sort(key=lambda item: item[0])
        compressed = " ".join(sentence for _, sentence in selected).strip()
        return compressed[:max_chars]
