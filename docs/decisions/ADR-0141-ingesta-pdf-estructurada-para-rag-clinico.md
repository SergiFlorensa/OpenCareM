# ADR-0141: Ingesta PDF estructurada para RAG clinico (para_blocks + limpieza + orden + telemetria)

- Fecha: 2026-02-26
- Estado: aceptada
- Alcance: `app/services/pdf_parser_service.py`, `app/services/document_ingestion_service.py`, `app/core/chunking.py`, `app/core/config.py`, `app/scripts/ingest_clinical_docs.py`

## Contexto

El rendimiento/calidad del chat clinico dependia de texto plano extraido, con riesgo de:

- perdida de estructura (tablas/formulas),
- ruido por encabezados/pies repetidos,
- orden de lectura inconsistente en documentos complejos,
- baja observabilidad de la calidad de ingesta.

Se requiere una capa de parsing que permita aprovechar MinerU cuando esta disponible,
sin bloquear la operacion local cuando no lo esta.

## Decision

Se implementa parser PDF desacoplado con salida estructurada y fallback:

1. `PDFParserService.parse(...)` retorna `PDFParseResult(text, blocks, trace)`.
2. Backend configurable `pypdf|mineru` y modo fail-open para continuidad operativa.
3. Soporte de bloques estructurados (`para_blocks` y variantes) con normalizacion de tipo:
   - `text`, `table`, `formula`.
4. Orden de lectura configurable (layout-first) y filtrado de artefactos repetidos por pagina.
5. `DocumentIngestionService` consume bloques estructurados y los pasa al chunker.
6. `SemanticChunker.chunk(..., parsed_blocks=...)` preserva `content_type` del bloque.
7. Telemetria agregada de parseo PDF en pipeline/script de ingesta.

## Configuracion nueva

- `CLINICAL_CHAT_PDF_OCR_MODE`
- `CLINICAL_CHAT_PDF_LAYOUT_READING_ORDER_ENABLED`
- `CLINICAL_CHAT_PDF_FILTER_REPEATED_EDGE_TEXT_ENABLED`
- `CLINICAL_CHAT_PDF_FILTER_REPEATED_EDGE_TEXT_MIN_PAGES`
- `CLINICAL_CHAT_PDF_TELEMETRY_ENABLED`

## Consecuencias

- Mejora de calidad de corpus RAG en documentos complejos.
- Reduccion de ruido sistematico de headers/footers repetidos.
- Mayor trazabilidad de la fase de ingesta para diagnostico de latencia/calidad.
- Riesgo controlado: si MinerU no responde, se conserva operacion con `pypdf`.

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/services/pdf_parser_service.py app/services/document_ingestion_service.py app/core/chunking.py app/core/config.py app/scripts/ingest_clinical_docs.py app/tests/test_pdf_parser_service.py app/tests/test_document_ingestion_service.py app/tests/test_chunking.py app/tests/test_settings_security.py -q`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_pdf_parser_service.py app/tests/test_document_ingestion_service.py app/tests/test_chunking.py app/tests/test_settings_security.py app/tests/test_ingest_clinical_docs_script.py -o addopts=""`
