# ADR-0059: Soporte Operativo de Cuidados Paliativos para Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

Faltaba una capa paliativa dedicada para resolver de forma trazable:

- distincion etico-legal entre rechazo al tratamiento, adecuacion del esfuerzo
  y solicitud de ayuda para morir,
- seguridad de opioides en insuficiencia renal y control del dolor irruptivo,
- decisiones de confort en demencia avanzada con disfagia,
- deteccion de neurotoxicidad por opioides y manejo de delirium.

## Decision

Crear el workflow `palliative_support_v1` y exponerlo mediante:

- `POST /api/v1/care-tasks/{task_id}/palliative/recommendation`

Persistir trazas en `agent_runs/agent_steps` con `run_output.palliative_support`.

Agregar metricas Prometheus:

- `palliative_support_runs_total`
- `palliative_support_runs_completed_total`
- `palliative_support_critical_alerts_total`

## Consecuencias

### Positivas

- Estandariza soporte operativo de decisiones paliativas complejas en urgencias.
- Mejora seguridad farmacologica en pacientes con deterioro renal.
- Aporta trazabilidad y observabilidad sin cambios de esquema de base de datos.

### Riesgos

- Riesgo de interpretar la salida como decision clinica final sin validacion humana.
- Variabilidad legal/organizativa local en procesos de final de vida.
- Dependencia de calidad documental sobre capacidad, consentimiento y objetivos de cuidado.

## Mitigaciones

- Advertencia explicita de no diagnostico en salida.
- Validacion humana obligatoria.
- Ajuste protocolizado con paliativos, urgencias y asesoria legal local.
