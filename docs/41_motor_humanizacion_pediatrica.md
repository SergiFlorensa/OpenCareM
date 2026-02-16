# TM-046 - Motor de Humanizacion Pediatrica

## Objetivo

Agregar un motor operativo para casos pediatricos de alta complejidad que:

- ordene acciones de comunicacion con familia,
- active soporte psicosocial y multidisciplinar,
- y deje trazabilidad completa para revision humana.

## Endpoint nuevo

- `POST /api/v1/care-tasks/{task_id}/humanization/recommendation`

Entrada: `HumanizationProtocolRequest`.

Salida: `CareTaskHumanizationProtocolResponse` con:

- `agent_run_id`
- `workflow_name=pediatric_neuro_onco_support_v1`
- `recommendation` (planes de comunicacion, familia, soporte, coordinacion, equipo y alertas).

## Reglas que aplica

Archivo: `app/services/humanization_protocol_service.py`

Bloques principales:

- plan de comunicacion clara y confirmacion de comprension familiar,
- integracion de familia como co-terapeuta,
- activacion de soporte social, espiritual o psicologico segun riesgo,
- coordinacion para contexto neuro-oncologico y ensayos clinicos,
- medidas de cuidado de equipo y prevencion de desgaste profesional.

## Trazabilidad de agente

Archivo: `app/services/agent_run_service.py`

Se persiste una corrida con:

- `workflow_name=pediatric_neuro_onco_support_v1`
- paso `humanization_operational_assessment`
- `run_input` y `run_output` para auditoria.

## Metricas Prometheus

Archivo: `app/metrics/agent_metrics.py`

Series nuevas:

- `pediatric_humanization_runs_total`
- `pediatric_humanization_runs_completed_total`

## Validacion ejecutada

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests`

## Limites y seguridad

- El motor no diagnostica ni sustituye criterio medico.
- La salida marca validacion humana obligatoria.
- Los datos de ejemplo no incluyen informacion clinica identificable real.
