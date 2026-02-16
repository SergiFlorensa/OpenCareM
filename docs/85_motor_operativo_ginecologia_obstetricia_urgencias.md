# Motor Operativo de Ginecologia y Obstetricia para Urgencias

## Problema

El sistema no tenia un motor dedicado para escenarios gineco-obstetricos
criticos con reglas operativas de seguridad.

Faltaba una capa trazable para:

- alertar patron hereditario compatible con Lynch/Amsterdam II,
- priorizar ruta de gestacion ectopica y probable rotura,
- reforzar reglas de datacion obstetrica (CRL), CIR precoz y STFF,
- gestionar profilaxis de varicela en embarazo no inmune,
- bloquear errores de seguridad en preeclampsia grave y farmacologia.

## Cambios implementados

- Nuevo schema: `app/schemas/gynecology_obstetrics_support_protocol.py`.
- Nuevo servicio: `app/services/gynecology_obstetrics_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/gynecology-obstetrics/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=gynecology_obstetrics_support_v1`
  - `step_name=gynecology_obstetrics_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `gynecology_obstetrics_support_runs_total`
  - `gynecology_obstetrics_support_runs_completed_total`
  - `gynecology_obstetrics_support_critical_alerts_total`

## Logica operativa cubierta

1. Oncogenetica hereditaria:
- Regla Amsterdam II para sospecha de sindrome de Lynch.
- Priorizacion de revision familiar en cancer de endometrio temprano.
- Riesgo por perfil molecular (POLE favorable relativo, P53 serous-like alto riesgo).

2. Urgencias ginecologicas:
- Triada de ectopico: test positivo + dolor abdominal intenso + manchado vaginal.
- Escalado de rotura ectopica ante liquido libre y trompa dilatada/violacea.
- Sugerencia operativa de endometriosis hormonodependiente y forma profunda digestiva.

3. Obstetricia y riesgo infeccioso:
- Ajuste de datacion si CRL y FUR difieren >=5 dias.
- Alerta de CIR severo precoz (<P3 antes de semana 28).
- Criterios operativos de STFF (oligo-polidramnios, Quintero estadio 2).
- Profilaxis postexposicion de varicela en no inmunes y bloqueo de vacunas vivas.

4. Seguridad terapeutica:
- Preeclampsia con sistolica >=160: flujo IV inmediato.
- Criterios graves sin magnesio: bloqueo de seguridad.
- Bloqueo de diureticos en linfedema cronico post-oncologico y sugerencia de
  fisioterapia descongestiva/ejercicio.
- Validacion de requisitos basales para anticoncepcion oral y umbrales de
  diabetes gestacional 75g (92/180/153).

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/gynecology_obstetrics_support_protocol.py app/services/gynecology_obstetrics_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/gynecology_obstetrics_support_protocol.py app/services/gynecology_obstetrics_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k gynecology_obstetrics`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k gynecology_obstetrics`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`165 passed`)

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza diagnostico clinico presencial.
- La calidad de salida depende de datos de imagen/laboratorio y antecedentes familiares.
- Requiere validacion humana obligatoria para decisiones terapeuticas de alto riesgo.
