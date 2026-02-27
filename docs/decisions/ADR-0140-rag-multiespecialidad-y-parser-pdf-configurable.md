# ADR-0140: Cobertura multi-especialidad RAG y parser PDF configurable (pypdf/mineru)

- Fecha: 2026-02-26
- Estado: aceptada
- Alcance: `app/services/rag_orchestrator.py`, `app/services/rag_retriever.py`, `app/core/chunking.py`, `app/scripts/ingest_clinical_docs.py`, `app/services/pdf_parser_service.py`, `app/services/document_ingestion_service.py`, `app/core/config.py`

## Contexto

El benchmark mostraba tres problemas recurrentes:

1. Sesgo de recuperacion hacia `critical_ops` en consultas generales.
2. Cobertura desigual por especialidad por metadatos incompletos (`specialty=NULL`) y
   `custom_questions` pobres/placeholder.
3. Ingesta PDF acoplada a `pypdf`, sin backend configurable para OCR/parser avanzado.

Ademas, el objetivo operativo exige que el chat consulte evidencia de todas las
especialidades y no dependa solo de oncologia/nefrologia.

## Decision

Se aplican cambios de hardening en tres capas:

1. Retrieval/orquestacion:
   - bypass de domain-search cuando el dominio detectado es fallback generico
     (`critical_ops`) en contexto general.
   - filtro anti-ruido de chunks no clinicos antes del ensamblado de contexto.
   - QA shortcut ampliado para considerar chunks sin especialidad y con relajacion
     de specialty filter.

2. Ingesta/cobertura:
   - ampliacion del `DEFAULT_SPECIALTY_MAP` para `docs/40_*` ... `docs/86_*` y
     `docs/pdf_raw/*`.
   - heuristica por nombre de archivo para inferir especialidad cuando falta mapeo.
   - comando de reconstruccion de `custom_questions` para corpus existente.

3. Parser PDF configurable:
   - nuevo `PDFParserService` con backend `pypdf|mineru`.
   - integracion en `DocumentIngestionService`.
   - modo fail-open configurable para no bloquear ingesta cuando MinerU no responde.

Configuracion nueva:

- `CLINICAL_CHAT_PDF_PARSER_BACKEND`
- `CLINICAL_CHAT_PDF_MINERU_BASE_URL`
- `CLINICAL_CHAT_PDF_MINERU_TIMEOUT_SECONDS`
- `CLINICAL_CHAT_PDF_MINERU_FAIL_OPEN`

## Consecuencias

- Mejora robustez de retrieval transversal por especialidad y reduce ruido de fuentes
  internas tecnicas/no clinicas.
- Permite activar MinerU en entornos con OCR/layout avanzado sin romper el flujo actual.
- Mantiene operacion local sin dependencia obligatoria de GPU: si MinerU falla, la
  ingesta continua con `pypdf`.

Riesgos:

- El filtro anti-ruido puede descartar algun fragmento util en documentos mixtos.
- Sin servicio MinerU activo, no hay parsing estructural avanzado (tablas/formulas),
  solo extraccion textual local.

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/services/rag_orchestrator.py app/scripts/ingest_clinical_docs.py app/tests/test_ingest_clinical_docs_script.py app/services/pdf_parser_service.py app/services/document_ingestion_service.py app/tests/test_pdf_parser_service.py app/tests/test_chunking.py -q`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_ingest_clinical_docs_script.py app/tests/test_chunking.py app/tests/test_pdf_parser_service.py app/tests/test_document_ingestion_service.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
