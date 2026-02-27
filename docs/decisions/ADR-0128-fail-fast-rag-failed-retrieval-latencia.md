# ADR-0128: Fail-fast en `failed_retrieval` para cortar latencia en cascada

- Fecha: 2026-02-25
- Estado: Aprobada

## Contexto
En benchmark de chat clinico se observo regresion de latencia (p95 > 10s) cuando RAG devolvia `failed_retrieval`.
El flujo seguia intentando un segundo pase LLM, generando esperas innecesarias y timeouts.

## Decision
1. En `ClinicalChatService`, omitir segundo pase LLM cuando `rag_status` sea `failed_retrieval` o `failed_exception`.
2. Emitir traza explicita: `llm_second_pass_skipped=rag_failed_retrieval`.
3. Relajar tuning de retrieval para reducir falsos `failed_retrieval`:
   - `CLINICAL_CHAT_RAG_FTS_CANDIDATE_POOL=96`
   - `CLINICAL_CHAT_RAG_SKIP_DOMAIN_SEARCH_TOKENS_OVER=18`

## Consecuencias
- Se reduce drásticamente la latencia de cola en fallos de retrieval.
- Se mantiene respuesta determinista y trazable en fallback.
- Riesgo residual: si retrieval falla de forma recurrente, la calidad depende del fallback estructurado; requiere seguimiento de cobertura documental y recall.

## Validacion requerida
- Test e2e que garantice que no se invoca LLM en `failed_retrieval`.
- Pruebas de regresion de settings y optimizaciones RAG.
