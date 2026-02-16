# Motor Operativo de Recurrencia Genetica en OI para Urgencias

## Problema

El sistema no tenia un motor dedicado para escenarios de recurrencia genetica
en osteogenesis imperfecta (OI) tipo II con patron dominante recurrente.

Faltaba una capa operativa trazable para:

- priorizar mosaicismo germinal cuando hay recurrencia en padres fenotipicamente sanos,
- evitar clasificar casos recurrentes como evento de novo aislado,
- ordenar diferencial con herencia recesiva, penetrancia incompleta y mosaicismo somatico,
- registrar alerta explicita de "mosaicismo" para soporte de consejo genetico.

## Cambios implementados

- Nuevo schema: `app/schemas/genetic_recurrence_support_protocol.py`.
- Nuevo servicio: `app/services/genetic_recurrence_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/genetic-recurrence/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=genetic_recurrence_support_v1`
  - `step_name=genetic_recurrence_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `genetic_recurrence_support_runs_total`
  - `genetic_recurrence_support_runs_completed_total`
  - `genetic_recurrence_support_critical_alerts_total`

## Logica operativa cubierta

1. Regla principal de recurrencia:
- Si hay condicion dominante sospechada + recurrencia + padres fenotipicamente
  sanos, se activa alerta critica de mosaicismo.
- Se prioriza `mosaicismo_germinal_probable`.

2. Confirmacion de mecanismo:
- Si existe confirmacion de mosaicismo germinal, el mecanismo pasa a
  `mosaicismo_germinal_confirmado`.
- Si se informa fraccion de gametos mutados, se preserva como riesgo estimado.

3. Bloqueos de seguridad:
- Recurrencia con hipotesis de novo activa: bloqueo para evitar clasificar como
  evento de novo aislado.
- Inconsistencias de fenotipo parental o mezcla de estados de mosaicismo:
  bloqueo de normalizacion.
- Falta de confirmacion molecular: bloqueo para no cerrar mecanismo.

4. Consejo genetico operativo:
- Activa acciones de consejeria reproductiva y ruta prenatal/preimplantacional.
- Refuerza validacion por genetica clinica y obstetricia.

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/genetic_recurrence_support_protocol.py app/services/genetic_recurrence_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/genetic_recurrence_support_protocol.py app/services/genetic_recurrence_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k genetic_recurrence`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k genetic_recurrence`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`161 passed`)

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza diagnostico genetico formal.
- El riesgo de recurrencia depende de calidad de datos moleculares y contexto familiar.
- La decision final de consejeria y manejo obstetrico requiere validacion humana.
