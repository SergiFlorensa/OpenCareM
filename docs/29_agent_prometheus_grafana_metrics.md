# Metricas de Agentes en Prometheus + Grafana

## Objetivo

Visualizar salud de agentes en dashboard sin depender de consultas manuales a endpoints JSON.

## Metricas nuevas en `/metrics`

- `agent_runs_total`
- `agent_runs_completed_total`
- `agent_runs_failed_total`
- `agent_steps_fallback_total`
- `agent_fallback_rate_percent`

Metricas globales de calidad IA clinica:

- `care_task_quality_audit_total`
- `care_task_quality_audit_match_total`
- `care_task_quality_audit_under_total`
- `care_task_quality_audit_over_total`
- `care_task_quality_audit_under_rate_percent`
- `care_task_quality_audit_over_rate_percent`
- `care_task_quality_audit_match_rate_percent`

Metricas de soporte cardiovascular:

- `cardio_risk_support_runs_total`
- `cardio_risk_support_runs_completed_total`
- `cardio_risk_support_alerts_total`
- `cardio_risk_audit_total`
- `cardio_risk_audit_match_total`
- `cardio_risk_audit_under_total`
- `cardio_risk_audit_over_total`
- `cardio_risk_audit_under_rate_percent`
- `cardio_risk_audit_over_rate_percent`
- `cardio_risk_rule_non_hdl_target_match_rate_percent`
- `cardio_risk_rule_pharmacologic_strategy_match_rate_percent`
- `cardio_risk_rule_intensive_lifestyle_match_rate_percent`

Metricas de soporte de reanimacion:

- `resuscitation_protocol_runs_total`
- `resuscitation_protocol_runs_completed_total`
- `resuscitation_protocol_alerts_total`
- `resuscitation_audit_total`
- `resuscitation_audit_match_total`
- `resuscitation_audit_under_total`
- `resuscitation_audit_over_total`
- `resuscitation_audit_under_rate_percent`
- `resuscitation_audit_over_rate_percent`
- `resuscitation_rule_shock_match_rate_percent`
- `resuscitation_rule_reversible_causes_match_rate_percent`
- `resuscitation_rule_airway_plan_match_rate_percent`

## Paneles nuevos en Grafana

En `Resumen API Gestor de Tareas`:

1. `Total de Ejecuciones de Agente`
2. `Ejecuciones Fallidas de Agente`
3. `Tasa de Fallback de Agente %`
4. `Pasos con Fallback de Agente`

Bloque SCASEST (calidad operativa):

5. `SCASEST Runs Total`
6. `SCASEST Under Rate %`
7. `SCASEST Over Rate %`
8. `SCASEST Escalation Match %`

Bloque Calidad Global IA:

9. `Calidad Global Audit Total`
10. `Calidad Global Under Rate %`
11. `Calidad Global Over Rate %`
12. `Calidad Global Match Rate %`

Bloque Reanimacion (calidad operativa):

13. `Reanimacion Runs Total`
14. `Reanimacion Under Rate %`
15. `Reanimacion Over Rate %`
16. `Reanimacion Shock Match %`

## Como validar rapido

1. Generar corridas:
   - `POST /api/v1/agents/run`
2. Ver metricas crudas:
   - `GET /metrics` y buscar `agent_`
3. Abrir Grafana:
   - `http://127.0.0.1:3000`
4. Revisar dashboard:
   - `Resumen API Gestor de Tareas`
5. Si un panel `stat/gauge` se queda en 0 pese a tener datos:
   - verificar que el target tenga `instant=true` (ya versionado en dashboard v3)
   - reiniciar stack para reprovisionar dashboard (`docker compose up --build`)

## Interpretacion operativa simple

- `failed_runs > 0`: hay corridas que terminaron con error.
- `fallback_rate_percent` alto: el sistema usa demasiado plan B y puede estar degradado.
- `fallback_steps` creciente: revisar reglas/provider.



