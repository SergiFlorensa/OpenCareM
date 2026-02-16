# Project Agent Rules

Estas reglas aplican a todo el repositorio.

## Prioridad de lectura

1. `docs/README.md`
2. `docs/01_current_state.md`
3. `agents/README.md`
4. `agents/shared/TASK_BOARD.md`

## Flujo obligatorio

1. Registrar objetivo y alcance en `agents/shared/TASK_BOARD.md`.
2. Pasar por contratos de handoff segun el tipo de cambio:
   - API: `agents/shared/api_contract.md`
   - Datos: `agents/shared/data_contract.md`
   - MCP: `agents/shared/mcp_contract.md`
   - QA: `agents/shared/test_plan.md`
   - DevOps: `agents/shared/deploy_notes.md`
3. Registrar decisiones estructurales en `docs/decisions/`.

## Criterios de calidad

- No hacer cambios sin plan de validacion.
- No cerrar una tarea sin riesgos pendientes identificados.
- Mantener documentacion y codigo alineados en el mismo cambio.

