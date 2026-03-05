# ADR-0172: Chat publico en pipeline estricto y endurecimiento del prompt de fuentes LLM

## Contexto

Tras aislar el canal del turno actual en TM-216, seguian apareciendo respuestas clinicas inadecuadas en la UI. El analisis del request real y de los registros persistidos mostro dos problemas fuera del RAG puro:

1. El frontend publico enviaba `pipeline_relaxed_mode: true`, activando `pipeline_profile=evaluation`.
2. El prompt del proveedor LLM seguia incluyendo instrucciones ambiguas como `menciona fuentes usadas`, lo que favorecia salidas con:
   - bibliografia inventada,
   - formatos `Referencias`,
   - citas no exactas o no presentes en `knowledge_sources`.

## Decision

1. La API publica de chat (`POST /api/v1/care-tasks/{id}/chat/messages` y su variante async) fuerza `pipeline_relaxed_mode=False` aunque el cliente lo envie.
2. El frontend deja de enviar `pipeline_relaxed_mode: true`.
3. `LLMChatProvider` cambia sus prompts clinicos para:
   - pedir solo `fuentes internas exactas`,
   - prohibir bibliografia inventada, revistas, anos y referencias externas.

## Consecuencias

- El chat que usa la UI publica y la API publica siempre entra en perfil `strict`.
- Los gates clinicos, safe-wrapper y reparaciones por evidencia quedan activos de forma consistente para usuarios reales.
- El LLM recibe instrucciones mas alineadas con grounding interno y menos permisivas con referencias libres.
- El modo relajado sigue existiendo solo como capacidad interna/test, no como comportamiento publico.

## Riesgos

- Integraciones externas que dependiesen de `pipeline_relaxed_mode=true` sobre la API publica dejaran de poder activarlo.
- Si una fuente interna del canal contiene ya contenido demasiado especifico, el LLM aun puede sobreconcretar; eso se corrige con mas curacion de chunking/rerank, no con el perfil estricto.

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "rag_relaxed_mode or bibliographic_reference_style or current_turn_keeps_only_current_domain_channel" -o addopts=""`
- `.\venv\Scripts\python.exe -m ruff check app/api/care_tasks.py app/services/llm_chat_provider.py app/services/clinical_chat_service.py app/services/rag_orchestrator.py app/tests/test_clinical_chat_operational.py`
- `npm --prefix frontend run build`
- Verificacion de codigo:
  - `frontend/src/App.tsx` ya no envia `pipeline_relaxed_mode: true`.
  - `app/api/care_tasks.py` normaliza el payload publico a `pipeline_relaxed_mode=False`.
