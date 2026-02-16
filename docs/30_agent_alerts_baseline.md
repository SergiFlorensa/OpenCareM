# Base Inicial de Alertas de Agentes

## Objetivo

Activar alertas minimas para detectar problemas de salud en workflows de agentes.

## Reglas configuradas

Archivo: `ops/prometheus/alerts.yml`

1. `AgentRunsFailedDetected`
- Condicion: `sum(agent_runs_failed_total) > 0`
- Ventana: `for: 1m`
- Significado: existe al menos una corrida fallida.

2. `AgentFallbackRateHigh`
- Condicion: `sum(agent_fallback_rate_percent) > 10`
- Ventana: `for: 2m`
- Significado: el sistema esta usando fallback en exceso.

3. `ScasestAuditUnderRateHigh`
- Condicion: `sum(scasest_audit_under_rate_percent) > 10`
- Ventana: `for: 2m`
- Significado: la IA SCASEST esta quedandose corta (infra-riesgo) con frecuencia alta.

4. `ScasestAuditOverRateHigh`
- Condicion: `sum(scasest_audit_over_rate_percent) > 20`
- Ventana: `for: 2m`
- Significado: la IA SCASEST esta sobreescalando en exceso.

5. `CardioRiskAuditUnderRateHigh`
- Condicion: `sum(cardio_risk_audit_under_rate_percent) > 10`
- Ventana: `for: 2m`
- Significado: el soporte cardiovascular esta infrapriorizando riesgo con frecuencia alta.

6. `CardioRiskAuditOverRateHigh`
- Condicion: `sum(cardio_risk_audit_over_rate_percent) > 20`
- Ventana: `for: 2m`
- Significado: el soporte cardiovascular esta sobreescalando riesgo en exceso.

7. `ResuscitationAuditUnderRateHigh`
- Condicion: `sum(resuscitation_audit_under_rate_percent) > 10`
- Ventana: `for: 2m`
- Significado: el soporte de reanimacion esta infrapriorizando severidad con frecuencia alta.

8. `ResuscitationAuditOverRateHigh`
- Condicion: `sum(resuscitation_audit_over_rate_percent) > 20`
- Ventana: `for: 2m`
- Significado: el soporte de reanimacion esta sobreescalando severidad en exceso.

9. `CareTaskQualityUnderRateHigh`
- Condicion: `sum(care_task_quality_audit_under_rate_percent) > 10`
- Ventana: `for: 2m`
- Significado: el scorecard global muestra infrapriorizacion agregada.

10. `CareTaskQualityOverRateHigh`
- Condicion: `sum(care_task_quality_audit_over_rate_percent) > 20`
- Ventana: `for: 2m`
- Significado: el scorecard global muestra sobreescalado agregado.

11. `CareTaskQualityMatchRateLow`
- Condicion: `sum(care_task_quality_audit_match_rate_percent) < 80 and sum(care_task_quality_audit_total) >= 10`
- Ventana: `for: 3m`
- Significado: baja coherencia global IA vs validacion humana.

## Donde se cargan

- Prometheus incluye reglas via `rule_files` en `ops/prometheus/prometheus.yml`.
- Docker Compose monta `alerts.yml` dentro del contenedor Prometheus.

## Como validarlo

1. Levantar stack:
- `docker compose up --build`

2. Revisar reglas en Prometheus:
- `http://127.0.0.1:9090/rules`

3. Revisar alertas activas:
- `http://127.0.0.1:9090/alerts`

## Guia rapida

Si `AgentRunsFailedDetected` se activa:
- revisar `GET /api/v1/agents/runs?status=failed`
- inspeccionar detalle con `GET /api/v1/agents/runs/{run_id}`

Si `AgentFallbackRateHigh` se activa:
- revisar `GET /api/v1/agents/ops/summary`
- analizar `source` y `fallback_used` en corridas recientes
- evaluar regresion de provider/keywords

Si salta una alerta SCASEST:
- seguir `docs/51_runbook_alertas_scasest.md`

Si salta una alerta de calidad cardiovascular:
- revisar `GET /api/v1/care-tasks/{id}/cardio-risk/audit/summary`
- revisar muestras de `under_cardio_risk` y `over_cardio_risk`
- ajustar umbrales/criterios de estratificacion

Si salta una alerta de calidad de reanimacion:
- revisar `GET /api/v1/care-tasks/{id}/resuscitation/audit/summary`
- revisar muestras de `under_resuscitation_risk` y `over_resuscitation_risk`
- contrastar con cumplimiento de RCP/choque/causas reversibles y entrenamiento operativo

Si salta una alerta de calidad global:
- seguir `docs/54_runbook_alertas_calidad_global.md`



