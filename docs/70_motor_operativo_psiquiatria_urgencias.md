# Motor Operativo de Psiquiatria en Urgencias

## Problema

El sistema no tenia un motor psiquiatrico estructurado para convertir reglas
de urgencias en acciones trazables y seguras en:

- Diferenciacion temporal de estres agudo, TEPT y trastorno adaptativo.
- Riesgo suicida infanto-juvenil con prioridad maxima en autolesiones.
- Pronostico operativo en psicosis.
- Seguridad farmacologica en embarazo y geriatria.
- Integracion de red flags internistas en TCA y analisis psicodinamico cualitativo.

## Cambios implementados

- Nuevo schema: `app/schemas/psychiatry_support_protocol.py`.
- Nuevo servicio: `app/services/psychiatry_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/psychiatry/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=psychiatry_support_v1`
  - `step_name=psychiatry_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `psychiatry_support_runs_total`
  - `psychiatry_support_runs_completed_total`
  - `psychiatry_support_critical_alerts_total`

## Logica operativa cubierta

1. Triage temporal post-estres:
- Evento traumatico + cluster sintomatico:
  - `< 30 dias`: soporte de reaccion de estres aguda.
  - `>= 30 dias`: soporte de ruta TEPT.
- Estresor psicosocial comun en primer mes:
  - soporte de trastorno adaptativo.

2. Riesgo suicida adolescente:
- `<18` con autolesiones:
  - eleva riesgo suicida a nivel maximo,
  - activa prioridad operativa maxima.
- Factores agregados (intento previo, antecedente familiar, aislamiento, sexo masculino):
  - refuerzan alertas de riesgo.

3. Pronostico en psicosis:
- Inicio agudo: bandera de mejor pronostico operativo.
- Inicio precoz y predominio de sintomas negativos: banderas de peor pronostico.

4. Seguridad farmacologica:
- Bipolaridad en embarazo:
  - alerta critica para litio (anomalia de Ebstein),
  - alerta critica para valproato (teratogenia grave),
  - alerta de alto riesgo para carbamazepina,
  - orientacion a lamotrigina como opcion de referencia.
- Insomnio en >80 anos:
  - activa flujo de deteccion de causas secundarias de dolor antes de hipnoticos,
  - alerta por benzodiacepinas (caidas/delirium/deterioro cognitivo).

5. Integracion de medicina interna y analisis cualitativo:
- TCA tipo anorexia:
  - soporte para lanugo, hipotension y bradicardia sinusal,
  - alerta critica ante taquicardia o purgas con alteraciones metabolicas.
- Trastorno delirante:
  - flags de proyeccion, negacion y formacion reactiva,
  - regresion marcada como menos caracteristica de psicosis delirante.

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/psychiatry_support_protocol.py app/services/psychiatry_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/psychiatry_support_protocol.py app/services/psychiatry_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k psychiatry_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k psychiatry_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza evaluacion psiquiatrica presencial.
- Las reglas temporales (CIE/DSM) deben validarse con protocolo local del centro.
- La salida psicodinamica es de apoyo cualitativo y no sustituye entrevista clinica estructurada.
