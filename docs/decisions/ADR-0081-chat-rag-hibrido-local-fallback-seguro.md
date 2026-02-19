# ADR-0081: Chat RAG Hibrido Local con Fallback Seguro

## Contexto

El chat clinico necesitaba respuestas mas fundamentadas en fuentes internas del
repositorio y mejor trazabilidad de evidencia, sin romper el flujo actual.
Ademas, el estado previo tenia un bug funcional en el endpoint de chat por
desempaquetado inconsistente de retorno.

## Decision

1. Integrar un pipeline RAG hibrido local en el flujo de chat:
- retrieval por similitud vectorial + busqueda lexical.
- augment de `knowledge_sources` con fragmentos recuperados.
- gatekeeper de validacion ligera para detectar riesgo de baja fundamentacion.
- auditoria por consulta en `rag_queries_audit`.

2. Mantener fallback seguro:
- si RAG no recupera contexto o falla, el chat conserva ruta LLM/fallback
  existente y no rompe contrato API.

3. Mantener compatibilidad de contrato:
- sin cambios en payload de request/response de
  `POST /api/v1/care-tasks/{task_id}/chat/messages`.
- trazabilidad ampliada via `interpretability_trace` con claves `rag_*`.

4. Corregir estabilidad del endpoint:
- alinear desempaquetado de retorno en `app/api/care_tasks.py`.

## Consecuencias

Positivas:
- mejora de grounding cuando hay corpus ingerido.
- trazabilidad operativa de retrieval y validacion en cada turno.
- continuidad operativa sin regresion por fallback.

Costes/riesgos:
- requiere migracion y carga inicial de documentos para aportar valor real.
- en SQLite la busqueda vectorial escala de forma lineal con el numero de
  chunks.
- validaciones del gatekeeper son heuristicas y requieren calibracion continua.

## Validacion

- `ruff check` sobre modulos afectados.
- `pytest -q app/tests/test_clinical_chat_operational.py`
- `pytest -q app/tests/test_care_tasks_api.py -k chat`
