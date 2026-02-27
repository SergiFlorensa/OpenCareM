# ADR-0131: Tuning de presupuesto RAG->LLM para mejorar calidad sin perder p95

- Fecha: 2026-02-25
- Estado: Aprobada

## Contexto
Benchmark actual mantiene `failed_retrieval_rate=0`, pero sigue con calidad baja y `llm_used_true_rate=0.0`, lo que sugiere infrauso de LLM por presupuesto estricto de tiempo.

## Decision
1. Reducir presupuesto total de latencia para contener p95.
2. Bajar margen minimo previo a LLM para permitir invocacion LLM en mas consultas donde aun hay tiempo util.
3. Ajustar candidate pool y threshold de skip de busqueda por dominio para balancear recall/latencia.

Parametros:
- `CLINICAL_CHAT_RAG_MAX_TOTAL_LATENCY_MS=3000`
- `CLINICAL_CHAT_RAG_LLM_MIN_REMAINING_BUDGET_MS=700`
- `CLINICAL_CHAT_RAG_FTS_CANDIDATE_POOL=88`
- `CLINICAL_CHAT_RAG_SKIP_DOMAIN_SEARCH_TOKENS_OVER=12`

## Consecuencias
- Esperado: mayor `llm_used_true_rate` sin reintroducir timeouts severos.
- Riesgo: en consultas extremadamente largas puede reducirse recall marginal.

## Validacion
- Rebenchmark obligatorio tras reinicio de API y verificacion de trazas `llm_enabled/llm_used/llm_error`.
