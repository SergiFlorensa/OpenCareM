# Motor Operativo de Epidemiologia Clinica en Urgencias

## Problema

El sistema no tenia un motor dedicado para traducir entradas epidemiologicas a
acciones operativas trazables sobre:

- eleccion correcta de metrica de frecuencia (incidencia acumulada, densidad y
  prevalencia),
- calculo seguro de NNT usando riesgos en tanto por uno,
- interpretacion condicional del RR en clave causal contrafactual,
- uso estructurado de Bradford Hill y clasificacion economica coste-utilidad.

## Cambios implementados

- Nuevo schema: `app/schemas/epidemiology_support_protocol.py`.
- Nuevo servicio: `app/services/epidemiology_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/epidemiology/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=epidemiology_support_v1`
  - `step_name=epidemiology_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `epidemiology_support_runs_total`
  - `epidemiology_support_runs_completed_total`
  - `epidemiology_support_critical_alerts_total`

## Logica operativa cubierta

1. Metricas de frecuencia:
- Calcula incidencia acumulada cuando hay casos nuevos y poblacion en riesgo.
- Calcula densidad de incidencia cuando hay persona-tiempo valido.
- Calcula prevalencia para foto poblacional actual.
- Prioriza incidencia acumulada para riesgo individual y prevalencia para
  estado actual poblacional.

2. NNT y analitica de impacto:
- Calcula RAR como diferencia absoluta de riesgo.
- Calcula NNT como `1 / RAR` solo cuando `RAR > 0`.
- Bloquea interpretacion cuando `RAR = 0`.
- Refuerza regla de entrada en escala `0..1` para evitar errores de magnitud.

3. Inferencia causal:
- Calcula RR como `riesgo_expuestos / riesgo_no_expuestos`.
- Genera mensaje contrafactual en condicional:
  - "se reduciria ... si ..."
- Añade criterio de gradiente biologico dentro de Bradford Hill.
- Bloquea inferencia causal robusta cuando falta temporalidad.

4. Evaluacion economica:
- Detecta coste-utilidad cuando el tipo de estudio corresponde.
- Verifica coherencia entre coste-utilidad y uso de AVAC/QALY/utilidades.
- Señala inconsistencias de clasificacion en seguridad metodologica.

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/epidemiology_support_protocol.py app/services/epidemiology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/epidemiology_support_protocol.py app/services/epidemiology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k epidemiology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k epidemiology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza evaluacion epidemiologica formal.
- La inferencia causal sigue dependiendo de calidad de diseño y sesgos no
  observados del estudio real.
- La interpretacion economica requiere marco institucional de costos y
  preferencias para decision final.
