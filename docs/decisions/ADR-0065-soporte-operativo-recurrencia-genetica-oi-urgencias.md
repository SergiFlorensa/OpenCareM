# ADR-0065: Soporte Operativo de Recurrencia Genetica en OI para Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

Faltaba una capa operativa trazable para casos de recurrencia de osteogenesis
imperfecta tipo II en parejas fenotipicamente sanas, donde el principal riesgo
de interpretacion era clasificar erronemente como de novo aislado.

Se necesitaba:

- priorizar mosaicismo germinal ante recurrencia dominante,
- registrar una alerta explicita de mosaicismo para la API,
- mantener trazabilidad completa en `agent_runs/agent_steps`,
- no introducir cambios de esquema en DB.

## Decision

Crear el workflow `genetic_recurrence_support_v1` y exponerlo mediante:

- `POST /api/v1/care-tasks/{task_id}/genetic-recurrence/recommendation`

Persistir trazas en `agent_runs/agent_steps` con
`run_output.genetic_recurrence_support`.

Agregar metricas Prometheus:

- `genetic_recurrence_support_runs_total`
- `genetic_recurrence_support_runs_completed_total`
- `genetic_recurrence_support_critical_alerts_total`

## Consecuencias

### Positivas

- Estandariza la regla operativa de "alerta de mosaicismo" en recurrencia dominante.
- Reduce riesgo de clasificar recurrencias repetidas como de novo aislado.
- Mejora explicabilidad con mecanismo priorizado, acciones de consejeria y bloqueos.

### Riesgos

- Riesgo de sobreinterpretacion si faltan datos moleculares o familiares.
- Variabilidad institucional en rutas de estudio genetico/prenatal.
- Necesidad de validacion humana obligatoria en decisiones asistenciales.

## Mitigaciones

- Salida marcada como no diagnostica.
- Bloqueos de seguridad ante inconsistencias y falta de confirmacion molecular.
- Validacion por genetica clinica y obstetricia como requisito operativo.
