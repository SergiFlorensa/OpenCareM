# Motor Operativo de Nefrologia en Urgencias

## Problema

El sistema no tenia un motor nefrologico unificado para transformar
hallazgos de crisis renal en acciones trazables sobre:

- clasificacion sindromica del FRA,
- sindrome renopulmonar y glomerulonefritis rapidamente progresiva,
- interpretacion acido-base y compensacion respiratoria,
- criterios AEIOU para dialisis urgente,
- nefroproteccion con iSGLT2 y seguridad farmacologica.

## Cambios implementados

- Nuevo schema: `app/schemas/nephrology_support_protocol.py`.
- Nuevo servicio: `app/services/nephrology_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/nephrology/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=nephrology_support_v1`
  - `step_name=nephrology_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `nephrology_support_runs_total`
  - `nephrology_support_runs_completed_total`
  - `nephrology_support_critical_alerts_total`

## Logica operativa cubierta

1. FRA y clasificacion:
- FRA prerrenal orientado por sodio urinario bajo.
- FRA parenquimatoso (NTA probable) por sodio urinario alto.
- FRA obstructivo por anuria brusca/hidronefrosis.

2. Sindrome renopulmonar:
- Activacion por triada glomerular + vidrio deslustrado bilateral + anemizacion.
- Escalado urgente de inmunosupresion/plasmaferesis.
- Plasmaferesis obligatoria en anti-MBG positivo, GNRP con dialisis y hemorragia pulmonar.
- Priorizacion sindromica ante error tipografico de plaquetas.

3. Acido-base:
- Deteccion de acidosis metabolica (pH < 7.35 + HCO3 < 24).
- Regla de compensacion respiratoria esperada.
- Alerta de trastorno mixto cuando PCO2 no compensa.

4. Dialisis urgente (AEIOU):
- Disparadores para acidosis refractaria, electrolitos refractarios, intoxicaciones dializables,
  sobrecarga de volumen refractaria y uremia sintomatica.

5. Nefroproteccion y seguridad:
- Recomendacion de iSGLT2 en nefropatia diabetica/proteinurica.
- Refuerzo de sinergia hemodinamica iSGLT2 + IECA/ARA-II.
- Alerta de seguridad por doble bloqueo IECA + ARA-II.

6. Glomerular/intersticial:
- Nefropatia IgA (hematuria glomerular + depositos mesangiales IgA/C3).
- Nefritis intersticial farmacologica (FRA + fiebre + rash + eosinofilia).
- Vasculitis ANCA pauci-inmune (semilunas >50% + IF negativa).

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/nephrology_support_protocol.py app/services/nephrology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/nephrology_support_protocol.py app/services/nephrology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k nephrology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k nephrology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza evaluacion nefrologica presencial.
- Las decisiones de plasmaferesis/dialisis dependen de disponibilidad local y protocolo institucional.
- La clasificacion del FRA requiere correlacion clinica, no solo umbrales aislados.
