# ADR-0035: Scorecard Global de Calidad IA Clinica

## Estado

Aprobado

## Contexto

El proyecto ya tenia auditorias por dominio (`triage`, `screening`, `medicolegal`, `scasest`),
pero faltaba una vista global unica para:

- seguimiento operativo rapido,
- lectura ejecutiva de calidad IA vs validacion humana,
- integracion simple con dashboards y runbooks.

Consultar cuatro summaries separados aumentaba friccion operativa.

## Decision

Agregar un scorecard global de solo lectura:

- endpoint:
  - `GET /care-tasks/quality/scorecard`
- servicio:
  - `CareTaskService.get_quality_scorecard`
- normalizacion por dominio:
  - `total_audits`
  - `matches`
  - `under_events`
  - `over_events`
  - `under_rate_percent`
  - `over_rate_percent`
  - `match_rate_percent`
- estado global:
  - `sin_datos`
  - `estable`
  - `atencion`
  - `degradado`

Tambien se publican metricas agregadas en Prometheus:

- `care_task_quality_audit_total`
- `care_task_quality_audit_match_total`
- `care_task_quality_audit_under_total`
- `care_task_quality_audit_over_total`
- `care_task_quality_audit_under_rate_percent`
- `care_task_quality_audit_over_rate_percent`
- `care_task_quality_audit_match_rate_percent`

## Consecuencias

### Positivas

- reduce tiempo de analisis operacional,
- estandariza calidad entre dominios heterogeneos,
- facilita visualizacion y alertado de calidad global.

### Riesgos / Costes

- los umbrales globales pueden ocultar problemas finos por dominio,
- requiere mantener coherencia entre clasificaciones de cada auditoria.

## Validacion

- pruebas API del endpoint de scorecard global,
- pruebas de metricas para series `care_task_quality_audit_*`,
- regresion enfocada:
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
