# ADR-0144: RAG Adaptive Budget Routing con Keyword-Only para Cola de Latencia

Fecha: 2026-02-26
Estado: Aprobada

## Contexto

Con LLM activado, la cola de latencia (p95) se degradaba por:
- costo variable de vector scoring en consultas complejas,
- intentos LLM cuando el presupuesto residual ya era insuficiente.

Esto introducia `TimeoutError/BudgetExhausted` y elevaba el p95.

## Decision

Aplicar enrutado adaptativo `budget-aware`:

1. `keyword_only` en retrieval hibrido para consultas complejas cuando la reserva de presupuesto LLM es alta.
2. presupuesto minimo de llamada LLM dinamico en runtime:
   - segun complejidad de consulta (`simple/medium/complex`),
   - ajustado por `pre_context_relevance`.

Implementacion:
- `app/services/rag_orchestrator.py`
  - compactacion y ruteo adaptativo.
  - trazas nuevas de presupuesto dinamico.
- `app/services/rag_retriever.py`
  - `search_hybrid(..., keyword_only=True)` para saltar vector scoring en el fast-path.

## Consecuencias

Positivas:
- reducción de p95 en consultas complejas.
- menor número de timeouts evitables en camino LLM.
- benchmark de aceptación vuelve a verde con LLM habilitado.

Trade-offs:
- `llm_used_true_rate` puede mantenerse bajo si la política prioriza SLA estricto.
- en consultas ambiguas, `keyword_only` puede perder recall semantico.

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/services/rag_orchestrator.py app/services/rag_retriever.py app/services/clinical_chat_service.py -q`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""`
- `./venv/Scripts/python.exe tmp/run_chat_benchmark.py`
- `./venv/Scripts/python.exe tmp/summarize_chat_benchmark.py`
- `./venv/Scripts/python.exe tmp/check_acceptance.py`

Resultado validado:
- `latency_ok_p95_ms: 2719.0`
- `BENCHMARK OK - criterios cumplidos.`

