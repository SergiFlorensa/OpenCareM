# TM-048 - Auditoria de Calidad de Screening

## Objetivo

Cerrar el ciclo de calidad del screening avanzado comparando:

- recomendacion de IA operativa,
- validacion humana final,
- y precision por regla clinico-operativa.

## Endpoints nuevos

- `POST /api/v1/care-tasks/{task_id}/screening/audit`
- `GET /api/v1/care-tasks/{task_id}/screening/audit`
- `GET /api/v1/care-tasks/{task_id}/screening/audit/summary`

## Que guarda la auditoria

Tabla: `care_task_screening_audit_logs`

- riesgo global IA vs humano,
- clasificacion global: `match`, `under_screening`, `over_screening`,
- comparacion por reglas:
  - cribado VIH,
  - ruta sepsis,
  - sospecha COVID persistente,
  - candidato long-acting.

## Metricas nuevas en `/metrics`

- `screening_audit_total`
- `screening_audit_match_total`
- `screening_audit_under_total`
- `screening_audit_over_total`
- `screening_audit_under_rate_percent`
- `screening_audit_over_rate_percent`
- `screening_rule_hiv_match_rate_percent`
- `screening_rule_sepsis_match_rate_percent`
- `screening_rule_persistent_covid_match_rate_percent`
- `screening_rule_long_acting_match_rate_percent`

## Validacion ejecutada

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests`
- `.\venv\Scripts\ruff.exe check` en archivos Python modificados

## Migracion necesaria

- `.\venv\Scripts\alembic.exe upgrade head`

## Interpretacion operativa

- `under_screening` indica riesgo de infravalorar severidad.
- `over_screening` indica riesgo de sobrecargar recursos.
- Las tasas por regla permiten calibrar el motor de forma incremental y transparente.
