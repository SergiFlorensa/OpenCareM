from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.clinical_document import ClinicalDocument
from app.models.document_chunk import DocumentChunk
from app.scripts.ingest_clinical_docs import (
    QualityGateProfile,
    _evaluate_document_quality,
    _infer_specialty_from_filename,
    _is_placeholder_custom_questions,
    _purge_existing_documents_for_sources,
    _resolve_source_file_for_db,
    _resolve_specialty_for_path,
    normalize_source_paths_in_db,
)


def test_resolve_specialty_from_default_path_mapping():
    specialty = _resolve_specialty_for_path(
        "docs/73_motor_operativo_nefrologia_urgencias.md",
        {"docs/73_": "nephrology"},
    )
    assert specialty == "nephrology"


def test_resolve_specialty_from_filename_hint_when_no_path_mapping():
    specialty = _resolve_specialty_for_path(
        "docs/guia_neonatologia_urgencias_2026.pdf",
        {},
    )
    assert specialty == "pediatrics_neonatology"


def test_infer_specialty_from_filename_returns_none_for_ambiguous_file():
    specialty = _infer_specialty_from_filename("docs/manual_operativo_general.pdf")
    assert specialty is None


def test_placeholder_custom_questions_detection():
    assert _is_placeholder_custom_questions(["\u00bfQu\u00e9 dice este fragmento?"]) is True
    assert _is_placeholder_custom_questions(["\u00bfQue dice este fragmento?"]) is True
    assert _is_placeholder_custom_questions(
        ["\u00bfCuales son los pasos iniciales para sepsis?"]
    ) is False


def test_quality_gate_rejects_low_signal_pdf():
    chunks = [
        type("Chunk", (), {"text": "abc", "chunk_index": 0})(),
    ]
    accepted, metrics, reasons = _evaluate_document_quality(
        file_path="docs/pdf_raw/critical_ops/scan.pdf",
        chunks=chunks,
        parse_trace={
            "pdf_parser_pages_total": "5",
            "pdf_parser_blocks_kept": "1",
        },
        profile=QualityGateProfile(),
    )
    assert accepted is False
    assert metrics["pdf_pages_total"] == 5.0
    assert "pdf_min_chars_per_page" in reasons
    assert "pdf_min_blocks_per_page" in reasons


def test_quality_gate_accepts_dense_text_document():
    chunks = [
        type("Chunk", (), {"text": "A" * 220, "chunk_index": 0})(),
        type("Chunk", (), {"text": "B" * 160, "chunk_index": 1})(),
    ]
    accepted, _metrics, reasons = _evaluate_document_quality(
        file_path="docs/47_motor_sepsis_urgencias.md",
        chunks=chunks,
        parse_trace={
            "pdf_parser_pages_total": "0",
            "pdf_parser_blocks_kept": "0",
        },
        profile=QualityGateProfile(),
    )
    assert accepted is True
    assert reasons == []


def test_purge_existing_documents_for_sources_removes_prior_version(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr("app.scripts.ingest_clinical_docs.SessionLocal", TestingSessionLocal)

    db = TestingSessionLocal()
    try:
        document = ClinicalDocument(
            title="Guia previa",
            source_file="docs/pdf_raw/ophthalmology/guia.pdf",
            specialty="ophthalmology",
            content_hash="a" * 64,
        )
        db.add(document)
        db.flush()
        db.add(
            DocumentChunk(
                document_id=document.id,
                chunk_text="contenido viejo",
                chunk_index=0,
                section_path="Documento > Inicio",
                tokens_count=10,
                chunk_embedding=b"1234",
                keywords=[],
                custom_questions=[],
                specialty="ophthalmology",
                content_type="paragraph",
            )
        )
        db.commit()
    finally:
        db.close()

    stats = _purge_existing_documents_for_sources(["docs/pdf_raw/ophthalmology/guia.pdf"])

    db = TestingSessionLocal()
    try:
        assert stats["documents_deleted"] == 1
        assert stats["chunks_deleted"] == 1
        assert db.query(ClinicalDocument).count() == 0
        assert db.query(DocumentChunk).count() == 0
    finally:
        db.close()


def test_resolve_source_file_for_db_normalizes_windows_separators():
    result = _resolve_source_file_for_db(
        Path(r"docs\pdf_raw\emergencies\12_Sepsis_4ed.pdf")
    )
    assert result == "docs/pdf_raw/emergencies/12_Sepsis_4ed.pdf"


def test_normalize_source_paths_in_db_rewrites_backslashes(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr("app.scripts.ingest_clinical_docs.SessionLocal", TestingSessionLocal)

    db = TestingSessionLocal()
    try:
        db.add(
            ClinicalDocument(
                title="Sepsis",
                source_file=r"docs\pdf_raw\emergencies\12_Sepsis_4ed.pdf",
                specialty="critical_ops",
                content_hash="b" * 64,
            )
        )
        db.commit()
    finally:
        db.close()

    stats = normalize_source_paths_in_db()

    db = TestingSessionLocal()
    try:
        document = db.query(ClinicalDocument).one()
        assert stats["documents_updated"] == 1
        assert document.source_file == "docs/pdf_raw/emergencies/12_Sepsis_4ed.pdf"
    finally:
        db.close()
