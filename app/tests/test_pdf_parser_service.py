from pathlib import Path

import pytest

from app.services.pdf_parser_service import PDFParseResult, PDFParserService


def test_pdf_parser_uses_pypdf_backend(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")

    monkeypatch.setattr(
        "app.services.pdf_parser_service.settings.CLINICAL_CHAT_PDF_PARSER_BACKEND",
        "pypdf",
    )
    monkeypatch.setattr(
        PDFParserService,
        "_parse_with_pypdf",
        staticmethod(
            lambda _path: PDFParseResult(
                text="texto pypdf",
                blocks=[],
                trace={"pdf_parser_backend": "pypdf"},
            )
        ),
    )

    result = PDFParserService.parse(pdf_path)
    assert result.text == "texto pypdf"
    assert result.trace["pdf_parser_backend"] == "pypdf"


def test_pdf_parser_mineru_fail_open_fallbacks_to_pypdf(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")

    monkeypatch.setattr(
        "app.services.pdf_parser_service.settings.CLINICAL_CHAT_PDF_PARSER_BACKEND",
        "mineru",
    )
    monkeypatch.setattr(
        "app.services.pdf_parser_service.settings.CLINICAL_CHAT_PDF_MINERU_FAIL_OPEN",
        True,
    )
    monkeypatch.setattr(
        PDFParserService,
        "_parse_with_mineru",
        classmethod(lambda cls, _path: (_ for _ in ()).throw(RuntimeError("down"))),
    )
    monkeypatch.setattr(
        PDFParserService,
        "_parse_with_pypdf",
        staticmethod(
            lambda _path: PDFParseResult(
                text="fallback pypdf",
                blocks=[],
                trace={"pdf_parser_backend": "pypdf"},
            )
        ),
    )

    result = PDFParserService.parse(pdf_path)
    assert result.text == "fallback pypdf"
    assert result.trace["pdf_parser_fail_open_used"] == "1"


def test_pdf_parser_mineru_fail_closed_raises(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")

    monkeypatch.setattr(
        "app.services.pdf_parser_service.settings.CLINICAL_CHAT_PDF_PARSER_BACKEND",
        "mineru",
    )
    monkeypatch.setattr(
        "app.services.pdf_parser_service.settings.CLINICAL_CHAT_PDF_MINERU_FAIL_OPEN",
        False,
    )
    monkeypatch.setattr(
        PDFParserService,
        "_parse_with_mineru",
        classmethod(lambda cls, _path: (_ for _ in ()).throw(RuntimeError("down"))),
    )

    with pytest.raises(RuntimeError, match="down"):
        PDFParserService.parse(pdf_path)


def test_drop_repeated_page_artifacts_filters_common_headers_and_footers():
    blocks = [
        {"page": 1, "content": "Hospital X - Guia Clinica", "type": "text"},
        {"page": 1, "content": "Contenido pagina 1", "type": "text"},
        {"page": 1, "content": "Pagina 1", "type": "footer"},
        {"page": 2, "content": "Hospital X - Guia Clinica", "type": "text"},
        {"page": 2, "content": "Contenido pagina 2", "type": "text"},
        {"page": 2, "content": "Pagina 2", "type": "footer"},
    ]

    cleaned, removed = PDFParserService._drop_repeated_page_artifacts(blocks)

    assert removed >= 2
    joined = "\n".join(str(item.get("content")) for item in cleaned)
    assert "Contenido pagina 1" in joined
    assert "Contenido pagina 2" in joined
