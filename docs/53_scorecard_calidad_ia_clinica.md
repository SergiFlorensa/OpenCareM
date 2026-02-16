# Scorecard Global de Calidad IA Clinica

## Objetivo

Tener una vista unica de calidad para auditorias IA vs humano sin consultar
seis endpoints separados.

El scorecard agrega:

- triaje
- screening avanzado
- soporte medico-legal
- soporte SCASEST
- soporte riesgo cardiovascular
- soporte reanimacion

## Endpoint

- `GET /api/v1/care-tasks/quality/scorecard`

## Respuesta

Campos globales:

- `total_audits`
- `matches`
- `under_events`
- `over_events`
- `under_rate_percent`
- `over_rate_percent`
- `match_rate_percent`
- `quality_status` (`sin_datos` | `estable` | `atencion` | `degradado`)

Campos por dominio (`domains`):

- `triage`
- `screening`
- `medicolegal`
- `scasest`
- `cardio_risk`
- `resuscitation`

Cada dominio incluye el mismo bloque normalizado:

- `total_audits`
- `matches`
- `under_events`
- `over_events`
- `under_rate_percent`
- `over_rate_percent`
- `match_rate_percent`

## Reglas de estado global

- `sin_datos`: no hay auditorias.
- `degradado`: `under_rate_percent > 10` o `over_rate_percent > 20`.
- `atencion`: hay desviaciones, pero no superan umbral de degradacion.
- `estable`: sin desviaciones (`under=0` y `over=0`).

## Metricas Prometheus asociadas

- `care_task_quality_audit_total`
- `care_task_quality_audit_match_total`
- `care_task_quality_audit_under_total`
- `care_task_quality_audit_over_total`
- `care_task_quality_audit_under_rate_percent`
- `care_task_quality_audit_over_rate_percent`
- `care_task_quality_audit_match_rate_percent`

## Validacion recomendada

1. Crear auditorias en varios dominios (`triage`, `screening`, `medicolegal`, `scasest`, `cardio_risk`, `resuscitation`).
2. Consultar `GET /api/v1/care-tasks/quality/scorecard`.
3. Comprobar que:
   - `total_audits` global coincide con la suma de dominios.
   - `matches + under_events + over_events = total_audits`.
4. Confirmar series en `GET /metrics` buscando `care_task_quality_audit_`.
