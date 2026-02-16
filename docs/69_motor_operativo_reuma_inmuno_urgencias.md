# Motor Operativo Reuma-Inmuno en Urgencias

## Problema

El sistema no tenia un motor reumatologico/inmunologico unificado para convertir
patrones clinicos de urgencias en acciones trazables:

- Riesgo vital trombotico/vascular (TEP en LES, isquemia digital critica).
- Diferenciales de alta relevancia (miopatias, Behcet, arteritis temporal).
- Cribado por imagen (pseudo-gota, sacroileitis).
- Seguridad materno-fetal por anticuerpos transplacentarios.
- Dominios de clasificacion para IgG4 y SAF.

## Cambios implementados

- Nuevo schema: `app/schemas/rheum_immuno_support_protocol.py`.
- Nuevo servicio: `app/services/rheum_immuno_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/rheum-immuno/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=rheum_immuno_support_v1`
  - `step_name=rheum_immuno_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `rheum_immuno_support_runs_total`
  - `rheum_immuno_support_runs_completed_total`
  - `rheum_immuno_support_critical_alerts_total`

## Logica operativa cubierta

1. Triage y alertas vitales:
- LES + disnea inexplicable activa ruta de sospecha TEP y Dimero D inmediato.
- TTPa prolongado previo refuerza riesgo por anticoagulante lupico.
- Isquemia digital en esclerosis sistemica: prioridad de prostaglandinas IV.
- Arteritis temporal: VSG normal en urgencias reduce probabilidad operativa.

2. Workflows diagnosticos:
- Miopatias inflamatorias con foco en debilidad proximal simetrica.
- Anti-MDA5 como alerta de vigilancia respiratoria por riesgo de EPI agresiva.
- Triada de Behcet y propuesta de primera linea (corticoides + azatioprina).
- Alerta de seguridad por ciclosporina en afectacion parenquimatosa cerebral.

3. Cribado por imagen:
- Pseudo-gota: si carpo negativo, ampliar a rodillas y sinfisis pubica.
- Espondiloartropatia axial: sacroileitis para soporte de confirmacion.

4. Seguridad materno-fetal y clasificacion:
- Anti-Ro/Anti-La con riesgo de bloqueo cardiaco/miocarditis fetal.
- Prioridad de corticoides fluorados cuando hay riesgo fetal precoz.
- Alertas de transferencia transplacentaria (antidesmogleina3, anti-AChR).
- Dominios obligatorios de IgG4 (infiltrado, flebitis obliterativa, fibrosis estoriforme).
- Entrada de SAF por evento clinico + alteracion analitica; trombopenia como dominio relevante.

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/rheum_immuno_support_protocol.py app/services/rheum_immuno_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/rheum_immuno_support_protocol.py app/services/rheum_immuno_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k rheum_immuno_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k rheum_immuno_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza diagnostico especializado.
- Los umbrales de disparo en vasculitis/miopatias/complicaciones fetales requieren calibracion local.
- La utilidad real depende de acceso a laboratorio, imagen y soporte obstetrico-fetal.
