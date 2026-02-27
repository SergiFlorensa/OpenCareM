# ADR-0142: Quality Gates de Ingesta y Aceptacion Offline RAG por Especialidad

Fecha: 2026-02-26
Estado: Aprobada

## Contexto

El stack local presentaba variabilidad de calidad en dos puntos:

1. Ingesta: documentos de baja señal (muy cortos, escaneos pobres, bloques insuficientes) entraban en el corpus y degradaban retrieval.
2. Evaluacion: `evaluate_rag_retrieval.py` no tenia un gate de aceptacion automatizable ni visibilidad agregada por especialidad.

## Decision

Se adopta una capa determinista, sin LLM, en ambos puntos:

1. `app/scripts/ingest_clinical_docs.py`
   - Quality gates por documento antes de persistir chunks.
   - Reglas base:
     - `min_chunks`
     - `min_total_chars`
     - `min_avg_chunk_chars`
     - para PDF: `pdf_min_chars_per_page`, `pdf_min_blocks_per_page`
   - Telemetria operativa:
     - `documents_rejected_quality`
     - `quality_rejection_reason_counts`
   - Flags CLI para calibracion y desactivacion controlada.

2. `app/scripts/evaluate_rag_retrieval.py`
   - Agregacion de metricas por especialidad (`summary.by_specialty`).
   - Umbrales de aceptacion configurables (`--acceptance-thresholds`).
   - Salida de estado de aceptacion:
     - `acceptance_passed`
     - `acceptance_failures`
   - `--fail-on-acceptance` para usar el script como gate en CI/local.

## Consecuencias

Positivas:
- Menos ruido en corpus y mejor estabilidad del retrieval.
- Evaluacion offline reusable como criterio de despliegue.
- Visibilidad de deuda por especialidad, no solo global.

Trade-offs:
- Umbrales no calibrados pueden reducir recall si son demasiado agresivos.
- Requiere mantenimiento del dataset offline con cobertura real por especialidad.

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/scripts/ingest_clinical_docs.py app/scripts/evaluate_rag_retrieval.py app/tests/test_ingest_clinical_docs_script.py app/tests/test_evaluate_rag_retrieval.py -q`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_ingest_clinical_docs_script.py app/tests/test_evaluate_rag_retrieval.py -o addopts=""`

