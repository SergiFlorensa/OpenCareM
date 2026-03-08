"""
Utilities para ensamblar contexto RAG.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Optional

from app.core.config import settings
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
    def _extract_page_hint(section_value: str) -> str:
        normalized = str(section_value or "").lower()
        match = re.search(r"(?:pag(?:ina)?|p)\.?\s*(\d{1,4})", normalized)
        if not match:
            return ""
        return str(match.group(1)).strip()

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
            source_title = ""
            if document is not None:
                source = getattr(document, "source_file", None)
                source_title = str(getattr(document, "title", "") or "").strip()
            section_value = str(getattr(chunk, "section_path", "") or "sin seccion")
            if not source_title:
                source_title = section_value
            page_hint = RAGContextAssembler._extract_page_hint(section_value)
            chunk_dict = {
                "id": int(getattr(chunk, "id")),
                "text": str(getattr(chunk, "chunk_text", "")),
                "section": section_value,
                "score": float(getattr(chunk, "_rag_score", 0.0) or 0.0),
                "keywords": list(getattr(chunk, "keywords", []) or []),
                "questions": list(getattr(chunk, "custom_questions", []) or []),
                "source": str(source or "catalogo interno"),
                "source_title": source_title,
                "source_page": page_hint,
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
        if not chunks:
            return chunks, {
                "rag_context_compressed": "0",
                "rag_context_original_chars": "0",
                "rag_context_compressed_chars": "0",
            }

        compression_mode = str(
            settings.CLINICAL_CHAT_RAG_CONTEXT_COMPRESS_MODE or "extractive"
        ).strip().lower()
        if compression_mode == "extractive":
            return RAGContextAssembler._compress_rag_context_extractive(
                query=query,
                chunks=chunks,
                max_chars_per_chunk=max_chars_per_chunk,
            )
        return RAGContextAssembler._compress_rag_context_overlap(
            query=query,
            chunks=chunks,
            max_chars_per_chunk=max_chars_per_chunk,
        )

    @staticmethod
    def _compress_rag_context_overlap(
        *,
        query: str,
        chunks: list[dict[str, Any]],
        max_chars_per_chunk: int,
    ) -> tuple[list[dict[str, Any]], dict[str, str]]:
        query_tokens = RAGContextAssembler._tokenize_text(query)
        compressed_chunks: list[dict[str, Any]] = []
        original_chars = 0
        compressed_chars = 0

        for chunk in chunks:
            original_text = str(chunk.get("text") or "")
            cleaned_text = RAGContextAssembler._strip_chunk_decontextualization(original_text)
            original_chars += len(cleaned_text)
            compressed_text = RAGContextAssembler._compress_text_by_query_overlap(
                cleaned_text,
                query_tokens=query_tokens,
                max_chars=max_chars_per_chunk,
            )
            compressed_chars += len(compressed_text)
            compact_chunk = dict(chunk)
            compact_chunk["text"] = compressed_text
            compressed_chunks.append(compact_chunk)

        trace = {
            "rag_context_compressed": "1",
            "rag_context_compression_mode": "overlap",
            "rag_context_original_chars": str(original_chars),
            "rag_context_compressed_chars": str(compressed_chars),
            "rag_context_compression_ratio": (
                f"{(compressed_chars / max(1, original_chars)):.3f}"
            ),
        }
        return compressed_chunks, trace

    @staticmethod
    def _compress_rag_context_extractive(
        *,
        query: str,
        chunks: list[dict[str, Any]],
        max_chars_per_chunk: int,
    ) -> tuple[list[dict[str, Any]], dict[str, str]]:
        query_tokens = RAGContextAssembler._tokenize_text(query)
        top_sentences_per_chunk = max(
            1,
            int(settings.CLINICAL_CHAT_RAG_CONTEXT_TOP_SENTENCES_PER_CHUNK),
        )
        max_sentences_total = max(
            top_sentences_per_chunk,
            int(settings.CLINICAL_CHAT_RAG_CONTEXT_MAX_SENTENCES_TOTAL),
        )
        min_relevance = float(settings.CLINICAL_CHAT_RAG_CONTEXT_MIN_SENTENCE_RELEVANCE)
        empty_on_low_relevance = bool(settings.CLINICAL_CHAT_RAG_CONTEXT_EMPTY_ON_LOW_RELEVANCE)

        selected_candidates: list[dict[str, Any]] = []
        original_chars = 0
        sentence_candidates_total = 0

        for chunk_position, chunk in enumerate(chunks):
            raw_text = str(chunk.get("text") or "")
            cleaned_text = RAGContextAssembler._strip_chunk_decontextualization(raw_text)
            original_chars += len(cleaned_text)
            if not cleaned_text:
                continue
            retrieval_score = max(0.0, min(1.0, float(chunk.get("score") or 0.0)))
            section_tokens = RAGContextAssembler._tokenize_text(
                " ".join(
                    [
                        str(chunk.get("section") or ""),
                        str(chunk.get("source_title") or ""),
                    ]
                )
            )
            sentences = RAGContextAssembler._split_sentences(cleaned_text) or [cleaned_text]
            chunk_candidates: list[dict[str, Any]] = []
            for sentence_index, sentence in enumerate(sentences):
                normalized_sentence = re.sub(r"\s+", " ", sentence).strip()
                if len(normalized_sentence) < 20:
                    continue
                relevance = RAGContextAssembler._sentence_relevance_score(
                    sentence=normalized_sentence,
                    query_tokens=query_tokens,
                    section_tokens=section_tokens,
                    retrieval_score=retrieval_score,
                )
                sentence_candidates_total += 1
                chunk_candidates.append(
                    {
                        "chunk_position": chunk_position,
                        "sentence_index": sentence_index,
                        "sentence": normalized_sentence,
                        "relevance": relevance,
                    }
                )
            if not chunk_candidates:
                continue
            chunk_candidates.sort(
                key=lambda item: (float(item["relevance"]), -int(item["sentence_index"])),
                reverse=True,
            )
            kept_for_chunk = [
                item
                for item in chunk_candidates
                if float(item["relevance"]) >= min_relevance
            ][:top_sentences_per_chunk]
            if not kept_for_chunk and not empty_on_low_relevance:
                kept_for_chunk = chunk_candidates[:1]
            selected_candidates.extend(kept_for_chunk)

        selected_candidates.sort(key=lambda item: float(item["relevance"]), reverse=True)
        selected_candidates = selected_candidates[:max_sentences_total]
        if not selected_candidates and empty_on_low_relevance:
            return [], {
                "rag_context_compressed": "1",
                "rag_context_compression_mode": "extractive",
                "rag_context_original_chars": str(original_chars),
                "rag_context_compressed_chars": "0",
                "rag_context_compression_ratio": "0.000",
                "rag_context_sentence_candidates": str(sentence_candidates_total),
                "rag_context_sentences_selected": "0",
                "rag_context_empty_on_low_relevance": "1",
                "rag_context_compression_empty": "1",
            }

        selected_candidates.sort(
            key=lambda item: (int(item["chunk_position"]), int(item["sentence_index"]))
        )
        grouped_sentences: dict[int, list[str]] = {}
        for item in selected_candidates:
            grouped_sentences.setdefault(int(item["chunk_position"]), []).append(
                str(item["sentence"])
            )

        compressed_chunks: list[dict[str, Any]] = []
        compressed_chars = 0
        for chunk_position, chunk in enumerate(chunks):
            sentences = grouped_sentences.get(chunk_position)
            if not sentences:
                continue
            compressed_text = " ".join(dict.fromkeys(sentences)).strip()
            section_anchor = RAGContextAssembler._section_anchor_label(
                str(chunk.get("section") or "")
            )
            if (
                section_anchor
                and RAGContextAssembler._normalize_text(section_anchor)
                not in RAGContextAssembler._normalize_text(compressed_text)
            ):
                compressed_text = f"{section_anchor}: {compressed_text}".strip()
            if len(compressed_text) > max_chars_per_chunk:
                compressed_text = compressed_text[:max_chars_per_chunk].rstrip()
            if not compressed_text:
                continue
            compact_chunk = dict(chunk)
            compact_chunk["text"] = compressed_text
            compressed_chunks.append(compact_chunk)
            compressed_chars += len(compressed_text)

        trace = {
            "rag_context_compressed": "1",
            "rag_context_compression_mode": "extractive",
            "rag_context_original_chars": str(original_chars),
            "rag_context_compressed_chars": str(compressed_chars),
            "rag_context_compression_ratio": (
                f"{(compressed_chars / max(1, original_chars)):.3f}"
            ),
            "rag_context_sentence_candidates": str(sentence_candidates_total),
            "rag_context_sentences_selected": str(len(selected_candidates)),
            "rag_context_empty_on_low_relevance": "1" if empty_on_low_relevance else "0",
            "rag_context_compression_empty": "1" if not compressed_chunks else "0",
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
            tokens = RAGContextAssembler._tokenize_text(sentence)
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

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        return [
            sentence.strip()
            for sentence in re.split(r"(?<=[\.\!\?\:\;])\s+|\n+", str(text or ""))
            if sentence and sentence.strip()
        ]

    @staticmethod
    def _strip_chunk_decontextualization(text: str) -> str:
        lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
        kept: list[str] = []
        for line in lines:
            lowered = line.lower()
            if lowered.startswith("documento:"):
                continue
            if lowered.startswith("seccion:"):
                continue
            if lowered.startswith("contenido:"):
                line = line.split(":", 1)[1].strip()
            if line:
                kept.append(line)
        return " ".join(kept).strip()

    @staticmethod
    def _normalize_text(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", str(text or ""))
        return normalized.encode("ascii", "ignore").decode("ascii").lower()

    @staticmethod
    def _tokenize_text(text: str) -> set[str]:
        normalized = RAGContextAssembler._normalize_text(text)
        return {
            token
            for token in re.findall(r"[a-z0-9]+", normalized)
            if len(token) > 2
        }

    @staticmethod
    def _sentence_relevance_score(
        *,
        sentence: str,
        query_tokens: set[str],
        section_tokens: set[str],
        retrieval_score: float,
    ) -> float:
        sentence_tokens = RAGContextAssembler._tokenize_text(sentence)
        if not sentence_tokens:
            return 0.0
        overlap = RAGContextAssembler._soft_overlap_ratio(
            reference_tokens=query_tokens,
            candidate_tokens=sentence_tokens,
        )
        section_overlap = RAGContextAssembler._soft_overlap_ratio(
            reference_tokens=section_tokens,
            candidate_tokens=sentence_tokens,
        )
        action_markers = (
            "iniciar",
            "activar",
            "monitorizar",
            "reevaluar",
            "derivar",
            "escalar",
            "administrar",
            "solicitar",
            "priorizar",
            "valorar",
        )
        actionability = (
            0.12
            if any(
                marker in RAGContextAssembler._normalize_text(sentence)
                for marker in action_markers
            )
            else 0.0
        )
        numeric_bonus = 0.06 if re.search(r"\b\d+(?:[\.,]\d+)?\b", sentence) else 0.0
        return round(
            min(
                1.0,
                (overlap * 0.62)
                + (section_overlap * 0.10)
                + (retrieval_score * 0.18)
                + actionability
                + numeric_bonus,
            ),
            4,
        )

    @staticmethod
    def _section_anchor_label(section_path: str) -> str:
        parts = [part.strip() for part in str(section_path or "").split(">") if part.strip()]
        if not parts:
            return ""
        for part in parts:
            if part.lower() != "documento":
                return part
        return parts[0]

    @staticmethod
    def _soft_overlap_ratio(*, reference_tokens: set[str], candidate_tokens: set[str]) -> float:
        if not reference_tokens or not candidate_tokens:
            return 0.0
        matched = 0
        for ref in reference_tokens:
            if any(RAGContextAssembler._tokens_soft_match(ref, cand) for cand in candidate_tokens):
                matched += 1
        return matched / max(1, len(reference_tokens))

    @staticmethod
    def _tokens_soft_match(left: str, right: str) -> bool:
        if left == right:
            return True
        if min(len(left), len(right)) < 5:
            return False
        prefix_len = min(7, len(left), len(right))
        return left[:prefix_len] == right[:prefix_len]
