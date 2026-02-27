from app.scripts.ingest_clinical_docs import (
    QualityGateProfile,
    _evaluate_document_quality,
    _infer_specialty_from_filename,
    _is_placeholder_custom_questions,
    _resolve_specialty_for_path,
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
