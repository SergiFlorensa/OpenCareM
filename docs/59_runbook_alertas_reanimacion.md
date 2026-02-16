# Runbook de Alertas de Reanimacion

## Objetivo

Definir respuesta operativa cuando se degrada la calidad IA vs humano en soporte de reanimacion.

## Alertas cubiertas

- `ResuscitationAuditUnderRateHigh`
- `ResuscitationAuditOverRateHigh`

## Umbrales actuales

- `under_rate > 10%` durante `2m`
- `over_rate > 20%` durante `2m`

## Diagnostico rapido (5 minutos)

1. Confirmar resumen del caso:
   - `GET /api/v1/care-tasks/{id}/resuscitation/audit/summary`
2. Confirmar metricas:
   - `GET /metrics`
   - buscar `resuscitation_audit_` y `resuscitation_protocol_`
3. Revisar trazas de ejecucion:
   - `GET /api/v1/agents/runs/{run_id}`
   - workflow esperado: `resuscitation_protocol_support_v1`
4. Revisar scorecard global:
   - `GET /api/v1/care-tasks/quality/scorecard`

## Acciones recomendadas por alerta

### `ResuscitationAuditUnderRateHigh`

- Riesgo: el sistema esta subestimando severidad en escenarios criticos.
- Acciones:
  - revisar casos con `classification=under_resuscitation_risk`,
  - reforzar criterios de inestabilidad y choque en validacion humana,
  - verificar que `shock_recommended` y `cpr_quality_ok` se usan correctamente.

### `ResuscitationAuditOverRateHigh`

- Riesgo: sobreescalado operativo y carga innecesaria sobre criticos.
- Acciones:
  - revisar casos con `classification=over_resuscitation_risk`,
  - ajustar umbrales de severidad en escenarios con pulso,
  - validar coherencia de recomendaciones de ventilacion y causas reversibles.

## Criterio de cierre

Cerrar incidencia cuando:

- alerta vuelve a `inactive`,
- y la tasa se mantiene bajo umbral al menos 30 minutos.

## Nota de seguridad

Este soporte es operativo y no diagnostico; siempre requiere validacion clinica humana inmediata.
