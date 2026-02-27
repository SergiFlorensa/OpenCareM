from pathlib import Path

from app.services.document_ingestion_service import DocumentIngestionService
from app.services.pdf_parser_service import PDFParseResult


def test_ingest_pdf_uses_structured_pdf_payload(monkeypatch, tmp_path: Path):
    service = DocumentIngestionService()
    pdf_path = tmp_path / "guia_urgencias.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")

    monkeypatch.setattr(
        DocumentIngestionService,
        "_parse_pdf",
        staticmethod(
            lambda _path: PDFParseResult(
                text="Contenido clinico relevante.",
                blocks=[
                    {
                        "type": "table",
                        "content": "| parametro | valor |",
                        "section_path": "Documento > Tabla",
                    }
                ],
                trace={
                    "pdf_parser_backend": "mineru",
                    "pdf_parser_pages_total": "1",
                    "pdf_parser_blocks_total": "1",
                    "pdf_parser_blocks_filtered": "0",
                },
            )
        ),
    )

    content_hash, chunks = service.ingest_from_file(
        file_path=pdf_path,
        title="Guia urgencias PDF",
        specialty="emergency",
    )

    assert content_hash
    assert len(chunks) >= 1
    assert "parametro" in chunks[0].text
    assert chunks[0].content_type.value in {"table", "paragraph"}


def test_ingestion_service_stores_parse_trace(monkeypatch, tmp_path: Path):
    service = DocumentIngestionService()
    pdf_path = tmp_path / "trace.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")

    monkeypatch.setattr(
        DocumentIngestionService,
        "_parse_pdf",
        staticmethod(
            lambda _path: PDFParseResult(
                text="texto",
                blocks=[],
                trace={"pdf_parser_backend": "mineru", "pdf_parser_latency_ms": "123.4"},
            )
        ),
    )

    service.ingest_from_file(file_path=pdf_path, title="trace", specialty="critical_ops")
    trace = service.get_parse_trace(pdf_path)

    assert trace.get("pdf_parser_backend") == "mineru"
    assert trace.get("pdf_parser_latency_ms") == "123.4"
