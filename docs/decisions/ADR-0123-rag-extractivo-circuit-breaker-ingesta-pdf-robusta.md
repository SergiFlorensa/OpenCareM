# ADR-0123: RAG extractivo resiliente + circuit breaker LLM + ingesta PDF robusta

- Fecha: 2026-02-25
- Estado: Aprobado
- Contexto:
  - El chat clinico mostraba `rag_status=failed_generation` cuando el LLM local no respondia a tiempo.
  - Se agregaron muchos PDF nuevos y la ingesta fallaba en Windows por errores de codificacion en consola.
  - Con `DATABASE_ECHO=true` se introducia ruido/log overhead y errores de salida con caracteres no ASCII.

## Decision

1. Orquestacion RAG resiliente:
- `RAGOrchestrator` genera salida extractiva basada en chunks recuperados cuando:
  - LLM esta deshabilitado, o
  - LLM falla y hay evidencia recuperada.
- Se incorpora traza `rag_generation_mode` para distinguir modo `llm` vs fallback extractivo.

2. Resiliencia de LLM local:
- `LLMChatProvider` incorpora circuit breaker con parametros configurables:
  - `CLINICAL_CHAT_LLM_CIRCUIT_BREAKER_ENABLED`
  - `CLINICAL_CHAT_LLM_CIRCUIT_BREAKER_FAILURE_THRESHOLD`
  - `CLINICAL_CHAT_LLM_CIRCUIT_BREAKER_OPEN_SECONDS`
- Evita cascadas de timeouts consecutivos y reduce latencia percibida bajo degradacion.

3. Higiene de retrieval/fallback:
- `HybridRetriever` excluye chunks con `specialty IS NULL` en candidate retrieval clinico.
- Se limpian snippets no clinicos (comandos/scripts/endpoints) en salidas extractivas.

4. Ingesta PDF robusta:
- `ingest_clinical_docs.py` robustecida para consola Windows (safe print).
- Se amplia mapeo de especialidad para `docs/pdf_raw/dermatology/`.
- Se recomienda `DATABASE_ECHO=false` para latencia/log limpio.

## Consecuencias

- Positivas:
  - Menos fallos operativos por timeout LLM.
  - RAG mantiene respuesta util con fuentes incluso sin generacion neuronal.
  - Ingesta masiva PDF estable en Windows.
- Riesgos:
  - El modo extractivo puede ser menos natural que LLM en casos complejos.
  - El corpus crece mucho y requiere monitorizar memoria/candidate pool.

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/llm_chat_provider.py app/services/rag_orchestrator.py app/services/rag_retriever.py app/services/clinical_chat_service.py app/scripts/ingest_clinical_docs.py app/tests/test_clinical_chat_operational.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_rag_retriever.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "rag_orchestrator_uses_extractive_fallback_when_generation_fails or llm_provider_circuit_breaker_short_circuits_after_failures" -o addopts=""`
- `./venv/Scripts/python.exe -m app.scripts.ingest_clinical_docs --paths docs/pdf_raw --backfill-specialty --skip-ollama-embeddings`
