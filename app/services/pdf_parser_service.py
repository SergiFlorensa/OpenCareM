"""
Servicio de parsing PDF con backend configurable.

Backends soportados:
- pypdf: extraccion local simple.
- mineru: endpoint externo/local orientado a layout+contenido.
"""
from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class PDFParseResult:
    """Resultado estructurado de parseo PDF."""

    text: str
    blocks: list[dict[str, Any]]
    trace: dict[str, str]


class PDFParserService:
    """Wrapper de parsing PDF para desacoplar estrategia OCR/layout."""

    @classmethod
    def extract_text(cls, file_path: Path) -> str:
        return cls.parse(file_path).text

    @classmethod
    def parse(cls, file_path: Path) -> PDFParseResult:
        backend = str(settings.CLINICAL_CHAT_PDF_PARSER_BACKEND or "pypdf").strip().lower()
        if backend == "mineru":
            try:
                return cls._parse_with_mineru(file_path)
            except Exception as exc:  # pragma: no cover - runtime externo
                if not settings.CLINICAL_CHAT_PDF_MINERU_FAIL_OPEN:
                    raise
                logger.warning(
                    "MinerU no disponible para %s (%s). Fallback a pypdf.",
                    file_path,
                    exc.__class__.__name__,
                )
                fallback = cls._parse_with_pypdf(file_path)
                fallback.trace["pdf_parser_backend_requested"] = "mineru"
                fallback.trace["pdf_parser_fail_open_used"] = "1"
                fallback.trace["pdf_parser_fail_reason"] = exc.__class__.__name__
                return fallback
        result = cls._parse_with_pypdf(file_path)
        result.trace["pdf_parser_fail_open_used"] = "0"
        return result

    @staticmethod
    def _parse_with_pypdf(file_path: Path) -> PDFParseResult:
        started_at = time.perf_counter()
        try:
            from pypdf import PdfReader
        except Exception as exc:  # pragma: no cover - depende del entorno
            raise RuntimeError(
                "No se pudo procesar PDF: instala 'pypdf' en el entorno activo."
            ) from exc

        reader = PdfReader(str(file_path))
        blocks: list[dict[str, Any]] = []
        pages_total = len(reader.pages)
        for index, page in enumerate(reader.pages, start=1):
            page_text = (page.extract_text() or "").strip()
            if not page_text:
                continue
            blocks.append(
                {
                    "type": "text",
                    "content": f"[PAGE {index}]\n{page_text}",
                    "section_path": f"Documento > Pagina {index}",
                    "page": index,
                    "order": index,
                }
            )

        text = "\n\n".join(str(item["content"]).strip() for item in blocks if item.get("content"))
        latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
        trace = {
            "pdf_parser_backend": "pypdf",
            "pdf_parser_pages_total": str(pages_total),
            "pdf_parser_blocks_total": str(len(blocks)),
            "pdf_parser_blocks_filtered": "0",
            "pdf_parser_ocr_mode": "none",
            "pdf_parser_latency_ms": str(latency_ms),
            "pdf_parser_reading_order_enabled": "0",
            "pdf_parser_filter_repeated_edges_enabled": "0",
        }
        return PDFParseResult(text=text.strip(), blocks=blocks, trace=trace)

    @classmethod
    def _parse_with_mineru(cls, file_path: Path) -> PDFParseResult:
        base_url = str(settings.CLINICAL_CHAT_PDF_MINERU_BASE_URL or "").strip().rstrip("/")
        if not base_url:
            raise RuntimeError("CLINICAL_CHAT_PDF_MINERU_BASE_URL vacio.")

        payload = {
            "file_path": str(file_path),
            "pipeline": "two_stage_layout_content",
            "return_format": "json_markdown",
            "table_format": "otsl",
            "formula_format": "latex",
            "include_layout": True,
            "reading_order": (
                "top_to_bottom_left_to_right"
                if settings.CLINICAL_CHAT_PDF_LAYOUT_READING_ORDER_ENABLED
                else "source_order"
            ),
            "drop_page_artifacts": settings.CLINICAL_CHAT_PDF_FILTER_REPEATED_EDGE_TEXT_ENABLED,
            "ocr": {
                "mode": settings.CLINICAL_CHAT_PDF_OCR_MODE,
                "layout_first": True,
            },
        }
        request = Request(
            url=f"{base_url}/v1/parse",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        started_at = time.perf_counter()
        try:
            with urlopen(
                request,
                timeout=max(10, int(settings.CLINICAL_CHAT_PDF_MINERU_TIMEOUT_SECONDS)),
            ) as response:
                raw = response.read().decode("utf-8")
        except URLError as exc:
            raise RuntimeError("MinerU endpoint no disponible.") from exc

        latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("MinerU devolvio payload invalido.") from exc

        raw_blocks = cls._extract_raw_blocks(data)
        normalized_blocks = cls._normalize_blocks(raw_blocks)
        ordered_blocks = (
            cls._sort_blocks_reading_order(normalized_blocks)
            if settings.CLINICAL_CHAT_PDF_LAYOUT_READING_ORDER_ENABLED
            else normalized_blocks
        )
        if settings.CLINICAL_CHAT_PDF_FILTER_REPEATED_EDGE_TEXT_ENABLED:
            cleaned_blocks, filtered_count = cls._drop_repeated_page_artifacts(ordered_blocks)
        else:
            cleaned_blocks, filtered_count = ordered_blocks, 0

        text = cls._compose_text_from_blocks(cleaned_blocks)
        if not text:
            fallback_text = cls._extract_text_fallback(data)
            text = fallback_text
        if not text:
            raise RuntimeError("MinerU no devolvio texto util.")

        table_blocks = sum(1 for block in cleaned_blocks if block.get("type") == "table")
        formula_blocks = sum(1 for block in cleaned_blocks if block.get("type") == "formula")
        trace = {
            "pdf_parser_backend": "mineru",
            "pdf_parser_pages_total": str(cls._infer_pages_total(data, cleaned_blocks)),
            "pdf_parser_blocks_total": str(len(ordered_blocks)),
            "pdf_parser_blocks_filtered": str(filtered_count),
            "pdf_parser_blocks_kept": str(len(cleaned_blocks)),
            "pdf_parser_table_blocks": str(table_blocks),
            "pdf_parser_formula_blocks": str(formula_blocks),
            "pdf_parser_ocr_mode": settings.CLINICAL_CHAT_PDF_OCR_MODE,
            "pdf_parser_latency_ms": str(latency_ms),
            "pdf_parser_reading_order_enabled": (
                "1" if settings.CLINICAL_CHAT_PDF_LAYOUT_READING_ORDER_ENABLED else "0"
            ),
            "pdf_parser_filter_repeated_edges_enabled": (
                "1" if settings.CLINICAL_CHAT_PDF_FILTER_REPEATED_EDGE_TEXT_ENABLED else "0"
            ),
        }
        if settings.CLINICAL_CHAT_PDF_TELEMETRY_ENABLED:
            logger.info(
                "PDF parseado con MinerU | file=%s blocks=%s filtered=%s latency_ms=%.2f",
                file_path,
                len(cleaned_blocks),
                filtered_count,
                latency_ms,
            )
        return PDFParseResult(text=text.strip(), blocks=cleaned_blocks, trace=trace)

    @staticmethod
    def _extract_raw_blocks(data: dict[str, Any]) -> list[dict[str, Any]]:
        for key in ("para_blocks", "blocks", "layout_blocks", "elements"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        pages = data.get("pages")
        if isinstance(pages, list):
            extracted: list[dict[str, Any]] = []
            for page_index, page in enumerate(pages, start=1):
                if not isinstance(page, dict):
                    continue
                page_blocks = page.get("para_blocks") or page.get("blocks") or []
                if isinstance(page_blocks, list):
                    for block in page_blocks:
                        if not isinstance(block, dict):
                            continue
                        block_copy = dict(block)
                        block_copy.setdefault("page", page.get("page") or page_index)
                        extracted.append(block_copy)
            return extracted
        return []

    @classmethod
    def _normalize_blocks(cls, blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for index, block in enumerate(blocks):
            block_type = cls._normalize_block_type(
                block.get("type")
                or block.get("block_type")
                or block.get("category")
            )
            content = cls._extract_block_content(block, block_type=block_type)
            if not content:
                continue
            page_value = cls._safe_int(block.get("page") or block.get("page_no")) or 1
            bbox = cls._extract_bbox(block)
            section_path = (
                str(
                    block.get("section_path")
                    or block.get("section")
                    or block.get("heading")
                    or ""
                ).strip()
                or f"Documento > Pagina {page_value}"
            )
            normalized.append(
                {
                    "type": block_type,
                    "content": content,
                    "section_path": section_path,
                    "page": page_value,
                    "bbox": bbox,
                    "order": index,
                }
            )
        return normalized

    @staticmethod
    def _normalize_block_type(raw_type: Any) -> str:
        normalized = str(raw_type or "text").strip().lower()
        if normalized in {"table", "otsl_table", "html_table"}:
            return "table"
        if normalized in {"formula", "equation", "latex"}:
            return "formula"
        if normalized in {"title", "header"}:
            return "header"
        if normalized in {"footer", "page_footer"}:
            return "footer"
        return "text"

    @staticmethod
    def _extract_block_content(block: dict[str, Any], *, block_type: str) -> str:
        if block_type == "table":
            content = (
                block.get("otsl")
                or block.get("markdown")
                or block.get("html")
                or block.get("text")
                or block.get("content")
            )
            if content:
                return str(content).strip()
            return ""
        if block_type == "formula":
            latex = block.get("latex") or block.get("text") or block.get("content")
            latex_text = str(latex or "").strip()
            if not latex_text:
                return ""
            if not latex_text.startswith("$$"):
                return f"$$ {latex_text} $$"
            return latex_text
        content = (
            block.get("markdown")
            or block.get("text")
            or block.get("content")
            or block.get("html")
        )
        return str(content or "").strip()

    @staticmethod
    def _extract_bbox(block: dict[str, Any]) -> list[float] | None:
        bbox = block.get("bbox")
        if isinstance(bbox, list) and len(bbox) >= 4:
            try:
                return [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])]
            except (TypeError, ValueError):
                return None
        keys = ("x0", "y0", "x1", "y1")
        if all(key in block for key in keys):
            try:
                return [
                    float(block["x0"]),
                    float(block["y0"]),
                    float(block["x1"]),
                    float(block["y1"]),
                ]
            except (TypeError, ValueError):
                return None
        return None

    @classmethod
    def _sort_blocks_reading_order(cls, blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        def sort_key(item: dict[str, Any]) -> tuple[int, float, float, int]:
            page = cls._safe_int(item.get("page")) or 1
            bbox = item.get("bbox")
            if isinstance(bbox, list) and len(bbox) >= 4:
                return (page, float(bbox[1]), float(bbox[0]), cls._safe_int(item.get("order")) or 0)
            return (page, 1e9, 1e9, cls._safe_int(item.get("order")) or 0)

        return sorted(blocks, key=sort_key)

    @classmethod
    def _drop_repeated_page_artifacts(
        cls,
        blocks: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], int]:
        if not blocks:
            return [], 0

        by_page: dict[int, list[dict[str, Any]]] = {}
        for block in blocks:
            page = cls._safe_int(block.get("page")) or 1
            by_page.setdefault(page, []).append(block)
        if len(by_page) < 2:
            return blocks, 0

        edge_counter: dict[str, int] = {}
        page_edges: dict[int, tuple[str | None, str | None]] = {}
        for page, page_blocks in by_page.items():
            head = cls._normalize_line(page_blocks[0].get("content", "")) if page_blocks else None
            tail = cls._normalize_line(page_blocks[-1].get("content", "")) if page_blocks else None
            page_edges[page] = (head, tail)
            if head:
                edge_counter[head] = edge_counter.get(head, 0) + 1
            if tail:
                edge_counter[tail] = edge_counter.get(tail, 0) + 1

        repeated_threshold = max(
            2,
            int(settings.CLINICAL_CHAT_PDF_FILTER_REPEATED_EDGE_TEXT_MIN_PAGES),
        )
        repeated_edges = {
            line
            for line, count in edge_counter.items()
            if line and count >= repeated_threshold and len(line) <= 120
        }
        if not repeated_edges:
            return blocks, 0

        cleaned: list[dict[str, Any]] = []
        removed = 0
        for page in sorted(by_page):
            page_blocks = by_page[page]
            for idx, block in enumerate(page_blocks):
                normalized_content = cls._normalize_line(block.get("content", ""))
                is_edge_block = idx == 0 or idx == (len(page_blocks) - 1)
                if is_edge_block and normalized_content in repeated_edges:
                    removed += 1
                    continue
                cleaned.append(block)
        return cleaned, removed

    @staticmethod
    def _compose_text_from_blocks(blocks: list[dict[str, Any]]) -> str:
        parts = [str(block.get("content", "")).strip() for block in blocks if block.get("content")]
        parts = [item for item in parts if item]
        return "\n\n".join(parts).strip()

    @staticmethod
    def _extract_text_fallback(data: dict[str, Any]) -> str:
        text = str(data.get("text") or data.get("markdown") or data.get("content") or "").strip()
        if text:
            return text
        pages = data.get("pages")
        if isinstance(pages, list):
            page_parts: list[str] = []
            for page_index, page in enumerate(pages, start=1):
                if not isinstance(page, dict):
                    continue
                page_text = str(page.get("text") or page.get("markdown") or "").strip()
                if not page_text:
                    continue
                page_parts.append(f"[PAGE {page_index}]\n{page_text}")
            return "\n\n".join(page_parts).strip()
        return ""

    @staticmethod
    def _infer_pages_total(data: dict[str, Any], blocks: list[dict[str, Any]]) -> int:
        pages = data.get("pages")
        if isinstance(pages, list) and pages:
            return len(pages)
        pages_from_blocks = {
            int(block.get("page"))
            for block in blocks
            if isinstance(block.get("page"), int)
        }
        return len(pages_from_blocks) if pages_from_blocks else 0

    @staticmethod
    def _normalize_line(value: Any) -> str:
        normalized = re.sub(r"\s+", " ", str(value or "").strip().lower())
        normalized = re.sub(r"[^a-z0-9\s:\-_/\.]", "", normalized)
        return normalized.strip()

    @staticmethod
    def _safe_int(value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
