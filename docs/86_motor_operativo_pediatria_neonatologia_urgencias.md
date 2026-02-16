# Motor Operativo de Pediatria y Neonatologia para Urgencias

## Problema

El sistema no tenia un motor dedicado para escenarios pediatrico-neonatales
con reglas operativas de seguridad en infecciones exantematicas, reanimacion
neonatal y urgencias digestivas.

Faltaba una capa trazable para:

- sospecha de sarampion (triada prodromica + Koplik/exantema),
- validacion vacunal por edad y aislamiento respiratorio inmediato,
- soporte neonatal por objetivos de SatO2 por minuto y uso de CPAP,
- profilaxis de contactos estrechos de tosferina,
- alertas por invaginacion intestinal y estigmas tardios de sifilis congenita.

## Cambios implementados

- Nuevo schema: `app/schemas/pediatrics_neonatology_support_protocol.py`.
- Nuevo servicio: `app/services/pediatrics_neonatology_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/pediatrics-neonatology/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=pediatrics_neonatology_support_v1`
  - `step_name=pediatrics_neonatology_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `pediatrics_neonatology_support_runs_total`
  - `pediatrics_neonatology_support_runs_completed_total`
  - `pediatrics_neonatology_support_critical_alerts_total`

## Logica operativa cubierta

1. Sarampion:
- Triada prodromica (fiebre alta + fotofobia + tos) como base de sospecha.
- Refuerzo por Koplik o exantema maculopapular con progresion cefalo-caudal.
- Aislamiento respiratorio obligatorio con bloqueo si no esta activo.
- Validacion por edad vacunal:
  - `<12 meses`: susceptible aunque esquema correcto para edad.
  - `>=12 meses` sin dosis: alerta de cobertura vacunal insuficiente.
- Ojo rojo con diferencial de Kawasaki.

2. Neonatologia y Apgar:
- Bloqueo si solo hay registro de minuto 0.
- Recordatorio operativo de Apgar obligatorio en minuto 1 y 5.
- Si FC >100 + respiracion espontanea + distres: sugerir CPAP.
- Objetivos de SatO2 por minuto (3/5/10) para evitar hiperoxia.
- Regla de seguridad: en minuto 3 con FC >100 y SatO2 60-80, bloquear aumento
  de O2 y priorizar CPAP con FiO2 21%.

3. Tosferina en contactos:
- Contacto estrecho (convivencia, secreciones, RN de madre infecciosa o
  exposicion sanitaria sin mascarilla) -> profilaxis con macrolidos.
- Riesgo de contagio hasta 5 dias tras tratamiento eficaz o 21 dias sin este.

4. Invaginacion intestinal:
- Alerta en 6-24 meses con colico intermitente y periodos asintomaticos.
- Escalado critico si hay signos de peritonitis.
- Nota de asociacion con adenovirus y ventana post-rotavirus (riesgo ligero).

5. Sifilis congenita tardia:
- Regla por triada de Hutchinson parcial/completa.
- Estigmas complementarios (nariz en silla de montar, molares de Morera,
  tibias en sable, frente prominente, articulaciones de Clutton).
- Recordatorio: cardiopatia congenita no es manifestacion tipica.

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/pediatrics_neonatology_support_protocol.py app/services/pediatrics_neonatology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/pediatrics_neonatology_support_protocol.py app/services/pediatrics_neonatology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k pediatrics_neonatology`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k pediatrics_neonatology`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`169 passed`)

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza valoracion pediatrica/neonatal presencial.
- La calidad de salida depende de registro temporal y datos clinicos fiables.
- Las decisiones de aislamiento, reanimacion y urgencia quirurgica requieren
  validacion humana y protocolo local.
