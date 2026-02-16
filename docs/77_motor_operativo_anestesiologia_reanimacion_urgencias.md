# Motor Operativo de Anestesiologia y Reanimacion en Urgencias

## Problema

El sistema no tenia un motor anestesiologico dedicado para transformar
datos de urgencias en acciones operativas trazables sobre:

- induccion de secuencia rapida (ISR) en escenarios de estomago lleno,
- control de riesgos en via aerea (ventilacion manual, via IV, Sellick),
- recomendacion de bloqueos simpaticos segun anatomia del dolor,
- priorizacion de bloqueo del ganglio impar en dolor perineal/pelvico complejo.

## Cambios implementados

- Nuevo schema: `app/schemas/anesthesiology_support_protocol.py`.
- Nuevo servicio: `app/services/anesthesiology_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/anesthesiology/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=anesthesiology_support_v1`
  - `step_name=anesthesiology_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `anesthesiology_support_runs_total`
  - `anesthesiology_support_runs_completed_total`
  - `anesthesiology_support_critical_alerts_total`

## Logica operativa cubierta

1. Induccion de secuencia rapida (ISR):
- Activa ISR en paciente con estomago lleno (sin ayuno, obstruccion intestinal,
  hematemesis u otro riesgo equivalente).
- Prioriza automaticamente el kit ISR cuando hay obstruccion intestinal o hematemesis.
- Recomienda preoxigenacion en ventana de 3-5 minutos.
- Emite alerta critica si se planea ventilacion manual bolsa-mascarilla en ISR.
- Bloquea uso de induccion inhalatoria halogenada y fuerza via IV exclusiva.
- Evalua ventana tecnica de intubacion esperada (45-60 segundos).
- Gestiona maniobra de Sellick hasta verificar posicion del tubo y cuff inflado.

2. Dolor complejo y bloqueos simpaticos:
- Sugiere bloqueo del ganglio impar como eleccion en masa presacra
  con dolor perineal/pelvico y opioides insuficientes/no tolerados.
- Mantiene recomendacion de ganglio impar en dolor interno perineal/pelvico
  neuropatico, visceral o vascular.

3. Diagnostico diferencial anatomico de bloqueos:
- Plexo celiaco para abdomen alto visceral.
- Nervios esplacnicos para dolor/disfuncion autonomica pelvica-genital.
- Nervios pudendos para dolor perineal y genitales externos.
- Ganglio impar para pelvis interna/perine de origen visceral/neuropatico.

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/anesthesiology_support_protocol.py app/services/anesthesiology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/anesthesiology_support_protocol.py app/services/anesthesiology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k anesthesiology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k anesthesiology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza valoracion anestesiologica presencial.
- La ejecucion de ISR y bloqueos debe ajustarse a protocolos y recursos locales.
- Las decisiones de analgesia intervencionista requieren correlacion anatomica
  e imagen guiada por el equipo tratante.
