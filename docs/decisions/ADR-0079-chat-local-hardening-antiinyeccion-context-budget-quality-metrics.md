# ADR-0079: Chat local endurecido con anti-inyeccion, presupuesto de contexto y metricas de calidad

## Contexto

El chat clinico local con Ollama ya estaba operativo, pero presentaba tres
riesgos relevantes para un despliegue open source sin pago por token:

- ausencia de capa explicita anti-prompt-injection en consulta de usuario,
- falta de control de presupuesto de contexto/tokens contra `num_ctx`,
- sin metricas de calidad por turno para seguimiento continuo.

Adicionalmente, el repositorio tenia conflictos de merge sin resolver en
servicios y contratos compartidos.

## Decision

Se decide implementar en backend:

- sanitizacion y deteccion de senales de inyeccion antes de construir prompt,
- constructor de mensajes con estimacion de tokens y truncado por presupuesto,
- metricas locales por turno (`answer_relevance`, `context_relevance`,
  `groundedness`, `quality_status`) expuestas en la respuesta de chat,
- limpieza de conflictos de merge pendientes en codigo y contratos.

## Consecuencias

Impacto positivo:

- menor superficie de ataque por inyeccion en prompts,
- menor riesgo de fallo por desborde de contexto en modelos locales,
- mayor observabilidad operativa de calidad conversacional por turno.

Coste/limitaciones:

- `quality_metrics` se basa en heuristicas lexicales y requiere calibracion.
- clientes con deserializacion estricta del schema anterior deben aceptar el
  nuevo bloque `quality_metrics`.

## Validacion

- `python -m py_compile app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/schemas/clinical_chat.py app/api/care_tasks.py app/tests/test_clinical_chat_operational.py app/tests/test_care_tasks_api.py`
- `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/schemas/clinical_chat.py app/api/care_tasks.py app/core/config.py app/tests/test_clinical_chat_operational.py app/tests/test_care_tasks_api.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat`
