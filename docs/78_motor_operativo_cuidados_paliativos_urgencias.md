# Motor Operativo de Cuidados Paliativos en Urgencias

## Problema

El sistema no tenia un motor paliativo dedicado para transformar
datos de urgencias en acciones operativas trazables sobre:

- distincion etico-legal entre rechazo informado, adecuacion terapeutica y ayuda para morir,
- seguridad de opioides en insuficiencia renal y manejo de dolor irruptivo,
- decisiones de confort en demencia avanzada con disfagia,
- deteccion temprana de neurotoxicidad opioide y manejo de delirium.

## Cambios implementados

- Nuevo schema: `app/schemas/palliative_support_protocol.py`.
- Nuevo servicio: `app/services/palliative_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/palliative/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=palliative_support_v1`
  - `step_name=palliative_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `palliative_support_runs_total`
  - `palliative_support_runs_completed_total`
  - `palliative_support_critical_alerts_total`

## Logica operativa cubierta

1. Decisiones eticas y marco de final de vida:
- Distingue rechazo del paciente (autonomia) de adecuacion del esfuerzo terapeutico
  (decision profesional por futilidad).
- Activa bloqueos de seguridad si falta documentacion de consentimiento informado
  o de fundamento de futilidad.
- Encauza solicitudes de ayuda para morir por circuito legal de LO 3/2021 y bloquea
  ejecucion fuera de formalizacion/reiteracion requeridas.

2. Seguridad opioide y funcion renal:
- Prioriza fentanilo/metadona/buprenorfina en insuficiencia renal.
- Emite alerta critica si existe morfina activa con riesgo renal por acumulacion
  de metabolitos neurotoxicos.
- Refuerza pauta basal de vida media larga para dolor cronico y rescate rapido
  para dolor irruptivo.

3. Demencia avanzada y confort:
- En demencia avanzada con disfagia/rechazo de ingesta, prioriza alimentacion de confort.
- Señala SNG/PEG como no indicada de rutina en este contexto por bajo beneficio y
  riesgo de broncoaspiracion.
- En broncoaspiracion terminal, orienta a objetivos de confort y planificacion compartida.

4. Neurotoxicidad opioide y delirium:
- Detecta triada de alarma (deterioro renal + somnolencia intensa + alucinaciones tactiles).
- Recomienda reduccion al 50% o rotacion opioide a fentanilo/metadona.
- En delirium, prioriza causa reversible y limita neurolepticos a uso sintomatico
  tras abordaje etiologico o persistencia.

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/palliative_support_protocol.py app/services/palliative_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/palliative_support_protocol.py app/services/palliative_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k palliative_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k palliative_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza valoracion paliativa presencial.
- Las decisiones de final de vida deben ajustarse a marco normativo y protocolo local.
- La rotacion opioide y el control de delirium requieren seguimiento clinico estrecho.
