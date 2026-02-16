# Motor Operativo de Inmunologia en Urgencias

## Problema

El sistema no tenia un motor dedicado para traducir hallazgos inmunologicos a
acciones operativas trazables sobre:

- sospecha de agammaglobulinemia ligada al X (Bruton/BTK),
- interpretacion del perfil humoral (CD19/CD20, IgG, IgA, IgM),
- ventana postnatal de IgG materna y riesgo infeccioso tras los 6 meses,
- rol de defensa innata pulmonar (macrofago alveolar y barreras asociadas),
- diferencial entre Bruton, deficit selectivo de IgA, sindrome hiper-IgM y CVID.

## Cambios implementados

- Nuevo schema: `app/schemas/immunology_support_protocol.py`.
- Nuevo servicio: `app/services/immunology_support_protocol_service.py`.
- Nuevo endpoint:
  - `POST /api/v1/care-tasks/{task_id}/immunology/recommendation`
- Nueva traza en `AgentRunService`:
  - `workflow_name=immunology_support_v1`
  - `step_name=immunology_operational_assessment`
- Nuevas metricas en `/metrics`:
  - `immunology_support_runs_total`
  - `immunology_support_runs_completed_total`
  - `immunology_support_critical_alerts_total`

## Logica operativa cubierta

1. Inmunodeficiencia humoral (Bruton/XLA):
- Activa alerta critica con patron combinado de ausencia CD19/CD20 +
  panhipogammaglobulinemia (IgG/IgA/IgM bajas).
- Refuerza trazabilidad para mutacion BTK y herencia ligada al X.
- Marca riesgo infeccioso critico cuando hay infecciones recurrentes tras la
  ventana de IgG materna (>6 meses).
- Añade bloque de seguridad si se reporta disfuncion monocitaria en patron
  Bruton clasico (hallazgo no esperado).

2. Defensa innata pulmonar:
- Prioriza acciones cuando existe infeccion respiratoria baja activa.
- Escala criticidad si hay sospecha de disfuncion de macrofago alveolar.
- Soporta chequeos de reclutamiento neutrofilico, barrera mucociliar,
  complemento y peptidos antimicrobianos.

3. Diferencial humoral:
- Detecta perfil de deficit selectivo de IgA.
- Detecta perfil de sindrome hiper-IgM (IgM alta con IgG/IgA bajas).
- Detecta perfil compatible con CVID (IgG baja con descenso parcial de otras
  inmunoglobulinas, sin ausencia franca de B perifericos).
- Incluye bloqueos de seguridad ante combinaciones analiticas inconsistentes o
  perfiles multiples simultaneos.

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/schemas/immunology_support_protocol.py app/services/immunology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/immunology_support_protocol.py app/services/immunology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k immunology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k immunology_support`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`157 passed`)

## Riesgos pendientes

- El motor es soporte operativo y no reemplaza valoracion inmunologica clinica.
- La calidad de salida depende de exactitud del perfil inmunologico cargado.
- La decision terapeutica final requiere validacion humana y protocolo local.
