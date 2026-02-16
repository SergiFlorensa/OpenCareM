# ADR-0054: Soporte Operativo de Nefrologia para Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

Faltaba una capa nefrologica dedicada para resolver de forma trazable:

- crisis de fracaso renal agudo con clasificacion sindromica,
- escenarios renopulmonares de alta mortalidad,
- criterios AEIOU para dialisis urgente,
- seguridad de nefroproteccion y farmacoterapia asociada.

## Decision

Crear el workflow `nephrology_support_v1` y exponerlo mediante:

- `POST /api/v1/care-tasks/{task_id}/nephrology/recommendation`

Persistir trazas en `agent_runs/agent_steps` con `run_output.nephrology_support`.

Agregar metricas Prometheus:

- `nephrology_support_runs_total`
- `nephrology_support_runs_completed_total`
- `nephrology_support_critical_alerts_total`

## Consecuencias

### Positivas

- Estandariza reglas operativas nefrologicas en urgencias.
- Refuerza deteccion de riesgo vital en sindromes renopulmonares y AEIOU.
- Mejora observabilidad sin nuevas tablas ni migraciones.

### Riesgos

- Riesgo de uso como diagnostico definitivo fuera de contexto clinico.
- Dependencia de disponibilidad local de laboratorio, imagen y dialisis.
- Necesidad de calibracion local para umbrales de activacion.

## Mitigaciones

- Advertencia explicita de no diagnostico en salida.
- Validacion humana obligatoria.
- Revision periodica de reglas por equipo clinico local.
