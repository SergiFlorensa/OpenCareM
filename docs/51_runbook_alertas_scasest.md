# Runbook de Alertas SCASEST

## Objetivo

Definir una respuesta operativa simple cuando salten alertas de calidad SCASEST.

## Alertas cubiertas

- `ScasestAuditUnderRateHigh`
- `ScasestAuditOverRateHigh`

## Umbrales actuales

- `under_rate > 10%` durante `2m`
- `over_rate > 20%` durante `2m`

## Diagnostico rapido (5 minutos)

1. Confirmar valor actual:
   - `GET /metrics`
   - buscar `scasest_audit_under_rate_percent` y `scasest_audit_over_rate_percent`.
2. Ver volumen de base:
   - `scasest_audit_total` (si es bajo, interpretar con cautela).
3. Revisar detalle por caso:
   - `GET /api/v1/care-tasks/{task_id}/scasest/audit`
   - `GET /api/v1/care-tasks/{task_id}/scasest/audit/summary`

## Acciones recomendadas por tipo de alerta

### Under-rate alto (`under_scasest_risk`)

- Riesgo: la IA está siendo conservadora y puede infrapriorizar.
- Acciones:
  - revisar reglas de `high_risk_scasest` y `escalation_actions`,
  - auditar casos con `hemodynamic_instability`, `arrhythmias`, `grace_score > 140`,
  - reforzar validación humana inmediata en guardia.

### Over-rate alto (`over_scasest_risk`)

- Riesgo: sobreescalado y carga operativa innecesaria.
- Acciones:
  - revisar criterios que disparan alto riesgo sin soporte suficiente,
  - comparar con troponina/ECG y validación clínica final,
  - ajustar umbrales para reducir falsos positivos.

## Criterio de cierre

Cerrar incidencia cuando:

- la alerta vuelve a `inactive`,
- y el porcentaje permanece por debajo del umbral al menos 30 minutos.

## Nota de seguridad

Estas alertas son de calidad operativa del asistente, no de diagnóstico clínico.
