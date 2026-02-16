# TM-044: Auditoria de over-triage y under-triage

## Que resuelve

Hasta ahora teniamos:

- recomendacion de triaje por IA,
- aprobacion humana del triaje.

Faltaba medir calidad de la recomendacion con una comparacion estructurada.

Con TM-044 se agrega auditoria persistida IA vs humano para clasificar:

- `match`
- `under_triage`
- `over_triage`

## Endpoints nuevos

- `POST /api/v1/care-tasks/{task_id}/triage/audit`
- `GET /api/v1/care-tasks/{task_id}/triage/audit`
- `GET /api/v1/care-tasks/{task_id}/triage/audit/summary`

## Modelo de datos

Tabla: `care_task_triage_audit_logs`

Campos clave:

- `care_task_id`
- `agent_run_id` (unico por corrida)
- `ai_recommended_level` (1..5)
- `human_validated_level` (1..5)
- `classification` (`match`, `under_triage`, `over_triage`)

## Regla de clasificacion

Como nivel 1 es mas urgente que nivel 5:

- `ai_level == human_level` -> `match`
- `ai_level > human_level` -> `under_triage` (IA menos urgente que humano)
- `ai_level < human_level` -> `over_triage` (IA mas urgente que humano)

## Inferencia de nivel IA

1. Si el run trae `triage_level`, se usa directamente.
2. Si no, se mapea por prioridad:
   - `critical -> 1`
   - `high -> 2`
   - `medium -> 3`
   - `low -> 4`
   - default: `3`

## Metricas Prometheus

Se exponen en `/metrics`:

- `triage_audit_total`
- `triage_audit_match_total`
- `triage_audit_under_total`
- `triage_audit_over_total`
- `triage_audit_under_rate_percent`
- `triage_audit_over_rate_percent`

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests`

Resultado final:

- `71 passed`
