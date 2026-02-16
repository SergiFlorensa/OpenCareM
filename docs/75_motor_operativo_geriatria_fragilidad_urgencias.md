# Motor Operativo de Geriatria y Fragilidad en Urgencias

## Problema

El sistema no tenia un motor geriatrico dedicado para transformar
hallazgos de fragilidad en acciones trazables sobre:

- cambios morfologicos esperables del envejecimiento (sin sobrediagnostico),
- sindrome de inmovilidad y balance nitrogenado negativo,
- manejo operativo del delirium con foco etiologico,
- seguridad de prescripcion en mayores (criterios START v3).

## Cambios implementados

- Nuevo schema: `app/schemas/geriatrics_support_protocol.py`.
- Nuevo servicio: `app/services/geriatrics_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/geriatrics/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=geriatrics_support_v1`
  - `step_name=geriatrics_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `geriatrics_support_runs_total`
  - `geriatrics_support_runs_completed_total`
  - `geriatrics_support_critical_alerts_total`

## Logica operativa cubierta

1. Cambios del envejecimiento:
- Interpreta expansion mesangial, engrosamiento de membrana basal y glomeruloesclerosis
  en contexto de edad para evitar sobrediagnostico aislado.
- Soporta patrones esperables de SNC (atrofia con surcos/ventriculos aumentados),
  reduccion de celulas marcapasos sinusales y calcificacion traqueocostal.

2. Sindrome de inmovilidad:
- Prioriza deteccion de balance nitrogenado negativo.
- Dispara recomendacion de soporte proteico y alerta de seguridad si no esta activo.
- Incluye vigilancia de intolerancia hidrocarbonada, taquicardia de reposo y enlentecimiento psicomotor.

3. Delirium:
- Prioriza tratamiento de causa subyacente (incluyendo foco infeccioso).
- Usa risperidona solo en trastorno conductual grave y propone retirada progresiva tras estabilizacion.
- Bloquea sugerencia de benzodiacepinas en insomnio con delirium sospechado.
- Evita evaluacion de progresion de demencia durante proceso confusional agudo.

4. START v3 y seguridad:
- Recomienda estrogenos topicos vaginales en vaginitis atrofica sintomatica.
- Bloquea lidocaina para dolor articular generalizado sin componente neuropatico localizado.
- Bloquea corticoides inhalados en EPOC GOLD 1-2 sin justificacion.
- Evita refuerzo antitetanico automatico sin revisar esquema previo y ultima dosis.

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/geriatrics_support_protocol.py app/services/geriatrics_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/geriatrics_support_protocol.py app/services/geriatrics_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k geriatrics_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k geriatrics_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza valoracion geriatrica presencial.
- La decision farmacologica final debe ajustarse a comorbilidades y protocolo local.
- La interpretacion de hallazgos de envejecimiento requiere correlacion clinico-funcional.
