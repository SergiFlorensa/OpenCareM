# ADR-0056: Soporte Operativo de Geriatria y Fragilidad para Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

Faltaba una capa geriatrica dedicada para resolver de forma trazable:

- diferenciacion entre hallazgos de envejecimiento y red flags reales,
- riesgo metabolico por inmovilidad y balance nitrogenado negativo,
- seguridad en delirium (incluyendo bloqueo de benzodiacepinas),
- optimizacion START v3 en poblacion mayor.

## Decision

Crear el workflow `geriatrics_support_v1` y exponerlo mediante:

- `POST /api/v1/care-tasks/{task_id}/geriatrics/recommendation`

Persistir trazas en `agent_runs/agent_steps` con `run_output.geriatrics_support`.

Agregar metricas Prometheus:

- `geriatrics_support_runs_total`
- `geriatrics_support_runs_completed_total`
- `geriatrics_support_critical_alerts_total`

## Consecuencias

### Positivas

- Estandariza reglas operativas geriatrico-funcionales en urgencias.
- Refuerza seguridad en delirium y prescripcion en fragilidad.
- Mejora observabilidad sin nuevas tablas ni migraciones.

### Riesgos

- Riesgo de uso como diagnostico definitivo sin validacion humana.
- Dependencia de calidad de datos funcionales/cognitivos de entrada.
- Necesidad de calibracion local de umbrales y rutas farmaco-clinicas.

## Mitigaciones

- Advertencia explicita de no diagnostico en salida.
- Validacion humana obligatoria.
- Revision periodica por equipo de geriatria y comite de seguridad clinica.
