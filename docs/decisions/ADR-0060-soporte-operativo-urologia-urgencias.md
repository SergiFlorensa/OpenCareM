# ADR-0060: Soporte Operativo de Urologia para Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

Faltaba una capa urologica dedicada para resolver de forma trazable:

- infeccion renal critica con gas en via urinaria y componente obstructivo,
- fracaso renal agudo obstructivo con prioridad de derivacion sobre imagen avanzada,
- trauma genital con sospecha de fractura de pene y riesgo de dano uretral,
- decisiones onco-urologicas en rinon unico y prostata metastasica de alto volumen.

## Decision

Crear el workflow `urology_support_v1` y exponerlo mediante:

- `POST /api/v1/care-tasks/{task_id}/urology/recommendation`

Persistir trazas en `agent_runs/agent_steps` con `run_output.urology_support`.

Agregar metricas Prometheus:

- `urology_support_runs_total`
- `urology_support_runs_completed_total`
- `urology_support_critical_alerts_total`

## Consecuencias

### Positivas

- Estandariza decisiones operativas urgentes de urologia con reglas interpretables.
- Refuerza seguridad al bloquear secuencias de alto riesgo (sondaje en trauma
  genital y retraso de desobstruccion por TAC).
- Aporta trazabilidad y observabilidad sin cambios de esquema de base de datos.

### Riesgos

- Riesgo de interpretar la salida como decision clinica final sin validacion humana.
- Variabilidad de protocolos locales en derivacion, trauma genital y manejo onco-urologico.
- Dependencia de calidad del dato de entrada para activar bloqueos de seguridad.

## Mitigaciones

- Advertencia explicita de no diagnostico en la salida.
- Validacion humana obligatoria.
- Ajuste protocolizado con urologia, urgencias y oncologia segun contexto local.
