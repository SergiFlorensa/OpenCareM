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


def test_pdf_parser_mineru_cli_backend(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")

    monkeypatch.setattr(
        "app.services.pdf_parser_service.settings.CLINICAL_CHAT_PDF_PARSER_BACKEND",
        "mineru",
    )
    monkeypatch.setattr(
        "app.services.pdf_parser_service.settings.CLINICAL_CHAT_PDF_MINERU_TRANSPORT",
        "cli",
    )
    monkeypatch.setattr(
        PDFParserService,
        "_parse_with_mineru_cli",
        classmethod(
            lambda cls, _path: PDFParseResult(
                text="texto mineru cli",
                blocks=[],
                trace={"pdf_parser_backend": "mineru", "pdf_parser_transport": "cli"},
            )
        ),
    )

    result = PDFParserService.parse(pdf_path)
    assert result.text == "texto mineru cli"
    assert result.trace["pdf_parser_transport"] == "cli"
    assert result.trace["pdf_parser_transport_requested"] == "cli"


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
        "app.services.pdf_parser_service.settings.CLINICAL_CHAT_PDF_MINERU_TRANSPORT",
        "cli",
    )
    monkeypatch.setattr(
        PDFParserService,
        "_parse_with_mineru_cli",
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
    assert result.trace["pdf_parser_transport_requested"] == "cli"


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
        "app.services.pdf_parser_service.settings.CLINICAL_CHAT_PDF_MINERU_TRANSPORT",
        "cli",
    )
    monkeypatch.setattr(
        PDFParserService,
        "_parse_with_mineru_cli",
        classmethod(lambda cls, _path: (_ for _ in ()).throw(RuntimeError("down"))),
    )

    with pytest.raises(RuntimeError, match="down"):
        PDFParserService.parse(pdf_path)


def test_pdf_parser_mineru_auto_falls_back_to_http(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")

    monkeypatch.setattr(
        "app.services.pdf_parser_service.settings.CLINICAL_CHAT_PDF_PARSER_BACKEND",
        "mineru",
    )
    monkeypatch.setattr(
        "app.services.pdf_parser_service.settings.CLINICAL_CHAT_PDF_MINERU_TRANSPORT",
        "auto",
    )
    monkeypatch.setattr(
        PDFParserService,
        "_parse_with_mineru_cli",
        classmethod(lambda cls, _path: (_ for _ in ()).throw(RuntimeError("cli down"))),
    )
    monkeypatch.setattr(
        PDFParserService,
        "_parse_with_mineru_http",
        classmethod(
            lambda cls, _path: PDFParseResult(
                text="texto mineru http",
                blocks=[],
                trace={"pdf_parser_backend": "mineru", "pdf_parser_transport": "http"},
            )
        ),
    )

    result = PDFParserService.parse(pdf_path)
    assert result.text == "texto mineru http"
    assert result.trace["pdf_parser_transport"] == "http"
    assert result.trace["pdf_parser_transport_requested"] == "auto"


def test_parse_with_mineru_cli_reads_structured_output(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
    output_dir = tmp_path / "mineru_out"
    output_dir.mkdir()
    nested = output_dir / "result"
    nested.mkdir()
    (nested / "content.md").write_text(
        "# Informe\n\n## Abdomen\n\nChecklist general abdominal",
        encoding="utf-8",
    )
    (nested / "middle.json").write_text(
        """
        {
          "pages": [
            {
              "page": 1,
              "blocks": [
                {"type": "text", "text": "Exploracion abdominal y constantes"},
                {"type": "table", "markdown": "| item | valor |\\n| --- | --- |\\n| dolor | alto |"}
              ]
            }
          ]
        }
        """.strip(),
        encoding="utf-8",
    )

    class Completed:
        returncode = 0
        stderr = ""
        stdout = ""

    monkeypatch.setattr(
        PDFParserService,
        "_build_mineru_cli_command",
        classmethod(
            lambda cls, *, file_path, output_dir, start_page=None, end_page=None: ["magic-pdf"]
        ),
    )
    monkeypatch.setattr(
        "app.services.pdf_parser_service.tempfile.mkdtemp",
        lambda prefix: str(output_dir),
    )
    monkeypatch.setattr(
        "app.services.pdf_parser_service.subprocess.run",
        lambda *args, **kwargs: Completed(),
    )

    result = PDFParserService._parse_with_mineru_cli(pdf_path)
    assert "Exploracion abdominal y constantes" in result.text
    assert result.trace["pdf_parser_transport"] == "cli"
    assert result.trace["pdf_parser_cli_json"] == "middle.json"


def test_resolve_mineru_cli_executable_accepts_legacy_alias(monkeypatch):
    monkeypatch.setattr(
        PDFParserService,
        "_command_exists",
        staticmethod(lambda command: command == "magic-pdf"),
    )

    resolved = PDFParserService._resolve_mineru_cli_executable("mineru")
    assert resolved == "magic-pdf"


def test_build_mineru_cli_command_uses_pipeline_cpu(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "sample.pdf"
    output_dir = tmp_path / "out"

    monkeypatch.setattr(
        PDFParserService,
        "_resolve_mineru_cli_executable",
        classmethod(lambda cls, command: command),
    )

    command = PDFParserService._build_mineru_cli_command(
        file_path=pdf_path,
        output_dir=output_dir,
    )
    assert "-m" in command and "txt" in command
    assert "-b" in command and "pipeline" in command
    assert "-d" in command and "cpu" in command
    assert "-f" in command and "false" in command
    assert "-t" in command and "true" in command


def test_build_mineru_cli_command_accepts_page_window(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "sample.pdf"
    output_dir = tmp_path / "out"

    monkeypatch.setattr(
        PDFParserService,
        "_resolve_mineru_cli_executable",
        classmethod(lambda cls, command: command),
    )

    command = PDFParserService._build_mineru_cli_command(
        file_path=pdf_path,
        output_dir=output_dir,
        start_page=10,
        end_page=19,
    )
    assert "-s" in command and "10" in command
    assert "-e" in command and "19" in command


def test_build_mineru_cli_env_sets_thread_and_render_limits(monkeypatch):
    monkeypatch.setattr(
        "app.services.pdf_parser_service.settings.CLINICAL_CHAT_PDF_MINERU_RENDER_TIMEOUT_SECONDS",
        120,
    )
    monkeypatch.setattr(
        "app.services.pdf_parser_service.settings.CLINICAL_CHAT_PDF_MINERU_CPU_INTRA_OP_THREADS",
        2,
    )
    monkeypatch.setattr(
        "app.services.pdf_parser_service.settings.CLINICAL_CHAT_PDF_MINERU_CPU_INTER_OP_THREADS",
        1,
    )

    env = PDFParserService._build_mineru_cli_env()
    assert env["MINERU_PDF_RENDER_TIMEOUT"] == "120"
    assert env["MINERU_INTRA_OP_NUM_THREADS"] == "2"
    assert env["MINERU_INTER_OP_NUM_THREADS"] == "1"


def test_pdf_parser_mineru_cli_uses_windowed_mode_for_large_pdf(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "large.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")

    monkeypatch.setattr(
        "app.services.pdf_parser_service.settings.CLINICAL_CHAT_PDF_MINERU_WINDOWED_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.pdf_parser_service.settings.CLINICAL_CHAT_PDF_MINERU_WINDOW_THRESHOLD_PAGES",
        4,
    )
    monkeypatch.setattr(
        "app.services.pdf_parser_service.settings.CLINICAL_CHAT_PDF_MINERU_WINDOW_SIZE_PAGES",
        2,
    )
    monkeypatch.setattr(
        PDFParserService,
        "_get_pdf_page_count",
        staticmethod(lambda _path: 6),
    )
    monkeypatch.setattr(
        PDFParserService,
        "_parse_with_mineru_cli_windowed",
        classmethod(
            lambda cls, _path, *, page_count: PDFParseResult(
                text="windowed",
                blocks=[],
                trace={"pdf_parser_backend": "mineru", "pdf_parser_windowed": "1"},
            )
        ),
    )

    result = PDFParserService._parse_with_mineru_cli(pdf_path)
    assert result.text == "windowed"
    assert result.trace["pdf_parser_windowed"] == "1"


def test_shift_blocks_to_window_offset_updates_page_and_fallback_section():
    shifted = PDFParserService._shift_blocks_to_window_offset(
        [
            {"page": 1, "section_path": "Documento > Pagina 1", "content": "uno"},
            {"page": 2, "section_path": "Documento > Titulo", "content": "dos"},
        ],
        page_offset=10,
    )
    assert shifted[0]["page"] == 11
    assert shifted[0]["section_path"] == "Documento > Pagina 11"
    assert shifted[1]["page"] == 12
    assert shifted[1]["section_path"] == "Documento > Titulo"


def test_extract_raw_blocks_supports_mineru_pdf_info_shape():
    data = {
        "pdf_info": [
            {"page_idx": 0, "para_blocks": [{"type": "text", "text": "pagina uno"}]},
            {"page_idx": 1, "para_blocks": [{"type": "text", "text": "pagina dos"}]},
        ]
    }

    blocks = PDFParserService._extract_raw_blocks(data)
    assert len(blocks) == 2
    assert blocks[0]["page"] == 1
    assert blocks[1]["page"] == 2


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
