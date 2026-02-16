# TM-045 - Motor de Protocolo Respiratorio Operativo

## Objetivo

Agregar un motor de recomendaciones operativas para urgencias respiratorias que:

- priorice tiempos (triaje, prueba, aislamiento, antiviral),
- sea trazable como workflow de agente,
- y no emita diagnostico medico automatizado.

## Que se implemento

### Endpoint nuevo

- `POST /api/v1/care-tasks/{task_id}/respiratory-protocol/recommendation`

Entrada: `RespiratoryProtocolRequest` (edad, inmunosupresion, comorbilidades, antigeno, sospecha de patogeno, etc.).

Salida: `CareTaskRespiratoryProtocolResponse` con:

- `agent_run_id`
- `workflow_name=respiratory_protocol_v1`
- `recommendation` (plan diagnostico, antiviral, aislamiento y alertas).

### Servicio de reglas

Archivo: `app/services/respiratory_protocol_service.py`

Reglas principales:

- deteccion de paciente vulnerable,
- sospecha de shock relativo (en perfil hipertenso basal),
- escalado de antigeno negativo a PCR en perfil de riesgo,
- recomendacion de antiviral por ventana temporal y patogeno sospechado,
- alertas operativas y warning explicito de validacion clinica humana.

### Trazabilidad en motor de agentes

Archivo: `app/services/agent_run_service.py`

Se agrega `run_respiratory_protocol_workflow(...)` para persistir:

- corrida en `agent_runs` (`workflow_name=respiratory_protocol_v1`),
- paso en `agent_steps` (`step_name=respiratory_protocol_assessment`),
- entrada/salida del protocolo para auditoria.

### Observabilidad

Archivo: `app/metrics/agent_metrics.py`

Metricas nuevas:

- `respiratory_protocol_runs_total`
- `respiratory_protocol_runs_completed_total`

## Validacion ejecutada

- `.\venv\Scripts\ruff.exe check app/services/agent_run_service.py app/services/respiratory_protocol_service.py app/tests/test_care_tasks_api.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests`

## Riesgos pendientes

- Falta calibrar umbrales clinicos con especialistas de urgencias.
- Falta versionar reglas por centro/hospital para evitar sesgo local.
- Falta panel dedicado en Grafana para seguimiento de este workflow por especialidad y turno.
