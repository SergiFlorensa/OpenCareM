# ADR-0051: Soporte Operativo de Psiquiatria para Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

El proyecto carecia de un workflow psiquiatrico dedicado para:

- discriminar temporalmente respuestas post-trauma vs trastornos estructurados,
- priorizar riesgo suicida adolescente con reglas especificas de urgencias,
- reforzar seguridad farmacologica en embarazo y geriatria,
- integrar red flags internistas asociadas a TCA.

## Decision

Crear el workflow `psychiatry_support_v1` y exponerlo mediante:

- `POST /api/v1/care-tasks/{task_id}/psychiatry/recommendation`

Persistir trazas en `agent_runs/agent_steps` con `run_output.psychiatry_support`.

Agregar metricas Prometheus:

- `psychiatry_support_runs_total`
- `psychiatry_support_runs_completed_total`
- `psychiatry_support_critical_alerts_total`

## Consecuencias

### Positivas

- Estandariza soporte operativo en urgencias psiquiatricas.
- Refuerza seguridad en poblaciones vulnerables (adolescentes, embarazadas, ancianos).
- Mantiene trazabilidad y observabilidad sin introducir migraciones.

### Riesgos

- Riesgo de sobreinterpretacion si se usa como diagnostico definitivo.
- Sensibilidad/especificidad dependiente de calibracion local.
- Variabilidad inter-centro en criterios temporales y protocolos farmacologicos.

## Mitigaciones

- Advertencia explicita de no diagnostico en todas las respuestas.
- Validacion humana obligatoria para cualquier accion de alto impacto.
- Revision periodica de reglas por comite clinico local.
