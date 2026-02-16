# Resumen Operativo de Agentes

## Objetivo

Exponer una vista corta de salud operativa de agentes para monitoreo diario.

## Endpoint

- `GET /api/v1/agents/ops/summary`

## Parametros

- `workflow_name` (opcional): limita el resumen a un workflow.

## Respuesta

- `total_runs`
- `completed_runs`
- `failed_runs`
- `fallback_steps`
- `fallback_rate_percent`

## Ejemplo

`/api/v1/agents/ops/summary?workflow_name=task_triage_v1`

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_agents_api.py`


