# ADR-0032: Motor Operativo de SCASEST en Urgencias

## Estado

Aprobado

## Contexto

En el pivot clinico-operativo ya existen motores especificos (respiratorio, sepsis, medico-legal). Faltaba un motor explicable para sospecha de SCASEST:

- dolor toracico es motivo tiempo-dependiente frecuente,
- el riesgo operativo aumenta cuando se retrasa el escalado,
- interesa dejar traza auditable de por que se propuso una accion.

## Decision

Implementar un workflow especifico:

- `scasest_protocol_support_v1`
- endpoint `POST /api/v1/care-tasks/{id}/scasest/recommendation`

El motor clasifica sospecha/riesgo y propone acciones operativas de:

- diagnostico inicial,
- tratamiento temprano orientativo,
- escalado.

No realiza diagnostico definitivo.

## Consecuencias

### Positivas

- estandariza una primera capa operativa para SCASEST,
- facilita priorizacion de casos de alto riesgo en guardia,
- mejora trazabilidad en `agent_runs/agent_steps`,
- habilita observabilidad con metricas especificas.

### Riesgos / Costes

- requiere ajuste continuo segun protocolos locales de cardiologia,
- puede inducir sobreconfianza si no se mantiene el principio de validacion humana.

## Validacion

- tests API de `care_tasks` (exito y 404),
- tests de metricas `/metrics` para series `scasest_protocol_*`,
- regresion enfocada:
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
