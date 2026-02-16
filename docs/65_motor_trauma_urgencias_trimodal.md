# Motor de Soporte Operativo de Trauma en Urgencias

## Problema

El repositorio cubria motores clinico-operativos por dominios especificos (sepsis, reanimacion, medico-legal, dermatologia), pero no tenia un flujo dedicado para trauma mayor que consolidara:

- Curva trimodal de mortalidad.
- Riesgo de via aerea critica por triada de trauma laringeo.
- Diferencial de sindromes medulares clave.
- Riesgo renal/metabolico en sindrome de aplastamiento.
- Ajustes en geriatria, pediatria y embarazo.
- Umbrales de hipotermia y signos ECG de alto riesgo.
- Clasificacion Gustilo-Anderson para fractura expuesta.

## Cambios implementados

- Nuevo schema: `app/schemas/trauma_support_protocol.py`.
- Nuevo servicio: `app/services/trauma_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/trauma/recommendation`
- Nueva traza de agente en `AgentRunService`:
  - `workflow_name=trauma_support_v1`
  - `step_name=trauma_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `trauma_support_runs_total`
  - `trauma_support_runs_completed_total`
  - `trauma_support_critical_alerts_total`
- Salida estructurada ampliada:
  - `condition_matrix[]` con:
    - condicion/patologia
    - categoria de clasificacion
    - signos y sintomas clave
    - metodo diagnostico
    - tratamiento inicial/inmediato
    - tratamiento definitivo/quirurgico
    - observaciones tecnicas
    - fuente

## Logica operativa cubierta

1. Curva trimodal:
- Clasificacion de riesgo en `immediate`, `early`, `late`, `mixed`.
- Priorizacion TECLA/TICLA en salida (`tecla_ticla_priority`).

2. Via aerea y trauma laringeo:
- Deteccion de triada laringea (fractura palpable + disfonia + enfisema subcutaneo).
- Escalado de prioridad de via aerea y alertas respiratorias de compromiso.
- Deteccion de condiciones que desplazan la curva de disociacion de oxihemoglobina a la derecha.

3. Sindromes medulares:
- Inferencia de patron compatible con:
  - `central_cord`
  - `anterior_cord`
  - `brown_sequard`
  - `indeterminado`

4. Aplastamiento y riesgo renal:
- Marcado de alerta por aplastamiento.
- Riesgo renal alto por contexto metabolico.
- Requisito de ECG seriados cuando aplica.

5. Extremos de la vida y embarazo:
- Ajustes operativos para perfil `geriatrico`, `pediatrico`, `embarazada`.
- Incluye Broselow/olfateo en pediatria y decubito lateral izquierdo en embarazo.

6. Hipotermia:
- Estadiaje `none|mild|moderate|severe`.
- Alertas por ondas J de Osborne y umbrales termicos criticos.

7. Fractura expuesta:
- Clasificacion Gustilo-Anderson (`grado_i|grado_ii|grado_iii`).
- Recomendacion de cobertura antibiotica segun grado.

8. Matriz de condiciones clinicas:
- `Paciente Politraumatizado` (ABCDE).
- `Choque Hipovolemico (Hemorragico)` (grados 1-4).
- `Neumotorax a Tension`.
- `Taponamiento Cardiaco`.
- `Traumatismo Craneoencefalico (TCE)`.
- `Sindrome Compartimental`.
- `Quemaduras`.
- Fuente operacional registrada por item: `CCM 2025 - Especialidad Urgencias`.

## Validacion

- Lint:
  - `./venv/Scripts/python.exe -m ruff check app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/schemas/__init__.py app/services/__init__.py app/schemas/trauma_support_protocol.py app/services/trauma_support_protocol_service.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- Tests focalizados:
  - `$env:COVERAGE_FILE='.coverage.trauma_tmp'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py -k trauma_support`
  - Resultado: `4 passed`

## Riesgos pendientes

- Es un motor de soporte operativo; no reemplaza protocolos institucionales de trauma mayor ni juicio clinico presencial.
- Los umbrales de alerta requieren calibracion local por centro para controlar sobre-alerta/infra-alerta.
