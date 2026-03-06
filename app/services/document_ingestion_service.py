"""
Servicio de ingesta de documentos clinicos con deduplicacion y versionado.

Carga documentos desde markdown/txt/pdf, los procesa con chunking semantico y
los prepara para ser almacenados en BD e indexados con embeddings.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.chunking import DocumentChunk, SemanticChunker, load_or_estimate_token_counter
from app.services.pdf_parser_service import PDFParseResult, PDFParserService

logger = logging.getLogger(__name__)


@dataclass
class IngestSourcePayload:
    """Carga parseada para ingesta (texto + bloques + trazas)."""

    text: str
    parsed_blocks: list[dict]
    parse_trace: dict[str, str]


class DocumentIngestionService:
    """Servicio de ingesta de documentos clinicos."""

    def __init__(self, token_counter=None):
        token_counter = token_counter or load_or_estimate_token_counter()
        self.chunker = SemanticChunker(token_counter=token_counter)
        self._document_hashes: set[str] = set()
        self._parse_trace_by_source: dict[str, dict[str, str]] = {}

    @staticmethod
    def _normalize_path(value: str | Path) -> str:
        return str(value).replace("\\", "/").lower()

    @staticmethod
    def _normalize_source_file(value: str | Path) -> str:
        return str(value).replace("\\", "/")

    @staticmethod
    def _extract_pdf_text(file_path: Path) -> str:
        """Compatibilidad: retorna solo texto PDF."""
        return PDFParserService.extract_text(file_path)

    @staticmethod
    def _parse_pdf(file_path: Path) -> PDFParseResult:
        return PDFParserService.parse(file_path)

    @classmethod
    def _read_supported_file(cls, file_path: Path) -> IngestSourcePayload:
        suffix = file_path.suffix.lower()
        if suffix in {".md", ".txt"}:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return IngestSourcePayload(
                text=content,
                parsed_blocks=[],
                parse_trace={
                    "pdf_parser_backend": "none",
                    "pdf_parser_blocks_total": "0",
                    "pdf_parser_blocks_kept": "0",
                },
            )

        if suffix == ".pdf":
            parsed_pdf = cls._parse_pdf(file_path)
            return IngestSourcePayload(
                text=parsed_pdf.text,
                parsed_blocks=parsed_pdf.blocks,
                parse_trace=parsed_pdf.trace,
            )

        raise ValueError(f"Extension no soportada para ingesta: {file_path.suffix}")

    def ingest_from_file(
        self,
        file_path: str | Path,
        title: Optional[str] = None,
        specialty: Optional[str] = None,
    ) -> tuple[str, list[DocumentChunk]]:
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        source_payload = self._read_supported_file(file_path)
        content = source_payload.text
        if not content.strip():
            raise ValueError(f"Archivo vacio: {file_path}")

        title = title or file_path.stem.replace("_", " ").title()
        if file_path.is_absolute():
            try:
                source_file = self._normalize_source_file(file_path.relative_to(Path.cwd()))
            except ValueError:
                source_file = self._normalize_source_file(file_path)
        else:
            source_file = self._normalize_source_file(file_path)

        # Guarda trazas de parse para telemetria de pipeline.
        trace_copy = dict(source_payload.parse_trace)
        self._parse_trace_by_source[source_file] = trace_copy
        self._parse_trace_by_source[str(file_path)] = trace_copy

        content_hash = hashlib.sha256(content.encode()).hexdigest()
        if content_hash in self._document_hashes:
            logger.warning("Documento duplicado (hash mismatch): %s", file_path)
            return content_hash, []

        self._document_hashes.add(content_hash)

        chunks = self.chunker.chunk(
            content=content,
            title=title,
            specialty=specialty,
            source_file=source_file,
            parsed_blocks=source_payload.parsed_blocks,
        )

        logger.info("Ingestado: %s -> %s chunks", file_path, len(chunks))
        return content_hash, chunks

    def ingest_from_directory(
        self,
        directory: str | Path,
        recursive: bool = True,
        specialty_map: Optional[dict[str, str]] = None,
    ) -> list[tuple[str, str, list[DocumentChunk]]]:
        directory = Path(directory)
        if not directory.is_dir():
            raise ValueError(f"No es un directorio: {directory}")

        specialty_map = specialty_map or {}
        results = []
        target_extensions = {".md", ".txt", ".pdf"}

        glob_pattern = "**/*" if recursive else "*"
        files = [f for f in directory.glob(glob_pattern) if f.suffix.lower() in target_extensions]

        logger.info("Buscando documentos en %s (%s encontrados)", directory, len(files))

        for file_path in sorted(files):
            specialty = None
            normalized_file_path = self._normalize_path(file_path)
            for path_key, spec_value in specialty_map.items():
                normalized_path_key = self._normalize_path(path_key)
                if normalized_path_key and normalized_path_key in normalized_file_path:
                    specialty = spec_value
                    break

            try:
                content_hash, chunks = self.ingest_from_file(
                    file_path=file_path,
                    specialty=specialty,
                )
                results.append((str(file_path), content_hash, chunks))
            except Exception as exc:
                logger.error("Error ingesting %s: %s", file_path, exc)
                continue

        logger.info(
            "Ingesta completa: %s archivos, %s chunks totales",
            len(results),
            sum(len(chunks) for _, _, chunks in results),
        )
        return results

    def ingest_from_memory(
        self,
        content: str,
        title: str = "documento_temporal",
        specialty: Optional[str] = None,
    ) -> tuple[str, list[DocumentChunk]]:
        if not content.strip():
            raise ValueError("Contenido vacio")

        content_hash = hashlib.sha256(content.encode()).hexdigest()
        if content_hash in self._document_hashes:
            logger.warning("Documento duplicado (memoria): %s", title)
            return content_hash, []

        self._document_hashes.add(content_hash)

        chunks = self.chunker.chunk(
            content=content,
            title=title,
            specialty=specialty,
            source_file=None,
        )

        logger.info("Ingestado en memoria: %s -> %s chunks", title, len(chunks))
        return content_hash, chunks

    def get_parse_trace(self, source_file: str | Path) -> dict[str, str]:
        return dict(self._parse_trace_by_source.get(str(source_file), {}))


class DocumentIngestionPipeline:
    """Pipeline de ingesta con estadisticas y reporte."""

    def __init__(self):
        self.service = DocumentIngestionService()
        self.stats = {
            "documents_processed": 0,
            "duplicates_skipped": 0,
            "total_chunks": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None,
            "pdf_parsed_documents": 0,
            "pdf_pages_total": 0,
            "pdf_blocks_total": 0,
            "pdf_blocks_filtered": 0,
            "pdf_parse_latency_ms_sum": 0.0,
        }

    def run(
        self,
        paths: list[str | Path],
        specialty_map: Optional[dict[str, str]] = None,
    ) -> dict:
        self.stats["start_time"] = datetime.now()
        all_results = {}

        for path in paths:
            path_obj = Path(path)

            if path_obj.is_file():
                try:
                    content_hash, chunks = self.service.ingest_from_file(path_obj)
                    if chunks:
                        self.stats["documents_processed"] += 1
                        self.stats["total_chunks"] += len(chunks)
                        all_results[str(path_obj)] = (content_hash, chunks)
                        self._accumulate_parse_trace(path_obj)
                    else:
                        self.stats["duplicates_skipped"] += 1
                except Exception as exc:
                    logger.error("Error procesando %s: %s", path_obj, exc)
                    self.stats["errors"] += 1

            elif path_obj.is_dir():
                results = self.service.ingest_from_directory(path_obj, specialty_map=specialty_map)
                for file_path, content_hash, chunks in results:
                    if chunks:
                        self.stats["documents_processed"] += 1
                        self.stats["total_chunks"] += len(chunks)
                        all_results[file_path] = (content_hash, chunks)
                        self._accumulate_parse_trace(file_path)
                    else:
                        self.stats["duplicates_skipped"] += 1

        self.stats["end_time"] = datetime.now()
        return {
            "stats": self.stats,
            "documents": all_results,
        }

    def get_summary(self) -> str:
        elapsed = (
            (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
            if self.stats["end_time"]
            else 0
        )
        return (
            f"Ingesta completada:\n"
            f"  - Documentos procesados: {self.stats['documents_processed']}\n"
            f"  - Duplicados: {self.stats['duplicates_skipped']}\n"
            f"  - Chunks totales: {self.stats['total_chunks']}\n"
            f"  - Errores: {self.stats['errors']}\n"
            f"  - PDFs parseados: {self.stats['pdf_parsed_documents']}\n"
            f"  - PDF paginas: {self.stats['pdf_pages_total']}\n"
            f"  - PDF bloques: {self.stats['pdf_blocks_total']}\n"
            f"  - PDF bloques filtrados: {self.stats['pdf_blocks_filtered']}\n"
            f"  - Tiempo: {elapsed:.2f}s"
        )

    def _accumulate_parse_trace(self, source_path: str | Path) -> None:
        trace = self.service.get_parse_trace(source_path)
        if not trace:
            return
        backend = str(trace.get("pdf_parser_backend", "")).strip().lower()
        if backend in {"", "none"}:
            return
        self.stats["pdf_parsed_documents"] += 1
        self.stats["pdf_pages_total"] += int(trace.get("pdf_parser_pages_total", "0") or 0)
        self.stats["pdf_blocks_total"] += int(trace.get("pdf_parser_blocks_total", "0") or 0)
        self.stats["pdf_blocks_filtered"] += int(trace.get("pdf_parser_blocks_filtered", "0") or 0)
        self.stats["pdf_parse_latency_ms_sum"] += float(
            trace.get("pdf_parser_latency_ms", "0") or 0
        )
