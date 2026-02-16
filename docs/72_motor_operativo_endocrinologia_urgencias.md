# Motor Operativo de Endocrinologia en Urgencias

## Problema

El sistema no tenia un motor endocrino-metabolico unificado para convertir
patrones de riesgo en acciones trazables sobre:

- hipoglucemia hipocetosica y errores de beta-oxidacion,
- patologia tiroidea pediatrica y carcinoma medular tiroideo,
- SIADH, hiperprolactinemia e insuficiencia suprarrenal aguda,
- cribado de incidentaloma suprarrenal,
- estadiaje operativo de DM1 y seguridad farmacologica en obesidad.

## Cambios implementados

- Nuevo schema: `app/schemas/endocrinology_support_protocol.py`.
- Nuevo servicio: `app/services/endocrinology_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/endocrinology/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=endocrinology_support_v1`
  - `step_name=endocrinology_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `endocrinology_support_runs_total`
  - `endocrinology_support_runs_completed_total`
  - `endocrinology_support_critical_alerts_total`

## Logica operativa cubierta

1. Emergencias metabolicas:
- Regla automatica: hipoglucemia sin cetosis dispara flujo de defectos de beta-oxidacion.
- Triada critica: hipoglucemia hipocetosica + acidosis lactica + hiperamonemia.
- Dicarboxilicos elevados como apoyo de bloqueo en oxidacion de acidos grasos.

2. Tiroides:
- Hashimoto pediatrico: desaceleracion de crecimiento + TSH/T4 + anti-TPO/anti-Tg + bocio firme difuso.
- CMT: metanefrinas urinarias preoperatorias obligatorias, cirugia de referencia y seguimiento con calcitonina/CEA.
- Alerta de seguridad: tiroglobulina no util para seguimiento del CMT.

3. Agua/hipofisis/suprarrenal:
- SIADH por perfil analitico (hiponatremia hipoosmolar + orina concentrada).
- SIADH grave: alerta para suero hipertonico lento.
- Tolvaptan: se marca como antagonista V2 y se alerta si se combina con restriccion hidrica estricta.
- Hiperprolactinemia: descarte inicial de causas fisiologicas/farmacologicas; RM si prolactina alta o inexplicada.
- Crisis suprarrenal: patron clinico-operativo de alto riesgo.

4. Incidentaloma y diabetes:
- Se rechaza cortisol serico aislado como cribado valido.
- Checklist funcional obligatorio: ARR (si HTA), supresion con 1 mg dexametasona y metanefrinas 24h.
- Soporte de estadiaje DM1 (estadios 1-3).
- Priorizacion de GLP-1 en obesidad con alto riesgo CV.
- Alertas para evitar pioglitazona/sulfonilureas/insulina cuando se prioriza evitar ganancia de peso e hipoglucemias.

5. Factores de confusion:
- Hipercalcemia con tiazidas.
- Hipertrigliceridemia asociada a alcohol cronico y descenso de HDL.
- Contexto molecular de resistencia a insulina (exoquinasa 2/FoxO1).

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/endocrinology_support_protocol.py app/services/endocrinology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/endocrinology_support_protocol.py app/services/endocrinology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k endocrinology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k endocrinology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza evaluacion endocrinologica presencial.
- Las decisiones terapeuticas definitivas dependen de protocolo local y recursos del centro.
- El uso de biomarcadores/hallazgos moleculares es de apoyo y no sustituye juicio clinico integral.
