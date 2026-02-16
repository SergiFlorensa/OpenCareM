# ADR-0053: Soporte Operativo de Endocrinologia para Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

Faltaba una capa endocrino-metabolica dedicada para resolver de forma trazable:

- emergencias bioquimicas con hipoglucemia hipocetosica,
- cribado estructurado de patologia tiroidea/suprarrenal,
- reglas de seguridad en SIADH e hiperprolactinemia,
- soporte operativo para estadiaje de DM1 y seleccion farmacologica.

## Decision

Crear el workflow `endocrinology_support_v1` y exponerlo mediante:

- `POST /api/v1/care-tasks/{task_id}/endocrinology/recommendation`

Persistir trazas en `agent_runs/agent_steps` con `run_output.endocrinology_support`.

Agregar metricas Prometheus:

- `endocrinology_support_runs_total`
- `endocrinology_support_runs_completed_total`
- `endocrinology_support_critical_alerts_total`

## Consecuencias

### Positivas

- Estandariza rutas operativas endocrinas de alta variabilidad.
- Refuerza seguridad al bloquear cribados incompletos en incidentaloma.
- Mejora trazabilidad y observabilidad sin nuevas migraciones.

### Riesgos

- Riesgo de sobrerreliance en reglas sin validacion clinica local.
- Dependencia de disponibilidad de laboratorio e imagen.
- Necesidad de calibrar umbrales operativos por centro.

## Mitigaciones

- Advertencia explicita de no diagnostico en la salida.
- Validacion humana obligatoria.
- Revision periodica de reglas por comite clinico local.
