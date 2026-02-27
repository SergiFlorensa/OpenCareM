"""
Motor de recuperacion hibrido para RAG.

Combina similitud semantica (embeddings) con coincidencia lexical.
"""
from __future__ import annotations

import json
import logging
import math
import re
import time
import unicodedata
from array import array
from bisect import bisect_left, bisect_right
from collections import Counter, OrderedDict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

try:
    import numpy as np
except Exception:  # pragma: no cover - fallback defensivo
    np = None

from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import OllamaEmbeddingService

logger = logging.getLogger(__name__)


class HybridRetriever:
    """Recuperador hibrido de fragmentos clinicos."""
    _fts_bootstrap_state: bool | None = None
    _fts_bootstrap_error: str | None = None
    _fts_vocab_cache_state: bool | None = None
    _fts_vocab_cache_error: str | None = None
    _fts_vocab_cache_terms: tuple[str, ...] = ()
    _fts_vocab_cache_doc_freq: dict[str, int] = {}
    _fts_vocab_cache_loaded_at: float = 0.0
    _fts_postings_cache: OrderedDict[str, tuple[float, bytes]] = OrderedDict()
    _global_thesaurus_cache_state: bool | None = None
    _global_thesaurus_cache_error: str | None = None
    _global_thesaurus_cache_loaded_at: float = 0.0
    _global_thesaurus_cache_terms: dict[str, tuple[str, ...]] = {}
    _BOOLEAN_OPERATORS = {"AND", "OR", "NOT"}
    _BOOLEAN_PRECEDENCE = {"OR": 1, "AND": 2, "NOT": 3}
    _BOOLEAN_TOKEN_PATTERN = re.compile(
        r'"[^"]+"|\(|\)|\bAND\b|\bOR\b|\bNOT\b|/\d+|[a-z0-9#\-\+/\*]+',
        flags=re.IGNORECASE,
    )
    _PROXIMITY_TOKEN_PATTERN = re.compile(r"^/\d+$")
    _NEAR_OPERAND_PREFIX = "__NEAR__"

    _QUERY_EXPANSIONS: dict[str, list[str]] = {
        "oliguria": ["anuria", "diuresis", "insuficiencia_renal_aguda", "fra"],
        "anuria": ["oliguria", "diuresis", "fra"],
        "hiperkalemia": ["hiperpotasemia", "potasio_alto", "k_alto", "ecg"],
        "hiperpotasemia": ["hiperkalemia", "potasio", "ecg", "qrs_ancho"],
        "cefalea": ["dolor_cabeza", "neurologico", "red_flag"],
        "fosfenos": ["alteraciones_visuales", "preclampsia", "hta"],
        "neutropenia": ["neutropenia_febril", "fiebre", "oncologia", "aislamiento"],
        "febril": ["fiebre", "sepsis", "infeccion"],
        "oncologia": ["neutropenia_febril", "iraes", "cardio_oncologia"],
        "sepsis": ["qsofa", "lactato", "bundle", "shock_septico"],
        "shock": ["hipotension", "vasopresor", "perfuson", "critico"],
        "embarazo": ["gestante", "obstetricia", "preeclampsia"],
        "gestante": ["embarazo", "obstetricia", "preeclampsia"],
        "dolor_pelvico": ["ginecologia", "ectopico", "sangrado_vaginal"],
        "beta-hcg": ["embarazo", "ectopico", "ginecologia"],
        "disnea": ["respiratorio", "hipoxemia", "neumologia"],
    }

    _SPECIALTY_HINTS: dict[str, list[str]] = {
        "nephrology": ["renal", "potasio", "creatinina", "dialisis", "aeiou"],
        "oncology": ["neutropenia", "iraes", "inmunoterapia", "quimioterapia"],
        "gynecology_obstetrics": ["gestante", "preeclampsia", "sangrado", "obstetricia"],
        "pneumology": ["disnea", "hipoxemia", "oxigenoterapia", "gasometria"],
        "urology": ["obstruccion", "hidronefrosis", "retencion", "urinario"],
        "critical_ops": ["red_flags", "estabilizacion", "priorizacion", "shock"],
    }

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

    @staticmethod
    def _extract_boolean_terms(query: str) -> tuple[list[str], list[str], list[str], bool]:
        """
        Extrae terminos para retrieval booleano.

        Retorna: (include_terms, optional_terms, exclude_terms, explicit_boolean_ops)
        """
        tokens = re.findall(r"[a-z0-9#\-\+/\*]+", query.lower())
        explicit = any(token in {"and", "or", "not"} for token in tokens)
        include_terms: list[str] = []
        optional_terms: list[str] = []
        exclude_terms: list[str] = []

        if explicit:
            op = "and"
            for token in tokens:
                if token in {"and", "or", "not"}:
                    op = token
                    continue
                if len(token) < 3:
                    continue
                if op == "not":
                    exclude_terms.append(token)
                    op = "and"
                elif op == "or":
                    optional_terms.append(token)
                else:
                    include_terms.append(token)
        else:
            include_terms = [token for token in tokens if len(token) >= 4][:8]

        def _dedupe(items: list[str]) -> list[str]:
            return list(dict.fromkeys(items))

        return _dedupe(include_terms), _dedupe(optional_terms), _dedupe(exclude_terms), explicit

    @classmethod
    def _is_operand_token(cls, token: str) -> bool:
        return (
            token not in cls._BOOLEAN_OPERATORS
            and token not in {"(", ")"}
            and not cls._is_proximity_token(token)
            and bool(token.strip())
        )

    @classmethod
    def _is_proximity_token(cls, token: str) -> bool:
        return bool(cls._PROXIMITY_TOKEN_PATTERN.match(token))

    @classmethod
    def _build_near_operand_token(cls, *, left: str, right: str, distance: int) -> str:
        safe_distance = max(1, int(distance))
        return f"{cls._NEAR_OPERAND_PREFIX}{safe_distance}::{left}::{right}"

    @classmethod
    def _parse_near_operand_token(cls, token: str) -> tuple[str, str, int] | None:
        if not token.startswith(cls._NEAR_OPERAND_PREFIX):
            return None
        payload = token[len(cls._NEAR_OPERAND_PREFIX):]
        parts = payload.split("::", maxsplit=2)
        if len(parts) != 3:
            return None
        distance_str, left, right = parts
        if not distance_str.isdigit():
            return None
        return left, right, max(1, int(distance_str))

    @classmethod
    def _collapse_proximity_tokens(cls, tokens: list[str]) -> list[str]:
        if not tokens:
            return []
        collapsed: list[str] = []
        index = 0
        while index < len(tokens):
            token = tokens[index]
            if cls._is_proximity_token(token):
                if collapsed and index + 1 < len(tokens):
                    left = collapsed[-1]
                    right = tokens[index + 1]
                    if cls._is_operand_token(left) and cls._is_operand_token(right):
                        collapsed.pop()
                        collapsed.append(
                            cls._build_near_operand_token(
                                left=left,
                                right=right,
                                distance=int(token[1:]),
                            )
                        )
                        index += 2
                        continue
                index += 1
                continue
            collapsed.append(token)
            index += 1
        return collapsed

    @classmethod
    def _tokenize_boolean_query(cls, query: str) -> list[str]:
        raw_tokens = cls._BOOLEAN_TOKEN_PATTERN.findall(query or "")
        normalized: list[str] = []
        for token in raw_tokens:
            stripped = token.strip()
            if not stripped:
                continue
            upper = stripped.upper()
            if upper in cls._BOOLEAN_OPERATORS:
                normalized.append(upper)
                continue
            if stripped in {"(", ")"}:
                normalized.append(stripped)
                continue
            if stripped.startswith('"') and stripped.endswith('"'):
                phrase_parts = re.findall(r"[a-z0-9#\-\+/]+", stripped.lower())
                if phrase_parts:
                    normalized.append(f"\"{' '.join(phrase_parts)}\"")
                continue
            term_parts = re.findall(r"[a-z0-9#\-\+/\*]+", stripped.lower())
            if term_parts:
                normalized.append(term_parts[0])

        normalized = cls._collapse_proximity_tokens(normalized)
        with_implicit_and: list[str] = []
        for token in normalized:
            if with_implicit_and:
                prev = with_implicit_and[-1]
                prev_closes = cls._is_operand_token(prev) or prev == ")"
                curr_opens = cls._is_operand_token(token) or token in {"(", "NOT"}
                if prev_closes and curr_opens:
                    with_implicit_and.append("AND")
            with_implicit_and.append(token)
        return with_implicit_and

    @classmethod
    def _to_rpn(cls, tokens: list[str]) -> list[str]:
        if not tokens:
            return []
        output: list[str] = []
        stack: list[str] = []
        for token in tokens:
            if cls._is_operand_token(token):
                output.append(token)
                continue
            if token in cls._BOOLEAN_OPERATORS:
                while stack and stack[-1] in cls._BOOLEAN_OPERATORS:
                    top = stack[-1]
                    token_prec = cls._BOOLEAN_PRECEDENCE[token]
                    top_prec = cls._BOOLEAN_PRECEDENCE[top]
                    # NOT es unario y asociativo a la derecha.
                    should_pop = (
                        token != "NOT" and token_prec <= top_prec
                    ) or (
                        token == "NOT" and token_prec < top_prec
                    )
                    if not should_pop:
                        break
                    output.append(stack.pop())
                stack.append(token)
                continue
            if token == "(":
                stack.append(token)
                continue
            if token == ")":
                found_open = False
                while stack:
                    top = stack.pop()
                    if top == "(":
                        found_open = True
                        break
                    output.append(top)
                if not found_open:
                    return []

        while stack:
            top = stack.pop()
            if top in {"(", ")"}:
                return []
            output.append(top)
        return output

    @classmethod
    def _extract_operands_from_rpn(cls, rpn_tokens: list[str]) -> list[str]:
        operands: list[str] = []
        for token in rpn_tokens:
            if cls._is_operand_token(token):
                operands.append(token)
        return list(dict.fromkeys(operands))

    @classmethod
    def _build_operand_context_map(
        cls,
        tokens: list[str],
    ) -> dict[str, tuple[str | None, str | None]]:
        operands = [token for token in tokens if cls._is_operand_token(token)]
        context_map: dict[str, tuple[str | None, str | None]] = {}
        for index, operand in enumerate(operands):
            left_neighbor = operands[index - 1] if index > 0 else None
            right_neighbor = operands[index + 1] if index + 1 < len(operands) else None
            context_map.setdefault(operand, (left_neighbor, right_neighbor))
        return context_map

    @classmethod
    def _context_term_from_neighbor(cls, token: str | None, *, use_last: bool) -> str | None:
        if not token:
            return None
        if token.startswith(cls._NEAR_OPERAND_PREFIX):
            return None
        if token.startswith('"') and token.endswith('"'):
            token_content = token[1:-1]
            terms = re.findall(r"[a-z0-9#\-\+/]+", token_content.lower())
        else:
            terms = re.findall(r"[a-z0-9#\-\+/]+", token.lower())
        if not terms:
            return None
        return terms[-1] if use_last else terms[0]

    @staticmethod
    def _levenshtein_distance(left: str, right: str, max_distance: int = 2) -> int:
        if left == right:
            return 0
        if not left:
            return len(right)
        if not right:
            return len(left)
        if abs(len(left) - len(right)) > max_distance:
            return max_distance + 1

        prev_row = list(range(len(right) + 1))
        for i, left_char in enumerate(left, start=1):
            current_row = [i]
            row_min = current_row[0]
            for j, right_char in enumerate(right, start=1):
                insert_cost = current_row[j - 1] + 1
                delete_cost = prev_row[j] + 1
                replace_cost = prev_row[j - 1] + int(left_char != right_char)
                value = min(insert_cost, delete_cost, replace_cost)
                current_row.append(value)
                if value < row_min:
                    row_min = value
            if row_min > max_distance:
                return max_distance + 1
            prev_row = current_row
        return prev_row[-1]

    @staticmethod
    def _strip_accents(value: str) -> str:
        normalized = unicodedata.normalize("NFD", value)
        return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")

    @classmethod
    def _is_wildcard_token(cls, token: str) -> bool:
        if "*" not in token:
            return False
        return bool(re.search(r"[a-z0-9#\-\+/]", token.lower()))

    @staticmethod
    def _build_kgrams(term: str, k: int) -> set[str]:
        clean = re.sub(r"[^a-z0-9]+", "", term.lower())
        if not clean:
            return set()
        if len(clean) < k:
            return {clean}
        padded = f"${clean}$"
        return {
            padded[index : index + k]
            for index in range(0, max(1, len(padded) - k + 1))
            if len(padded[index : index + k]) == k
        }

    @staticmethod
    def _jaccard_similarity(left: set[str], right: set[str]) -> float:
        if not left and not right:
            return 1.0
        if not left or not right:
            return 0.0
        inter = len(left.intersection(right))
        union = len(left.union(right))
        if union <= 0:
            return 0.0
        return inter / union

    @classmethod
    def _soundex(cls, term: str) -> str:
        if not term:
            return ""
        normalized = cls._strip_accents(term.lower())
        clean = re.sub(r"[^a-z]", "", normalized)
        if not clean:
            return ""
        first = clean[0].upper()
        code_map = {
            "b": "1",
            "f": "1",
            "p": "1",
            "v": "1",
            "c": "2",
            "g": "2",
            "j": "2",
            "k": "2",
            "q": "2",
            "s": "2",
            "x": "2",
            "z": "2",
            "d": "3",
            "t": "3",
            "l": "4",
            "m": "5",
            "n": "5",
            "r": "6",
        }
        encoded: list[str] = []
        previous = code_map.get(clean[0], "0")
        for char in clean[1:]:
            current = code_map.get(char, "0")
            if current != previous:
                encoded.append(current)
            previous = current
        filtered = [item for item in encoded if item != "0"]
        value = first + "".join(filtered)
        return (value + "000")[:4]

    @staticmethod
    def _intersect_sorted_ids(left: list[int], right: list[int]) -> list[int]:
        """Interseccion lineal O(x+y) con dos punteros."""
        i = 0
        j = 0
        result: list[int] = []
        while i < len(left) and j < len(right):
            a = left[i]
            b = right[j]
            if a == b:
                result.append(a)
                i += 1
                j += 1
            elif a < b:
                i += 1
            else:
                j += 1
        return result

    @staticmethod
    def _intersect_sorted_ids_with_skips(
        left: list[int],
        right: list[int],
    ) -> tuple[list[int], int]:
        """Interseccion con atajos tipo skip pointer (heuristica sqrt(P))."""
        if not left or not right:
            return [], 0
        i = 0
        j = 0
        result: list[int] = []
        shortcuts = 0
        skip_left = max(2, int(math.sqrt(len(left))))
        skip_right = max(2, int(math.sqrt(len(right))))
        while i < len(left) and j < len(right):
            a = left[i]
            b = right[j]
            if a == b:
                result.append(a)
                i += 1
                j += 1
                continue
            if a < b:
                jumped = False
                next_i = i + skip_left
                while next_i < len(left) and left[next_i] <= b:
                    i = next_i
                    next_i += skip_left
                    jumped = True
                    shortcuts += 1
                if not jumped or (i < len(left) and left[i] < b):
                    i += 1
                continue
            jumped = False
            next_j = j + skip_right
            while next_j < len(right) and right[next_j] <= a:
                j = next_j
                next_j += skip_right
                jumped = True
                shortcuts += 1
            if not jumped or (j < len(right) and right[j] < a):
                j += 1
        return result, shortcuts

    @staticmethod
    def _union_sorted_ids(left: list[int], right: list[int]) -> list[int]:
        i = 0
        j = 0
        result: list[int] = []
        while i < len(left) and j < len(right):
            a = left[i]
            b = right[j]
            if a == b:
                result.append(a)
                i += 1
                j += 1
            elif a < b:
                result.append(a)
                i += 1
            else:
                result.append(b)
                j += 1
        if i < len(left):
            result.extend(left[i:])
        if j < len(right):
            result.extend(right[j:])
        return result

    @staticmethod
    def _difference_sorted_ids(base: list[int], excluded: list[int]) -> list[int]:
        i = 0
        j = 0
        result: list[int] = []
        while i < len(base) and j < len(excluded):
            a = base[i]
            b = excluded[j]
            if a == b:
                i += 1
                j += 1
            elif a < b:
                result.append(a)
                i += 1
            else:
                j += 1
        if i < len(base):
            result.extend(base[i:])
        return result

    @staticmethod
    def _gaps_from_ids(ids: list[int]) -> list[int]:
        gaps: list[int] = []
        previous = 0
        for value in ids:
            safe_value = max(0, int(value))
            gap = safe_value - previous
            if gap <= 0:
                continue
            gaps.append(gap)
            previous = safe_value
        return gaps

    @staticmethod
    def _ids_from_gaps(gaps: list[int]) -> list[int]:
        ids: list[int] = []
        current = 0
        for gap in gaps:
            safe_gap = max(0, int(gap))
            if safe_gap <= 0:
                continue
            current += safe_gap
            ids.append(current)
        return ids

    @staticmethod
    def _vb_encode_number(value: int) -> bytes:
        safe_value = max(1, int(value))
        chunks: list[int] = [safe_value % 128]
        safe_value //= 128
        while safe_value > 0:
            chunks.append(safe_value % 128)
            safe_value //= 128
        chunks.reverse()
        chunks[-1] |= 0x80
        return bytes(chunks)

    @classmethod
    def _vb_encode_gaps(cls, gaps: list[int]) -> bytes:
        payload = bytearray()
        for gap in gaps:
            payload.extend(cls._vb_encode_number(gap))
        return bytes(payload)

    @staticmethod
    def _vb_decode_gaps(payload: bytes) -> list[int]:
        result: list[int] = []
        current = 0
        for byte in payload:
            current = (current * 128) + (byte & 0x7F)
            if byte & 0x80:
                if current > 0:
                    result.append(current)
                current = 0
        return result

    @staticmethod
    def _gamma_encode_gaps(gaps: list[int]) -> bytes:
        bits: list[str] = []
        for gap in gaps:
            safe_gap = max(1, int(gap))
            binary = f"{safe_gap:b}"
            unary = ("1" * (len(binary) - 1)) + "0"
            bits.append(unary + binary[1:])
        bit_stream = "".join(bits)
        bit_len = len(bit_stream)
        if bit_len == 0:
            return (0).to_bytes(4, byteorder="big")
        pad_len = (8 - (bit_len % 8)) % 8
        padded = bit_stream + ("0" * pad_len)
        payload = bytearray(int(padded[index : index + 8], 2) for index in range(0, len(padded), 8))
        return bit_len.to_bytes(4, byteorder="big") + bytes(payload)

    @staticmethod
    def _gamma_decode_gaps(payload: bytes) -> list[int]:
        if len(payload) < 4:
            return []
        bit_len = int.from_bytes(payload[:4], byteorder="big")
        if bit_len <= 0:
            return []
        raw_bytes = payload[4:]
        bit_stream = "".join(f"{byte:08b}" for byte in raw_bytes)[:bit_len]
        gaps: list[int] = []
        index = 0
        while index < len(bit_stream):
            ones = 0
            while index < len(bit_stream) and bit_stream[index] == "1":
                ones += 1
                index += 1
            if index >= len(bit_stream):
                break
            index += 1  # consume delimiter '0'
            offset_len = ones
            if index + offset_len > len(bit_stream):
                break
            offset = bit_stream[index : index + offset_len]
            index += offset_len
            binary = "1" + offset
            gap = int(binary, 2)
            if gap > 0:
                gaps.append(gap)
        return gaps

    @classmethod
    def _encode_postings_ids(cls, ids: list[int]) -> bytes:
        gaps = cls._gaps_from_ids(ids)
        if not gaps:
            return b""
        if settings.CLINICAL_CHAT_RAG_POSTINGS_CACHE_ENCODING == "gamma":
            return cls._gamma_encode_gaps(gaps)
        return cls._vb_encode_gaps(gaps)

    @classmethod
    def _decode_postings_ids(cls, payload: bytes) -> list[int]:
        if not payload:
            return []
        if settings.CLINICAL_CHAT_RAG_POSTINGS_CACHE_ENCODING == "gamma":
            gaps = cls._gamma_decode_gaps(payload)
        else:
            gaps = cls._vb_decode_gaps(payload)
        return cls._ids_from_gaps(gaps)

    @staticmethod
    def _build_postings_cache_key(
        *,
        kind: str,
        match_query: str,
        specialty_filter: Optional[str],
        limit: int,
    ) -> str:
        specialty = str(specialty_filter or "").strip().lower() or "*"
        return f"{kind}|{specialty}|{int(max(1, limit))}|{match_query}"

    @classmethod
    def _prune_postings_cache(cls) -> None:
        ttl_seconds = settings.CLINICAL_CHAT_RAG_POSTINGS_CACHE_TTL_SECONDS
        now = time.time()
        expired_keys = [
            cache_key
            for cache_key, (saved_at, _) in cls._fts_postings_cache.items()
            if (now - saved_at) > ttl_seconds
        ]
        for cache_key in expired_keys:
            cls._fts_postings_cache.pop(cache_key, None)
        max_entries = settings.CLINICAL_CHAT_RAG_POSTINGS_CACHE_MAX_ENTRIES
        while len(cls._fts_postings_cache) > max_entries:
            cls._fts_postings_cache.popitem(last=False)

    @classmethod
    def _get_cached_postings(
        cls,
        *,
        cache_key: str,
        cache_stats: dict[str, int] | None = None,
    ) -> list[int] | None:
        if not settings.CLINICAL_CHAT_RAG_POSTINGS_CACHE_ENABLED:
            return None
        cls._prune_postings_cache()
        item = cls._fts_postings_cache.get(cache_key)
        if item is None:
            if cache_stats is not None:
                cache_stats["misses"] = cache_stats.get("misses", 0) + 1
            return None
        saved_at, payload = item
        if (time.time() - saved_at) > settings.CLINICAL_CHAT_RAG_POSTINGS_CACHE_TTL_SECONDS:
            cls._fts_postings_cache.pop(cache_key, None)
            if cache_stats is not None:
                cache_stats["misses"] = cache_stats.get("misses", 0) + 1
            return None
        cls._fts_postings_cache.move_to_end(cache_key)
        if cache_stats is not None:
            cache_stats["hits"] = cache_stats.get("hits", 0) + 1
        return cls._decode_postings_ids(payload)

    @classmethod
    def _set_cached_postings(
        cls,
        *,
        cache_key: str,
        ids: list[int],
        cache_stats: dict[str, int] | None = None,
    ) -> None:
        if not settings.CLINICAL_CHAT_RAG_POSTINGS_CACHE_ENABLED:
            return
        payload = cls._encode_postings_ids(ids)
        cls._fts_postings_cache[cache_key] = (time.time(), payload)
        cls._fts_postings_cache.move_to_end(cache_key)
        pre_size = len(cls._fts_postings_cache)
        cls._prune_postings_cache()
        post_size = len(cls._fts_postings_cache)
        if cache_stats is not None and post_size < pre_size:
            cache_stats["evictions"] = cache_stats.get("evictions", 0) + (pre_size - post_size)

    @classmethod
    def _ensure_sqlite_fts_index(cls, db: Session) -> tuple[bool, dict[str, str]]:
        trace: dict[str, str] = {
            "fts_candidate_enabled": (
                "1" if settings.CLINICAL_CHAT_RAG_FTS_CANDIDATE_ENABLED else "0"
            )
        }
        if not settings.CLINICAL_CHAT_RAG_FTS_CANDIDATE_ENABLED:
            trace["fts_candidate_reason"] = "disabled_by_config"
            return False, trace

        bind = db.get_bind()
        if bind.dialect.name != "sqlite":
            trace["fts_candidate_reason"] = "non_sqlite_backend"
            return False, trace

        if cls._fts_bootstrap_state is True:
            trace["fts_candidate_ready"] = "1"
            return True, trace
        if cls._fts_bootstrap_state is False:
            trace["fts_candidate_ready"] = "0"
            trace["fts_candidate_error"] = cls._fts_bootstrap_error or "bootstrap_failed"
            return False, trace

        try:
            with bind.begin() as conn:
                conn.exec_driver_sql(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS document_chunks_fts
                    USING fts5(
                        chunk_text,
                        section_path,
                        keywords,
                        specialty,
                        content='document_chunks',
                        content_rowid='id',
                        tokenize='unicode61 remove_diacritics 2'
                    );
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS document_chunks_fts_vocab
                    USING fts5vocab(document_chunks_fts, 'row');
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TRIGGER IF NOT EXISTS document_chunks_fts_ai
                    AFTER INSERT ON document_chunks BEGIN
                        INSERT INTO document_chunks_fts(
                            rowid, chunk_text, section_path, keywords, specialty
                        )
                        VALUES (
                            new.id,
                            new.chunk_text,
                            COALESCE(new.section_path, ''),
                            COALESCE(CAST(new.keywords AS TEXT), ''),
                            COALESCE(new.specialty, '')
                        );
                    END;
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TRIGGER IF NOT EXISTS document_chunks_fts_ad
                    AFTER DELETE ON document_chunks BEGIN
                        INSERT INTO document_chunks_fts(
                            document_chunks_fts,
                            rowid,
                            chunk_text,
                            section_path,
                            keywords,
                            specialty
                        )
                        VALUES (
                            'delete',
                            old.id,
                            old.chunk_text,
                            COALESCE(old.section_path, ''),
                            COALESCE(CAST(old.keywords AS TEXT), ''),
                            COALESCE(old.specialty, '')
                        );
                    END;
                    """
                )
                conn.exec_driver_sql(
                    """
                    CREATE TRIGGER IF NOT EXISTS document_chunks_fts_au
                    AFTER UPDATE ON document_chunks BEGIN
                        INSERT INTO document_chunks_fts(
                            document_chunks_fts,
                            rowid,
                            chunk_text,
                            section_path,
                            keywords,
                            specialty
                        )
                        VALUES (
                            'delete',
                            old.id,
                            old.chunk_text,
                            COALESCE(old.section_path, ''),
                            COALESCE(CAST(old.keywords AS TEXT), ''),
                            COALESCE(old.specialty, '')
                        );
                        INSERT INTO document_chunks_fts(
                            rowid, chunk_text, section_path, keywords, specialty
                        )
                        VALUES (
                            new.id,
                            new.chunk_text,
                            COALESCE(new.section_path, ''),
                            COALESCE(CAST(new.keywords AS TEXT), ''),
                            COALESCE(new.specialty, '')
                        );
                    END;
                    """
                )
                conn.exec_driver_sql(
                    """
                    INSERT INTO document_chunks_fts(document_chunks_fts)
                    VALUES ('rebuild');
                    """
                )
            cls._fts_bootstrap_state = True
            trace["fts_candidate_ready"] = "1"
            return True, trace
        except Exception as exc:  # pragma: no cover - depende de build sqlite
            cls._fts_bootstrap_state = False
            cls._fts_bootstrap_error = exc.__class__.__name__
            trace["fts_candidate_ready"] = "0"
            trace["fts_candidate_error"] = exc.__class__.__name__
            logger.warning("No se pudo inicializar FTS candidate index: %s", exc)
            return False, trace

    @classmethod
    def _ensure_fts_vocab_cache(cls, db: Session) -> bool:
        if not settings.CLINICAL_CHAT_RAG_VOCAB_CACHE_ENABLED:
            return False
        now = time.time()
        ttl_seconds = settings.CLINICAL_CHAT_RAG_VOCAB_CACHE_TTL_SECONDS
        if (
            cls._fts_vocab_cache_state is True
            and cls._fts_vocab_cache_terms
            and (now - cls._fts_vocab_cache_loaded_at) <= ttl_seconds
        ):
            return True
        try:
            rows = db.execute(
                text(
                    """
                    SELECT term, doc
                    FROM document_chunks_fts_vocab
                    ORDER BY term ASC
                    LIMIT :limit_n
                    """
                ),
                {"limit_n": int(settings.CLINICAL_CHAT_RAG_VOCAB_CACHE_MAX_TERMS)},
            ).fetchall()
            terms: list[str] = []
            doc_freq: dict[str, int] = {}
            for term_value, doc_value in rows:
                normalized = str(term_value or "").strip().lower()
                if not normalized:
                    continue
                if normalized not in doc_freq:
                    terms.append(normalized)
                doc_freq[normalized] = int(doc_value or 0)
            cls._fts_vocab_cache_terms = tuple(terms)
            cls._fts_vocab_cache_doc_freq = doc_freq
            cls._fts_vocab_cache_loaded_at = now
            cls._fts_vocab_cache_state = True
            cls._fts_vocab_cache_error = None
            return True
        except Exception as exc:  # pragma: no cover - depende de sqlite/fts5 local
            cls._fts_vocab_cache_state = False
            cls._fts_vocab_cache_error = exc.__class__.__name__
            return False

    @staticmethod
    def _glob_to_regex(glob_pattern: str) -> re.Pattern[str]:
        escaped = re.escape(glob_pattern)
        regex_pattern = "^" + escaped.replace(r"\*", ".*") + "$"
        return re.compile(regex_pattern)

    @classmethod
    def _query_vocab_rows(
        cls,
        *,
        db: Session,
        glob_pattern: str,
        limit: int,
        min_len: int | None = None,
        max_len: int | None = None,
    ) -> tuple[list[tuple[str, int]], str]:
        use_cache = cls._ensure_fts_vocab_cache(db)
        if use_cache:
            terms = cls._fts_vocab_cache_terms
            doc_freq = cls._fts_vocab_cache_doc_freq
            candidates: list[str] = []
            simple_prefix = glob_pattern.endswith("*") and glob_pattern.count("*") == 1
            if simple_prefix:
                prefix = glob_pattern[:-1]
                start = bisect_left(terms, prefix)
                end = bisect_right(terms, f"{prefix}\uffff")
                candidates = list(terms[start:end])
            else:
                regex = cls._glob_to_regex(glob_pattern)
                for term_value in terms:
                    if regex.match(term_value):
                        candidates.append(term_value)
            filtered: list[tuple[str, int]] = []
            for candidate in candidates:
                candidate_len = len(candidate)
                if min_len is not None and candidate_len < min_len:
                    continue
                if max_len is not None and candidate_len > max_len:
                    continue
                filtered.append((candidate, int(doc_freq.get(candidate, 0))))
            filtered.sort(key=lambda item: item[1], reverse=True)
            return filtered[: int(max(1, limit))], "cache"

        stmt = """
            SELECT term, doc
            FROM document_chunks_fts_vocab
            WHERE term GLOB :glob_pattern
        """
        params: dict[str, object] = {
            "glob_pattern": glob_pattern,
            "limit_n": int(max(1, limit)),
        }
        if min_len is not None:
            stmt += " AND length(term) >= :min_len"
            params["min_len"] = int(min_len)
        if max_len is not None:
            stmt += " AND length(term) <= :max_len"
            params["max_len"] = int(max_len)
        stmt += " ORDER BY doc DESC LIMIT :limit_n"
        rows = db.execute(text(stmt), params).fetchall()
        normalized_rows = [
            (str(term_value or "").strip().lower(), int(doc_value or 0))
            for term_value, doc_value in rows
            if str(term_value or "").strip()
        ]
        return normalized_rows, "db"

    @staticmethod
    def _build_match_operand(term: str, *, is_phrase: bool = False) -> str:
        normalized_term = " ".join(re.findall(r"[a-z0-9#\-\+/]+", term.lower()))
        if not normalized_term:
            return ""
        must_quote = is_phrase or bool(re.search(r"[^a-z0-9_]", normalized_term))
        return f"\"{normalized_term}\"" if must_quote else normalized_term

    @staticmethod
    def _term_variants(term: str) -> list[str]:
        normalized_term = " ".join(re.findall(r"[a-z0-9#\-\+/]+", term.lower()))
        if not normalized_term:
            return []
        variants = [normalized_term]
        compact = normalized_term.replace("-", "").replace("_", "")
        if compact and compact != normalized_term:
            variants.append(compact)
        space_variant = normalized_term.replace("-", " ").replace("_", " ")
        if space_variant and space_variant != normalized_term:
            variants.append(space_variant)
        return list(dict.fromkeys(variants))

    @classmethod
    def _fetch_postings_for_term(
        cls,
        *,
        db: Session,
        term: str,
        specialty_filter: Optional[str],
        limit: int,
        is_phrase: bool = False,
        cache_stats: dict[str, int] | None = None,
    ) -> list[int]:
        if not term:
            return []
        match_query = cls._build_match_operand(term, is_phrase=is_phrase)
        if not match_query:
            return []
        cache_key = cls._build_postings_cache_key(
            kind="phrase" if is_phrase else "term",
            match_query=match_query,
            specialty_filter=specialty_filter,
            limit=limit,
        )
        cached = cls._get_cached_postings(cache_key=cache_key, cache_stats=cache_stats)
        if cached is not None:
            return cached
        stmt = """
            SELECT dc.id
            FROM document_chunks_fts fts
            JOIN document_chunks dc ON dc.id = fts.rowid
            WHERE document_chunks_fts MATCH :match_query
        """
        params: dict[str, object] = {
            "match_query": match_query,
            "limit_n": int(max(1, limit)),
        }
        if specialty_filter:
            stmt += " AND lower(COALESCE(dc.specialty, '')) = :specialty"
            params["specialty"] = str(specialty_filter).strip().lower()
        stmt += " ORDER BY dc.id ASC LIMIT :limit_n"
        rows = db.execute(text(stmt), params).fetchall()
        postings = [int(row[0]) for row in rows]
        cls._set_cached_postings(
            cache_key=cache_key,
            ids=postings,
            cache_stats=cache_stats,
        )
        return postings

    @classmethod
    def _fetch_postings_for_near(
        cls,
        *,
        db: Session,
        left_term: str,
        right_term: str,
        distance: int,
        specialty_filter: Optional[str],
        limit: int,
        cache_stats: dict[str, int] | None = None,
    ) -> list[int]:
        left_is_phrase = left_term.startswith('"') and left_term.endswith('"')
        right_is_phrase = right_term.startswith('"') and right_term.endswith('"')
        left_clean = left_term[1:-1] if left_is_phrase else left_term
        right_clean = right_term[1:-1] if right_is_phrase else right_term
        left_operand = cls._build_match_operand(left_clean, is_phrase=left_is_phrase)
        right_operand = cls._build_match_operand(right_clean, is_phrase=right_is_phrase)
        if not left_operand or not right_operand:
            return []
        near_distance = max(1, int(distance))
        match_query = f"NEAR({left_operand} {right_operand}, {near_distance})"
        cache_key = cls._build_postings_cache_key(
            kind="near",
            match_query=match_query,
            specialty_filter=specialty_filter,
            limit=limit,
        )
        cached = cls._get_cached_postings(cache_key=cache_key, cache_stats=cache_stats)
        if cached is not None:
            return cached
        stmt = """
            SELECT dc.id
            FROM document_chunks_fts fts
            JOIN document_chunks dc ON dc.id = fts.rowid
            WHERE document_chunks_fts MATCH :match_query
        """
        params: dict[str, object] = {
            "match_query": match_query,
            "limit_n": int(max(1, limit)),
        }
        if specialty_filter:
            stmt += " AND lower(COALESCE(dc.specialty, '')) = :specialty"
            params["specialty"] = str(specialty_filter).strip().lower()
        stmt += " ORDER BY dc.id ASC LIMIT :limit_n"
        rows = db.execute(text(stmt), params).fetchall()
        postings = [int(row[0]) for row in rows]
        cls._set_cached_postings(
            cache_key=cache_key,
            ids=postings,
            cache_stats=cache_stats,
        )
        return postings

    @staticmethod
    def _fetch_universe_ids(
        *,
        db: Session,
        specialty_filter: Optional[str],
        limit: int,
    ) -> list[int]:
        stmt = "SELECT id FROM document_chunks"
        params: dict[str, object] = {"limit_n": int(max(1, limit))}
        if specialty_filter:
            stmt += " WHERE lower(COALESCE(specialty, '')) = :specialty"
            params["specialty"] = str(specialty_filter).strip().lower()
        stmt += " ORDER BY id ASC LIMIT :limit_n"
        rows = db.execute(text(stmt), params).fetchall()
        return [int(row[0]) for row in rows]

    def _expand_wildcard_term(
        self,
        *,
        db: Session,
        term: str,
        limit: int,
        vocab_stats: dict[str, int] | None = None,
    ) -> list[str]:
        if not settings.CLINICAL_CHAT_RAG_WILDCARD_ENABLED:
            return []
        normalized = " ".join(re.findall(r"[a-z0-9#\-\+/\*]+", term.lower()))
        if not normalized or "*" not in normalized:
            return []
        if normalized in {"*", "**"}:
            return []
        glob_pattern = re.sub(r"[^a-z0-9\*]", "", normalized)
        if not glob_pattern:
            return []
        core_for_kgram = glob_pattern.replace("*", "")
        query_kgrams = self._build_kgrams(
            core_for_kgram,
            settings.CLINICAL_CHAT_RAG_KGRAM_SIZE,
        )
        try:
            rows, source = self._query_vocab_rows(
                db=db,
                glob_pattern=glob_pattern,
                limit=max(8, limit),
            )
            if vocab_stats is not None:
                vocab_stats[f"{source}_hits"] = vocab_stats.get(f"{source}_hits", 0) + 1
        except Exception:  # pragma: no cover - depende de sqlite/fts5 local
            return []
        if not rows:
            return []

        accepted: list[tuple[str, int]] = []
        for term_value, doc_freq in rows:
            candidate = str(term_value or "").strip().lower()
            if not candidate:
                continue
            if query_kgrams:
                candidate_kgrams = self._build_kgrams(
                    candidate,
                    settings.CLINICAL_CHAT_RAG_KGRAM_SIZE,
                )
                similarity = self._jaccard_similarity(query_kgrams, candidate_kgrams)
                if similarity < settings.CLINICAL_CHAT_RAG_KGRAM_JACCARD_MIN:
                    continue
            accepted.append((candidate, int(doc_freq or 0)))
        if not accepted:
            return []
        accepted.sort(key=lambda item: item[1], reverse=True)
        max_expansions = settings.CLINICAL_CHAT_RAG_WILDCARD_MAX_EXPANSIONS
        return list(
            dict.fromkeys(
                term_value
                for term_value, _ in accepted[:max_expansions]
            )
        )

    def _bigram_phrase_count(
        self,
        *,
        db: Session,
        left_term: str,
        right_term: str,
        specialty_filter: Optional[str],
    ) -> int:
        left_clean = self._context_term_from_neighbor(left_term, use_last=True)
        right_clean = self._context_term_from_neighbor(right_term, use_last=False)
        if not left_clean or not right_clean:
            return 0
        match_query = self._build_match_operand(
            f"{left_clean} {right_clean}",
            is_phrase=True,
        )
        if not match_query:
            return 0
        stmt = """
            SELECT COUNT(1)
            FROM document_chunks_fts fts
            JOIN document_chunks dc ON dc.id = fts.rowid
            WHERE document_chunks_fts MATCH :match_query
        """
        params: dict[str, object] = {"match_query": match_query}
        if specialty_filter:
            stmt += " AND lower(COALESCE(dc.specialty, '')) = :specialty"
            params["specialty"] = str(specialty_filter).strip().lower()
        try:
            value = db.execute(text(stmt), params).scalar()
        except Exception:  # pragma: no cover - depende de sqlite/fts5 local
            return 0
        return int(value or 0)

    def _suggest_term_correction(
        self,
        *,
        db: Session,
        term: str,
        max_distance: int,
        left_context: str | None = None,
        right_context: str | None = None,
        specialty_filter: Optional[str] = None,
        candidate_limit: int = 128,
        vocab_stats: dict[str, int] | None = None,
    ) -> Optional[str]:
        if not settings.CLINICAL_CHAT_RAG_SPELL_CORRECTION_ENABLED:
            return None
        normalized_term = " ".join(re.findall(r"[a-z0-9#\-\+/]+", term.lower()))
        if len(normalized_term) < 5:
            return None
        if " " in normalized_term:
            return None
        prefix = f"{normalized_term[0]}*"
        min_len = max(3, len(normalized_term) - max_distance)
        max_len = len(normalized_term) + max_distance
        try:
            rows, source = self._query_vocab_rows(
                db=db,
                glob_pattern=prefix,
                min_len=min_len,
                max_len=max_len,
                limit=max(16, candidate_limit),
            )
            if vocab_stats is not None:
                vocab_stats[f"{source}_hits"] = vocab_stats.get(f"{source}_hits", 0) + 1
        except Exception:  # pragma: no cover - depende de sqlite/fts5 local
            return None
        if not rows:
            return None

        query_kgrams = self._build_kgrams(
            normalized_term,
            settings.CLINICAL_CHAT_RAG_KGRAM_SIZE,
        )
        best_term: Optional[str] = None
        best_distance: Optional[int] = None
        best_context_score = -1
        best_doc_freq = -1
        soundex_target = self._soundex(normalized_term)
        soundex_best_term: Optional[str] = None
        soundex_best_context_score = -1
        soundex_best_doc_freq = -1
        contextual_enabled = bool(
            settings.CLINICAL_CHAT_RAG_CONTEXTUAL_SPELL_ENABLED
            and (left_context or right_context)
        )
        context_cache: dict[tuple[str, str], int] = {}
        if contextual_enabled:
            max_candidates = settings.CLINICAL_CHAT_RAG_CONTEXTUAL_SPELL_MAX_CANDIDATES
            rows = rows[: max(8, max_candidates)]

        def phrase_count(left_term: str, right_term: str) -> int:
            cache_key = (left_term, right_term)
            cached = context_cache.get(cache_key)
            if cached is not None:
                return cached
            value = self._bigram_phrase_count(
                db=db,
                left_term=left_term,
                right_term=right_term,
                specialty_filter=specialty_filter,
            )
            context_cache[cache_key] = value
            return value

        for candidate_term, doc_freq in rows:
            if not candidate_term:
                continue
            candidate = str(candidate_term).strip().lower()
            if not candidate or candidate == normalized_term:
                continue
            doc_freq_int = int(doc_freq or 0)
            if query_kgrams:
                candidate_kgrams = self._build_kgrams(
                    candidate,
                    settings.CLINICAL_CHAT_RAG_KGRAM_SIZE,
                )
                similarity = self._jaccard_similarity(query_kgrams, candidate_kgrams)
                if similarity < settings.CLINICAL_CHAT_RAG_KGRAM_JACCARD_MIN:
                    continue
            context_score = 0
            if contextual_enabled:
                if left_context:
                    context_score += phrase_count(left_context, candidate)
                if right_context:
                    context_score += phrase_count(candidate, right_context)
            distance = self._levenshtein_distance(
                normalized_term,
                candidate,
                max_distance=max_distance,
            )
            if distance > max_distance:
                if (
                    settings.CLINICAL_CHAT_RAG_SOUNDEX_ENABLED
                    and soundex_target
                    and self._soundex(candidate) == soundex_target
                    and (
                        context_score > soundex_best_context_score
                        or (
                            context_score == soundex_best_context_score
                            and doc_freq_int > soundex_best_doc_freq
                        )
                    )
                ):
                    soundex_best_term = candidate
                    soundex_best_context_score = context_score
                    soundex_best_doc_freq = doc_freq_int
                continue
            if (
                best_distance is None
                or distance < best_distance
                or (
                    distance == best_distance
                    and (
                        context_score > best_context_score
                        or (
                            context_score == best_context_score
                            and doc_freq_int > best_doc_freq
                        )
                    )
                )
            ):
                best_term = candidate
                best_distance = distance
                best_context_score = context_score
                best_doc_freq = doc_freq_int
        if best_term:
            return best_term
        return soundex_best_term

    def _fetch_candidate_chunks(
        self,
        *,
        query: str,
        db: Session,
        specialty_filter: Optional[str],
        candidate_pool: int,
    ) -> tuple[list[DocumentChunk], dict[str, str]]:
        trace: dict[str, str] = {}
        use_fts, fts_trace = self._ensure_sqlite_fts_index(db)
        trace.update(fts_trace)

        if not use_fts:
            query_builder = db.query(DocumentChunk).filter(DocumentChunk.specialty.isnot(None))
            if specialty_filter:
                query_builder = query_builder.filter_by(specialty=specialty_filter)
            chunks = query_builder.all()
            trace["candidate_strategy"] = "full_scan_fallback"
            trace["candidate_chunks_pool"] = str(len(chunks))
            return chunks, trace

        vocab_cache_ready = self._ensure_fts_vocab_cache(db)
        trace["candidate_vocab_cache_enabled"] = (
            "1" if settings.CLINICAL_CHAT_RAG_VOCAB_CACHE_ENABLED else "0"
        )
        trace["candidate_vocab_cache_ready"] = "1" if vocab_cache_ready else "0"
        trace["candidate_vocab_cache_terms"] = str(len(self._fts_vocab_cache_terms))

        legacy_include, legacy_optional, legacy_exclude, legacy_explicit = (
            self._extract_boolean_terms(query)
        )
        boolean_tokens = self._tokenize_boolean_query(query)
        operand_context_map = self._build_operand_context_map(boolean_tokens)
        rpn_tokens = self._to_rpn(boolean_tokens)
        parsed_operands = self._extract_operands_from_rpn(rpn_tokens)
        if not parsed_operands:
            parsed_operands = [
                token for token in boolean_tokens if self._is_operand_token(token)
            ]
        postings_limit = max(candidate_pool * 6, 180)

        trace["candidate_strategy"] = "fts_postings_boolean"
        trace["candidate_boolean_explicit"] = "1" if legacy_explicit else "0"
        trace["candidate_boolean_parser"] = "precedence_v1"
        trace["candidate_boolean_tokens"] = (
            ",".join(boolean_tokens[:20]) if boolean_tokens else "none"
        )
        trace["candidate_boolean_rpn"] = ",".join(rpn_tokens[:24]) if rpn_tokens else "none"
        trace["candidate_terms_included"] = (
            ",".join(legacy_include[:8]) if legacy_include else "none"
        )
        trace["candidate_terms_optional"] = (
            ",".join(legacy_optional[:8]) if legacy_optional else "none"
        )
        trace["candidate_terms_excluded"] = (
            ",".join(legacy_exclude[:8]) if legacy_exclude else "none"
        )

        postings_map: dict[str, list[int]] = {}
        corrected_terms: dict[str, str] = {}
        spell_stats = {"attempted": 0, "applied": 0}
        wildcard_stats = {"attempted": 0, "expanded_terms": 0}
        vocab_stats = {"cache_hits": 0, "db_hits": 0}
        postings_cache_stats = {"hits": 0, "misses": 0, "evictions": 0}
        spell_max_distance = settings.CLINICAL_CHAT_RAG_SPELL_MAX_EDIT_DISTANCE
        skip_stats = {"intersections": 0, "shortcuts": 0}

        def resolve_postings(token: str) -> list[int]:
            if token in postings_map:
                return postings_map[token]
            left_neighbor_token, right_neighbor_token = operand_context_map.get(
                token,
                (None, None),
            )
            left_context_term = self._context_term_from_neighbor(
                left_neighbor_token,
                use_last=True,
            )
            right_context_term = self._context_term_from_neighbor(
                right_neighbor_token,
                use_last=False,
            )
            near_parts = self._parse_near_operand_token(token)
            if near_parts is not None:
                left_term, right_term, distance = near_parts
                postings = self._fetch_postings_for_near(
                    db=db,
                    left_term=left_term,
                    right_term=right_term,
                    distance=distance,
                    specialty_filter=specialty_filter,
                    limit=postings_limit,
                    cache_stats=postings_cache_stats,
                )
                if not postings:
                    left_is_phrase = left_term.startswith('"') and left_term.endswith('"')
                    right_is_phrase = right_term.startswith('"') and right_term.endswith('"')
                    corrected_left = left_term
                    corrected_right = right_term
                    if not left_is_phrase:
                        spell_stats["attempted"] += 1
                        suggestion_left = self._suggest_term_correction(
                            db=db,
                            term=left_term,
                            max_distance=spell_max_distance,
                            left_context=left_context_term,
                            right_context=(
                                self._context_term_from_neighbor(right_term, use_last=False)
                                or right_context_term
                            ),
                            specialty_filter=specialty_filter,
                            vocab_stats=vocab_stats,
                        )
                        if suggestion_left and suggestion_left != left_term:
                            corrected_left = suggestion_left
                            corrected_terms[left_term] = suggestion_left
                            spell_stats["applied"] += 1
                    if not right_is_phrase:
                        spell_stats["attempted"] += 1
                        suggestion_right = self._suggest_term_correction(
                            db=db,
                            term=right_term,
                            max_distance=spell_max_distance,
                            left_context=(
                                self._context_term_from_neighbor(left_term, use_last=True)
                                or left_context_term
                            ),
                            right_context=right_context_term,
                            specialty_filter=specialty_filter,
                            vocab_stats=vocab_stats,
                        )
                        if suggestion_right and suggestion_right != right_term:
                            corrected_right = suggestion_right
                            corrected_terms[right_term] = suggestion_right
                            spell_stats["applied"] += 1
                    if corrected_left != left_term or corrected_right != right_term:
                        postings = self._fetch_postings_for_near(
                            db=db,
                            left_term=corrected_left,
                            right_term=corrected_right,
                            distance=distance,
                            specialty_filter=specialty_filter,
                            limit=postings_limit,
                            cache_stats=postings_cache_stats,
                        )
                postings_map[token] = postings
                return postings
            is_phrase = token.startswith('"') and token.endswith('"')
            raw_term = token[1:-1] if is_phrase else token
            normalized = raw_term
            has_wildcard = (not is_phrase) and self._is_wildcard_token(raw_term)
            postings: list[int] = []
            if is_phrase:
                postings = self._fetch_postings_for_term(
                    db=db,
                    term=normalized,
                    specialty_filter=specialty_filter,
                    limit=postings_limit,
                    is_phrase=True,
                    cache_stats=postings_cache_stats,
                )
            elif has_wildcard:
                wildcard_stats["attempted"] += 1
                wildcard_terms = self._expand_wildcard_term(
                    db=db,
                    term=raw_term,
                    limit=settings.CLINICAL_CHAT_RAG_WILDCARD_MAX_EXPANSIONS,
                    vocab_stats=vocab_stats,
                )
                wildcard_stats["expanded_terms"] += len(wildcard_terms)
                for wildcard_term in wildcard_terms:
                    wildcard_postings = self._fetch_postings_for_term(
                        db=db,
                        term=wildcard_term,
                        specialty_filter=specialty_filter,
                        limit=postings_limit,
                        is_phrase=False,
                        cache_stats=postings_cache_stats,
                    )
                    postings = self._union_sorted_ids(postings, wildcard_postings)
            else:
                for variant in self._term_variants(normalized):
                    variant_postings = self._fetch_postings_for_term(
                        db=db,
                        term=variant,
                        specialty_filter=specialty_filter,
                        limit=postings_limit,
                        is_phrase=False,
                        cache_stats=postings_cache_stats,
                    )
                    postings = self._union_sorted_ids(postings, variant_postings)
            if (
                len(postings) <= settings.CLINICAL_CHAT_RAG_SPELL_TRIGGER_MAX_POSTINGS
                and not is_phrase
                and not has_wildcard
            ):
                spell_stats["attempted"] += 1
                suggestion = self._suggest_term_correction(
                    db=db,
                    term=normalized,
                    max_distance=spell_max_distance,
                    left_context=left_context_term,
                    right_context=right_context_term,
                    specialty_filter=specialty_filter,
                    vocab_stats=vocab_stats,
                )
                if suggestion and suggestion != normalized:
                    corrected_postings = self._fetch_postings_for_term(
                        db=db,
                        term=suggestion,
                        specialty_filter=specialty_filter,
                        limit=postings_limit,
                        is_phrase=False,
                        cache_stats=postings_cache_stats,
                    )
                    if corrected_postings:
                        corrected_terms[normalized] = suggestion
                        spell_stats["applied"] += 1
                        postings = corrected_postings
            postings_map[token] = postings
            return postings

        candidate_ids: list[int] = []
        parse_error = False
        if rpn_tokens:
            eval_stack: list[list[int]] = []
            universe_ids: list[int] = []
            for token in rpn_tokens:
                if self._is_operand_token(token):
                    eval_stack.append(resolve_postings(token))
                    continue
                if token == "NOT":
                    if not eval_stack:
                        parse_error = True
                        break
                    operand = eval_stack.pop()
                    if not universe_ids:
                        universe_ids = self._fetch_universe_ids(
                            db=db,
                            specialty_filter=specialty_filter,
                            limit=max(candidate_pool * 8, 640),
                        )
                    eval_stack.append(self._difference_sorted_ids(universe_ids, operand))
                    continue
                if token in {"AND", "OR"}:
                    if len(eval_stack) < 2:
                        parse_error = True
                        break
                    right = eval_stack.pop()
                    left = eval_stack.pop()
                    if token == "AND":
                        if (
                            settings.CLINICAL_CHAT_RAG_SKIP_POINTERS_ENABLED
                            and len(left) >= settings.CLINICAL_CHAT_RAG_SKIP_POINTERS_MIN_LIST
                            and len(right) >= settings.CLINICAL_CHAT_RAG_SKIP_POINTERS_MIN_LIST
                        ):
                            inter, shortcuts = self._intersect_sorted_ids_with_skips(left, right)
                            eval_stack.append(inter)
                            skip_stats["intersections"] += 1
                            skip_stats["shortcuts"] += shortcuts
                        else:
                            eval_stack.append(self._intersect_sorted_ids(left, right))
                    else:
                        eval_stack.append(self._union_sorted_ids(left, right))
                    continue
                parse_error = True
                break
            if not parse_error and len(eval_stack) == 1:
                candidate_ids = eval_stack[0]
            else:
                trace["candidate_boolean_parse_error"] = "1"
        relaxed_union_terms: list[str] = []
        if legacy_include:
            relaxed_union_terms.extend(legacy_include)
        if legacy_optional:
            relaxed_union_terms.extend(legacy_optional)
        if not relaxed_union_terms and parsed_operands:
            relaxed_union_terms = [
                token
                for token in parsed_operands
                if len(self._tokenize_terms(token)) >= 1 and len(token) >= 4
            ]

        should_apply_relaxed_union = (
            not candidate_ids
            and bool(relaxed_union_terms)
            and (not rpn_tokens or parse_error or not legacy_explicit)
        )
        if should_apply_relaxed_union:
            # Consulta no booleana explicita: evita que los AND implicitos vacien recall.
            for token in relaxed_union_terms[:16]:
                candidate_ids = self._union_sorted_ids(candidate_ids, resolve_postings(token))
            if candidate_ids:
                trace["candidate_strategy"] = "fts_boolean_relaxed_union"
        trace["candidate_boolean_relaxed_union"] = "1" if should_apply_relaxed_union else "0"
        trace["candidate_boolean_relaxed_union_terms"] = (
            ",".join(relaxed_union_terms[:12]) if relaxed_union_terms else "none"
        )

        candidate_ids = candidate_ids[: max(1, candidate_pool)]
        trace["candidate_postings_terms"] = str(len(postings_map))
        trace["candidate_postings_operands"] = str(len(parsed_operands))

        def has_phrase_signal(token: str) -> bool:
            if token.startswith('"') and token.endswith('"'):
                return True
            near_parts = self._parse_near_operand_token(token)
            if near_parts is None:
                return False
            left_term, right_term, _ = near_parts
            return (
                (left_term.startswith('"') and left_term.endswith('"'))
                or (right_term.startswith('"') and right_term.endswith('"'))
            )

        trace["candidate_phrase_terms"] = str(
            sum(1 for token in parsed_operands if has_phrase_signal(token))
        )
        trace["candidate_spell_attempted"] = str(spell_stats["attempted"])
        trace["candidate_spell_applied"] = str(spell_stats["applied"])
        trace["candidate_spell_corrections"] = (
            ";".join(f"{src}->{dst}" for src, dst in corrected_terms.items())
            if corrected_terms
            else "none"
        )
        trace["candidate_contextual_spell_enabled"] = (
            "1" if settings.CLINICAL_CHAT_RAG_CONTEXTUAL_SPELL_ENABLED else "0"
        )
        trace["candidate_contextual_spell_max_candidates"] = str(
            settings.CLINICAL_CHAT_RAG_CONTEXTUAL_SPELL_MAX_CANDIDATES
        )
        trace["candidate_did_you_mean"] = (
            ", ".join(dict.fromkeys(corrected_terms.values()))
            if corrected_terms
            else "none"
        )
        trace["candidate_spell_trigger_max_postings"] = str(
            settings.CLINICAL_CHAT_RAG_SPELL_TRIGGER_MAX_POSTINGS
        )
        trace["candidate_wildcard_enabled"] = (
            "1" if settings.CLINICAL_CHAT_RAG_WILDCARD_ENABLED else "0"
        )
        trace["candidate_wildcard_attempted"] = str(wildcard_stats["attempted"])
        trace["candidate_wildcard_expanded_terms"] = str(wildcard_stats["expanded_terms"])
        trace["candidate_vocab_lookup_cache_hits"] = str(vocab_stats["cache_hits"])
        trace["candidate_vocab_lookup_db_hits"] = str(vocab_stats["db_hits"])
        trace["candidate_postings_cache_enabled"] = (
            "1" if settings.CLINICAL_CHAT_RAG_POSTINGS_CACHE_ENABLED else "0"
        )
        trace["candidate_postings_cache_encoding"] = (
            settings.CLINICAL_CHAT_RAG_POSTINGS_CACHE_ENCODING
        )
        trace["candidate_postings_cache_hits"] = str(postings_cache_stats["hits"])
        trace["candidate_postings_cache_misses"] = str(postings_cache_stats["misses"])
        trace["candidate_postings_cache_evictions"] = str(postings_cache_stats["evictions"])
        trace["candidate_postings_cache_size"] = str(len(self._fts_postings_cache))
        trace["candidate_soundex_enabled"] = (
            "1" if settings.CLINICAL_CHAT_RAG_SOUNDEX_ENABLED else "0"
        )
        trace["candidate_skip_enabled"] = (
            "1" if settings.CLINICAL_CHAT_RAG_SKIP_POINTERS_ENABLED else "0"
        )
        trace["candidate_skip_threshold"] = str(
            settings.CLINICAL_CHAT_RAG_SKIP_POINTERS_MIN_LIST
        )
        trace["candidate_skip_intersections"] = str(skip_stats["intersections"])
        trace["candidate_skip_shortcuts"] = str(skip_stats["shortcuts"])
        trace["candidate_chunks_pool"] = str(len(candidate_ids))
        if not candidate_ids:
            if rpn_tokens and legacy_explicit:
                trace["candidate_strategy"] = "fts_boolean_no_match"
                return [], trace
            trace["candidate_strategy"] = "fts_empty_fallback_full_scan"
            query_builder = db.query(DocumentChunk).filter(DocumentChunk.specialty.isnot(None))
            if specialty_filter:
                query_builder = query_builder.filter_by(specialty=specialty_filter)
            chunks = query_builder.all()
            trace["candidate_chunks_pool"] = str(len(chunks))
            return chunks, trace

        query_builder = db.query(DocumentChunk).filter(
            DocumentChunk.id.in_(candidate_ids),
            DocumentChunk.specialty.isnot(None),
        )
        if specialty_filter:
            query_builder = query_builder.filter_by(specialty=specialty_filter)
        loaded = query_builder.all()
        chunks_by_id = {int(chunk.id): chunk for chunk in loaded}
        ordered_chunks = [
            chunks_by_id[item_id]
            for item_id in candidate_ids
            if item_id in chunks_by_id
        ]
        return ordered_chunks, trace

    def _score_vector_candidates(
        self,
        *,
        query: str,
        chunks: list[DocumentChunk],
        k: int,
    ) -> tuple[list[tuple[DocumentChunk, float]], dict[str, str]]:
        started_at = time.perf_counter()
        trace_info: dict[str, str] = {}
        try:
            query_vec, embedding_trace = self.embedding_service.embed_text(query)
            trace_info.update(embedding_trace)
            if not query_vec:
                trace_info["vector_search_error"] = "empty_query_embedding"
                trace_info["vector_search_chunks_found"] = "0"
                return [], trace_info

            candidate_chunks: list[DocumentChunk] = []
            candidate_vectors: list[list[float]] = []
            for chunk in chunks:
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
            scored = list(zip(candidate_chunks, similarities, strict=False))
            scored.sort(key=lambda item: item[1], reverse=True)
            top_scores = [(chunk, float(score)) for chunk, score in scored[:k]]

            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            avg_score = (
                sum(float(score) for _, score in top_scores) / len(top_scores)
                if top_scores
                else 0.0
            )
            trace_info.update(
                {
                    "vector_search_chunks_found": str(len(top_scores)),
                    "vector_search_avg_score": f"{avg_score:.3f}",
                    "vector_search_latency_ms": str(latency_ms),
                    "vector_search_method": "cosine_similarity",
                }
            )
            return top_scores, trace_info
        except Exception as exc:  # pragma: no cover - defensivo
            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            trace_info["vector_search_error"] = exc.__class__.__name__
            trace_info["vector_search_latency_ms"] = str(latency_ms)
            logger.error("Error en busqueda vectorial: %s", exc)
            return [], trace_info

    @staticmethod
    def _tokenize_terms(value: str) -> list[str]:
        return re.findall(r"[a-z0-9#\-\+/]+", str(value or "").lower())

    @staticmethod
    def _sublinear_tf(term_frequency: int) -> float:
        safe_tf = int(term_frequency)
        if safe_tf <= 0:
            return 0.0
        return 1.0 + math.log(float(safe_tf))

    @staticmethod
    def _bm25_idf(*, collection_size: int, doc_freq: float) -> float:
        n_docs = max(1.0, float(collection_size))
        df_value = max(0.0, min(float(doc_freq), n_docs))
        return math.log(((n_docs - df_value + 0.5) / (df_value + 0.5)) + 1.0)

    @staticmethod
    def _dirichlet_smoothed_prob(
        *,
        doc_tf: float,
        doc_len: float,
        collection_prob: float,
        mu: float,
    ) -> float:
        safe_mu = max(1.0, float(mu))
        safe_len = max(1.0, float(doc_len))
        safe_collection_prob = max(1e-12, float(collection_prob))
        return (float(doc_tf) + (safe_mu * safe_collection_prob)) / (safe_len + safe_mu)

    @staticmethod
    def _jm_smoothed_prob(
        *,
        doc_tf: float,
        doc_len: float,
        collection_prob: float,
        lambda_value: float,
    ) -> float:
        safe_lambda = min(1.0, max(0.0, float(lambda_value)))
        safe_len = max(1.0, float(doc_len))
        safe_collection_prob = max(1e-12, float(collection_prob))
        doc_prob = max(0.0, float(doc_tf)) / safe_len
        return (safe_lambda * doc_prob) + ((1.0 - safe_lambda) * safe_collection_prob)

    @staticmethod
    def _minimum_window_span(tokens: list[str], required_terms: set[str]) -> int | None:
        if not tokens or not required_terms:
            return None
        required = {term for term in required_terms if term}
        if not required:
            return None
        positions: dict[str, list[int]] = {}
        for index, token in enumerate(tokens):
            if token in required:
                positions.setdefault(token, []).append(index)
        if len(positions) < len(required):
            return None

        have_counts: dict[str, int] = {}
        covered = 0
        left = 0
        best_span: int | None = None
        for right, token in enumerate(tokens):
            if token in required:
                prev = have_counts.get(token, 0)
                have_counts[token] = prev + 1
                if prev == 0:
                    covered += 1
            while covered == len(required) and left <= right:
                span = right - left + 1
                if best_span is None or span < best_span:
                    best_span = span
                left_token = tokens[left]
                if left_token in required:
                    next_count = have_counts.get(left_token, 0) - 1
                    if next_count <= 0:
                        have_counts.pop(left_token, None)
                        covered -= 1
                    else:
                        have_counts[left_token] = next_count
                left += 1
        return best_span

    @staticmethod
    def _normalize_weight_map(weights: dict[str, float]) -> dict[str, float]:
        clipped = {name: max(0.0, float(value)) for name, value in weights.items()}
        total = sum(clipped.values())
        if total <= 0:
            even_weight = 1.0 / max(1, len(clipped))
            return {name: even_weight for name in clipped}
        return {name: value / total for name, value in clipped.items()}

    def _build_zone_weights(self) -> dict[str, float]:
        return self._normalize_weight_map(
            {
                "title": settings.CLINICAL_CHAT_RAG_ZONE_WEIGHT_TITLE,
                "section": settings.CLINICAL_CHAT_RAG_ZONE_WEIGHT_SECTION,
                "body": settings.CLINICAL_CHAT_RAG_ZONE_WEIGHT_BODY,
                "keywords": settings.CLINICAL_CHAT_RAG_ZONE_WEIGHT_KEYWORDS,
                "custom_questions": settings.CLINICAL_CHAT_RAG_ZONE_WEIGHT_CUSTOM_QUESTIONS,
            }
        )

    @staticmethod
    def _estimate_static_quality(chunk: DocumentChunk) -> float:
        document = getattr(chunk, "document", None)
        title = str(getattr(document, "title", "") or "").lower()
        source_file = str(getattr(document, "source_file", "") or "").lower()
        section = str(chunk.section_path or "").lower()
        quality = 0.0

        if "motor operativo" in title:
            quality += 0.45
        if source_file.startswith("docs/"):
            quality += 0.20
        if "pdf_raw" in source_file:
            quality += 0.08
        if any(marker in section for marker in ("algoritmo", "validacion", "riesgos", "pasos")):
            quality += 0.10
        if str(chunk.specialty or "").strip():
            quality += 0.07
        if "recomendacion" in section or "recommendation" in section:
            quality += 0.10
        return max(0.0, min(1.0, quality))

    @classmethod
    def _extract_chunk_zone_texts(cls, chunk: DocumentChunk) -> dict[str, str]:
        title_parts: list[str] = []
        document = getattr(chunk, "document", None)
        if document is not None:
            title_parts.append(str(getattr(document, "title", "") or ""))
            title_parts.append(str(getattr(document, "source_file", "") or ""))
        keywords_value = " ".join(str(item) for item in (chunk.keywords or []))
        custom_questions_value = " ".join(str(item) for item in (chunk.custom_questions or []))
        return {
            "title": " ".join(part for part in title_parts if part).strip().lower(),
            "section": str(chunk.section_path or "").lower(),
            "body": str(chunk.chunk_text or "").lower(),
            "keywords": keywords_value.lower(),
            "custom_questions": custom_questions_value.lower(),
        }

    def _score_keyword_candidates(
        self,
        *,
        query: str,
        chunks: list[DocumentChunk],
        k: int,
    ) -> tuple[list[tuple[DocumentChunk, float]], dict[str, str]]:
        started_at = time.perf_counter()
        bm25_enabled = bool(settings.CLINICAL_CHAT_RAG_BM25_ENABLED)
        bm25_k1 = float(settings.CLINICAL_CHAT_RAG_BM25_K1)
        bm25_b = float(settings.CLINICAL_CHAT_RAG_BM25_B)
        bm25_blend = float(settings.CLINICAL_CHAT_RAG_BM25_BLEND)
        bim_bonus_enabled = bool(settings.CLINICAL_CHAT_RAG_BIM_BINARY_BONUS_ENABLED)
        bim_bonus_weight = float(settings.CLINICAL_CHAT_RAG_BIM_BINARY_BONUS_WEIGHT)
        qlm_enabled = bool(settings.CLINICAL_CHAT_RAG_QLM_ENABLED)
        qlm_smoothing = str(settings.CLINICAL_CHAT_RAG_QLM_SMOOTHING).strip().lower()
        qlm_mu = float(settings.CLINICAL_CHAT_RAG_QLM_DIRICHLET_MU)
        qlm_jm_lambda = float(settings.CLINICAL_CHAT_RAG_QLM_JM_LAMBDA)
        qlm_blend = float(settings.CLINICAL_CHAT_RAG_QLM_BLEND)
        lsi_enabled = bool(settings.CLINICAL_CHAT_RAG_LSI_ENABLED)
        lsi_blend = float(settings.CLINICAL_CHAT_RAG_LSI_BLEND)
        lsi_k = int(settings.CLINICAL_CHAT_RAG_LSI_K)
        trace_info: dict[str, str] = {
            "keyword_search_method": "tfidf_zone_cosine_pivoted",
            "keyword_search_bm25_enabled": "1" if bm25_enabled else "0",
            "keyword_search_bm25_k1": f"{bm25_k1:.2f}",
            "keyword_search_bm25_b": f"{bm25_b:.2f}",
            "keyword_search_bm25_blend": f"{bm25_blend:.2f}",
            "keyword_search_bim_bonus_enabled": "1" if bim_bonus_enabled else "0",
            "keyword_search_bim_bonus_weight": f"{bim_bonus_weight:.2f}",
            "keyword_search_qlm_enabled": "1" if qlm_enabled else "0",
            "keyword_search_qlm_smoothing": qlm_smoothing,
            "keyword_search_qlm_mu": f"{qlm_mu:.1f}",
            "keyword_search_qlm_jm_lambda": f"{qlm_jm_lambda:.2f}",
            "keyword_search_qlm_blend": f"{qlm_blend:.2f}",
            "keyword_search_lsi_enabled": "1" if lsi_enabled else "0",
            "keyword_search_lsi_k": str(lsi_k),
            "keyword_search_lsi_blend": f"{lsi_blend:.2f}",
        }

        if not chunks:
            trace_info["keyword_search_chunks_found"] = "0"
            return [], trace_info

        query_tokens = self._tokenize_terms(query)
        if not query_tokens:
            trace_info["keyword_search_chunks_found"] = "0"
            trace_info["keyword_search_error"] = "empty_query_terms"
            return [], trace_info

        query_term_counts_full = Counter(query_tokens)
        max_query_terms = int(settings.CLINICAL_CHAT_RAG_TFIDF_MAX_QUERY_TERMS)
        if len(query_term_counts_full) > max_query_terms:
            allowed = {
                term for term, _ in query_term_counts_full.most_common(max_query_terms)
            }
            query_term_counts = Counter(
                {term: count for term, count in query_term_counts_full.items() if term in allowed}
            )
        else:
            query_term_counts = query_term_counts_full

        query_terms = list(query_term_counts.keys())
        zone_weights = self._build_zone_weights()
        prepared_chunks: list[tuple[DocumentChunk, dict[str, Counter[str]], int]] = []
        doc_frequency: dict[str, int] = {term: 0 for term in query_terms}
        doc_lengths: list[float] = []

        for chunk in chunks:
            zone_texts = self._extract_chunk_zone_texts(chunk)
            zone_counts: dict[str, Counter[str]] = {
                zone_name: Counter(self._tokenize_terms(text_value))
                for zone_name, text_value in zone_texts.items()
            }
            term_seen_in_doc = set()
            for term in query_terms:
                if any(zone_counts[zone].get(term, 0) > 0 for zone in zone_counts):
                    term_seen_in_doc.add(term)
            for term in term_seen_in_doc:
                doc_frequency[term] = doc_frequency.get(term, 0) + 1

            body_tokens_count = sum(zone_counts["body"].values())
            doc_length = max(1, int(chunk.tokens_count or 0), int(body_tokens_count))
            prepared_chunks.append((chunk, zone_counts, doc_length))
            doc_lengths.append(float(doc_length))

        if not prepared_chunks:
            trace_info["keyword_search_chunks_found"] = "0"
            return [], trace_info

        collection_size = len(prepared_chunks)
        idf_by_term: dict[str, float] = {}
        for term in query_terms:
            df_value = float(doc_frequency.get(term, 0))
            idf_by_term[term] = math.log((collection_size + 1.0) / (df_value + 1.0)) + 1.0

        query_weight_sq_sum = 0.0
        query_weights: dict[str, float] = {}
        for term, query_tf in query_term_counts.items():
            query_weight = self._sublinear_tf(query_tf) * idf_by_term.get(term, 1.0)
            query_weights[term] = query_weight
            query_weight_sq_sum += query_weight * query_weight

        query_terms_ordered = list(query_weights.keys())
        if settings.CLINICAL_CHAT_RAG_IDF_TERM_PRUNING_ENABLED:
            idf_sorted = sorted(
                query_terms_ordered,
                key=lambda term_value: idf_by_term.get(term_value, 0.0),
                reverse=True,
            )
            threshold = float(settings.CLINICAL_CHAT_RAG_IDF_MIN_THRESHOLD)
            keep_terms = [
                term_value
                for term_value in idf_sorted
                if idf_by_term.get(term_value, 0.0) >= threshold
            ]
            min_keep = min(
                len(idf_sorted),
                int(settings.CLINICAL_CHAT_RAG_IDF_MIN_KEEP_TERMS),
            )
            if len(keep_terms) < min_keep:
                keep_terms = idf_sorted[:min_keep]
            active_terms = keep_terms
        else:
            active_terms = query_terms_ordered

        if active_terms:
            query_weights = {term: query_weights[term] for term in active_terms}
        query_weight_sq_sum = sum(weight * weight for weight in query_weights.values())
        query_norm = math.sqrt(query_weight_sq_sum) if query_weight_sq_sum > 0 else 1.0
        query_tf_active = {
            term: int(query_term_counts.get(term, 0))
            for term in query_weights
        }

        collection_tf_by_term: dict[str, float] = {term: 0.0 for term in query_weights}
        for _chunk, zone_counts, _doc_length in prepared_chunks:
            for term in collection_tf_by_term:
                weighted_tf_count = 0.0
                for zone_name, zone_weight in zone_weights.items():
                    term_frequency = int(zone_counts[zone_name].get(term, 0))
                    if term_frequency <= 0:
                        continue
                    weighted_tf_count += zone_weight * float(term_frequency)
                collection_tf_by_term[term] += weighted_tf_count
        collection_tf_total = max(1e-9, sum(collection_tf_by_term.values()))
        collection_prob_by_term = {
            term: max(1e-12, float(tf_value) / collection_tf_total)
            for term, tf_value in collection_tf_by_term.items()
        }

        avg_doc_length = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 1.0
        pivot_slope = float(settings.CLINICAL_CHAT_RAG_TFIDF_PIVOT_SLOPE)
        zone_blend = float(settings.CLINICAL_CHAT_RAG_TFIDF_ZONE_BLEND)
        proximity_enabled = bool(settings.CLINICAL_CHAT_RAG_PROXIMITY_BONUS_ENABLED)
        proximity_weight = float(settings.CLINICAL_CHAT_RAG_PROXIMITY_BONUS_WEIGHT)
        static_quality_enabled = bool(settings.CLINICAL_CHAT_RAG_STATIC_QUALITY_ENABLED)
        static_quality_weight = float(settings.CLINICAL_CHAT_RAG_STATIC_QUALITY_WEIGHT)

        scored_raw: list[tuple[DocumentChunk, float, float, float, float, float]] = []
        active_term_set = set(query_weights.keys())
        for chunk, zone_counts, doc_length in prepared_chunks:
            dot_product = 0.0
            doc_weight_sq_sum = 0.0
            zone_binary_sum = 0.0
            bm25_raw = 0.0
            bim_raw = 0.0
            qlm_log_raw = 0.0

            for term, query_weight in query_weights.items():
                weighted_tf = 0.0
                zone_binary = 0.0
                weighted_tf_count = 0.0
                for zone_name, zone_weight in zone_weights.items():
                    term_frequency = int(zone_counts[zone_name].get(term, 0))
                    if term_frequency <= 0:
                        continue
                    weighted_tf += zone_weight * self._sublinear_tf(term_frequency)
                    weighted_tf_count += zone_weight * float(term_frequency)
                    zone_binary += zone_weight
                if weighted_tf <= 0:
                    continue
                doc_weight = weighted_tf * idf_by_term.get(term, 1.0)
                dot_product += query_weight * doc_weight
                doc_weight_sq_sum += doc_weight * doc_weight
                zone_binary_sum += zone_binary

                if qlm_enabled:
                    collection_prob = float(collection_prob_by_term.get(term, 1e-12))
                    if qlm_smoothing == "jm":
                        smoothed_prob = self._jm_smoothed_prob(
                            doc_tf=weighted_tf_count,
                            doc_len=float(doc_length),
                            collection_prob=collection_prob,
                            lambda_value=qlm_jm_lambda,
                        )
                    else:
                        smoothed_prob = self._dirichlet_smoothed_prob(
                            doc_tf=weighted_tf_count,
                            doc_len=float(doc_length),
                            collection_prob=collection_prob,
                            mu=qlm_mu,
                        )
                    term_query_tf = max(1, int(query_tf_active.get(term, 1)))
                    qlm_log_raw += float(term_query_tf) * math.log(max(1e-12, smoothed_prob))

                if bm25_enabled and weighted_tf_count > 0:
                    df_value = float(doc_frequency.get(term, 0))
                    idf_prob = self._bm25_idf(
                        collection_size=collection_size,
                        doc_freq=df_value,
                    )
                    norm_len = max(1.0, float(doc_length) / max(1.0, avg_doc_length))
                    denominator = weighted_tf_count + (
                        bm25_k1 * ((1.0 - bm25_b) + (bm25_b * norm_len))
                    )
                    if denominator > 0:
                        bm25_raw += idf_prob * (
                            (weighted_tf_count * (bm25_k1 + 1.0)) / denominator
                        )
                    if bim_bonus_enabled:
                        odds_num = max(1e-9, (collection_size - df_value + 0.5))
                        odds_den = max(1e-9, (df_value + 0.5))
                        bim_raw += math.log(odds_num / odds_den)

            if dot_product <= 0 or doc_weight_sq_sum <= 0:
                continue

            cosine_score = dot_product / (math.sqrt(doc_weight_sq_sum) * query_norm)
            zone_score = zone_binary_sum / max(1, len(query_weights))
            pivot_denominator = (
                (1.0 - pivot_slope)
                + pivot_slope * (float(doc_length) / max(1.0, avg_doc_length))
            )
            pivot_denominator = max(0.20, pivot_denominator)
            combined_score = (
                ((1.0 - zone_blend) * cosine_score) + (zone_blend * zone_score)
            ) / pivot_denominator
            static_quality = (
                self._estimate_static_quality(chunk)
                if static_quality_enabled
                else 0.0
            )
            proximity_score = 0.0
            if proximity_enabled and len(active_term_set) >= 2:
                body_tokens = self._tokenize_terms(chunk.chunk_text or "")
                span = self._minimum_window_span(body_tokens, active_term_set)
                if span and span > 0:
                    proximity_score = min(1.0, len(active_term_set) / float(span))
            scored_raw.append(
                (
                    chunk,
                    float(combined_score),
                    float(static_quality),
                    float(bm25_raw),
                    float(proximity_score),
                    float(qlm_log_raw),
                )
            )

        if not scored_raw:
            trace_info["keyword_search_chunks_found"] = "0"
            return [], trace_info

        bm25_norm_by_id: dict[int, float] = {}
        if bm25_enabled and bm25_blend > 0:
            bm25_norm_by_id = self._normalize_raw_score_map(
                {
                    int(chunk.id): bm25_raw
                    for chunk, _base, _sq, bm25_raw, _prox, _qlm in scored_raw
                }
            )

        qlm_norm_by_id: dict[int, float] = {}
        if qlm_enabled and qlm_blend > 0:
            qlm_norm_by_id = self._normalize_raw_score_map(
                {
                    int(chunk.id): qlm_raw
                    for chunk, _base, _sq, _bm25_raw, _prox, qlm_raw in scored_raw
                }
            )

        bim_norm_by_id: dict[int, float] = {}
        if bim_bonus_enabled and bim_bonus_weight > 0:
            bim_values_by_id: dict[int, float] = {}
            for chunk, _base, _sq, _bm25_raw, _prox, _qlm in scored_raw:
                score = 0.0
                zone_texts = self._extract_chunk_zone_texts(chunk)
                doc_text = " ".join(zone_texts.values())
                doc_tokens = set(self._tokenize_terms(doc_text))
                for term in query_weights:
                    if term not in doc_tokens:
                        continue
                    df_value = float(doc_frequency.get(term, 0))
                    odds_num = max(1e-9, (collection_size - df_value + 0.5))
                    odds_den = max(1e-9, (df_value + 0.5))
                    score += math.log(odds_num / odds_den)
                bim_values_by_id[int(chunk.id)] = score
            bim_norm_by_id = self._normalize_raw_score_map(bim_values_by_id)

        lsi_norm_by_id: dict[int, float] = {}
        if lsi_enabled and lsi_blend > 0:
            lsi_norm_by_id, lsi_trace = self._compute_lsi_norm_scores(
                prepared_chunks=prepared_chunks,
                query_term_counts=query_term_counts,
                zone_weights=zone_weights,
            )
            trace_info.update(lsi_trace)

        scored: list[tuple[DocumentChunk, float, float]] = []
        for chunk, base_score, static_quality, _bm25_raw, proximity_score, _qlm_raw in scored_raw:
            score = float(base_score)
            if bm25_norm_by_id:
                score = ((1.0 - bm25_blend) * score) + (
                    bm25_blend * bm25_norm_by_id.get(int(chunk.id), 0.0)
                )
            if qlm_norm_by_id:
                score = ((1.0 - qlm_blend) * score) + (
                    qlm_blend * qlm_norm_by_id.get(int(chunk.id), 0.0)
                )
            if lsi_norm_by_id:
                score = ((1.0 - lsi_blend) * score) + (
                    lsi_blend * lsi_norm_by_id.get(int(chunk.id), 0.0)
                )
            if bim_norm_by_id:
                score += bim_bonus_weight * bim_norm_by_id.get(int(chunk.id), 0.0)
            score += (static_quality_weight * static_quality) + (
                proximity_weight * proximity_score
            )
            if score > 0:
                scored.append((chunk, float(score), float(static_quality)))

        scored.sort(key=lambda item: item[1], reverse=True)
        if settings.CLINICAL_CHAT_RAG_TIERED_RANKING_ENABLED:
            tier_threshold = float(settings.CLINICAL_CHAT_RAG_TIER1_MIN_STATIC_QUALITY)
            tier1 = [item for item in scored if item[2] >= tier_threshold]
            tier2 = [item for item in scored if item[2] < tier_threshold]
            scored = tier1 + tier2
        top_scores = [(chunk, float(score)) for chunk, score, _quality in scored[:k]]
        top_ids = [int(chunk.id) for chunk, _score in top_scores]
        bm25_norm_top_avg = (
            sum(float(bm25_norm_by_id.get(chunk_id, 0.0)) for chunk_id in top_ids)
            / len(top_ids)
            if bm25_norm_by_id and top_ids
            else 0.0
        )
        bim_norm_top_avg = (
            sum(float(bim_norm_by_id.get(chunk_id, 0.0)) for chunk_id in top_ids)
            / len(top_ids)
            if bim_norm_by_id and top_ids
            else 0.0
        )
        qlm_norm_top_avg = (
            sum(float(qlm_norm_by_id.get(chunk_id, 0.0)) for chunk_id in top_ids)
            / len(top_ids)
            if qlm_norm_by_id and top_ids
            else 0.0
        )
        lsi_norm_top_avg = (
            sum(float(lsi_norm_by_id.get(chunk_id, 0.0)) for chunk_id in top_ids)
            / len(top_ids)
            if lsi_norm_by_id and top_ids
            else 0.0
        )
        method_parts = ["tfidf_zone_cosine_pivoted"]
        if bm25_enabled and bm25_blend > 0:
            method_parts.append("bm25")
        if qlm_enabled and qlm_blend > 0:
            method_parts.append("qlm")
        if lsi_enabled and lsi_blend > 0 and lsi_norm_by_id:
            method_parts.append("lsi")
        if bim_bonus_enabled and bim_bonus_weight > 0:
            method_parts.append("bim")
        method_name = "+".join(method_parts)
        latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
        avg_score = (
            sum(float(score) for _, score in top_scores) / len(top_scores)
            if top_scores
            else 0.0
        )
        trace_info.update(
            {
                "keyword_search_chunks_found": str(len(top_scores)),
                "keyword_search_avg_score": f"{avg_score:.2f}",
                "keyword_search_latency_ms": str(latency_ms),
                "keyword_search_method": method_name,
                "keyword_search_query_terms": str(len(query_weights)),
                "keyword_search_active_terms": ",".join(list(query_weights.keys())[:16]) or "none",
                "keyword_search_idf_pruned_terms": str(
                    max(0, len(query_term_counts_full) - len(query_weights))
                ),
                "keyword_search_zone_blend": f"{zone_blend:.2f}",
                "keyword_search_pivot_slope": f"{pivot_slope:.2f}",
                "keyword_search_bm25_top_avg": f"{bm25_norm_top_avg:.3f}",
                "keyword_search_qlm_top_avg": f"{qlm_norm_top_avg:.3f}",
                "keyword_search_lsi_top_avg": f"{lsi_norm_top_avg:.3f}",
                "keyword_search_bim_top_avg": f"{bim_norm_top_avg:.3f}",
                "keyword_search_avg_doc_length": f"{avg_doc_length:.1f}",
                "keyword_search_proximity_enabled": "1" if proximity_enabled else "0",
                "keyword_search_static_quality_enabled": "1" if static_quality_enabled else "0",
                "keyword_search_tiered_enabled": (
                    "1" if settings.CLINICAL_CHAT_RAG_TIERED_RANKING_ENABLED else "0"
                ),
                "keyword_search_tier1_selected": str(
                    len(
                        [
                            item
                            for item in scored[:k]
                            if item[2] >= float(settings.CLINICAL_CHAT_RAG_TIER1_MIN_STATIC_QUALITY)
                        ]
                    )
                ),
            }
        )
        return top_scores, trace_info

    @staticmethod
    def _normalize_candidate_scores(
        scored: list[tuple[DocumentChunk, float]],
    ) -> dict[int, float]:
        if not scored:
            return {}
        values = [float(score) for _, score in scored]
        min_value = min(values)
        max_value = max(values)
        if max_value - min_value <= 1e-9:
            total = len(scored)
            return {
                int(chunk.id): (1.0 - (index / max(1, total)))
                for index, (chunk, _score) in enumerate(scored)
            }
        scale = max_value - min_value
        normalized: dict[int, float] = {}
        for chunk, score in scored:
            normalized[int(chunk.id)] = (float(score) - min_value) / scale
        return normalized

    @staticmethod
    def _normalize_raw_score_map(values_by_id: dict[int, float]) -> dict[int, float]:
        if not values_by_id:
            return {}
        min_value = min(values_by_id.values())
        max_value = max(values_by_id.values())
        if max_value - min_value <= 1e-9:
            return {item_id: 0.0 for item_id in values_by_id}
        scale = max_value - min_value
        return {
            item_id: (float(value) - min_value) / scale
            for item_id, value in values_by_id.items()
        }

    def _compute_lsi_norm_scores(
        self,
        *,
        prepared_chunks: list[tuple[DocumentChunk, dict[str, Counter[str]], int]],
        query_term_counts: Counter[str],
        zone_weights: dict[str, float],
    ) -> tuple[dict[int, float], dict[str, str]]:
        lsi_enabled = bool(settings.CLINICAL_CHAT_RAG_LSI_ENABLED)
        lsi_k = int(settings.CLINICAL_CHAT_RAG_LSI_K)
        lsi_max_vocab = int(settings.CLINICAL_CHAT_RAG_LSI_MAX_VOCAB_TERMS)
        lsi_min_docs = int(settings.CLINICAL_CHAT_RAG_LSI_MIN_DOCS)
        trace: dict[str, str] = {
            "keyword_search_lsi_enabled": "1" if lsi_enabled else "0",
            "keyword_search_lsi_k": str(lsi_k),
            "keyword_search_lsi_blend": f"{float(settings.CLINICAL_CHAT_RAG_LSI_BLEND):.2f}",
            "keyword_search_lsi_max_vocab_terms": str(lsi_max_vocab),
            "keyword_search_lsi_min_docs": str(lsi_min_docs),
            "keyword_search_lsi_vocab_size": "0",
            "keyword_search_lsi_components": "0",
            "keyword_search_lsi_doc_count": "0",
        }
        if not lsi_enabled:
            return {}, trace
        if np is None:
            trace["keyword_search_lsi_error"] = "numpy_unavailable"
            return {}, trace
        if len(prepared_chunks) < max(2, lsi_min_docs):
            trace["keyword_search_lsi_error"] = "insufficient_docs"
            trace["keyword_search_lsi_doc_count"] = str(len(prepared_chunks))
            return {}, trace

        try:
            doc_term_weights: list[dict[str, float]] = []
            doc_frequency: Counter[str] = Counter()
            collection_tf: Counter[str] = Counter()
            chunk_ids: list[int] = []
            for chunk, zone_counts, _doc_length in prepared_chunks:
                chunk_ids.append(int(chunk.id))
                merged_weights: dict[str, float] = {}
                for zone_name, zone_weight in zone_weights.items():
                    if zone_weight <= 0:
                        continue
                    counts = zone_counts.get(zone_name, Counter())
                    for term, term_count in counts.items():
                        safe_count = int(term_count)
                        if safe_count <= 0:
                            continue
                        merged_weights[term] = merged_weights.get(term, 0.0) + (
                            float(zone_weight) * float(safe_count)
                        )
                doc_term_weights.append(merged_weights)
                for term, tf_value in merged_weights.items():
                    collection_tf[term] += float(tf_value)
                for term in merged_weights:
                    doc_frequency[term] += 1

            query_terms = [term for term in query_term_counts if term]
            ranked_terms = [
                term for term, _value in collection_tf.most_common(max(1, lsi_max_vocab * 2))
            ]
            vocab: list[str] = []
            seen_vocab: set[str] = set()
            for term in query_terms + ranked_terms:
                if term in seen_vocab:
                    continue
                seen_vocab.add(term)
                vocab.append(term)
                if len(vocab) >= lsi_max_vocab:
                    break

            if len(vocab) < 2:
                trace["keyword_search_lsi_error"] = "insufficient_vocab"
                return {}, trace

            n_docs = len(doc_term_weights)
            n_terms = len(vocab)
            matrix = np.zeros((n_docs, n_terms), dtype=np.float32)
            idf_by_term: dict[str, float] = {}
            for term in vocab:
                df_value = float(doc_frequency.get(term, 0))
                idf_by_term[term] = math.log((n_docs + 1.0) / (df_value + 1.0)) + 1.0

            for row_id, term_weights in enumerate(doc_term_weights):
                for col_id, term in enumerate(vocab):
                    tf_value = float(term_weights.get(term, 0.0))
                    if tf_value <= 0:
                        continue
                    matrix[row_id, col_id] = float((1.0 + math.log(tf_value)) * idf_by_term[term])

            if not np.any(matrix):
                trace["keyword_search_lsi_error"] = "empty_matrix"
                return {}, trace

            query_vector = np.zeros((n_terms,), dtype=np.float32)
            for col_id, term in enumerate(vocab):
                query_tf = int(query_term_counts.get(term, 0))
                if query_tf <= 0:
                    continue
                query_vector[col_id] = float((1.0 + math.log(float(query_tf))) * idf_by_term[term])
            if not np.any(query_vector):
                trace["keyword_search_lsi_error"] = "empty_query_vector"
                return {}, trace

            u, singular_values, vt = np.linalg.svd(matrix, full_matrices=False)
            max_components = min(
                max(1, lsi_k),
                int(len(singular_values)),
                n_docs,
                n_terms,
            )
            if max_components <= 0:
                trace["keyword_search_lsi_error"] = "empty_components"
                return {}, trace

            u_k = u[:, :max_components]
            s_k = singular_values[:max_components]
            vt_k = vt[:max_components, :]
            safe_inv = np.where(s_k > 1e-8, 1.0 / s_k, 0.0)
            doc_latent = u_k * s_k
            query_latent = (query_vector @ vt_k.T) * safe_inv
            query_norm = float(np.linalg.norm(query_latent))
            if query_norm <= 0:
                trace["keyword_search_lsi_error"] = "zero_query_norm"
                return {}, trace

            doc_norms = np.linalg.norm(doc_latent, axis=1)
            raw_scores: dict[int, float] = {}
            for row_id, chunk_id in enumerate(chunk_ids):
                doc_norm = float(doc_norms[row_id])
                if doc_norm <= 0:
                    continue
                cosine_score = float(
                    np.dot(doc_latent[row_id], query_latent) / (doc_norm * query_norm)
                )
                raw_scores[int(chunk_id)] = max(0.0, cosine_score)

            normalized = self._normalize_raw_score_map(raw_scores)
            trace["keyword_search_lsi_vocab_size"] = str(len(vocab))
            trace["keyword_search_lsi_components"] = str(max_components)
            trace["keyword_search_lsi_doc_count"] = str(n_docs)
            return normalized, trace
        except Exception as exc:  # pragma: no cover - defensivo
            trace["keyword_search_lsi_error"] = exc.__class__.__name__
            return {}, trace

    @classmethod
    def _resolve_thesaurus_path(cls) -> Path:
        configured = Path(settings.CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_PATH)
        if configured.is_absolute():
            return configured
        candidate = Path.cwd() / configured
        if candidate.exists():
            return candidate
        repo_candidate = Path(__file__).resolve().parents[2] / configured
        return repo_candidate

    @classmethod
    def _load_global_thesaurus(cls) -> dict[str, tuple[str, ...]]:
        if not settings.CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_ENABLED:
            return {}
        now = time.time()
        ttl_seconds = settings.CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_TTL_SECONDS
        if (
            cls._global_thesaurus_cache_state is True
            and cls._global_thesaurus_cache_terms
            and (now - cls._global_thesaurus_cache_loaded_at) <= ttl_seconds
        ):
            return cls._global_thesaurus_cache_terms

        path = cls._resolve_thesaurus_path()
        if not path.exists():
            cls._global_thesaurus_cache_state = False
            cls._global_thesaurus_cache_error = "path_not_found"
            return {}

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                cls._global_thesaurus_cache_state = False
                cls._global_thesaurus_cache_error = "invalid_format"
                return {}

            normalized_map: dict[str, tuple[str, ...]] = {}
            max_expansions = max(
                1,
                int(settings.CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_MAX_EXPANSIONS_PER_TERM),
            )
            for raw_key, raw_values in payload.items():
                key_tokens = cls._tokenize_terms(str(raw_key or ""))
                if not key_tokens:
                    continue
                key = " ".join(key_tokens).strip().lower()
                values_iter = raw_values if isinstance(raw_values, list) else [raw_values]
                candidates: list[str] = []
                for raw_value in values_iter:
                    value_tokens = cls._tokenize_terms(str(raw_value or ""))
                    if not value_tokens:
                        continue
                    candidate = " ".join(value_tokens).strip().lower()
                    if not candidate or candidate == key:
                        continue
                    if candidate not in candidates:
                        candidates.append(candidate)
                if candidates:
                    normalized_map[key] = tuple(candidates[:max_expansions])

            cls._global_thesaurus_cache_terms = normalized_map
            cls._global_thesaurus_cache_loaded_at = now
            cls._global_thesaurus_cache_state = True
            cls._global_thesaurus_cache_error = None
            return cls._global_thesaurus_cache_terms
        except Exception as exc:  # pragma: no cover - defensivo I/O
            cls._global_thesaurus_cache_state = False
            cls._global_thesaurus_cache_error = exc.__class__.__name__
            return {}

    @classmethod
    def _expand_query_for_retrieval_details(
        cls,
        query: str,
        specialty_filter: Optional[str] = None,
    ) -> tuple[str, list[str], list[str], list[str], list[str]]:
        raw_tokens = re.findall(r"[a-z0-9#\-\+/]+", query.lower())
        normalized = [token.strip() for token in raw_tokens if token.strip()]
        expanded_terms: list[str] = []
        local_terms: list[str] = []
        global_terms: list[str] = []
        specialty_terms: list[str] = []
        seen_terms = set(normalized)
        global_thesaurus = cls._load_global_thesaurus()
        max_global = max(
            1,
            int(settings.CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_MAX_EXPANSIONS_PER_TERM),
        )

        def _append_term(term: str, bucket: list[str]) -> None:
            normalized_term = " ".join(cls._tokenize_terms(term)).strip().lower()
            if not normalized_term or normalized_term in seen_terms:
                return
            seen_terms.add(normalized_term)
            expanded_terms.append(normalized_term)
            bucket.append(normalized_term)

        for token in normalized:
            for extra in cls._QUERY_EXPANSIONS.get(token, []):
                _append_term(extra.replace("_", " "), local_terms)
            thesaurus_values = list(global_thesaurus.get(token, ()))
            if not thesaurus_values:
                token_plain = cls._strip_accents(token)
                if token_plain != token:
                    thesaurus_values = list(global_thesaurus.get(token_plain, ()))
            for extra in thesaurus_values[:max_global]:
                _append_term(extra, global_terms)

        specialty_key = str(specialty_filter or "").strip().lower()
        for hint in cls._SPECIALTY_HINTS.get(specialty_key, []):
            _append_term(hint, specialty_terms)

        if not expanded_terms:
            return query, [], [], [], []
        expanded_query = f"{query} {' '.join(expanded_terms)}"
        return expanded_query, expanded_terms, local_terms, global_terms, specialty_terms

    @classmethod
    def _expand_query_for_retrieval(
        cls,
        query: str,
        specialty_filter: Optional[str] = None,
    ) -> tuple[str, list[str]]:
        expanded_query, expanded_terms, _local, _global, _specialty = (
            cls._expand_query_for_retrieval_details(
                query=query,
                specialty_filter=specialty_filter,
            )
        )
        return expanded_query, expanded_terms

    def _derive_prf_terms(
        self,
        *,
        query: str,
        seed_chunks: list[DocumentChunk],
    ) -> list[str]:
        if not settings.CLINICAL_CHAT_RAG_PRF_ENABLED:
            return []
        if not seed_chunks:
            return []

        min_term_len = int(settings.CLINICAL_CHAT_RAG_PRF_MIN_TERM_LEN)
        query_terms = [term for term in self._tokenize_terms(query) if len(term) >= min_term_len]
        query_set = set(query_terms)
        if not query_set:
            return []

        top_k = max(1, int(settings.CLINICAL_CHAT_RAG_PRF_TOPK))
        selected = seed_chunks[:top_k]
        if not selected:
            return []

        term_tf_sum: dict[str, float] = {}
        term_df: dict[str, int] = {}
        for chunk in selected:
            text = " ".join(
                [
                    str(chunk.section_path or ""),
                    str(chunk.chunk_text or ""),
                    " ".join(str(item) for item in (chunk.keywords or [])),
                    " ".join(str(item) for item in (chunk.custom_questions or [])),
                ]
            )
            tokens = [
                token
                for token in self._tokenize_terms(text)
                if len(token) >= min_term_len and token not in query_set
            ]
            if not tokens:
                continue
            counts = Counter(tokens)
            for term, count in counts.items():
                term_tf_sum[term] = term_tf_sum.get(term, 0.0) + self._sublinear_tf(count)
                term_df[term] = term_df.get(term, 0) + 1

        if not term_tf_sum:
            return []

        beta = float(settings.CLINICAL_CHAT_RAG_PRF_BETA)
        gamma = float(settings.CLINICAL_CHAT_RAG_PRF_GAMMA)
        denominator = max(1.0, float(len(selected)))
        scores: list[tuple[str, float]] = []
        for term, tf_sum in term_tf_sum.items():
            df_value = float(term_df.get(term, 0))
            idf_local = math.log((denominator + 1.0) / (df_value + 1.0)) + 1.0
            mean_tf = tf_sum / denominator
            score = (beta * mean_tf * idf_local) - (gamma * (df_value / denominator))
            if score > 0:
                scores.append((term, score))

        if not scores:
            return []
        scores.sort(key=lambda item: item[1], reverse=True)
        max_terms = max(1, int(settings.CLINICAL_CHAT_RAG_PRF_MAX_TERMS))
        return [term for term, _score in scores[:max_terms]]

    def _expand_query_with_feedback(
        self,
        *,
        query: str,
        db: Session,
        specialty_filter: Optional[str],
        candidate_pool: int,
    ) -> tuple[str, dict[str, str]]:
        (
            expanded_query,
            expansion_terms,
            local_terms,
            global_terms,
            specialty_terms,
        ) = self._expand_query_for_retrieval_details(
            query=query,
            specialty_filter=specialty_filter,
        )
        trace = {
            "retrieval_query_expanded": "1" if expansion_terms else "0",
            "retrieval_query_expansion_terms": (
                ",".join(expansion_terms[:12]) if expansion_terms else "none"
            ),
            "retrieval_query_expansion_local_terms": (
                ",".join(local_terms[:8]) if local_terms else "none"
            ),
            "retrieval_query_expansion_global_terms": (
                ",".join(global_terms[:8]) if global_terms else "none"
            ),
            "retrieval_query_expansion_specialty_terms": (
                ",".join(specialty_terms[:8]) if specialty_terms else "none"
            ),
        }

        if not settings.CLINICAL_CHAT_RAG_PRF_ENABLED:
            trace["retrieval_query_prf_enabled"] = "0"
            trace["retrieval_query_prf_terms"] = "none"
            return expanded_query, trace

        seed_pool = max(candidate_pool, max(48, int(settings.CLINICAL_CHAT_RAG_PRF_TOPK) * 12))
        seed_chunks, _seed_trace = self._fetch_candidate_chunks(
            query=expanded_query,
            db=db,
            specialty_filter=specialty_filter,
            candidate_pool=seed_pool,
        )
        seed_ranked, _seed_rank_trace = self._score_keyword_candidates(
            query=expanded_query,
            chunks=seed_chunks,
            k=max(1, int(settings.CLINICAL_CHAT_RAG_PRF_TOPK)),
        )
        ranked_seed_chunks = [chunk for chunk, _score in seed_ranked] or seed_chunks
        prf_terms = self._derive_prf_terms(query=expanded_query, seed_chunks=ranked_seed_chunks)
        if prf_terms:
            expanded_query = f"{expanded_query} {' '.join(prf_terms)}"
        trace["retrieval_query_prf_enabled"] = "1"
        trace["retrieval_query_prf_terms"] = ",".join(prf_terms[:8]) if prf_terms else "none"
        trace["retrieval_query_prf_topk"] = str(int(settings.CLINICAL_CHAT_RAG_PRF_TOPK))
        return expanded_query, trace

    def search_vector(
        self,
        query: str,
        db: Session,
        *,
        k: int = 5,
        specialty_filter: Optional[str] = None,
    ) -> tuple[list[DocumentChunk], dict[str, str]]:
        candidate_pool = max(settings.CLINICAL_CHAT_RAG_FTS_CANDIDATE_POOL, max(k * 8, 80))
        all_chunks, candidate_trace = self._fetch_candidate_chunks(
            query=query,
            db=db,
            specialty_filter=specialty_filter,
            candidate_pool=candidate_pool,
        )
        scored, trace_info = self._score_vector_candidates(
            query=query,
            chunks=all_chunks,
            k=k,
        )
        results: list[DocumentChunk] = []
        for chunk, score in scored:
            setattr(chunk, "_rag_score", float(score))
            results.append(chunk)
        trace_info.update(candidate_trace)
        return results, trace_info

    def search_keyword(
        self,
        query: str,
        db: Session,
        *,
        k: int = 5,
        specialty_filter: Optional[str] = None,
    ) -> tuple[list[DocumentChunk], dict[str, str]]:
        candidate_pool = max(settings.CLINICAL_CHAT_RAG_FTS_CANDIDATE_POOL, max(k * 8, 80))
        expanded_query, expansion_trace = self._expand_query_with_feedback(
            query=query,
            db=db,
            specialty_filter=specialty_filter,
            candidate_pool=candidate_pool,
        )
        all_chunks, candidate_trace = self._fetch_candidate_chunks(
            query=expanded_query,
            db=db,
            specialty_filter=specialty_filter,
            candidate_pool=candidate_pool,
        )
        scored, trace_info = self._score_keyword_candidates(
            query=expanded_query,
            chunks=all_chunks,
            k=k,
        )
        results: list[DocumentChunk] = []
        for chunk, score in scored:
            setattr(chunk, "_rag_score", float(score))
            results.append(chunk)
        trace_info.update(candidate_trace)
        trace_info.update(expansion_trace)
        return results, trace_info

    def search_hybrid(
        self,
        query: str,
        db: Session,
        *,
        k: int = 5,
        specialty_filter: Optional[str] = None,
        keyword_only: bool = False,
    ) -> tuple[list[DocumentChunk], dict[str, str]]:
        started_at = time.perf_counter()
        trace: dict[str, str] = {}
        candidate_pool = max(settings.CLINICAL_CHAT_RAG_FTS_CANDIDATE_POOL, max(k * 12, 120))
        expanded_query, expansion_trace = self._expand_query_with_feedback(
            query=query,
            db=db,
            specialty_filter=specialty_filter,
            candidate_pool=candidate_pool,
        )
        trace.update(expansion_trace)
        all_chunks, candidate_trace = self._fetch_candidate_chunks(
            query=expanded_query,
            db=db,
            specialty_filter=specialty_filter,
            candidate_pool=candidate_pool,
        )
        trace.update(candidate_trace)
        candidate_k = max(k * 2, 8)

        if keyword_only:
            vector_scored = []
            vector_trace = {
                "vector_search_chunks_found": "0",
                "vector_search_latency_ms": "0.0",
                "vector_search_method": "disabled_keyword_only",
            }
            keyword_scored, keyword_trace = self._score_keyword_candidates(
                query=expanded_query,
                chunks=all_chunks,
                k=candidate_k,
            )
            trace["hybrid_parallelized"] = "0"
            trace["hybrid_vector_disabled"] = "1"
        elif settings.CLINICAL_CHAT_RAG_PARALLEL_HYBRID_ENABLED:
            with ThreadPoolExecutor(max_workers=2) as executor:
                vector_future = executor.submit(
                    self._score_vector_candidates,
                    query=query,
                    chunks=all_chunks,
                    k=candidate_k,
                )
                keyword_future = executor.submit(
                    self._score_keyword_candidates,
                    query=expanded_query,
                    chunks=all_chunks,
                    k=candidate_k,
                )
                vector_scored, vector_trace = vector_future.result()
                keyword_scored, keyword_trace = keyword_future.result()
            trace["hybrid_parallelized"] = "1"
            trace["hybrid_vector_disabled"] = "0"
        else:
            vector_scored, vector_trace = self._score_vector_candidates(
                query=query,
                chunks=all_chunks,
                k=candidate_k,
            )
            keyword_scored, keyword_trace = self._score_keyword_candidates(
                query=expanded_query,
                chunks=all_chunks,
                k=candidate_k,
            )
            trace["hybrid_parallelized"] = "0"
            trace["hybrid_vector_disabled"] = "0"

        trace.update(vector_trace)
        trace.update(keyword_trace)

        combined_scores: dict[int, float] = {}
        chunks_by_id: dict[int, DocumentChunk] = {}
        vector_scores_by_id = self._normalize_candidate_scores(vector_scored)
        keyword_scores_by_id = self._normalize_candidate_scores(keyword_scored)

        if vector_scored:
            for chunk, _score in vector_scored:
                weighted = vector_scores_by_id.get(int(chunk.id), 0.0) * self.vector_weight
                combined_scores[int(chunk.id)] = combined_scores.get(int(chunk.id), 0.0) + weighted
                chunks_by_id[chunk.id] = chunk

        if keyword_scored:
            for chunk, _score in keyword_scored:
                weighted = keyword_scores_by_id.get(int(chunk.id), 0.0) * self.keyword_weight
                combined_scores[int(chunk.id)] = combined_scores.get(int(chunk.id), 0.0) + weighted
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
                    "keyword_only" if keyword_only else (
                        "normalized_score_mix "
                        f"vector({self.vector_weight:.0%})"
                        f"+keyword({self.keyword_weight:.0%})"
                    )
                ),
            }
        )
        return result, trace

    def search_by_domain(
        self,
        detected_domains: list[str],
        db: Session,
        *,
        query: str = "",
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
            "nephrology": ["nefrologia", "renal", "oliguria", "anuria", "potasio", "dialisis"],
            "oncology": ["oncologia", "neutropenia", "iraes", "quimioterapia", "inmunoterapia"],
            "gynecology_obstetrics": [
                "ginecologia",
                "obstetricia",
                "gestante",
                "preeclampsia",
                "sangrado",
            ],
            "pneumology": ["neumologia", "disnea", "hipoxemia", "oxigeno", "gasometria"],
            "urology": ["urologia", "hidronefrosis", "retencion", "urinaria", "obstruccion"],
            "pediatrics_neonatology": ["pediatria", "neonatal", "lactante", "fiebre"],
            "palliative": ["paliativo", "dolor total", "sedacion paliativa", "final de vida"],
            "anisakis": ["anisakis", "anisakiasis", "pescado", "epigastrico"],
            "genetic_recurrence": ["genetica", "recurrencia", "mutacion", "mosaicismo"],
        }
        domain_specialties = {
            "scasest": {"scasest", "cardiology", "critical_ops"},
            "sepsis": {"sepsis", "critical_ops", "infectious_disease"},
            "resuscitation": {"resuscitation", "critical_ops", "anesthesiology"},
            "critical_ops": {"critical_ops", "emergencies"},
            "neurology": {"neurology"},
            "trauma": {"trauma"},
            "medicolegal": {"medicolegal"},
            "nephrology": {"nephrology"},
            "oncology": {"oncology", "hematology", "odontology"},
            "gynecology_obstetrics": {"gynecology_obstetrics"},
            "pneumology": {"pneumology"},
            "urology": {"urology"},
            "pediatrics_neonatology": {"pediatrics_neonatology"},
            "palliative": {"palliative", "palliative_care"},
            "anisakis": {"anisakis", "infectious_disease"},
            "genetic_recurrence": {"genetic_recurrence", "genetics"},
        }

        terms: list[str] = []
        specialty_candidates: set[str] = set()
        for domain in detected_domains:
            terms.extend(domain_terms.get(domain, [domain]))
            specialty_candidates.update(domain_specialties.get(domain, set()))
        terms = [term for term in terms if term]
        unique_terms = list(dict.fromkeys(terms))
        if query.strip():
            query_terms = [
                term
                for term in re.findall(r"[a-zA-Z0-9áéíóúñÁÉÍÓÚÑ\-]+", query.lower())
                if len(term) >= 4
            ]
            for term in query_terms[:12]:
                if term not in unique_terms:
                    unique_terms.append(term)

        filters = []
        for term in unique_terms[:12]:
            like_term = f"%{term}%"
            filters.append(DocumentChunk.chunk_text.ilike(like_term))
            filters.append(DocumentChunk.section_path.ilike(like_term))
            filters.append(DocumentChunk.specialty.ilike(like_term))

        query_builder = db.query(DocumentChunk)
        if filters:
            query_builder = query_builder.filter(or_(*filters))
        specialty_candidates = {item.strip().lower() for item in specialty_candidates if item}
        specialty_filtered_count = 0
        raw_results: list[DocumentChunk]
        if specialty_candidates:
            specialty_query = query_builder.filter(
                func.lower(DocumentChunk.specialty).in_(sorted(specialty_candidates))
            )
            raw_results = specialty_query.limit(max(k * 8, 32)).all()
            specialty_filtered_count = len(raw_results)
            if not raw_results:
                raw_results = query_builder.limit(max(k * 8, 32)).all()
                trace["domain_search_specialty_fallback"] = "1"
            else:
                trace["domain_search_specialty_fallback"] = "0"
        else:
            raw_results = query_builder.limit(max(k * 8, 32)).all()
            trace["domain_search_specialty_fallback"] = "na"

        scored: list[tuple[DocumentChunk, float]] = []
        for chunk in raw_results:
            text = f"{chunk.section_path or ''} {chunk.chunk_text or ''}".lower()
            keyword_hits = 0
            for keyword in chunk.keywords or []:
                keyword_text = str(keyword).lower()
                if keyword_text and keyword_text in unique_terms:
                    keyword_hits += 1
            question_hits = 0
            for question in chunk.custom_questions or []:
                question_text = str(question).lower()
                if any(term in question_text for term in unique_terms[:8]):
                    question_hits += 1

            score = float(sum(1 for term in unique_terms if term.lower() in text))
            score += float(keyword_hits) * 1.4
            score += float(question_hits) * 1.1
            chunk_specialty = str(getattr(chunk, "specialty", "") or "").strip().lower()
            if specialty_candidates and chunk_specialty in specialty_candidates:
                score += 1.6
            if score > 0:
                scored.append((chunk, score))
        scored.sort(key=lambda item: item[1], reverse=True)

        result: list[DocumentChunk] = []
        for chunk, score in scored[:k]:
            setattr(chunk, "_rag_score", float(score))
            result.append(chunk)

        trace["domain_search_chunks_found"] = str(len(result))
        trace["domain_search_terms"] = ",".join(unique_terms[:8]) if unique_terms else "none"
        trace["domain_search_specialties"] = (
            ",".join(sorted(specialty_candidates)[:8]) if specialty_candidates else "none"
        )
        trace["domain_search_specialty_hits"] = str(specialty_filtered_count)
        return result, trace
