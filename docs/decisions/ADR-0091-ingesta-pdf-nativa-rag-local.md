# ADR-0091: Ingesta PDF Nativa en RAG Local

- Fecha: 2026-02-22
- Estado: Aprobado

## Contexto

El flujo de RAG solo aceptaba `.md` y `.txt`, obligando conversion manual de PDFs clinicos largos.

## Decision

Extender `DocumentIngestionService` para soportar `.pdf` multipagina usando `pypdf` en local.

- Extraccion por pagina con marcador `[PAGE n]`.
- Reutilizacion del pipeline actual de chunking semantico y embeddings.
- Sin cambios de esquema en BD.

## Consecuencias

### Positivas

- Carga directa de guias/protocolos en PDF sin conversion manual.
- Mismo flujo de ingesta y mismas tablas (`clinical_documents`, `document_chunks`).

### Riesgos

- PDFs escaneados sin OCR pueden extraer poco texto.
- Depende de tener `pypdf` instalado.

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/services/document_ingestion_service.py app/scripts/ingest_clinical_docs.py app/tests/test_document_ingestion_service.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_document_ingestion_service.py`
