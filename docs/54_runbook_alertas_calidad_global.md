# Runbook de Alertas de Calidad Global IA Clinica

## Objetivo

Definir respuesta operativa cuando se degrada la calidad global IA vs humano.

## Alertas cubiertas

- `CareTaskQualityUnderRateHigh`
- `CareTaskQualityOverRateHigh`
- `CareTaskQualityMatchRateLow`

## Umbrales actuales

- `under_rate > 10%` durante `2m`
- `over_rate > 20%` durante `2m`
- `match_rate < 80%` durante `3m` y con `>= 10` auditorias

## Diagnostico rapido (5 minutos)

1. Confirmar scorecard:
   - `GET /api/v1/care-tasks/quality/scorecard`
2. Confirmar metricas:
   - `GET /metrics`
   - buscar `care_task_quality_audit_`
3. Revisar dominio con peor calidad:
   - `triage`: `GET /api/v1/care-tasks/{id}/triage/audit/summary`
   - `screening`: `GET /api/v1/care-tasks/{id}/screening/audit/summary`
   - `medicolegal`: `GET /api/v1/care-tasks/{id}/medicolegal/audit/summary`
   - `scasest`: `GET /api/v1/care-tasks/{id}/scasest/audit/summary`
   - `cardio_risk`: `GET /api/v1/care-tasks/{id}/cardio-risk/audit/summary`
   - `resuscitation`: `GET /api/v1/care-tasks/{id}/resuscitation/audit/summary`

## Acciones recomendadas por alerta

### `CareTaskQualityUnderRateHigh`

- Riesgo: infrapriorizacion agregada.
- Acciones:
  - revisar reglas conservadoras por dominio,
  - reforzar validacion humana en casos criticos,
  - auditar ejemplos recientes de `under`.

### `CareTaskQualityOverRateHigh`

- Riesgo: sobreescalado y carga operativa.
- Acciones:
  - revisar umbrales que disparan riesgo alto,
  - ajustar reglas para reducir falsos positivos,
  - validar impacto en tiempos de respuesta.

### `CareTaskQualityMatchRateLow`

- Riesgo: divergencia sistematica IA vs humano.
- Acciones:
  - revisar drift de criterios entre turnos/equipos,
  - alinear checklist operativo por dominio,
  - recalibrar reglas con casos auditados reales.

## Criterio de cierre

Cerrar incidencia cuando:

- alerta vuelve a `inactive`,
- y metricas permanecen bajo umbral al menos 30 minutos.

## Nota de seguridad

Estas alertas miden calidad operativa del asistente, no diagnostico clinico.
