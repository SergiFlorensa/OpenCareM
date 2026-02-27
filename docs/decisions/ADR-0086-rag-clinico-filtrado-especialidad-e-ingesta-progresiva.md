# ADR-0086: RAG clinico con filtrado por especialidad e ingesta progresiva

## Estado

Aprobado.

## Contexto

El chat clinico recuperaba fragmentos no clinicos (estado de repo, contratos operativos)
cuando la busqueda por dominio detectaba terminos generales. Esto degradaba
groundedness y respuesta final.

Adicionalmente, la ingesta masiva incluia rutas no clinicas por defecto y no facilitaba
backfill de `specialty` para documentos/chunks existentes.

## Decision

1. Filtrar en `RAGOrchestrator` los chunks de estrategia `domain` por especialidad
   efectiva antes de construir contexto para LLM.
2. Reestructurar ingesta en `ingest_clinical_docs`:
   - default `--paths docs`
   - mapa de especialidades por defecto para `docs/45_*` a `docs/86_*`
   - flags `--backfill-specialty` y `--backfill-only`.
3. Normalizar matching de paths en `DocumentIngestionService` para consistencia
   Windows/Linux.

## Consecuencias

- Positivas:
  - menor ruido no clinico en retrieval.
  - mejor trazabilidad por especialidad.
  - mejor operativa para incorporar documentacion clinica de forma progresiva.
- Riesgos:
  - parte del corpus previo queda en `specialty=null` hasta limpieza/curacion adicional.
  - filtros estrictos por especialidad pueden reducir recall en casos transversales.

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/services/rag_orchestrator.py app/services/document_ingestion_service.py app/scripts/ingest_clinical_docs.py app/tests/test_clinical_chat_operational.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py`
- `.\venv\Scripts\python.exe -m app.scripts.ingest_clinical_docs --backfill-only`
