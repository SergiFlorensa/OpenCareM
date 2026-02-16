---
name: tm-orchestrator-workflow
description: "Orquesta cambios del repositorio con el flujo obligatorio de gobierno del proyecto: registrar alcance en TASK_BOARD, enrutar por contratos compartidos, ejecutar puertas de validacion y cerrar con evidencia y riesgos. Usar al implementar o planificar cambios no triviales, especialmente para solicitudes como 'siguiente paso', 'seguimos', 'haz el analisis', 'implementa', o cuando el alcance toque varias areas (API, datos, MCP, QA, DevOps)."
---

# TM Flujo de Orquestacion

## Vision general

Usa esta skill para imponer disciplina de ejecucion, no para reemplazar skills de dominio.
Conduce el proceso y llama skills especializadas cuando haga falta.

## Flujo

1. Lee contexto en este orden:
   - `docs/README.md`
   - `docs/01_current_state.md`
   - `agents/README.md`
   - `agents/shared/TASK_BOARD.md`
2. Registra objetivo y alcance en `agents/shared/TASK_BOARD.md` antes de tocar codigo.
3. Enruta el cambio por contratos compartidos segun tipo de cambio.
4. Ejecuta implementacion iterativa con pruebas y validacion.
5. Actualiza docs/decisiones en el mismo cambio.
6. Cierra la tarea con evidencia y riesgos pendientes explicitos.

## Enrutado de contratos

Carga `references/contract-routing.md` y actualiza los contratos compartidos relevantes:

- `agents/shared/api_contract.md`
- `agents/shared/data_contract.md`
- `agents/shared/mcp_contract.md`
- `agents/shared/test_plan.md`
- `agents/shared/deploy_notes.md`

## Puertas de validacion

Carga `references/quality-gates.md`.
Ejecuta primero checks dirigidos y despues puertas completas.
Nunca cierres la tarea sin evidencia reproducible.

## Reglas de cierre de tareas

Carga `references/task-lifecycle.md`.
Antes de marcar una tarea como completada, verifica:

- estado del tablero actualizado,
- evidencia con comandos/archivos,
- riesgos residuales registrados en docs o task board.

