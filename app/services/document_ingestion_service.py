"""
Servicio de ingesta de documentos clínicos con deduplicación y versionado.

Carga documentos desde markdown, los procesa con chunking semántico y los
prepara para ser almacenados en BD e indexados con embeddings.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.chunking import DocumentChunk, SemanticChunker, load_or_estimate_token_counter

logger = logging.getLogger(__name__)


class DocumentIngestionService:
    """Servicio de ingesta de documentos clínicos."""

    def __init__(self, token_counter=None):
        """
        Args:
            token_counter: función para contar tokens (por defecto, estimación simple)
        """
        token_counter = token_counter or load_or_estimate_token_counter()
        self.chunker = SemanticChunker(token_counter=token_counter)
        self._document_hashes: set[str] = set()

    def ingest_from_file(
        self,
        file_path: str | Path,
        title: Optional[str] = None,
        specialty: Optional[str] = None,
    ) -> tuple[str, list[DocumentChunk]]:
        """
        Ingesta un documento individual desde archivo markdown.

        Args:
            file_path: ruta al archivo (.md o .txt)
            title: título del documento (se infiere del nombre si no se proporciona)
            specialty: especialidad médica asociada (cardiology, neurology, etc.)

        Returns:
            Tupla (document_hash, chunks)

        Raises:
            FileNotFoundError: si archivo no existe
            ValueError: si archivo está vacío
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            raise ValueError(f"Archivo vacío: {file_path}")

        title = title or file_path.stem.replace("_", " ").title()
        source_file = str(
            file_path.relative_to(Path.cwd()) if file_path.is_absolute() else file_path
        )

        # Calcular hash del contenido para deduplicación
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        if content_hash in self._document_hashes:
            logger.warning(f"Documento duplicado (hash mismatch): {file_path}")
            return content_hash, []

        self._document_hashes.add(content_hash)

        # Procesar con chunker
        chunks = self.chunker.chunk(
            content=content,
            title=title,
            specialty=specialty,
            source_file=source_file,
        )

        logger.info(f"Ingestado: {file_path} → {len(chunks)} chunks")
        return content_hash, chunks

    def ingest_from_directory(
        self,
        directory: str | Path,
        recursive: bool = True,
        specialty_map: Optional[dict[str, str]] = None,
    ) -> list[tuple[str, str, list[DocumentChunk]]]:
        """
        Ingesta múltiples documentos desde directorio.

        Args:
            directory: ruta al directorio
            recursive: si buscar archivos recursivamente
            specialty_map: mapeo de rutas/nombres a especialidades
                ej: {"docs/cardiologia/": "cardiology"}

        Returns:
            Lista de tuplas (file_path, content_hash, chunks)
        """
        directory = Path(directory)
        if not directory.is_dir():
            raise ValueError(f"No es un directorio: {directory}")

        specialty_map = specialty_map or {}
        results = []
        target_extensions = {".md", ".txt"}

        glob_pattern = "**/*" if recursive else "*"
        files = [f for f in directory.glob(glob_pattern) if f.suffix.lower() in target_extensions]

        logger.info(f"Buscando documentos en {directory} ({len(files)} encontrados)")

        for file_path in sorted(files):
            # Inferir especialidad del path si es posible
            specialty = None
            for path_key, spec_value in specialty_map.items():
                if path_key in str(file_path):
                    specialty = spec_value
                    break

            try:
                content_hash, chunks = self.ingest_from_file(
                    file_path=file_path,
                    specialty=specialty,
                )
                results.append((str(file_path), content_hash, chunks))
            except Exception as e:
                logger.error(f"Error ingesting {file_path}: {e}")
                continue

        logger.info(
            f"Ingesta completa: {len(results)} archivos, "
            f"{sum(len(chunks) for _, _, chunks in results)} chunks totales"
        )
        return results

    def ingest_from_memory(
        self,
        content: str,
        title: str = "documento_temporal",
        specialty: Optional[str] = None,
    ) -> tuple[str, list[DocumentChunk]]:
        """
        Ingesta desde contenido en memoria (sin archivo).

        Args:
            content: texto del documento
            title: título del documento
            specialty: especialidad médica

        Returns:
            Tupla (content_hash, chunks)
        """
        if not content.strip():
            raise ValueError("Contenido vacío")

        content_hash = hashlib.sha256(content.encode()).hexdigest()

        if content_hash in self._document_hashes:
            logger.warning(f"Documento duplicado (memoria): {title}")
            return content_hash, []

        self._document_hashes.add(content_hash)

        chunks = self.chunker.chunk(
            content=content,
            title=title,
            specialty=specialty,
            source_file=None,
        )

        logger.info(f"Ingestado en memoria: {title} → {len(chunks)} chunks")
        return content_hash, chunks


class DocumentIngestionPipeline:
    """Pipeline de ingesta con estadísticas y reporte."""

    def __init__(self):
        self.service = DocumentIngestionService()
        self.stats = {
            "documents_processed": 0,
            "duplicates_skipped": 0,
            "total_chunks": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None,
        }

    def run(
        self,
        paths: list[str | Path],
        specialty_map: Optional[dict[str, str]] = None,
    ) -> dict:
        """
        Ejecuta pipeline de ingesta sobre múltiples rutas.

        Args:
            paths: lista de rutas (archivos o directorios)
            specialty_map: mapeo de paths a especialidades

        Returns:
            Dict con estadísticas y chunks por documento
        """
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
                    else:
                        self.stats["duplicates_skipped"] += 1
                except Exception as e:
                    logger.error(f"Error procesando {path_obj}: {e}")
                    self.stats["errors"] += 1

            elif path_obj.is_dir():
                results = self.service.ingest_from_directory(path_obj, specialty_map=specialty_map)
                for file_path, content_hash, chunks in results:
                    if chunks:
                        self.stats["documents_processed"] += 1
                        self.stats["total_chunks"] += len(chunks)
                        all_results[file_path] = (content_hash, chunks)
                    else:
                        self.stats["duplicates_skipped"] += 1

        self.stats["end_time"] = datetime.now()
        return {
            "stats": self.stats,
            "documents": all_results,
        }

    def get_summary(self) -> str:
        """Retorna resumen de estadísticas."""
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
            f"  - Tiempo: {elapsed:.2f}s"
        )
