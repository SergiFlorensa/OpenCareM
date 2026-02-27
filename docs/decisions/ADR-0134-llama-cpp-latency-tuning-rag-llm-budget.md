# ADR-0134: Tuning de latencia para `llama.cpp` con presupuesto RAG/LLM

- Fecha: 2026-02-25
- Estado: Aprobada

## Contexto
En benchmark local persistian `llm_used=false` con `TimeoutError` y `BudgetExhausted`, elevando p95 y degradando calidad.

## Decision
Se aplica perfil de baja latencia en CPU:
- `CLINICAL_CHAT_LLM_TIMEOUT_SECONDS=35`
- `CLINICAL_CHAT_LLM_MAX_OUTPUT_TOKENS=48`
- `CLINICAL_CHAT_LLM_MAX_INPUT_TOKENS=220`
- `CLINICAL_CHAT_LLM_PROMPT_MARGIN_TOKENS=40`
- `CLINICAL_CHAT_LLM_MAX_DIALOGUE_TURNS=2`
- `CLINICAL_CHAT_LLM_CIRCUIT_BREAKER_OPEN_SECONDS=12`
- `CLINICAL_CHAT_RAG_MAX_TOTAL_LATENCY_MS=2200`
- `CLINICAL_CHAT_RAG_LLM_MIN_REMAINING_BUDGET_MS=250`
- `CLINICAL_CHAT_RAG_FTS_CANDIDATE_POOL=48`
- `CLINICAL_CHAT_RAG_WILDCARD_ENABLED=false`
- `CLINICAL_CHAT_RAG_SOUNDEX_ENABLED=false`
- `CLINICAL_CHAT_RAG_CONTEXTUAL_SPELL_ENABLED=false`

## Consecuencias
- Mayor probabilidad de que el LLM llegue a generar respuesta antes del fallback.
- Menor costo temporal en retrieval lexical avanzado.
- Riesgo: ligera reduccion de recall en consultas con errores ortograficos severos.
