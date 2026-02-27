# ADR-0127: Fast-path de recuperación RAG para bajar p95

## Estado
Aprobada (2026-02-25)

## Contexto
Persistía cola larga en latencia (p95 alto) concentrada en consultas con mayor
coste de recuperación (`rag_total_latency_ms`), aun con estabilidad funcional.

## Decisión
- Introducir fast-path en orquestador:
  - saltar búsqueda por dominio cuando el número de tokens de consulta supera
    `CLINICAL_CHAT_RAG_SKIP_DOMAIN_SEARCH_TOKENS_OVER`.
  - traza explícita: `rag_domain_search_skipped`.
- Endurecer tuning de recuperación/contexto para carga local CPU:
  - `CLINICAL_CHAT_RAG_MAX_TOTAL_LATENCY_MS=3200`
  - `CLINICAL_CHAT_RAG_LLM_MIN_REMAINING_BUDGET_MS=1100`
  - `CLINICAL_CHAT_RAG_FTS_CANDIDATE_POOL=80`
  - `CLINICAL_CHAT_RAG_WILDCARD_MAX_EXPANSIONS=16`
  - `CLINICAL_CHAT_RAG_CONTEXTUAL_SPELL_MAX_CANDIDATES=10`
  - `CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_MAX_EXPANSIONS_PER_TERM=4`

## Impacto esperado
- Menor varianza en latencia de recuperación (especialmente en queries largas).
- Menor probabilidad de superar SLA local por cascada de etapas de retrieval.
- Trade-off controlado: posible ligera reducción de recall marginal en consultas
  de cobertura muy amplia.

## Validación
- `ruff` sobre `config`, `rag_orchestrator`, tests.
- `pytest`:
  - `app/tests/test_rag_orchestrator_optimizations.py`
  - `app/tests/test_settings_security.py`
- Evaluación retrieval de control sin degradación material.

