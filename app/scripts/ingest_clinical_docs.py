"""
Script para ingerir documentos markdown/txt/pdf en tablas RAG.
"""
from __future__ import annotations

import argparse
import re
import sys
import time
import unicodedata
from array import array
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.exc import OperationalError

from app.core.chunking import DocumentParser
from app.core.database import SessionLocal
from app.models.clinical_document import ClinicalDocument
from app.models.document_chunk import DocumentChunk
from app.services.document_ingestion_service import DocumentIngestionPipeline
from app.services.embedding_service import OllamaEmbeddingService

DEFAULT_SPECIALTY_MAP: dict[str, str] = {
    "docs/40_": "pneumology",
    "docs/41_": "pediatrics_neonatology",
    "docs/42_": "critical_ops",
    "docs/43_": "critical_ops",
    "docs/44_": "pneumology",
    "docs/45_": "medicolegal",
    "docs/46_": "medicolegal",
    "docs/47_": "sepsis",
    "docs/48_": "critical_ops",
    "docs/49_": "scasest",
    "docs/50_": "scasest",
    "docs/51_": "scasest",
    "docs/52_": "scasest",
    "docs/53_": "critical_ops",
    "docs/54_": "critical_ops",
    "docs/55_": "critical_ops",
    "docs/56_": "critical_ops",
    "docs/57_": "scasest",
    "docs/58_": "resuscitation",
    "docs/59_": "resuscitation",
    "docs/60_": "resuscitation",
    "docs/61_": "resuscitation",
    "docs/62_": "medicolegal",
    "docs/63_": "dermatology",
    "docs/64_": "dermatology",
    "docs/65_": "trauma",
    "docs/66_": "critical_ops",
    "docs/67_": "neurology",
    "docs/68_": "gastro_hepato",
    "docs/69_": "rheum_immuno",
    "docs/70_": "psychiatry",
    "docs/71_": "hematology",
    "docs/72_": "endocrinology",
    "docs/73_": "nephrology",
    "docs/74_": "pneumology",
    "docs/75_": "geriatrics",
    "docs/76_": "oncology",
    "docs/77_": "anesthesiology",
    "docs/78_": "palliative",
    "docs/79_": "urology",
    "docs/80_": "anisakis",
    "docs/81_": "epidemiology",
    "docs/82_": "ophthalmology",
    "docs/83_": "immunology",
    "docs/84_": "genetic_recurrence",
    "docs/85_": "gynecology_obstetrics",
    "docs/86_": "pediatrics_neonatology",
    # Corpus PDF crudo organizado por especialidad.
    "docs/pdf_raw/critical_ops/": "critical_ops",
    "docs/pdf_raw/sepsis/": "sepsis",
    "docs/pdf_raw/scasest/": "scasest",
    "docs/pdf_raw/cardiology/": "scasest",
    "docs/pdf_raw/resuscitation/": "resuscitation",
    "docs/pdf_raw/medicolegal/": "medicolegal",
    "docs/pdf_raw/trauma/": "trauma",
    "docs/pdf_raw/neurology/": "neurology",
    "docs/pdf_raw/gastro_hepato/": "gastro_hepato",
    "docs/pdf_raw/rheum_immuno/": "rheum_immuno",
    "docs/pdf_raw/psychiatry/": "psychiatry",
    "docs/pdf_raw/hematology/": "hematology",
    "docs/pdf_raw/endocrinology/": "endocrinology",
    "docs/pdf_raw/nephrology/": "nephrology",
    "docs/pdf_raw/pneumology/": "pneumology",
    "docs/pdf_raw/geriatrics/": "geriatrics",
    "docs/pdf_raw/oncology/": "oncology",
    "docs/pdf_raw/dermatology/": "dermatology",
    "docs/pdf_raw/anesthesiology/": "anesthesiology",
    "docs/pdf_raw/palliative/": "palliative",
    "docs/pdf_raw/palliative_care/": "palliative_care",
    "docs/pdf_raw/urology/": "urology",
    "docs/pdf_raw/anisakis/": "anisakis",
    "docs/pdf_raw/infectious_disease/": "infectious_disease",
    "docs/pdf_raw/epidemiology/": "epidemiology",
    "docs/pdf_raw/ophthalmology/": "ophthalmology",
    "docs/pdf_raw/immunology/": "immunology",
    "docs/pdf_raw/genetic_recurrence/": "genetic_recurrence",
    "docs/pdf_raw/genetics/": "genetics",
    "docs/pdf_raw/gynecology_obstetrics/": "gynecology_obstetrics",
    "docs/pdf_raw/pediatrics_neonatology/": "pediatrics_neonatology",
    "docs/pdf_raw/emergencies/": "critical_ops",
    "docs/pdf_raw/odontology/": "oncology",
    "docs/pdf_raw/primary_care/": "endocrinology",
}

FILENAME_SPECIALTY_HINTS: tuple[tuple[str, str], ...] = (
    ("sepsis", "sepsis"),
    ("scasest", "scasest"),
    ("coronari", "scasest"),
    ("troponina", "scasest"),
    ("reanimacion", "resuscitation"),
    ("soporte_vital", "resuscitation"),
    ("medico_legal", "medicolegal"),
    ("bioetica", "medicolegal"),
    ("neurolog", "neurology"),
    ("gastro", "gastro_hepato"),
    ("hepato", "gastro_hepato"),
    ("reuma", "rheum_immuno"),
    ("inmuno", "immunology"),
    ("psiquiatr", "psychiatry"),
    ("hematolog", "hematology"),
    ("endocrin", "endocrinology"),
    ("nefrolog", "nephrology"),
    ("neumolog", "pneumology"),
    ("geriatr", "geriatrics"),
    ("oncolog", "oncology"),
    ("anestesi", "anesthesiology"),
    ("paliativ", "palliative"),
    ("urolog", "urology"),
    ("oftalmolog", "ophthalmology"),
    ("genetic", "genetic_recurrence"),
    ("genet", "genetic_recurrence"),
    ("ginecolog", "gynecology_obstetrics"),
    ("obstetric", "gynecology_obstetrics"),
    ("pediatri", "pediatrics_neonatology"),
    ("neonat", "pediatrics_neonatology"),
    ("epidemiolog", "epidemiology"),
    ("anisak", "anisakis"),
    ("trauma", "trauma"),
    ("critico", "critical_ops"),
    ("urgencias", "critical_ops"),
)


@dataclass(frozen=True)
class QualityGateProfile:
    enabled: bool = True
    min_chunks: int = 1
    min_total_chars: int = 180
    min_avg_chunk_chars: int = 48
    pdf_min_chars_per_page: int = 80
    pdf_min_blocks_per_page: float = 0.35


def _safe_console_text(value: str) -> str:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    return str(value).encode(encoding, errors="replace").decode(encoding, errors="replace")


def _normalize_path(value: str | Path) -> str:
    return str(value).replace("\\", "/").lower()


def _resolve_source_file_for_db(file_path: Path) -> str:
    if file_path.is_absolute():
        try:
            return str(file_path.relative_to(Path.cwd()))
        except ValueError:
            return str(file_path)
    return str(file_path)


def _collect_supported_files(paths: list[str]) -> list[Path]:
    supported = {".md", ".txt", ".pdf"}
    discovered: list[Path] = []
    for raw_path in paths:
        path_obj = Path(raw_path)
        if path_obj.is_file():
            if path_obj.suffix.lower() in supported:
                discovered.append(path_obj)
            continue
        if path_obj.is_dir():
            for candidate in path_obj.rglob("*"):
                if candidate.suffix.lower() in supported:
                    discovered.append(candidate)
    dedup = {str(item.resolve()): item for item in discovered}
    return sorted(dedup.values(), key=lambda item: _normalize_path(item))


def _load_existing_source_paths_norm() -> set[str]:
    db = SessionLocal()
    try:
        rows = (
            db.query(ClinicalDocument.source_file)
            .filter(ClinicalDocument.source_file.isnot(None))
            .all()
        )
        return {_normalize_path(row[0]) for row in rows if row and row[0]}
    finally:
        db.close()


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


def _infer_specialty_from_filename(file_path: str) -> str | None:
    normalized = _normalize_path(file_path)
    basename = normalized.rsplit("/", maxsplit=1)[-1]
    basename_plain = re.sub(r"[^a-z0-9_.-]", "", basename)
    for hint, specialty in FILENAME_SPECIALTY_HINTS:
        if hint in basename_plain:
            return specialty
    return None


def _resolve_specialty_for_path(file_path: str, specialty_map: dict[str, str]) -> str | None:
    normalized_file_path = _normalize_path(file_path)
    for path_key, specialty in specialty_map.items():
        normalized_path_key = _normalize_path(path_key)
        if normalized_path_key and normalized_path_key in normalized_file_path:
            return specialty
    return _infer_specialty_from_filename(file_path)


def backfill_specialty_from_source_map(specialty_map: dict[str, str]) -> dict[str, int]:
    db = SessionLocal()
    stats = {
        "documents_backfilled": 0,
        "chunks_backfilled_from_path": 0,
        "chunks_backfilled_from_document": 0,
    }
    try:
        documents = db.query(ClinicalDocument).filter(ClinicalDocument.specialty.is_(None)).all()
        for document in documents:
            inferred_specialty = _resolve_specialty_for_path(document.source_file, specialty_map)
            if not inferred_specialty:
                continue
            document.specialty = inferred_specialty
            affected_chunks = (
                db.query(DocumentChunk)
                .filter(DocumentChunk.document_id == document.id)
                .update(
                    {DocumentChunk.specialty: inferred_specialty},
                    synchronize_session=False,
                )
            )
            stats["documents_backfilled"] += 1
            stats["chunks_backfilled_from_path"] += int(affected_chunks or 0)

        # Sincroniza chunks sin especialidad cuando el documento ya la tiene.
        docs_with_specialty = (
            db.query(ClinicalDocument.id, ClinicalDocument.specialty)
            .filter(ClinicalDocument.specialty.isnot(None))
            .all()
        )
        for document_id, specialty in docs_with_specialty:
            if not specialty:
                continue
            affected_chunks = (
                db.query(DocumentChunk)
                .filter(
                    DocumentChunk.document_id == int(document_id),
                    DocumentChunk.specialty.is_(None),
                )
                .update(
                    {DocumentChunk.specialty: str(specialty)},
                    synchronize_session=False,
                )
            )
            stats["chunks_backfilled_from_document"] += int(affected_chunks or 0)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return stats


def _normalize_placeholder_text(value: str) -> str:
    lowered = str(value or "").lower().strip()
    decomposed = unicodedata.normalize("NFKD", lowered)
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9\s]", "", ascii_text).strip()


def _is_placeholder_custom_questions(values: list[str] | None) -> bool:
    if not values:
        return True
    normalized = [
        _normalize_placeholder_text(str(item or ""))
        for item in values
        if str(item or "").strip()
    ]
    if not normalized:
        return True
    if len(normalized) == 1 and normalized[0] in {
        "que dice este fragmento",
        "qu dice este fragmento",
    }:
        return True
    return False


def _safe_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _evaluate_document_quality(
    *,
    file_path: str,
    chunks: list[Any],
    parse_trace: dict[str, str],
    profile: QualityGateProfile,
) -> tuple[bool, dict[str, float], list[str]]:
    chunk_count = len(chunks)
    total_chars = sum(len(str(chunk.text or "").strip()) for chunk in chunks)
    avg_chunk_chars = (total_chars / max(1, chunk_count)) if chunk_count > 0 else 0.0
    pages_total = max(0, _safe_int(parse_trace.get("pdf_parser_pages_total", "0"), default=0))
    blocks_kept = max(0, _safe_int(parse_trace.get("pdf_parser_blocks_kept", "0"), default=0))

    chars_per_page = (
        float(total_chars) / float(max(1, pages_total))
        if pages_total > 0
        else 0.0
    )
    blocks_per_page = (
        float(blocks_kept) / float(max(1, pages_total))
        if pages_total > 0
        else 0.0
    )
    metrics = {
        "chunk_count": float(chunk_count),
        "total_chars": float(total_chars),
        "avg_chunk_chars": float(round(avg_chunk_chars, 2)),
        "pdf_pages_total": float(pages_total),
        "pdf_blocks_kept": float(blocks_kept),
        "pdf_chars_per_page": float(round(chars_per_page, 2)),
        "pdf_blocks_per_page": float(round(blocks_per_page, 2)),
    }

    if not profile.enabled:
        return True, metrics, []

    reasons: list[str] = []
    if chunk_count < max(1, int(profile.min_chunks)):
        reasons.append("min_chunks")
    if total_chars < max(1, int(profile.min_total_chars)):
        reasons.append("min_total_chars")
    if avg_chunk_chars < float(profile.min_avg_chunk_chars):
        reasons.append("min_avg_chunk_chars")

    is_pdf = str(file_path).lower().endswith(".pdf")
    if is_pdf and pages_total > 0:
        if chars_per_page < float(profile.pdf_min_chars_per_page):
            reasons.append("pdf_min_chars_per_page")
        if blocks_per_page < float(profile.pdf_min_blocks_per_page):
            reasons.append("pdf_min_blocks_per_page")
    return len(reasons) == 0, metrics, reasons


def rebuild_custom_questions_for_existing_chunks(
    *,
    only_placeholder: bool = True,
    limit: int = 0,
) -> dict[str, int]:
    db = SessionLocal()
    parser = DocumentParser()
    stats = {
        "chunks_scanned": 0,
        "chunks_updated": 0,
    }
    try:
        query_builder = db.query(DocumentChunk)
        if limit > 0:
            query_builder = query_builder.limit(limit)
        chunks = query_builder.all()
        for chunk in chunks:
            stats["chunks_scanned"] += 1
            current_questions = (
                list(chunk.custom_questions)
                if isinstance(chunk.custom_questions, list)
                else []
            )
            if only_placeholder and not _is_placeholder_custom_questions(current_questions):
                continue
            rebuilt = parser.generate_hypothetical_questions(
                str(chunk.chunk_text or ""),
                str(chunk.section_path or ""),
            )
            if not rebuilt:
                continue
            chunk.custom_questions = rebuilt[:6]
            stats["chunks_updated"] += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return stats


def run_ingestion(
    paths: list[str],
    specialty_map: dict[str, str],
    *,
    backfill_existing_specialty: bool = False,
    skip_ollama_embeddings: bool = False,
    skip_existing_paths: bool = True,
    quality_profile: QualityGateProfile | None = None,
) -> dict[str, Any]:
    discovered_files = _collect_supported_files(paths)
    existing_source_paths_norm: set[str] = set()
    if skip_existing_paths:
        existing_source_paths_norm = _load_existing_source_paths_norm()

    files_to_ingest: list[str] = []
    files_skipped_existing_path = 0
    for discovered in discovered_files:
        source_file = _resolve_source_file_for_db(discovered)
        source_norm = _normalize_path(source_file)
        if skip_existing_paths and source_norm in existing_source_paths_norm:
            files_skipped_existing_path += 1
            continue
        files_to_ingest.append(str(discovered))

    quality_profile = quality_profile or QualityGateProfile()

    pipeline = DocumentIngestionPipeline()
    result = pipeline.run(paths=files_to_ingest, specialty_map=specialty_map)
    documents = result["documents"]
    pipeline_stats = result.get("stats", {})
    embedding_service = OllamaEmbeddingService()

    stats = {
        "files_discovered": len(discovered_files),
        "files_skipped_existing_path": files_skipped_existing_path,
        "documents_saved": 0,
        "documents_skipped": 0,
        "documents_backfilled_specialty": 0,
        "chunks_saved": 0,
        "documents_retried": 0,
        "documents_rejected_quality": 0,
        "quality_gate_enabled": 1 if quality_profile.enabled else 0,
        "pdf_parsed_documents": int(pipeline_stats.get("pdf_parsed_documents", 0) or 0),
        "pdf_pages_total": int(pipeline_stats.get("pdf_pages_total", 0) or 0),
        "pdf_blocks_total": int(pipeline_stats.get("pdf_blocks_total", 0) or 0),
        "pdf_blocks_filtered": int(pipeline_stats.get("pdf_blocks_filtered", 0) or 0),
        "pdf_parse_latency_ms_sum": float(
            pipeline_stats.get("pdf_parse_latency_ms_sum", 0.0) or 0.0
        ),
    }
    quality_rejection_reason_counts: dict[str, int] = {}
    for file_path, payload in documents.items():
        content_hash, chunks = payload
        parse_trace = pipeline.service.get_parse_trace(file_path)
        accepted, quality_metrics, rejection_reasons = _evaluate_document_quality(
            file_path=file_path,
            chunks=chunks,
            parse_trace=parse_trace,
            profile=quality_profile,
        )
        if not accepted:
            stats["documents_rejected_quality"] += 1
            stats["documents_skipped"] += 1
            reason_label = ",".join(sorted(set(rejection_reasons)))
            for reason in rejection_reasons:
                quality_rejection_reason_counts[reason] = (
                    quality_rejection_reason_counts.get(reason, 0) + 1
                )
            print(
                _safe_console_text(
                    "[quality-gate] rechazado "
                    f"{Path(file_path).name} reasons={reason_label} metrics={quality_metrics}"
                )
            )
            continue

        last_error: OperationalError | None = None
        max_retries = 5
        for attempt in range(max_retries):
            db = SessionLocal()
            try:
                existing = (
                    db.query(ClinicalDocument)
                    .filter(ClinicalDocument.content_hash == content_hash)
                    .one_or_none()
                )
                if existing:
                    inferred_specialty = _resolve_specialty_for_path(file_path, specialty_map)
                    if (
                        backfill_existing_specialty
                        and inferred_specialty
                        and not str(existing.specialty or "").strip()
                    ):
                        existing.specialty = inferred_specialty
                        db.query(DocumentChunk).filter(
                            DocumentChunk.document_id == existing.id
                        ).update(
                            {DocumentChunk.specialty: inferred_specialty},
                            synchronize_session=False,
                        )
                        stats["documents_backfilled_specialty"] += 1
                        db.commit()
                    else:
                        db.rollback()
                    stats["documents_skipped"] += 1
                    break

                title = chunks[0].document_title if chunks else Path(file_path).stem
                specialty = chunks[0].specialty if chunks else None
                if not specialty:
                    specialty = _resolve_specialty_for_path(file_path, specialty_map)
                document = ClinicalDocument(
                    title=title,
                    source_file=file_path,
                    specialty=specialty,
                    content_hash=content_hash,
                )
                db.add(document)
                db.flush()

                chunks_saved_current = 0
                for chunk in chunks:
                    if skip_ollama_embeddings:
                        embedding = embedding_service._fallback_vector(chunk.text)
                    else:
                        embedding, _trace = embedding_service.embed_text(chunk.text)
                    embedding_bytes = array("f", embedding).tobytes()
                    chunk_specialty = chunk.specialty or specialty
                    db_chunk = DocumentChunk(
                        document_id=document.id,
                        chunk_text=chunk.text,
                        chunk_index=chunk.chunk_index,
                        section_path=chunk.section_path,
                        tokens_count=chunk.token_count,
                        chunk_embedding=embedding_bytes,
                        keywords=chunk.keywords,
                        custom_questions=chunk.custom_questions,
                        specialty=chunk_specialty,
                        content_type=chunk.content_type.value,
                    )
                    db.add(db_chunk)
                    chunks_saved_current += 1
                    if chunks_saved_current % 25 == 0:
                        progress_message = (
                            f"[ingest] {Path(file_path).name}: "
                            f"{chunks_saved_current}/{len(chunks)} chunks procesados"
                        )
                        print(_safe_console_text(progress_message))

                db.commit()
                stats["documents_saved"] += 1
                stats["chunks_saved"] += chunks_saved_current
                break
            except OperationalError as exc:
                db.rollback()
                last_error = exc
                if "database is locked" not in str(exc).lower() or attempt >= max_retries - 1:
                    raise
                stats["documents_retried"] += 1
                time.sleep(1.2 * (attempt + 1))
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()
        else:
            if last_error:
                raise last_error

    stats["quality_rejection_reason_counts"] = quality_rejection_reason_counts
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingesta documentos clinicos en RAG DB")
    parser.add_argument(
        "--paths",
        nargs="+",
        default=["docs"],
        help="Rutas de archivos/directorios a ingerir",
    )
    parser.add_argument(
        "--include-shared",
        action="store_true",
        help="Incluye agentes/shared en la ingesta (no recomendado para corpus clinico principal).",
    )
    parser.add_argument(
        "--specialty-map",
        action="append",
        default=[],
        help="Mapeo path=specialty (ej: docs/49_=cardiology)",
    )
    parser.add_argument(
        "--no-default-specialty-map",
        action="store_true",
        help="Desactiva el mapeo clinico por defecto (docs/45-86 -> specialty).",
    )
    parser.add_argument(
        "--backfill-specialty",
        action="store_true",
        help="Rellena specialty en documentos/chunks existentes cuando este vacio.",
    )
    parser.add_argument(
        "--backfill-only",
        action="store_true",
        help="Solo ejecuta backfill de specialty sobre registros existentes, sin nueva ingesta.",
    )
    parser.add_argument(
        "--rebuild-custom-questions",
        action="store_true",
        help=(
            "Reconstruye custom_questions de chunks existentes para mejorar QA shortcut "
            "multi-especialidad."
        ),
    )
    parser.add_argument(
        "--rebuild-custom-questions-all",
        action="store_true",
        help="Reconstruye custom_questions en todos los chunks (no solo placeholders).",
    )
    parser.add_argument(
        "--rebuild-custom-questions-limit",
        type=int,
        default=0,
        help="Limite opcional de chunks a procesar en reconstruccion de custom_questions.",
    )
    parser.add_argument(
        "--skip-ollama-embeddings",
        action="store_true",
        help=(
            "Usa embeddings fallback hash (rapido) sin llamar a Ollama. "
            "Util para ingesta masiva inicial."
        ),
    )
    parser.add_argument(
        "--force-reprocess-existing-paths",
        action="store_true",
        help=(
            "Reprocesa archivos aunque ya exista source_file en BD. "
            "Por defecto se omiten para acelerar ingestas incrementales."
        ),
    )
    parser.add_argument(
        "--disable-quality-gates",
        action="store_true",
        help="Desactiva quality gates de ingesta (no recomendado).",
    )
    parser.add_argument(
        "--quality-min-chunks",
        type=int,
        default=1,
        help="Minimo de chunks requeridos por documento.",
    )
    parser.add_argument(
        "--quality-min-total-chars",
        type=int,
        default=180,
        help="Minimo de caracteres agregados requeridos por documento.",
    )
    parser.add_argument(
        "--quality-min-avg-chunk-chars",
        type=int,
        default=48,
        help="Minimo de longitud media (caracteres) por chunk.",
    )
    parser.add_argument(
        "--quality-pdf-min-chars-per-page",
        type=int,
        default=80,
        help="Minimo de caracteres por pagina para documentos PDF parseados.",
    )
    parser.add_argument(
        "--quality-pdf-min-blocks-per-page",
        type=float,
        default=0.35,
        help="Minimo de bloques kept/page para documentos PDF parseados.",
    )
    args = parser.parse_args()

    specialty_map: dict[str, str] = {}
    if not args.no_default_specialty_map:
        specialty_map.update(DEFAULT_SPECIALTY_MAP)
    specialty_map.update(_parse_specialty_map(args.specialty_map))

    paths = list(args.paths)
    if args.include_shared and "agents/shared" not in paths:
        paths.append("agents/shared")

    backfill_stats = {
        "documents_backfilled": 0,
        "chunks_backfilled_from_path": 0,
        "chunks_backfilled_from_document": 0,
    }
    question_rebuild_stats = {
        "chunks_scanned": 0,
        "chunks_updated": 0,
    }
    if args.backfill_specialty or args.backfill_only:
        backfill_stats = backfill_specialty_from_source_map(specialty_map)
    if args.rebuild_custom_questions:
        question_rebuild_stats = rebuild_custom_questions_for_existing_chunks(
            only_placeholder=not args.rebuild_custom_questions_all,
            limit=max(0, int(args.rebuild_custom_questions_limit or 0)),
        )

    if args.backfill_only:
        print(
            _safe_console_text(
                "Backfill completado | "
                f"documents_backfilled={backfill_stats['documents_backfilled']} "
                f"chunks_backfilled_from_path={backfill_stats['chunks_backfilled_from_path']} "
                "chunks_backfilled_from_document="
                f"{backfill_stats['chunks_backfilled_from_document']} "
                f"chunks_scanned_questions={question_rebuild_stats['chunks_scanned']} "
                f"chunks_updated_questions={question_rebuild_stats['chunks_updated']}"
            )
        )
        return

    quality_profile = QualityGateProfile(
        enabled=not args.disable_quality_gates,
        min_chunks=max(1, int(args.quality_min_chunks)),
        min_total_chars=max(1, int(args.quality_min_total_chars)),
        min_avg_chunk_chars=max(1, int(args.quality_min_avg_chunk_chars)),
        pdf_min_chars_per_page=max(1, int(args.quality_pdf_min_chars_per_page)),
        pdf_min_blocks_per_page=max(0.05, _safe_float(args.quality_pdf_min_blocks_per_page)),
    )

    stats = run_ingestion(
        paths,
        specialty_map,
        backfill_existing_specialty=args.backfill_specialty,
        skip_ollama_embeddings=args.skip_ollama_embeddings,
        skip_existing_paths=not args.force_reprocess_existing_paths,
        quality_profile=quality_profile,
    )
    rejection_reasons = stats.get("quality_rejection_reason_counts", {})
    summary = (
        "Ingesta completada | "
        f"files_discovered={stats['files_discovered']} "
        f"files_skipped_existing_path={stats['files_skipped_existing_path']} "
        f"documents_saved={stats['documents_saved']} "
        f"documents_skipped={stats['documents_skipped']} "
        f"documents_rejected_quality={stats['documents_rejected_quality']} "
        f"quality_gate_enabled={stats['quality_gate_enabled']} "
        f"documents_backfilled_specialty={stats['documents_backfilled_specialty']} "
        f"backfilled_existing_specialty={backfill_stats['documents_backfilled']} "
        f"chunks_backfilled_from_path={backfill_stats['chunks_backfilled_from_path']} "
        "chunks_backfilled_from_document="
        f"{backfill_stats['chunks_backfilled_from_document']} "
        f"chunks_scanned_questions={question_rebuild_stats['chunks_scanned']} "
        f"chunks_updated_questions={question_rebuild_stats['chunks_updated']} "
        f"chunks_saved={stats['chunks_saved']} "
        f"pdf_parsed_documents={stats['pdf_parsed_documents']} "
        f"pdf_pages_total={stats['pdf_pages_total']} "
        f"pdf_blocks_total={stats['pdf_blocks_total']} "
        f"pdf_blocks_filtered={stats['pdf_blocks_filtered']} "
        f"pdf_parse_latency_ms_sum={stats['pdf_parse_latency_ms_sum']:.2f}"
    )
    print(_safe_console_text(summary))
    if rejection_reasons:
        print(_safe_console_text(f"quality_rejection_reason_counts={rejection_reasons}"))


if __name__ == "__main__":
    main()
