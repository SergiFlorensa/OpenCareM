# Auditoria de Calidad SCASEST

## Objetivo

Medir la calidad del soporte operativo SCASEST comparando:

- recomendacion de IA,
- validacion humana final.

La meta es detectar desviaciones operativas (`under`/`over`) y mejorar seguridad del flujo.

## Endpoints

- `POST /api/v1/care-tasks/{task_id}/scasest/audit`
- `GET /api/v1/care-tasks/{task_id}/scasest/audit`
- `GET /api/v1/care-tasks/{task_id}/scasest/audit/summary`

## Entrada (`CareTaskScasestAuditRequest`)

- `agent_run_id`
- `human_validated_high_risk_scasest`
- `human_escalation_required`
- `human_immediate_antiischemic_strategy`
- `reviewed_by`, `reviewer_note` (opcionales)

## Salida (`CareTaskScasestAuditResponse`)

- riesgo IA (`ai_high_risk_scasest`) vs humano (`human_validated_high_risk_scasest`)
- `classification`:
  - `match`
  - `under_scasest_risk`
  - `over_scasest_risk`
- coincidencia por reglas clave:
  - `escalation_required`
  - `immediate_antiischemic_strategy`

## Reglas de clasificacion

- `match`: IA y humano coinciden en riesgo global.
- `under_scasest_risk`: IA marcó menos riesgo que humano.
- `over_scasest_risk`: IA marcó más riesgo que humano.

## Metricas Prometheus

- `scasest_audit_total`
- `scasest_audit_match_total`
- `scasest_audit_under_total`
- `scasest_audit_over_total`
- `scasest_audit_under_rate_percent`
- `scasest_audit_over_rate_percent`
- `scasest_rule_escalation_match_rate_percent`
- `scasest_rule_immediate_antiischemic_match_rate_percent`

## Validacion recomendada

1. Crear `care-task`.
2. Ejecutar `POST /scasest/recommendation`.
3. Registrar auditoria con `POST /scasest/audit`.
4. Consultar resumen `GET /scasest/audit/summary`.
5. Confirmar series en `GET /metrics`.

## Limites

- No reemplaza decision clinica humana.
- Evalua calidad operativa de soporte, no efectividad clinica real.
