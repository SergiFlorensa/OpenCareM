# Motor Operativo Critico Transversal en Urgencias

## Problema

El sistema ya tenia motores por dominio (sepsis, reanimacion, SCASEST, trauma), pero faltaba un soporte unico para reglas transversales de guardia:

- SLA tiempo-dependientes (ECG <10 min, sepsis <60 min, triaje rojo <5 min).
- Seleccion de soporte respiratorio segun perfil gasometrico/hemodinamico.
- Ruta TEP en dolor toracico con Wells + Dimero D.
- Decision inmediata en anafilaxia y escalado con glucagon en refractariedad con betabloqueo.
- Perfil hemodinamico orientativo de shock (distributivo/cardiogenico/obstructivo).
- Reversion/antidotos en toxicologia critica.
- Banderas rojas quirurgicas y obstetrico-urologicas.

## Cambios implementados

- Nuevo schema: `app/schemas/critical_ops_protocol.py`.
- Nuevo servicio: `app/services/critical_ops_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/critical-ops/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=critical_ops_support_v1`
  - `step_name=critical_ops_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `critical_ops_support_runs_total`
  - `critical_ops_support_runs_completed_total`
  - `critical_ops_support_critical_alerts_total`

## Logica operativa cubierta

1. SLA y alertas de tiempo:
- ECG en dolor toracico no traumatico <=10 min.
- Antibioterapia en shock septico <=60 min.
- Valoracion en triaje rojo <=5 min.

2. Soporte respiratorio:
- Gafas nasales / Venturi / Reservorio.
- CPAP en EAP sin contraindicacion hemodinamica.
- BiPAP en acidosis respiratoria/hipercapnia.
- Objetivo de saturacion ajustado por riesgo de hipercapnia.

3. Ruta dolor toracico-TEP:
- Wells >6: Angio-TAC directo.
- Wells <=6: Dimero D y escalado segun resultado.

4. Anafilaxia:
- Adrenalina IM inmediata en patron clinico compatible.
- Consideracion de glucagon si refractaria con betabloqueo.

5. Hemodinamica:
- Perfil orientativo distributivo/cardiogenico/obstructivo.
- Lactato seriado cada 2 horas y deteccion de no-clearance.

6. Toxicologia:
- Coma no filiado: naloxona/flumacenilo tras descartar hipoglucemia.
- Tiamina en malnutricion/alcoholismo.
- Humo: O2 100% y hidroxocobalamina si sospecha de cianuro.
- Paracetamol: decision con nomograma de Rumack-Matthew.
- Hipotermia: regla operativa de recalentamiento previo a certificar asistolia irreversible.

7. Red flags:
- Isquemia digital en esclerosis/Raynaud.
- Anuria brusca obstructiva.
- Ectopico probable (dolor + sangrado + liquido libre).
- Hemotorax masivo (>1500 ml inmediatos por tubo).

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/critical_ops_protocol.py app/services/critical_ops_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/critical_ops_protocol.py app/services/critical_ops_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k critical_ops`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k critical_ops`

## Riesgos pendientes

- Es soporte operativo y no reemplaza protocolos institucionales ni juicio clinico presencial.
- Umbrales hemodinamicos y de alertado requieren calibracion local para evitar sobre-alerta.
- El bloque toxicologico es orientativo y debe integrarse con guias y laboratorio del centro.
