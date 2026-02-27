# ADR-0135: Chat clinico asincrono con pausa/reanudacion (Plan B)

- Fecha: 2026-02-25
- Estado: Aprobada

## Contexto
En entorno local CPU, el flujo sincrono sufre `TimeoutError` y `BudgetExhausted` cuando
la inferencia LLM tarda mas que el presupuesto de request.

## Decision
Se agrega un canal asincrono para chat clinico:
1. `POST /api/v1/care-tasks/{task_id}/chat/messages/async` encola trabajo y devuelve `job_id`.
2. Worker local en memoria procesa el trabajo en segundo plano.
3. `GET /api/v1/care-tasks/{task_id}/chat/messages/async/{job_id}` expone estado y resultado.
4. El endpoint sincrono existente no cambia.

## Consecuencias
- Mejora UX en hardware modesto: evita bloquear request HTTP por inferencia larga.
- Mantiene trazabilidad clinica (mensaje persistido + `agent_run_id`) cuando el job finaliza.
- Limitacion conocida: cola en memoria (single-process), orientada a escala baja/local.

## Validacion
- `./venv/Scripts/python.exe -m ruff check app/services/clinical_chat_async_service.py app/api/care_tasks.py app/schemas/clinical_chat.py app/schemas/__init__.py app/services/__init__.py app/tests/test_care_tasks_api.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_care_tasks_api.py -k "chat_message_async" -o addopts=""`
