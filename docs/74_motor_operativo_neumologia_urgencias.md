# Motor Operativo de Neumologia en Urgencias

## Problema

El sistema no tenia un motor neumologico unificado para transformar
hallazgos de urgencias en acciones trazables sobre:

- diferenciales tomograficos en enfermedad parenquimatosa,
- interpretacion operativa de hipoxemia/hipercapnia,
- escalado terapeutico EPOC y seleccion biologica en asma grave,
- seguridad en decisiones intervencionistas por funcion pulmonar.

## Cambios implementados

- Nuevo schema: `app/schemas/pneumology_support_protocol.py`.
- Nuevo servicio: `app/services/pneumology_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/pneumology/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=pneumology_support_v1`
  - `step_name=pneumology_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `pneumology_support_runs_total`
  - `pneumology_support_runs_completed_total`
  - `pneumology_support_critical_alerts_total`

## Logica operativa cubierta

1. Diferenciales por imagen:
- Soporte para NOC por consolidacion periferica/subpleural con broncograma.
- Diferencial con bronquiolitis respiratoria en fumador (nodulos centrilobulillares).
- Diferencial con patron intersticial (NII).
- Descarte operativo de atelectasia si no hay obstruccion ni perdida de volumen relevante.

2. Control ventilatorio:
- Hipoxemia asociada a activacion de quimiorreceptores perifericos.
- Hipercapnia/acidosis asociada a control central.
- Regla operativa CPAP para insuficiencia hipoxemica pura y BiPAP en hipercapnia/acidosis.
- Registro de atenuacion de respuesta al CO2 en hipercapnia sostenida.

3. Exploracion fisica y red flags:
- Hemoptisis con prioridad diagnostica de bronquiectasias.
- Perfil fibrosante por crepitantes tipo Velcro, acropaquias y murmullo disminuido.
- Alerta de diferencial cuando hay sibilancias en contexto fibrosante.

4. EPOC/asma:
- Escalada a triple terapia en EPOC agudizador persistente con eosinofilos >100/uL
  pese a LABA+LAMA.
- Alerta de seguridad para estrategia LABA+CI sin LAMA como ruta no preferente en EPOC.
- Seleccion de biologico:
  - Mepolizumab en fenotipo eosinofilico con poliposis.
  - Benralizumab en fenotipo eosinofilico sin poliposis dominante.
  - Omalizumab en fenotipo alergico mediado por IgE.

5. LBA e intervencionismo:
- Valor diagnostico alto del LBA en proteinosis alveolar.
- Uso del LBA como apoyo (no definitivo) en sarcoidosis/neumonitis por hipersensibilidad.
- Regla de seguridad: evitar estrategia quirurgica si `VO2 max < 10 ml/kg/min`.
- Alternativa operativa en alto riesgo funcional: priorizar radioterapia.

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/pneumology_support_protocol.py app/services/pneumology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/pneumology_support_protocol.py app/services/pneumology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k pneumology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k pneumology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza evaluacion neumologica presencial.
- La eleccion final de estrategia intervencionista requiere comite multidisciplinar local.
- Los umbrales y rutas de escalado deben calibrarse con protocolo institucional.
