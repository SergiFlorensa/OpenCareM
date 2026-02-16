# ADR-0061: Soporte Operativo de Anisakis para Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

Faltaba una capa dedicada para manejar de forma trazable:

- sospecha de alergia a anisakis tras ingesta de pescado en ventana temporal
  compatible,
- separacion entre cuadro digestivo por infestacion y reaccion alergica IgE,
- solicitud sistematica de IgE especifica en fenotipos cutaneos/sistemicos,
- recomendaciones estandar al alta para evitar parasitos vivos.

## Decision

Crear el workflow `anisakis_support_v1` y exponerlo mediante:

- `POST /api/v1/care-tasks/{task_id}/anisakis/recommendation`

Persistir trazas en `agent_runs/agent_steps` con `run_output.anisakis_support`.

Agregar metricas Prometheus:

- `anisakis_support_runs_total`
- `anisakis_support_runs_completed_total`
- `anisakis_support_critical_alerts_total`

## Consecuencias

### Positivas

- Estandariza el triaje operativo de sospecha por anisakis en urgencias.
- Refuerza seguridad al no omitir IgE especifica en fenotipo alergico activo.
- Automatiza recomendaciones preventivas al alta sin cambios de esquema en BD.

### Riesgos

- Riesgo de sobreinterpretar salida automatica como diagnostico definitivo.
- Dependencia de calidad de datos de ingesta/latencia/coccion reportados.
- Variabilidad de protocolos locales para manejo de anafilaxia y derivacion.

## Mitigaciones

- Advertencia explicita de no diagnostico en salida.
- Validacion humana obligatoria.
- Ajuste protocolizado con urgencias y alergologia segun contexto local.
