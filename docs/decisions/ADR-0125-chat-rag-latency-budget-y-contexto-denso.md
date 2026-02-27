# ADR-0125: Perfil Latencia-Primero para Chat RAG local

## Estado
Aprobada (2026-02-25)

## Contexto
El chat local con Ollama presentaba variabilidad de latencia por exceso de contexto
e intentos LLM cuando la request ya llegaba tarde a la fase de generación.

## Decisión
Aplicar una configuración y flujo orientados a latencia:

- Presupuesto de latencia en orquestación RAG:
  - `CLINICAL_CHAT_RAG_MAX_TOTAL_LATENCY_MS`
  - `CLINICAL_CHAT_RAG_LLM_MIN_REMAINING_BUDGET_MS`
- Si el presupuesto restante no alcanza el umbral, saltar LLM y responder con fallback
  extractivo con fuentes internas.
- Compacción de contexto LLM:
  - reducir turnos de diálogo en prompt (`CLINICAL_CHAT_LLM_MAX_DIALOGUE_TURNS`)
  - evitar duplicar historial en el bloque de usuario
  - recortar tamaño de payload de resultados de herramientas.
- Ajuste de defaults de request para bajar carga por defecto:
  - menos historial
  - menos fuentes internas/web.

## Impacto
- Menos timeouts de generación en picos de carga local.
- Menor TTFT/TBT en hardware CPU modesto.
- Se mantiene resiliencia por fallback extractivo cuando LLM no entra en presupuesto.

## Riesgos
- Menor contexto puede reducir calidad en casos muy complejos.
- Si se necesita mayor exhaustividad en una sesión concreta, debe aumentarse
  explícitamente `max_history_messages` y fuentes por request.

## Validación
- `ruff` sobre `config`, `llm_chat_provider`, `rag_orchestrator`, `clinical_chat schema`, tests.
- `pytest` focal:
  - `app/tests/test_rag_orchestrator_optimizations.py`
  - tests LLM provider en `app/tests/test_clinical_chat_operational.py`
  - `app/tests/test_settings_security.py`

