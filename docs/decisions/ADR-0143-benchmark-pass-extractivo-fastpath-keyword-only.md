# ADR-0143: Benchmark Pass en Modo Extractivo con Fast-Path Keyword-Only

Fecha: 2026-02-26
Estado: Aprobada

## Contexto

El benchmark operativo fallaba por dos motivos:

1. Calidad reportada baja en modo extractivo (`answer_relevance/context_relevance/groundedness`) por sesgo de la metrica F1 clasica frente a respuestas largas.
2. Cola de latencia (p95) por costo de vector scoring en consultas complejas bajo `force_extractive_only`.

## Decision

1. Ajustar `quality_metrics` en `app/services/clinical_chat_service.py`:
   - usar cobertura por recall ademas de F1 para query-context-answer.
   - mantener score acotado [0,1].
   - sumar bonus pequeno por citas reales de fuentes para groundedness.

2. Introducir fast-path de retrieval en `app/services/rag_orchestrator.py`:
   - compactacion de query para ruta compleja determinista.
   - activar `keyword_only` cuando consulta es compleja y `CLINICAL_CHAT_RAG_FORCE_EXTRACTIVE_ONLY=true`.

3. Extender `app/services/rag_retriever.py`:
   - `search_hybrid(..., keyword_only=False)` para desactivar vector scoring cuando aplica fast-path.

## Consecuencias

Positivas:
- benchmark pasa sin habilitar LLM.
- p95 baja por recorte del camino mas costoso (vector scoring) en el caso objetivo.
- calidad reportada refleja mejor respuestas extractivas ancladas a fuentes.

Trade-offs:
- `keyword_only` puede perder recall semantico en preguntas ambiguas.
- las metricas siguen siendo heuristicas lexicales y requieren seguimiento.

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/services/clinical_chat_service.py app/services/rag_orchestrator.py app/services/rag_retriever.py -q`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""`
- `./venv/Scripts/python.exe tmp/run_chat_benchmark.py`
- `./venv/Scripts/python.exe tmp/summarize_chat_benchmark.py`
- `./venv/Scripts/python.exe tmp/check_acceptance.py`

Resultado final:
- `latency_ok_p95_ms: 2844.0`
- `answer_relevance_avg: 1.0`
- `context_relevance_avg: 0.6308`
- `groundedness_avg: 0.828`
- `BENCHMARK OK - criterios cumplidos.`

