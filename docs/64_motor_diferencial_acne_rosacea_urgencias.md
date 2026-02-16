# TM-070 - Motor diferencial acne/rosacea en urgencias

## Problema que resuelve

En triage/consulta inicial, lesiones inflamatorias faciales se confunden entre acne y rosacea. El error de clasificacion impacta en tratamiento inicial y seguridad farmacologica.

El objetivo es entregar una recomendacion operativa interpretable con:

- hipotesis principal y subtipo probable,
- nivel de severidad,
- escalado terapeutico inicial,
- checklist de monitorizacion para isotretinoina,
- red flags de derivacion urgente.

## Cambios implementados

- Nuevo schema:
  - `app/schemas/acne_rosacea_protocol.py`
- Nuevo servicio:
  - `app/services/acne_rosacea_protocol_service.py`
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/acne-rosacea/recommendation`
  - `app/api/care_tasks.py`
- Nuevo workflow trazable:
  - `workflow_name=acne_rosacea_differential_support_v1`
  - `app/services/agent_run_service.py`
- Nuevas metricas:
  - `acne_rosacea_differential_runs_total`
  - `acne_rosacea_differential_runs_completed_total`
  - `acne_rosacea_differential_red_flags_total`
  - `app/metrics/agent_metrics.py`

## Contrato de salida (resumen)

- `most_likely_condition`
- `suspected_subtype`
- `severity_level`
- `differential_diagnoses`
- `supporting_findings`
- `initial_management`
- `pharmacologic_considerations`
- `isotretinoin_monitoring_checklist`
- `urgent_red_flags`
- `follow_up_recommendations`
- `human_validation_required`
- `non_diagnostic_warning`

## Validacion ejecutada

- `.\venv\Scripts\python.exe -m py_compile app/schemas/acne_rosacea_protocol.py app/services/acne_rosacea_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/acne_rosacea_protocol.py app/services/acne_rosacea_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k acne_rosacea_differential`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k acne_rosacea_differential`

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza evaluacion dermatologica presencial.
- El checklist de isotretinoina orienta, pero no sustituye protocolo institucional.
- Reglas de severidad/subtipo requieren ajuste con validacion clinica local.
