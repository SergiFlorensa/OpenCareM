# ADR-0124: Ingesta incremental RAG con skip por `source_file`

## Estado
Aprobada (2026-02-25)

## Contexto
La ingesta de `docs/pdf_raw` reprocesaba en cada corrida archivos ya existentes en BD.
En corpus grandes esto eleva la latencia operativa aun cuando no hay documentos nuevos.

## Decision
Optimizar `app/scripts/ingest_clinical_docs.py` con pre-scan incremental:

- Descubrir archivos soportados (`.md`, `.txt`, `.pdf`) antes de parsear.
- Consultar `clinical_documents.source_file` y omitir rutas ya presentes.
- Exponer override explicito para reingesta total:
  - `--force-reprocess-existing-paths`

## Impacto
- Reduce significativamente el tiempo de mantenimiento incremental del corpus RAG.
- No cambia contratos de API ni modelo de datos.
- Riesgo conocido: si el contenido cambia sin cambiar `source_file`, la ruta incremental no lo detecta; para ese caso se usa `--force-reprocess-existing-paths`.

## Validacion
- `./venv/Scripts/python.exe -m ruff check app/scripts/ingest_clinical_docs.py`
- `./venv/Scripts/python.exe -m app.scripts.ingest_clinical_docs --paths docs/pdf_raw --backfill-specialty`

