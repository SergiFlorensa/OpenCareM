# ADR-0157: Modo RAG Fact-Only, Early Goal Test y Cache de Consulta Local

## Estado

Aprobado

## Contexto

En entorno local (portatil), la latencia y la variabilidad aumentaban cuando el flujo dependia
de generacion LLM incluso en preguntas con evidencia interna suficiente. Tambien se repetian
consultas similares que recalculaban retrieval y ensamblado completo.

Se necesitaba:

- reducir latencia p95/p99 en casos repetidos;
- minimizar fallback a generacion razonada cuando hay evidencia accionable;
- mantener respuesta determinista y trazable sin cambios de schema API/DB.

## Decision

1. Introducir un modo opcional fact-only:
   - `CLINICAL_CHAT_RAG_FACT_ONLY_MODE_ENABLED`;
   - fuerza ruta extractiva/determinista en RAG;
   - omite segundo pase LLM en `ClinicalChatService`.
2. Activar corte temprano por evidencia (early-goal test) en orquestador RAG:
   - habilitado por `CLINICAL_CHAT_RAG_EARLY_GOAL_TEST_ENABLED`;
   - umbrales configurables:
     - `CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_SCORE`
     - `CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_ACTIONABILITY`
     - `CLINICAL_CHAT_RAG_EARLY_GOAL_MIN_RETRIEVAL_SCORE`
3. Agregar memoizacion de consultas en memoria de proceso:
   - TTL y tamano maximo configurables:
     - `CLINICAL_CHAT_RAG_QUERY_CACHE_ENABLED`
     - `CLINICAL_CHAT_RAG_QUERY_CACHE_TTL_SECONDS`
     - `CLINICAL_CHAT_RAG_QUERY_CACHE_MAX_ENTRIES`
   - reutilizacion exacta por clave normalizada;
   - poda por estado resoluble (subset de tokens) para consultas mas especificas->mas breves.

## Consecuencias

- Menor latencia en consultas repetidas y en rutas con evidencia clara.
- Menor uso de LLM en modo local cuando se habilita fact-only.
- Sin migraciones ni cambios de contrato externo.
- Cache no persistente: se pierde al reiniciar proceso (aceptado para local).

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/rag_orchestrator.py app/services/clinical_chat_service.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py`
- `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
- Resultado: `129 passed`.

## Riesgos pendientes

- En activacion de fact-only, queries sin evidencia suficiente pueden terminar en respuesta mas conservadora.
- La poda por subset depende de tokenizacion lexical; no sustituye un sistema semantico de estados completo.
