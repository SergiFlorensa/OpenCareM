# Endpoints de Historial de Ejecuciones de Agente

## Objetivo

Poder revisar ejecuciones de agentes sin entrar manualmente a base de datos.

## Endpoints nuevos

1. `GET /api/v1/agents/runs`
- Lista corridas recientes.
- Query param: `limit` (1 a 100, default 20).
- Devuelve vista resumida (id, estado, latencia, coste, timestamps).

2. `GET /api/v1/agents/runs/{run_id}`
- Devuelve una corrida completa.
- Incluye `run_input`, `run_output` y `steps`.
- Si no existe, responde `404`.

## Por que aporta valor

- Operaciones puede ver rapidamente si el agente esta sano.
- QA puede depurar un caso concreto por `run_id`.
- Facilita crear dashboards y alertas basadas en estado de corridas.

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_agents_api.py`


