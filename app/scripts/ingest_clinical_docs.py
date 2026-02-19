"""
Script para ingerir documentos markdown/txt en tablas RAG.
"""
from __future__ import annotations

import argparse
from array import array
from pathlib import Path

from app.core.database import SessionLocal
from app.models.clinical_document import ClinicalDocument
from app.models.document_chunk import DocumentChunk
from app.services.document_ingestion_service import DocumentIngestionPipeline
from app.services.embedding_service import OllamaEmbeddingService


def _parse_specialty_map(raw_items: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in raw_items:
        if "=" not in item:
            continue
        path_key, specialty = item.split("=", maxsplit=1)
        key = path_key.strip()
        value = specialty.strip()
        if key and value:
            parsed[key] = value
    return parsed


def run_ingestion(paths: list[str], specialty_map: dict[str, str]) -> dict[str, int]:
    pipeline = DocumentIngestionPipeline()
    result = pipeline.run(paths=paths, specialty_map=specialty_map)
    documents = result["documents"]
    embedding_service = OllamaEmbeddingService()

    stats = {
        "documents_saved": 0,
        "documents_skipped": 0,
        "chunks_saved": 0,
    }
    db = SessionLocal()
    try:
        for file_path, payload in documents.items():
            content_hash, chunks = payload
            existing = (
                db.query(ClinicalDocument)
                .filter(ClinicalDocument.content_hash == content_hash)
                .one_or_none()
            )
            if existing:
                stats["documents_skipped"] += 1
                continue

            title = chunks[0].document_title if chunks else Path(file_path).stem
            specialty = chunks[0].specialty if chunks else None
            document = ClinicalDocument(
                title=title,
                source_file=file_path,
                specialty=specialty,
                content_hash=content_hash,
            )
            db.add(document)
            db.flush()

            for chunk in chunks:
                embedding, _trace = embedding_service.embed_text(chunk.text)
                embedding_bytes = array("f", embedding).tobytes()
                db_chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_text=chunk.text,
                    chunk_index=chunk.chunk_index,
                    section_path=chunk.section_path,
                    tokens_count=chunk.token_count,
                    chunk_embedding=embedding_bytes,
                    keywords=chunk.keywords,
                    custom_questions=chunk.custom_questions,
                    specialty=chunk.specialty,
                    content_type=chunk.content_type.value,
                )
                db.add(db_chunk)
                stats["chunks_saved"] += 1

            stats["documents_saved"] += 1

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingesta documentos clinicos en RAG DB")
    parser.add_argument(
        "--paths",
        nargs="+",
        default=["docs", "agents/shared"],
        help="Rutas de archivos/directorios a ingerir",
    )
    parser.add_argument(
        "--specialty-map",
        action="append",
        default=[],
        help="Mapeo path=specialty (ej: docs/49_=cardiology)",
    )
    args = parser.parse_args()

    specialty_map = _parse_specialty_map(args.specialty_map)
    stats = run_ingestion(args.paths, specialty_map)
    print(
        "Ingesta completada | "
        f"documents_saved={stats['documents_saved']} "
        f"documents_skipped={stats['documents_skipped']} "
        f"chunks_saved={stats['chunks_saved']}"
    )


if __name__ == "__main__":
    main()
