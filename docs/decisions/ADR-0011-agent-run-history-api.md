# ADR-0011: API de historial para ejecuciones de agentes

## Contexto

Ya persistimos `AgentRun` y `AgentStep`, pero faltaba una forma simple de consultar esa informacion desde API para operacion diaria.

## Decision

Agregar endpoints de lectura:

- `GET /api/v1/agents/runs`
- `GET /api/v1/agents/runs/{run_id}`

El primero devuelve resumen para monitoreo rapido y el segundo detalle completo para debugging.

## Consecuencias

Beneficios:

- Mejor observabilidad operativa de workflows agentes.
- Menor dependencia de acceso directo a base de datos.
- Base para paneles de historial y alertas.

Costes:

- Superficie adicional de API que mantener y testear.

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_agents_api.py`



