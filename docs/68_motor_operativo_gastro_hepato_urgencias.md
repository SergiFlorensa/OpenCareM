# Motor Operativo Gastro-Hepato en Urgencias

## Problema

El sistema no tenia un motor digestivo/hepatobiliar unificado para traducir hallazgos
de urgencias en acciones trazables:

- Urgencias vasculares/hemodinamicas (trombosis portal, HDA en cirrosis).
- Red flags de imagen (gas portal, neumatosis gastrica, Courvoisier).
- Abdomen agudo y riesgo quirurgico (diverticulitis, hernia crural).
- Seguridad farmacologica y criterios funcionales/geneticos (EII, ERGE, PAF).

## Cambios implementados

- Nuevo schema: `app/schemas/gastro_hepato_support_protocol.py`.
- Nuevo servicio: `app/services/gastro_hepato_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/gastro-hepato/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=gastro_hepato_support_v1`
  - `step_name=gastro_hepato_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `gastro_hepato_support_runs_total`
  - `gastro_hepato_support_runs_completed_total`
  - `gastro_hepato_support_critical_alerts_total`

## Logica operativa cubierta

1. Vascular/hemodinamica:
- Trombosis portal aguda por patron clinico + Doppler sin flujo.
- Anticoagulacion oral como primera linea.
- Escalada endovascular (TIPS/angioplastia) solo ante fracaso terapeutico.
- HDA en cirrotico: fluidoterapia, somatostatina inmediata y endoscopia <12h.
- TIPS de rescate ante fracaso de bandas o resangrado precoz.

2. Imagen y pronostico:
- Triada critica dolor + hipotension + gas portal + neumatosis gastrica.
- Diferencial aerobilia central (post-CPRE/CTPH) vs gas portal periferico.
- Signo de Courvoisier para sospecha de obstruccion maligna distal.

3. Abdomen agudo y cirugia:
- Patrón de diverticulitis aguda no oclusiva.
- Alerta de complicacion en hernia crural con obstruccion/incarceracion.
- Criterios de colecistectomia (vesicula en porcelana, escenarios seleccionados).
- Tecnica Shouldice como referencia sin malla.
- Whipple en adenocarcinoma duodenal resecable.

4. Seguridad/funcional/genetica:
- Riesgo de cancer cutaneo en EII con azatioprina/biologicos.
- Recordatorio tecnico de abordaje abierto izquierdo en Zenker.
- Manometria esofagica como gold standard funcional prequirurgico en ERGE.
- Mutacion APC y manifestaciones extracolonicas en PAF.

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/gastro_hepato_support_protocol.py app/services/gastro_hepato_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/gastro_hepato_support_protocol.py app/services/gastro_hepato_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k gastro_hepato_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k gastro_hepato_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza decision de digestivo/cirugia.
- Umbrales de activacion (isquemia intestinal, HDA, criterios quirurgicos) requieren calibracion local.
- La aplicabilidad depende de disponibilidad real de Doppler, TAC y endoscopia urgente.
