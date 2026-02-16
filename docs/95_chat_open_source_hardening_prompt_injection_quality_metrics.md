# 95. Chat local open source endurecido: anti-inyeccion, presupuesto de contexto y metricas de calidad

## Problema que resuelve

El chat local ya funcionaba con Ollama y fallback, pero faltaban tres capas
clave para operar de forma mas robusta en entornos sin pago por token:

- defensa explicita ante prompt injection en entrada de usuario,
- control de presupuesto de contexto para no exceder `num_ctx`,
- metricas de calidad por turno para seguimiento continuo.

## Que se implementa

- Endurecimiento anti-inyeccion en backend:
  - deteccion de senales de inyeccion (`override`, `role tags`, probes de prompt),
  - sanitizacion de consulta antes de construir prompt LLM.
- Presupuesto de contexto/tokens en proveedor Ollama:
  - estimacion local de tokens de entrada,
  - truncado de historial y prompt cuando supera presupuesto,
  - trazas operativas de budget y truncado.
- Metricas de calidad locales por turno:
  - `answer_relevance`,
  - `context_relevance`,
  - `groundedness`,
  - `quality_status` (`ok`, `attention`, `degraded`).
- Cambio de contrato en respuesta chat:
  - `POST /api/v1/care-tasks/{task_id}/chat/messages` agrega `quality_metrics`.

## Archivos principales

- `app/services/clinical_chat_service.py`
- `app/services/llm_chat_provider.py`
- `app/schemas/clinical_chat.py`
- `app/api/care_tasks.py`
- `app/core/config.py`
- `.env.example`
- `.env.docker`
- `app/tests/test_clinical_chat_operational.py`
- `app/tests/test_care_tasks_api.py`

## Configuracion nueva

- `CLINICAL_CHAT_LLM_MAX_INPUT_TOKENS` (default `3200`)
- `CLINICAL_CHAT_LLM_PROMPT_MARGIN_TOKENS` (default `256`)

## Validacion ejecutada

- `python -m py_compile app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/schemas/clinical_chat.py app/api/care_tasks.py app/core/config.py app/tests/test_clinical_chat_operational.py app/tests/test_care_tasks_api.py`
- `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/schemas/clinical_chat.py app/api/care_tasks.py app/core/config.py app/tests/test_clinical_chat_operational.py app/tests/test_care_tasks_api.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat`

## Riesgos pendientes

- Las metricas de calidad son heuristicas lexicales; requieren calibracion
  progresiva con casos reales curados.
- La sanitizacion anti-inyeccion reduce riesgo, pero no sustituye auditoria
  clinica ni revisiones de seguridad periodicas.
- La latencia y calidad final siguen dependiendo del modelo local y hardware.
