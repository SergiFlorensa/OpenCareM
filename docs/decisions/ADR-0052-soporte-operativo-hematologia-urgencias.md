# ADR-0052: Soporte Operativo de Hematologia para Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

Faltaba una capa hematologica dedicada para resolver de forma trazable:

- rutas de alto riesgo en microangiopatia y hemolisis intravascular,
- seguridad terapeutica en TIH y hemofilia con inhibidores,
- soporte de calidad diagnostica en onco-hematologia,
- control de seguridad perioperatoria en esplenectomia.

## Decision

Crear el workflow `hematology_support_v1` y exponerlo mediante:

- `POST /api/v1/care-tasks/{task_id}/hematology/recommendation`

Persistir trazas en `agent_runs/agent_steps` con `run_output.hematology_support`.

Agregar metricas Prometheus:

- `hematology_support_runs_total`
- `hematology_support_runs_completed_total`
- `hematology_support_critical_alerts_total`

## Consecuencias

### Positivas

- Estandariza decisiones operativas en hematologia de urgencias.
- Refuerza seguridad en escenarios de sangrado/trombosis de alto impacto.
- Aumenta observabilidad sin crear nuevas tablas.

### Riesgos

- Riesgo de uso inapropiado como diagnostico definitivo.
- Dependencia de disponibilidad de laboratorio, banco de sangre e interconsultas.
- Necesidad de calibracion local de reglas terapeuticas.

## Mitigaciones

- Advertencia explicita de no diagnostico en la salida.
- Validacion humana obligatoria.
- Revision periodica de reglas por comite clinico local.
