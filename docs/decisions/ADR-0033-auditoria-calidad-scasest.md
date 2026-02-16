# ADR-0033: Auditoria de Calidad para Soporte SCASEST

## Estado

Aprobado

## Contexto

El motor SCASEST ya entrega recomendacion operativa, pero faltaba medir calidad contra validacion humana de forma sistematica para:

- detectar under/over riesgo,
- monitorizar consistencia por reglas criticas,
- habilitar mejora continua basada en datos.

## Decision

Implementar auditoria dedicada SCASEST con:

- tabla `care_task_scasest_audit_logs`,
- endpoints:
  - `POST /care-tasks/{id}/scasest/audit`
  - `GET /care-tasks/{id}/scasest/audit`
  - `GET /care-tasks/{id}/scasest/audit/summary`
- metricas Prometheus:
  - `scasest_audit_*`
  - `scasest_rule_*_match_rate_percent`.

## Consecuencias

### Positivas

- trazabilidad de calidad IA vs humano en SCASEST,
- observabilidad cuantitativa de desviaciones,
- base para gates de calidad operativa por workflow.

### Riesgos / Costes

- añade carga de registro manual si no se integra en flujo clinico,
- si no hay volumen de auditorias, las metricas pueden ser poco representativas.

## Validacion

- tests API para registro/listado/resumen de auditoria SCASEST,
- tests `/metrics` para series `scasest_audit_*`,
- regresion enfocada:
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`.
