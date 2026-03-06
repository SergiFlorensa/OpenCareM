"""
Servicio de parsing PDF con backend configurable.

Backends soportados:
- pypdf: extraccion local simple.
- mineru: CLI local OSS o endpoint HTTP orientado a layout+contenido.
"""
from __future__ import annotations

import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
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
            requested_transport = cls._normalize_transport(
                settings.CLINICAL_CHAT_PDF_MINERU_TRANSPORT
            )
            failures: list[str] = []
            last_exc: Exception | None = None
            for transport in cls._resolve_mineru_transports(requested_transport):
                try:
                    if transport == "cli":
                        result = cls._parse_with_mineru_cli(file_path)
                    else:
                        result = cls._parse_with_mineru_http(file_path)
                    result.trace["pdf_parser_backend_requested"] = "mineru"
                    result.trace["pdf_parser_transport_requested"] = requested_transport
                    result.trace["pdf_parser_fail_open_used"] = "0"
                    return result
                except Exception as exc:  # pragma: no cover - runtime externo
                    last_exc = exc
                    failures.append(f"{transport}:{exc.__class__.__name__}")
                    logger.warning(
                        "MinerU %s no disponible para %s (%s).",
                        transport,
                        file_path,
                        exc.__class__.__name__,
                    )
            if not settings.CLINICAL_CHAT_PDF_MINERU_FAIL_OPEN and last_exc is not None:
                raise last_exc
            if last_exc is not None:
                logger.warning(
                    "MinerU no disponible para %s (%s). Fallback a pypdf.",
                    file_path,
                    last_exc.__class__.__name__,
                )
                fallback = cls._parse_with_pypdf(file_path)
                fallback.trace["pdf_parser_backend_requested"] = "mineru"
                fallback.trace["pdf_parser_transport_requested"] = requested_transport
                fallback.trace["pdf_parser_fail_open_used"] = "1"
                fallback.trace["pdf_parser_fail_reason"] = last_exc.__class__.__name__
                fallback.trace["pdf_parser_failures"] = "|".join(failures)
                return fallback
        result = cls._parse_with_pypdf(file_path)
        result.trace["pdf_parser_fail_open_used"] = "0"
        return result

    @staticmethod
    def _normalize_transport(raw_value: Any) -> str:
        transport = str(raw_value or "cli").strip().lower()
        return transport or "cli"

    @classmethod
    def _resolve_mineru_transports(cls, requested_transport: str) -> list[str]:
        normalized = cls._normalize_transport(requested_transport)
        if normalized == "auto":
            return ["cli", "http"]
        return [normalized]

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
    def _parse_with_mineru_cli(cls, file_path: Path) -> PDFParseResult:
        page_count = cls._get_pdf_page_count(file_path)
        if cls._should_window_mineru_cli(page_count):
            return cls._parse_with_mineru_cli_windowed(file_path, page_count=page_count)

        output_dir = Path(tempfile.mkdtemp(prefix="mineru_cli_"))
        try:
            return cls._run_mineru_cli_once(file_path=file_path, output_dir=output_dir)
        finally:
            shutil.rmtree(output_dir, ignore_errors=True)

    @classmethod
    def _parse_with_mineru_cli_windowed(cls, file_path: Path, *, page_count: int) -> PDFParseResult:
        window_size = max(2, int(settings.CLINICAL_CHAT_PDF_MINERU_WINDOW_SIZE_PAGES))
        window_ranges: list[tuple[int, int]] = []
        start_page = 0
        while start_page < page_count:
            end_page = min(page_count - 1, start_page + window_size - 1)
            window_ranges.append((start_page, end_page))
            start_page = end_page + 1

        merged_blocks: list[dict[str, Any]] = []
        total_blocks = 0
        total_filtered = 0
        total_kept = 0
        total_tables = 0
        total_formulas = 0
        total_latency = 0.0
        cli_json_names: list[str] = []
        cli_markdown_names: list[str] = []

        for window_start, window_end in window_ranges:
            output_dir = Path(tempfile.mkdtemp(prefix="mineru_cli_window_"))
            try:
                result = cls._run_mineru_cli_once(
                    file_path=file_path,
                    output_dir=output_dir,
                    start_page=window_start,
                    end_page=window_end,
                )
            finally:
                shutil.rmtree(output_dir, ignore_errors=True)
            shifted_blocks = cls._shift_blocks_to_window_offset(
                result.blocks,
                page_offset=window_start,
            )
            merged_blocks.extend(shifted_blocks)
            total_blocks += cls._safe_int(result.trace.get("pdf_parser_blocks_total")) or 0
            total_filtered += cls._safe_int(result.trace.get("pdf_parser_blocks_filtered")) or 0
            total_kept += cls._safe_int(result.trace.get("pdf_parser_blocks_kept")) or len(
                shifted_blocks
            )
            total_tables += cls._safe_int(result.trace.get("pdf_parser_table_blocks")) or 0
            total_formulas += cls._safe_int(result.trace.get("pdf_parser_formula_blocks")) or 0
            total_latency += float(result.trace.get("pdf_parser_latency_ms") or 0.0)
            cli_json_name = str(result.trace.get("pdf_parser_cli_json") or "").strip()
            cli_markdown_name = str(result.trace.get("pdf_parser_cli_markdown") or "").strip()
            if cli_json_name:
                cli_json_names.append(cli_json_name)
            if cli_markdown_name:
                cli_markdown_names.append(cli_markdown_name)

        ordered_blocks = (
            cls._sort_blocks_reading_order(merged_blocks)
            if settings.CLINICAL_CHAT_PDF_LAYOUT_READING_ORDER_ENABLED
            else merged_blocks
        )
        if settings.CLINICAL_CHAT_PDF_FILTER_REPEATED_EDGE_TEXT_ENABLED:
            cleaned_blocks, filtered_count = cls._drop_repeated_page_artifacts(ordered_blocks)
        else:
            cleaned_blocks, filtered_count = ordered_blocks, 0

        text = cls._compose_text_from_blocks(cleaned_blocks)
        if not text:
            raise RuntimeError("MinerU CLI windowed no devolvio texto util.")

        trace = {
            "pdf_parser_backend": "mineru",
            "pdf_parser_transport": "cli",
            "pdf_parser_pages_total": str(page_count),
            "pdf_parser_blocks_total": str(total_blocks or len(ordered_blocks)),
            "pdf_parser_blocks_filtered": str(total_filtered + filtered_count),
            "pdf_parser_blocks_kept": str(total_kept or len(cleaned_blocks)),
            "pdf_parser_table_blocks": str(total_tables),
            "pdf_parser_formula_blocks": str(total_formulas),
            "pdf_parser_ocr_mode": settings.CLINICAL_CHAT_PDF_OCR_MODE,
            "pdf_parser_latency_ms": str(round(total_latency, 2)),
            "pdf_parser_reading_order_enabled": (
                "1" if settings.CLINICAL_CHAT_PDF_LAYOUT_READING_ORDER_ENABLED else "0"
            ),
            "pdf_parser_filter_repeated_edges_enabled": (
                "1" if settings.CLINICAL_CHAT_PDF_FILTER_REPEATED_EDGE_TEXT_ENABLED else "0"
            ),
            "pdf_parser_cli_command": str(
                settings.CLINICAL_CHAT_PDF_MINERU_CLI_COMMAND
            ).strip(),
            "pdf_parser_windowed": "1",
            "pdf_parser_window_count": str(len(window_ranges)),
            "pdf_parser_window_size_pages": str(window_size),
        }
        if cli_json_names:
            trace["pdf_parser_cli_json"] = ",".join(cli_json_names[:6])
        if cli_markdown_names:
            trace["pdf_parser_cli_markdown"] = ",".join(cli_markdown_names[:6])
        if settings.CLINICAL_CHAT_PDF_TELEMETRY_ENABLED:
            logger.info(
                (
                    "PDF parseado con MinerU CLI windowed | "
                    "file=%s windows=%s blocks=%s latency_ms=%.2f"
                ),
                file_path,
                len(window_ranges),
                len(cleaned_blocks),
                total_latency,
            )
        return PDFParseResult(text=text.strip(), blocks=cleaned_blocks, trace=trace)

    @classmethod
    def _run_mineru_cli_once(
        cls,
        *,
        file_path: Path,
        output_dir: Path,
        start_page: int | None = None,
        end_page: int | None = None,
    ) -> PDFParseResult:
        command = cls._build_mineru_cli_command(
            file_path=file_path,
            output_dir=output_dir,
            start_page=start_page,
            end_page=end_page,
        )
        started_at = time.perf_counter()
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=max(10, int(settings.CLINICAL_CHAT_PDF_MINERU_TIMEOUT_SECONDS)),
                check=False,
                env=cls._build_mineru_cli_env(),
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("MinerU CLI excedio el timeout configurado.") from exc
        latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
        if completed.returncode != 0:
            stderr = (completed.stderr or completed.stdout or "").strip()
            stderr = stderr[:300] if stderr else "sin detalle"
            raise RuntimeError(f"MinerU CLI fallo ({completed.returncode}): {stderr}")

        cli_payload, cli_json_path = cls._load_best_mineru_cli_json(output_dir)
        markdown_text, cli_markdown_path = cls._load_best_mineru_cli_markdown(
            output_dir,
            cli_payload,
        )
        raw_blocks = cls._extract_raw_blocks(cli_payload) if cli_payload else []
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

        markdown_blocks = cls._markdown_to_blocks(markdown_text) if markdown_text else []
        effective_blocks = cleaned_blocks or markdown_blocks
        text = cls._compose_text_from_blocks(effective_blocks)
        if not text and cli_payload:
            text = cls._extract_text_fallback(cli_payload)
        if not text and markdown_text:
            text = markdown_text.strip()
        if not text:
            raise RuntimeError("MinerU CLI no devolvio texto util.")

        table_blocks = sum(1 for block in effective_blocks if block.get("type") == "table")
        formula_blocks = sum(1 for block in effective_blocks if block.get("type") == "formula")
        pages_total = (
            cls._infer_pages_total(cli_payload, effective_blocks)
            if cli_payload
            else len(
                {
                    int(block.get("page"))
                    for block in effective_blocks
                    if isinstance(block.get("page"), int)
                }
            )
        )
        trace = {
            "pdf_parser_backend": "mineru",
            "pdf_parser_transport": "cli",
            "pdf_parser_pages_total": str(pages_total),
            "pdf_parser_blocks_total": str(len(ordered_blocks) or len(markdown_blocks)),
            "pdf_parser_blocks_filtered": str(filtered_count),
            "pdf_parser_blocks_kept": str(len(effective_blocks)),
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
            "pdf_parser_cli_command": str(
                settings.CLINICAL_CHAT_PDF_MINERU_CLI_COMMAND
            ).strip(),
            "pdf_parser_windowed": "0",
        }
        if cli_json_path is not None:
            trace["pdf_parser_cli_json"] = cli_json_path.name
        if cli_markdown_path is not None:
            trace["pdf_parser_cli_markdown"] = cli_markdown_path.name
        return PDFParseResult(text=text.strip(), blocks=effective_blocks, trace=trace)

    @classmethod
    def _parse_with_mineru_http(cls, file_path: Path) -> PDFParseResult:
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
            "pdf_parser_transport": "http",
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
                "PDF parseado con MinerU HTTP | file=%s blocks=%s filtered=%s latency_ms=%.2f",
                file_path,
                len(cleaned_blocks),
                filtered_count,
                latency_ms,
            )
        return PDFParseResult(text=text.strip(), blocks=cleaned_blocks, trace=trace)

    @classmethod
    def _build_mineru_cli_command(
        cls,
        *,
        file_path: Path,
        output_dir: Path,
        start_page: int | None = None,
        end_page: int | None = None,
    ) -> list[str]:
        command_text = str(settings.CLINICAL_CHAT_PDF_MINERU_CLI_COMMAND or "").strip()
        if not command_text:
            raise RuntimeError("CLINICAL_CHAT_PDF_MINERU_CLI_COMMAND vacio.")
        command = shlex.split(command_text, posix=False)
        if not command:
            raise RuntimeError("CLINICAL_CHAT_PDF_MINERU_CLI_COMMAND invalido.")
        executable = cls._resolve_mineru_cli_executable(command[0])
        if not executable:
            raise RuntimeError(f"MinerU CLI no disponible: {command[0]}")
        command[0] = executable
        mineru_method = str(settings.CLINICAL_CHAT_PDF_MINERU_CLI_METHOD or "txt").strip()
        built = [
            *command,
            "-p",
            str(file_path),
            "-o",
            str(output_dir),
            "-m",
            mineru_method,
            "-b",
            str(settings.CLINICAL_CHAT_PDF_MINERU_CLI_BACKEND).strip(),
            "-d",
            str(settings.CLINICAL_CHAT_PDF_MINERU_DEVICE).strip(),
            "-f",
            "true" if settings.CLINICAL_CHAT_PDF_MINERU_PARSE_FORMULAS else "false",
            "-t",
            "true" if settings.CLINICAL_CHAT_PDF_MINERU_PARSE_TABLES else "false",
        ]
        if start_page is not None:
            built.extend(["-s", str(max(0, int(start_page)))])
        if end_page is not None:
            built.extend(["-e", str(max(0, int(end_page)))])
        return built

    @staticmethod
    def _build_mineru_cli_env() -> dict[str, str]:
        env = dict(os.environ)
        render_timeout = max(0, int(settings.CLINICAL_CHAT_PDF_MINERU_RENDER_TIMEOUT_SECONDS))
        intra_threads = max(0, int(settings.CLINICAL_CHAT_PDF_MINERU_CPU_INTRA_OP_THREADS))
        inter_threads = max(0, int(settings.CLINICAL_CHAT_PDF_MINERU_CPU_INTER_OP_THREADS))
        if render_timeout > 0:
            env["MINERU_PDF_RENDER_TIMEOUT"] = str(render_timeout)
        if intra_threads > 0:
            env["MINERU_INTRA_OP_NUM_THREADS"] = str(intra_threads)
        if inter_threads > 0:
            env["MINERU_INTER_OP_NUM_THREADS"] = str(inter_threads)
        return env

    @classmethod
    def _should_window_mineru_cli(cls, page_count: int) -> bool:
        if not settings.CLINICAL_CHAT_PDF_MINERU_WINDOWED_ENABLED:
            return False
        threshold = max(4, int(settings.CLINICAL_CHAT_PDF_MINERU_WINDOW_THRESHOLD_PAGES))
        window_size = max(2, int(settings.CLINICAL_CHAT_PDF_MINERU_WINDOW_SIZE_PAGES))
        return page_count >= threshold and window_size < page_count

    @staticmethod
    def _get_pdf_page_count(file_path: Path) -> int:
        try:
            from pypdf import PdfReader
        except Exception:
            return 0
        try:
            reader = PdfReader(str(file_path))
            return max(0, len(reader.pages))
        except Exception:
            return 0

    @classmethod
    def _shift_blocks_to_window_offset(
        cls,
        blocks: list[dict[str, Any]],
        *,
        page_offset: int,
    ) -> list[dict[str, Any]]:
        if page_offset <= 0:
            return [dict(block) for block in blocks]
        shifted: list[dict[str, Any]] = []
        for block in blocks:
            block_copy = dict(block)
            page_value = cls._safe_int(block_copy.get("page")) or 1
            new_page = page_value + page_offset
            block_copy["page"] = new_page
            section_path = str(block_copy.get("section_path") or "").strip()
            if re.fullmatch(r"Documento > Pagina \d+", section_path):
                block_copy["section_path"] = f"Documento > Pagina {new_page}"
            shifted.append(block_copy)
        return shifted

    @staticmethod
    def _command_exists(command: str) -> bool:
        candidate = Path(command)
        if candidate.exists():
            return True
        python_scripts = Path(sys.executable).resolve().parent
        sibling_candidates = [python_scripts / command]
        if not Path(command).suffix:
            sibling_candidates.append(python_scripts / f"{command}.exe")
        for sibling in sibling_candidates:
            if sibling.exists():
                return True
        return shutil.which(command) is not None

    @classmethod
    def _resolve_mineru_cli_executable(cls, requested_command: str) -> str | None:
        candidates = [requested_command]
        normalized = requested_command.strip().lower()
        if normalized == "mineru":
            candidates.append("magic-pdf")
        elif normalized == "magic-pdf":
            candidates.append("mineru")
        for candidate in candidates:
            if cls._command_exists(candidate):
                python_scripts = Path(sys.executable).resolve().parent
                sibling = python_scripts / candidate
                sibling_exe = python_scripts / f"{candidate}.exe"
                if sibling.exists():
                    return str(sibling)
                if sibling_exe.exists():
                    return str(sibling_exe)
                return candidate
        return None

    @classmethod
    def _load_best_mineru_cli_markdown(
        cls,
        output_dir: Path,
        cli_payload: dict[str, Any] | None,
    ) -> tuple[str, Path | None]:
        if cli_payload:
            inline_markdown = str(
                cli_payload.get("md_content")
                or cli_payload.get("markdown")
                or cli_payload.get("text")
                or ""
            ).strip()
            if inline_markdown:
                return inline_markdown, None
        candidates = [path for path in output_dir.rglob("*.md") if path.is_file()]
        best = cls._pick_best_cli_artifact(candidates, preferred_tokens=("content", "middle"))
        if best is None:
            return "", None
        return best.read_text(encoding="utf-8", errors="ignore").strip(), best

    @classmethod
    def _load_best_mineru_cli_json(
        cls,
        output_dir: Path,
    ) -> tuple[dict[str, Any] | None, Path | None]:
        candidates = [path for path in output_dir.rglob("*.json") if path.is_file()]
        best = cls._pick_best_cli_artifact(
            candidates,
            preferred_tokens=("middle", "content", "layout", "blocks"),
        )
        if best is None:
            return None, None
        raw = best.read_text(encoding="utf-8", errors="ignore").strip()
        if not raw:
            return None, best
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return None, best
        if isinstance(payload, dict):
            return payload, best
        if isinstance(payload, list):
            return {"blocks": payload}, best
        return None, best

    @staticmethod
    def _pick_best_cli_artifact(
        candidates: list[Path],
        *,
        preferred_tokens: tuple[str, ...],
    ) -> Path | None:
        if not candidates:
            return None

        def sort_key(path: Path) -> tuple[int, int, int, str]:
            name = path.name.lower()
            preference = 0 if any(token in name for token in preferred_tokens) else 1
            try:
                size = -int(path.stat().st_size)
            except OSError:
                size = 0
            return (preference, len(path.parts), size, name)

        return sorted(candidates, key=sort_key)[0]

    @classmethod
    def _markdown_to_blocks(cls, markdown_text: str) -> list[dict[str, Any]]:
        if not markdown_text.strip():
            return []

        blocks: list[dict[str, Any]] = []
        section_stack: list[str] = []
        buffer: list[str] = []
        current_page = 1

        def current_section_path() -> str:
            if section_stack:
                return "Documento > " + " > ".join(section_stack)
            return f"Documento > Pagina {current_page}"

        def flush_buffer() -> None:
            content = "\n".join(buffer).strip()
            buffer.clear()
            if not content:
                return
            block_type = "table" if cls._looks_like_markdown_table(content) else "text"
            blocks.append(
                {
                    "type": block_type,
                    "content": content,
                    "section_path": current_section_path(),
                    "page": current_page,
                    "order": len(blocks),
                }
            )

        for raw_line in markdown_text.splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()
            page_match = re.match(r"^\[page\s+(\d+)\]$", stripped, flags=re.IGNORECASE)
            if page_match:
                flush_buffer()
                current_page = int(page_match.group(1))
                continue
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
            if heading_match:
                flush_buffer()
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                section_stack[:] = section_stack[: level - 1]
                section_stack.append(title)
                continue
            if not stripped:
                flush_buffer()
                continue
            buffer.append(line)
        flush_buffer()
        return blocks

    @staticmethod
    def _looks_like_markdown_table(content: str) -> bool:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if len(lines) < 2:
            return False
        if not all(line.startswith("|") and line.endswith("|") for line in lines[:2]):
            return False
        return True

    @staticmethod
    def _extract_raw_blocks(data: dict[str, Any]) -> list[dict[str, Any]]:
        for key in ("para_blocks", "blocks", "layout_blocks", "elements"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        pdf_info = data.get("pdf_info")
        if isinstance(pdf_info, list):
            extracted: list[dict[str, Any]] = []
            for page_index, page in enumerate(pdf_info, start=1):
                if not isinstance(page, dict):
                    continue
                page_no = (
                    PDFParserService._safe_int(page.get("page"))
                    or (
                        (PDFParserService._safe_int(page.get("page_idx")) or 0) + 1
                    )
                    or page_index
                )
                page_blocks = page.get("para_blocks") or page.get("blocks") or []
                if isinstance(page_blocks, list):
                    for block in page_blocks:
                        if not isinstance(block, dict):
                            continue
                        block_copy = dict(block)
                        block_copy.setdefault("page", page_no)
                        extracted.append(block_copy)
            return extracted
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
        text = str(
            data.get("md_content")
            or data.get("text")
            or data.get("markdown")
            or data.get("content")
            or ""
        ).strip()
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
        pdf_info = data.get("pdf_info")
        if isinstance(pdf_info, list) and pdf_info:
            return len(pdf_info)
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
