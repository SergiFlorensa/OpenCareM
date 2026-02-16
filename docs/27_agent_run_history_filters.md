# Filtros de Historial de Ejecuciones de Agente

## Objetivo

Permitir busqueda operativa de corridas agente sin revisar toda la lista manualmente.

## Endpoint

- `GET /api/v1/agents/runs`

## Filtros disponibles

- `status`: filtra por estado (`completed`, `failed`, etc.).
- `workflow_name`: filtra por workflow exacto.
- `created_from`: devuelve corridas creadas desde fecha/hora (ISO 8601).
- `created_to`: devuelve corridas hasta fecha/hora (ISO 8601).
- `limit`: maximo de resultados (1 a 100, default 20).

## Ejemplos

1. Solo fallidos:
- `/api/v1/agents/runs?status=failed`

2. Solo un workflow:
- `/api/v1/agents/runs?workflow_name=task_triage_v1`

3. Ventana temporal:
- `/api/v1/agents/runs?created_from=2026-02-10T00:00:00Z&created_to=2026-02-10T23:59:59Z`

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_agents_api.py`


