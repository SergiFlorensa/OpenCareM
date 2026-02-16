# ADR-0058: Soporte Operativo de Anestesiologia y Reanimacion para Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

Faltaba una capa anestesiologica dedicada para resolver de forma trazable:

- activacion de ISR por riesgo de aspiracion en estomago lleno,
- control operativo de tiempos y seguridad de via aerea (preoxigenacion,
  ventilacion manual, via IV y maniobra de Sellick),
- seleccion anatomica de bloqueos simpaticos para dolor complejo,
- priorizacion del ganglio impar en masa presacra con dolor perineal/pelvico.

## Decision

Crear el workflow `anesthesiology_support_v1` y exponerlo mediante:

- `POST /api/v1/care-tasks/{task_id}/anesthesiology/recommendation`

Persistir trazas en `agent_runs/agent_steps` con `run_output.anesthesiology_support`.

Agregar metricas Prometheus:

- `anesthesiology_support_runs_total`
- `anesthesiology_support_runs_completed_total`
- `anesthesiology_support_critical_alerts_total`

## Consecuencias

### Positivas

- Estandariza rutas operativas de ISR y analgesia intervencionista en urgencias.
- Mejora seguridad al bloquear conductas de riesgo en via aerea.
- Aporta trazabilidad y observabilidad sin cambios de esquema de base de datos.

### Riesgos

- Riesgo de uso como diagnostico definitivo sin validacion humana.
- Dependencia de calidad de datos sobre contexto de ayuno y topografia del dolor.
- Variabilidad de recursos locales para bloqueos intervencionistas guiados.

## Mitigaciones

- Advertencia explicita de no diagnostico en salida.
- Validacion humana obligatoria.
- Ajuste protocolizado con anestesia, reanimacion y urgencias locales.
