# ADR-0063: Soporte Operativo de Oftalmologia para Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

Faltaba una capa operativa trazable para urgencias oftalmologicas sobre:

- diferenciacion inicial OVCR/OACR ante perdida visual brusca,
- localizacion neuro-oftalmologica de anisocoria y riesgo compresivo del III par,
- diferencial de superficie ocular con alerta de glaucoma neovascular,
- seguridad quirurgica por IFIS en usuarios de tamsulosina,
- clasificacion DMAE seca/humeda y escalado anti-VEGF.

## Decision

Crear el workflow `ophthalmology_support_v1` y exponerlo mediante:

- `POST /api/v1/care-tasks/{task_id}/ophthalmology/recommendation`

Persistir trazas en `agent_runs/agent_steps` con `run_output.ophthalmology_support`.

Agregar metricas Prometheus:

- `ophthalmology_support_runs_total`
- `ophthalmology_support_runs_completed_total`
- `ophthalmology_support_critical_alerts_total`

## Consecuencias

### Positivas

- Estandariza el triaje operativo oftalmologico en una salida interpretable y auditable.
- Introduce bloqueos de seguridad en escenarios de alto riesgo (IFIS, DPAR inconsistente,
  sospecha compresiva del III par, DMAE humeda sin plan anti-VEGF).
- No requiere cambios de esquema ni migraciones de base de datos.

### Riesgos

- Riesgo de sobreinterpretacion si el fondo de ojo o la exploracion pupilar estan mal descritos.
- Dependencia de disponibilidad real de oftalmologia/neuroimagen para cierre de ruta.
- El flujo puede quedar incompleto si no se documenta el plan sistemico asociado (cardiologia/arritmia).

## Mitigaciones

- Advertencia explicita de soporte no diagnostico en la salida.
- Validacion humana obligatoria (`human_validation_required=true`).
- Trazabilidad completa en `AgentRun`/`AgentStep` para auditoria y mejora continua.
