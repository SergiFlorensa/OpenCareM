# Motor de Riesgo Cardiovascular Operativo

## Objetivo

Agregar soporte operativo para estratificacion inicial de riesgo cardiovascular en urgencias, con validacion humana obligatoria, auditoria IA vs humano y observabilidad completa.

No es un diagnostico medico autonomo.

## Endpoint de recomendacion

- `POST /api/v1/care-tasks/{task_id}/cardio-risk/recommendation`

### Entrada principal

- edad, sexo, tabaquismo
- tension sistolica
- colesterol no-HDL
- ApoB (opcional)
- diabetes, ERC, ECV aterosclerotica establecida
- antecedentes familiares y contexto inflamatorio

### Salida principal

- `risk_level`: `low|moderate|high|very_high`
- `estimated_10y_risk_percent`
- objetivos operativos: `ldl_target_mg_dl`, `non_hdl_target_mg_dl`
- banderas:
  - `non_hdl_target_required`
  - `pharmacologic_strategy_suggested`
  - `intensive_lifestyle_required`
- `priority_actions`, `additional_markers_recommended`, `alerts`
- `human_validation_required=true`

## Auditoria de calidad cardiovascular

- `POST /api/v1/care-tasks/{task_id}/cardio-risk/audit`
- `GET /api/v1/care-tasks/{task_id}/cardio-risk/audit`
- `GET /api/v1/care-tasks/{task_id}/cardio-risk/audit/summary`

Clasificacion:

- `match`
- `under_cardio_risk`
- `over_cardio_risk`

Resumen agrega precision por reglas:

- `non_hdl_target_required_match_rate_percent`
- `pharmacologic_strategy_match_rate_percent`
- `intensive_lifestyle_match_rate_percent`

## Trazabilidad de agente

- Workflow: `cardio_risk_support_v1`
- Paso: `cardio_risk_operational_assessment`
- Persistencia en:
  - `agent_runs`
  - `agent_steps`

## Metricas Prometheus

Workflow:

- `cardio_risk_support_runs_total`
- `cardio_risk_support_runs_completed_total`
- `cardio_risk_support_alerts_total`

Calidad:

- `cardio_risk_audit_total`
- `cardio_risk_audit_match_total`
- `cardio_risk_audit_under_total`
- `cardio_risk_audit_over_total`
- `cardio_risk_audit_under_rate_percent`
- `cardio_risk_audit_over_rate_percent`
- `cardio_risk_rule_non_hdl_target_match_rate_percent`
- `cardio_risk_rule_pharmacologic_strategy_match_rate_percent`
- `cardio_risk_rule_intensive_lifestyle_match_rate_percent`

## Alertas Prometheus

- `CardioRiskAuditUnderRateHigh` (`>10%`, 2m)
- `CardioRiskAuditOverRateHigh` (`>20%`, 2m)

## Validacion recomendada

```powershell
.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py app/tests/test_quality_regression_gate.py
```
