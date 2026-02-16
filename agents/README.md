# Espacio de Agentes

Este directorio define roles de agentes y su mecanismo de colaboracion.

## Objetivo

- Separar responsabilidades por especialidad.
- Evitar perdida de contexto entre tareas.
- Tener handoff explicito y trazable.

## Roles

- `orchestrator.md`
- `api-agent.md`
- `data-agent.md`
- `mcp-agent.md`
- `qa-agent.md`
- `devops-agent.md`

## Comparticion de contexto

Todos los agentes leen y escriben en `agents/shared/`.

Orden recomendado:

1. `agents/shared/TASK_BOARD.md`
2. `agents/shared/api_contract.md`
3. `agents/shared/data_contract.md`
4. `agents/shared/mcp_contract.md`
5. `agents/shared/test_plan.md`
6. `agents/shared/deploy_notes.md`

## Regla de handoff

Antes de pasar a otro agente, completar `agents/shared/HANDOFF_TEMPLATE.md`.






