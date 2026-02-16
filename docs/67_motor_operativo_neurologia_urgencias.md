# Motor Operativo de Neurologia en Urgencias

## Problema

El sistema no tenia un motor neurologico transversal para convertir reglas de alto riesgo en acciones operativas trazables:

- HSA e ictus (incluyendo inicio desconocido y perfusion).
- Diferenciales semiologicos de alto impacto.
- Alertas de seguridad terapeutica en neuromuscular/autoinmune.
- Interpretacion operativa de biomarcadores y decisiones avanzadas.

## Cambios implementados

- Nuevo schema: `app/schemas/neurology_support_protocol.py`.
- Nuevo servicio: `app/services/neurology_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/neurology/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=neurology_support_v1`
  - `step_name=neurology_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `neurology_support_runs_total`
  - `neurology_support_runs_completed_total`
  - `neurology_support_critical_alerts_total`

## Logica operativa cubierta

1. Riesgo vascular:
- Cefalea brusca como disparador de TAC urgente.
- Identificacion de HSA por hiperdensidad subaracnoidea.
- Reconocimiento de patron perimesencefalico con angiografia normal y mejor pronostico.

2. Codigo ictus:
- Ventana de fibrinolisis <=4.5 h.
- Ruta de trombectomia hasta 24 h si hay penumbra salvable.
- Inicio desconocido/wake-up stroke con prioridad de TAC perfusion.
- Lectura operativa de ASPECTS (8-10 favorece reperfusion activa).

3. Diferencial neurologico:
- Parkinson vs parkinsonismos atipicos con respuesta a levodopa y red flags.
- Limitaciones de DaTSCAN para diferenciar subtipos.
- Mapeo central/periferico de paralisis facial.
- Claves funcionales de cefalea tensional vs migrana.

4. Autoinmune/neuromuscular:
- SGB con alerta de contraindicacion de corticoides.
- Miastenia gravis con debilidad fluctuante y afectacion ocular.
- Perfil anti-NMDA con accion obligatoria de busqueda de teratoma ovarico.

5. Biomarcadores y decisiones avanzadas:
- Perfil de LCR en Alzheimer (Tau alta + Abeta42 baja).
- ApoE4 como riesgo no diagnostico por si solo.
- Angiografia como patron oro para aneurismas/MAV.
- Soporte de decision en DBS y mielopatia cervical compresiva.

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/neurology_support_protocol.py app/services/neurology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/neurology_support_protocol.py app/services/neurology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k neurology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k neurology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza decision neurologica/neuroquirurgica presencial.
- Los umbrales de activacion de rutas vasculares y autoinmunes deben calibrarse por centro.
- La recomendacion de pruebas avanzadas depende de disponibilidad local de imagen/laboratorio.
