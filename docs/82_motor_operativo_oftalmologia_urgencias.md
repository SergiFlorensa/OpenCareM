# Motor Operativo de Oftalmologia en Urgencias

## Problema

El sistema no tenia un motor especifico para transformar hallazgos oftalmologicos
de urgencias en acciones trazables sobre:

- perdida visual brusca con diferenciacion operativa OVCR/OACR por fondo de ojo,
- localizacion neuro-oftalmologica de anisocoria y DPAR,
- diferencial rapido de conjuntivitis alergica frente a red flags de glaucoma neovascular,
- seguridad perioperatoria de catarata con riesgo IFIS por tamsulosina,
- clasificacion operativa de DMAE seca/humeda con alerta de escalado anti-VEGF.

## Cambios implementados

- Nuevo schema: `app/schemas/ophthalmology_support_protocol.py`.
- Nuevo servicio: `app/services/ophthalmology_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/ophthalmology/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=ophthalmology_support_v1`
  - `step_name=ophthalmology_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `ophthalmology_support_runs_total`
  - `ophthalmology_support_runs_completed_total`
  - `ophthalmology_support_critical_alerts_total`

## Logica operativa cubierta

1. Triaje vascular retiniano:
- Prioriza OVCR cuando hay perdida visual brusca y patron con hemorragias en llama
  / edema papilar / exudados algodonosos.
- Prioriza OACR cuando hay mancha rojo cereza o blanqueamiento retiniano difuso.
- Agrega bloque de seguridad en patron mixto OVCR/OACR para reevaluacion urgente.
- Integra PIO elevada como factor de agravamiento en contexto de OVCR.

2. Neuro-oftalmologia pupilar:
- Interpreta anisocoria mayor en oscuridad como orientacion simpatica (Horner).
- Interpreta anisocoria mayor con luz intensa como orientacion parasimpatica.
- Activa alerta critica ante sospecha de lesion compresiva del III par
  (incluido aneurisma de comunicante posterior).
- Valida coherencia de DPAR (Marcus Gunn) con sospecha aferente optica/retiniana.

3. Superficie ocular e inflamacion:
- Reconoce patron de conjuntivitis alergica aguda por exposicion + quemosis + prurito.
- Dispara alerta critica de diferencial de glaucoma neovascular en diabetes de
  larga evolucion con dolor ocular y PIO alta.

4. Seguridad en cirugia de catarata:
- Dispara alerta IFIS cuando hay tamsulosina/alfabloqueante activo y cirugia programada.
- Recomienda fenilefrina intracamerular y bloquea ausencia de plan preventivo.
- Marca como bloque de seguridad la recomendacion de suspender tamsulosina como
  unica medida (riesgo IFIS persistente).
- Incluye riesgo aumentado de desprendimiento de retina en paciente miope joven.

5. Clasificacion DMAE:
- Identifica perfil de DMAE seca por drusas + cambios del epitelio pigmentario
  + evolucion lenta.
- Identifica perfil de DMAE humeda por neovascularizacion/exudacion o perdida visual
  brusca con drusas.
- Escala a alerta critica cuando se sospecha DMAE humeda sin plan anti-VEGF.

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/ophthalmology_support_protocol.py app/services/ophthalmology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/ophthalmology_support_protocol.py app/services/ophthalmology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k ophthalmology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k ophthalmology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`153 passed`)

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza valoracion oftalmologica presencial.
- La discriminacion OVCR/OACR depende de la calidad del reporte de fondo de ojo.
- La decision terapeutica final (anti-VEGF, antiarritmico, hipotensores oculares)
  requiere validacion clinica humana y protocolo local.
