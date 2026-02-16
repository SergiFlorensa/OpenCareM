# ADR-0012: Filtrado operativo en historial de corridas agente

## Contexto

Con el crecimiento de corridas, listar todo sin filtros reduce utilidad para operaciones y debugging.

## Decision

Extender `GET /api/v1/agents/runs` con filtros:

- `status`
- `workflow_name`
- `created_from`
- `created_to`
- `limit`

## Consecuencias

Beneficios:

- Diagnostico mas rapido de incidentes.
- Mejor base para paneles operativos.
- Menor ruido en consultas manuales.

Costes:

- Mayor superficie de validacion en API.
- Necesidad de mantener ejemplos de uso en docs/runbooks.

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_agents_api.py`



