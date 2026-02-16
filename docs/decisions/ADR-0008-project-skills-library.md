# ADR-0008: Libreria de skills de proyecto para agentes

## Contexto

El proyecto tiene procesos repetitivos (orquestacion de tareas, entrega API, operacion de observabilidad)
que se ejecutan en muchas sesiones. Sin skills, estos flujos dependen demasiado del contexto conversacional.

## Decision

Crear una libreria local versionada en `skills/` con tres skills:

- `tm-orchestrator-workflow`
- `tm-api-change-delivery`
- `tm-observability-ops`

Disenar cada skill siguiendo patrones oficiales:

- frontmatter claro con triggers,
- progressive disclosure usando `references/`,
- validacion con `quick_validate.py`.

## Consecuencias

Beneficios:

- Mayor consistencia entre sesiones/agentes.
- Menor costo de contexto para instrucciones repetitivas.
- Mejor trazabilidad y onboarding de workflows.

Costes:

- Mantenimiento de skills cuando cambia el proceso del repo.
- Necesidad de iteracion para ajustar over/under-triggering.

## Validacion

- `quick_validate.py` en los 3 skills -> `Skill is valid!`



