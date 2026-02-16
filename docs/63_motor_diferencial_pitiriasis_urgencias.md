# TM-069 - Motor diferencial de pitiriasis en urgencias

## Problema que resuelve

En consulta de urgencias/atencion inicial, las lesiones descamativas hipocromicas pueden confundirse entre:

- Pitiriasis versicolor (fúngica, recidivante).
- Pitiriasis rosada (exantema agudo autolimitado).
- Pitiriasis alba (curso cronico pediatrico).

El objetivo es ordenar el diferencial de forma interpretable y activar red flags que obligan a descartar diagnósticos alternativos de mayor riesgo (ej. lepra tuberculoide, celulitis/erisipela).

## Cambios implementados

- Nuevo schema:
  - `app/schemas/pityriasis_protocol.py`
- Nuevo servicio de reglas:
  - `app/services/pityriasis_protocol_service.py`
- Nuevo endpoint por CareTask:
  - `POST /api/v1/care-tasks/{task_id}/pityriasis-differential/recommendation`
  - Archivo: `app/api/care_tasks.py`
- Persistencia de traza de workflow:
  - `workflow_name=pityriasis_differential_support_v1`
  - Archivo: `app/services/agent_run_service.py`
- Metricas Prometheus:
  - `pityriasis_differential_runs_total`
  - `pityriasis_differential_runs_completed_total`
  - `pityriasis_differential_red_flags_total`
  - Archivo: `app/metrics/agent_metrics.py`

## Contrato de salida (resumen)

La recomendacion devuelve:

- `most_likely_condition` (`pitiriasis_versicolor` | `pitiriasis_rosada` | `pitiriasis_alba` | `indeterminado`)
- `differential_diagnoses`
- `supporting_findings`
- `recommended_tests`
- `initial_management`
- `urgent_red_flags`
- `follow_up_recommendations`
- `human_validation_required`
- `non_diagnostic_warning`

## Validacion ejecutada

- `.\venv\Scripts\python.exe -m py_compile app/schemas/pityriasis_protocol.py app/services/pityriasis_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/pityriasis_protocol.py app/services/pityriasis_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k pityriasis_differential`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k pityriasis_differential`

## Riesgos pendientes

- El motor es soporte operativo; no sustituye diagnostico dermatologico presencial.
- Los umbrales de reglas deben recalibrarse con validacion clinica local para minimizar falsos positivos/negativos.
- Red flags (lepra/celulitis) son de priorizacion y requieren confirmacion diagnostica formal.
