# ADR-0018: Triaje de agente ligado a recurso `CareTask`

- Estado: aceptado
- Fecha: 2026-02-11

## Contexto

La base ya tenia:

- Recurso `CareTask` para dominio clinico-operativo.
- Flujo general de agentes en `POST /api/v1/agents/run`.
- Persistencia de trazas en `agent_runs` y `agent_steps`.

Faltaba un punto de entrada directo para ejecutar triaje sobre un caso clinico-operativo existente sin reconstruir manualmente payloads.

## Decision

Se incorpora endpoint orientado a recurso:

- `POST /api/v1/care-tasks/{task_id}/triage`

El endpoint:

- Lee el `CareTask`.
- Ejecuta workflow dedicado `care_task_triage_v1`.
- Persiste traza completa reutilizando `agent_runs` y `agent_steps`.
- Devuelve `care_task_id`, `agent_run_id`, `workflow_name` y `triage`.

## Consecuencias

Positivas:

- Menor friccion operativa para ejecutar triaje sobre casos reales.
- Trazabilidad natural entre caso (`care_task_id`) y corrida (`agent_run_id`).
- Reutilizacion de infraestructura existente de observabilidad.

Riesgos:

- Falta flujo de aprobacion humana posterior al triaje.
- Falta historial de cambios de prioridad a nivel de negocio.
