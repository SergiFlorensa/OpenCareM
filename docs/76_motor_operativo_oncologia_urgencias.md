# Motor Operativo de Oncologia en Urgencias

## Problema

El sistema no tenia un motor oncologico dedicado para transformar
datos de urgencias en acciones operativas trazables sobre:

- mecanismos y seleccion inicial de inmunoterapia por checkpoint,
- manejo temprano de toxicidades inmunomediadas (irAEs),
- seguridad cardio-oncologica previa a terapias cardiotoxicas,
- activacion de ruta de neutropenia febril,
- lectura pronostica post-neoadyuvancia en sarcomas oseos.

## Cambios implementados

- Nuevo schema: `app/schemas/oncology_support_protocol.py`.
- Nuevo servicio: `app/services/oncology_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/oncology/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=oncology_support_v1`
  - `step_name=oncology_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `oncology_support_runs_total`
  - `oncology_support_runs_completed_total`
  - `oncology_support_critical_alerts_total`

## Logica operativa cubierta

1. Inmuno-oncologia y biomarcadores:
- Registra mecanismo de PD-1, PD-L1/L2 y CTLA-4 segun clase/agente.
- Prioriza estrategia de inmunoterapia en CCR metastasico irresecable
  de primera linea con dMMR/MSI-high.

2. Toxicidad inmunomediada:
- Detecta hepatotoxicidad grado >=3 por grado clinico y/o umbrales de transaminasas/bilirrubina.
- Activa suspension del farmaco y corticoides 1-2 mg/kg/dia.
- Eleva alerta si no hay suspension documentada o dosis insuficiente.
- En refractarios, fuerza escalado a segunda linea y contempla infliximab.

3. Cardio-oncologia:
- Bloquea inicio de trastuzumab/antraciclinas sin FEVI basal.
- Dispara alerta critica si FEVI basal <50% para valoracion cardio-oncologica prioritaria.

4. Neutropenia febril:
- Aplica criterio de fiebre (single >38.3, >38 sostenida o 3 tomas/24h)
  y criterio de neutropenia (<500 o 500-1000 con caida esperada).
- Si se cumplen ambos, activa aislamiento y antibioterapia empirica inmediata.

5. Respuesta en sarcomas oseos:
- Registra tasa de necrosis de pieza post-neoadyuvancia como
  principal marcador pronostico.
- Interpreta mejor respuesta con necrosis alta y riesgo mayor con necrosis suboptima.
- En Ewing, obliga a documentar estado de reordenamiento EWSR1.

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/oncology_support_protocol.py app/services/oncology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/oncology_support_protocol.py app/services/oncology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k oncology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k oncology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza evaluacion oncologica presencial.
- El manejo definitivo de irAEs y su reintroduccion terapeutica debe ajustarse
  a protocolo institucional y comite tratante.
- La decision final en neutropenia febril y cardio-oncologia requiere
  correlacion clinica integral y disponibilidad local.
