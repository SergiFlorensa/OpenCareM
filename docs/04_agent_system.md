# Sistema de Agentes

Este proyecto usa un esquema de agentes especializados con handoff por artefactos.

## Objetivo

- Reducir cambios ambiguos.
- Mantener trazabilidad entre analisis, implementacion y validacion.
- Reutilizar contexto entre tareas sin perder calidad.

## Agentes definidos

- `orchestrator`: define alcance y orden de ejecucion.
- `api-agent`: diseÃ±a y modifica endpoints/schemas.
- `data-agent`: evoluciona modelos, DB y migraciones.
- `mcp-agent`: mantiene server MCP y contrato de tools.
- `qa-agent`: define y ejecuta estrategia de pruebas.
- `devops-agent`: container, CI/CD, despliegue y observabilidad.

## Flujo de colaboracion

1. `orchestrator` crea plan en `agents/shared/TASK_BOARD.md`.
2. `api-agent` propone contrato en `agents/shared/api_contract.md`.
3. `data-agent` valida impacto en modelo/DB y actualiza `agents/shared/data_contract.md`.
4. `mcp-agent` adapta tools y registra cambios en `agents/shared/mcp_contract.md`.
5. `qa-agent` define casos y evidencia en `agents/shared/test_plan.md`.
6. `devops-agent` documenta ejecucion/entorno en `agents/shared/deploy_notes.md`.
7. `orchestrator` cierra decision en `docs/decisions/`.

## Regla principal de handoff

Cada agente debe consumir el output del anterior y dejar un output minimo estructurado:

- Contexto recibido.
- Cambios propuestos.
- Comandos de validacion.
- Riesgos abiertos.



