# Motor Operativo de Hematologia en Urgencias

## Problema

El sistema no tenia un motor hematologico unificado para convertir patrones
de riesgo critico en acciones trazables para:

- microangiopatias tromboticas y hemolisis intravascular,
- trombocitopenia inducida por heparina (TIH),
- sangrado agudo en hemofilia con inhibidores,
- soporte de clasificacion onco-hematologica,
- seguridad perioperatoria en esplenectomia,
- hallazgos de quimerismo post-trasplante.

## Cambios implementados

- Nuevo schema: `app/schemas/hematology_support_protocol.py`.
- Nuevo servicio: `app/services/hematology_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/hematology/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=hematology_support_v1`
  - `step_name=hematology_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `hematology_support_runs_total`
  - `hematology_support_runs_completed_total`
  - `hematology_support_critical_alerts_total`

## Logica operativa cubierta

1. MAT y hemolisis:
- Triada MAT (anemia hemolitica microangiopatica + trombopenia + dano organico).
- Sospecha Donath-Landsteiner en hemolisis intravascular post-frio.
- SHU tipico posdiarreico con Coombs negativo y esquistocitos elevados.
- Regla operativa: no priorizar plasmaferesis en SHU tipico.

2. TIH:
- Ventana 5-10 dias con caida plaquetaria >50%.
- Accion inmediata: suspender heparina.
- Seleccion operativa de alternativa segun fallo renal/hepatico.

3. Hemofilia:
- Hemofilia A grave con inhibidores y hemartrosis aguda: ruta de agentes bypass.
- Alerta critica si se planifica complejo protrombinico con Emicizumab.

4. Onco-hematologia:
- Alerta de calidad de muestra: PAAF aislada no suficiente, priorizar biopsia.
- Soporte de inmunofenotipo para LBDCG, Hodgkin clasico, LLC y linfoma del manto.
- Asociaciones virales relevantes (HHV-8, EBV, HTLV-1).

5. Fanconi y seguridad post-esplenectomia:
- Fenotipo pediatrico compatible con fallo de reparacion de ADN y riesgo onco-hematologico.
- Checklist de vacunacion preoperatoria ante esplenectomia.
- Alerta por ausencia de tromboprofilaxis en posesplenectomia sin sangrado activo.

6. Trasplante hematopoyetico:
- Flag de quimerismo compatible con posible Klinefelter en donante (47,XXY).

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/hematology_support_protocol.py app/services/hematology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/hematology_support_protocol.py app/services/hematology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k hematology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k hematology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza evaluacion hematologica presencial.
- La estrategia terapeutica definitiva en MAT/TIH requiere protocolos y recursos locales.
- Las sugerencias de clasificacion de linfoma son de apoyo y no sustituyen anatomia patologica.
