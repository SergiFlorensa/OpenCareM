# Motor Operativo de Anisakis en Urgencias

## Problema

El sistema no tenia un motor dedicado para traducir cuadros compatibles con
Anisakis simplex a acciones operativas trazables sobre:

- sospecha de reaccion alergica inmediata post-ingesta de pescado,
- diferenciacion entre cuadro digestivo por infestacion y fenotipo alergico IgE,
- solicitud diagnostica de IgE especifica y pruebas cutaneas,
- recomendaciones preventivas estandarizadas al alta (congelacion/coccion).

## Cambios implementados

- Nuevo schema: `app/schemas/anisakis_support_protocol.py`.
- Nuevo servicio: `app/services/anisakis_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/anisakis/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=anisakis_support_v1`
  - `step_name=anisakis_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `anisakis_support_runs_total`
  - `anisakis_support_runs_completed_total`
  - `anisakis_support_critical_alerts_total`

## Logica operativa cubierta

1. Disparo de sospecha alergica:
- Activa alerta cuando hay urticaria/angioedema o compromiso sistemico tras
  ingesta de pescado con latencia compatible (<= 6h).
- Prioriza via de anafilaxia cuando hay compromiso respiratorio, hipotension
  o anafilaxia declarada.

2. Diferencial clinico:
- Mantiene rama de perfil digestivo para infestacion sin fenotipo alergico.
- Estructura recomendacion para separar carga parasitaria digestiva de
  hipersensibilidad tipo 1.

3. Diagnostico operativo:
- Solicita IgE especifica frente a Anisakis ante sospecha alergica.
- Incluye prick test en ruta de confirmacion alergologica.
- Bloquea omision de IgE especifica cuando el fenotipo alergico esta activo.

4. Prevencion al alta:
- Incluye de forma automatica:
  - congelacion a `-20 C` durante `72h`,
  - coccion `>60 C`,
  - evitar preparaciones insuficientes (vuelta y vuelta/microondas incompleto).
- Refuerza preferencia por pescado ultracongelado/eviscerado en altamar y
  menor riesgo en piezas de cola.

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/anisakis_support_protocol.py app/services/anisakis_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/anisakis_support_protocol.py app/services/anisakis_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k anisakis_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k anisakis_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza valoracion clinica presencial.
- La confirmacion diagnostica requiere contexto clinico completo y validacion
  alergologica posterior.
- Las medidas de prevencion deben adaptarse a protocolo institucional y
  educacion alimentaria individual del paciente.
