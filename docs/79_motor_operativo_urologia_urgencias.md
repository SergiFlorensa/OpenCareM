# Motor Operativo de Urologia en Urgencias

## Problema

El sistema no tenia un motor urologico dedicado para traducir datos de
urgencias a acciones operativas trazables sobre:

- infeccion renal critica con gas en via urinaria y riesgo metabolico,
- fracaso renal agudo obstructivo con necesidad de desobstruccion inmediata,
- trauma genital con sospecha de fractura de pene y riesgo uretral,
- decisiones onco-urologicas de preservacion renal y enfermedad prostatica
  metastasica de alto volumen.

## Cambios implementados

- Nuevo schema: `app/schemas/urology_support_protocol.py`.
- Nuevo servicio: `app/services/urology_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/urology/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=urology_support_v1`
  - `step_name=urology_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `urology_support_runs_total`
  - `urology_support_runs_completed_total`
  - `urology_support_critical_alerts_total`

## Logica operativa cubierta

1. Pielonefritis enfisematosa (PFE):
- Detecta gas urinario como evento critico.
- Prioriza antibiotico de amplio espectro y derivacion urinaria urgente si
  hay componente obstructivo.
- Refuerza diferencial con pielonefritis xantogranulomatosa (curso cronico).

2. FRA obstructivo:
- Activa alerta por triada de colico/anuria/deterioro renal con dilatacion
  pielocalicial bilateral.
- Prioriza derivacion urinaria urgente por delante de TAC avanzado.
- Bloquea secuencias de imagen que retrasen la desobstruccion.

3. Trauma genital (fractura de pene):
- Activa flujo de revision quirurgica urgente ante traumatismo en ereccion
  con hematoma/edema y pene flacido post-trauma.
- Bloquea sondaje vesical cuando existe sospecha de lesion uretral asociada.
- Bloquea gasometria cavernosa en este contexto (reservada al diferencial de
  priapismo).

4. Onco-urologia:
- Prioriza nefrectomia parcial en tumor renal localizado con rinon unico
  funcionante o rinon contralateral atrofico.
- Recomienda biopsia transperineal por fusion RM-ecografia para lesiones
  prostaticas anteriores.
- En prostata metastasica de alto volumen, orienta a triple terapia
  sistemica (LHRH + docetaxel + antiandrogeno de nueva generacion) y bloquea
  estrategias locales curativas fuera de perfil.

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/urology_support_protocol.py app/services/urology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/urology_support_protocol.py app/services/urology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k urology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k urology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza valoracion urologica presencial.
- La decision final de derivacion, revision quirurgica y estrategia sistemica
  depende de protocolo local y disponibilidad de recursos.
- La salida no sustituye confirmacion diagnostica por imagen, laboratorio y
  juicio clinico integral.
