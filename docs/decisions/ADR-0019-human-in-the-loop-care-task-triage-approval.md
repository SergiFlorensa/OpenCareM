# ADR-0019: Aprobacion humana obligatoria sobre triaje de CareTask

- Estado: aceptado
- Fecha: 2026-02-11

## Contexto

El sistema ya podia:

- ejecutar triaje en `CareTask`,
- guardar trazas de agente.

Pero faltaba registrar decision humana final sobre esa recomendacion.

## Decision

Se agrega:

- endpoint `POST /api/v1/care-tasks/{task_id}/triage/approve`,
- tabla `care_task_triage_reviews` para persistir aprobacion/rechazo.

Reglas:

- una corrida (`agent_run_id`) tiene una revision unica,
- la revision solo es valida si la corrida pertenece a ese `CareTask`,
- solo aplica a `workflow_name=care_task_triage_v1`.

## Consecuencias

Positivas:

- Se formaliza `human-in-the-loop`.
- Mejora auditoria y trazabilidad.
- Permite medir calidad real: recomendacion vs decision humana.

Coste:

- Nueva tabla y migracion.
- Mantenimiento de contrato adicional en API.
