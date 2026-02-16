# ADR-0062: Soporte Operativo de Epidemiologia Clinica para Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

Faltaba una capa operativa para tratar de forma consistente:

- seleccion de metrica epidemiologica segun objetivo (individual/colectivo),
- calculo de NNT con control de escala (riesgos en tanto por uno),
- interpretacion condicional del RR en lenguaje causal contrafactual,
- validacion basica de Bradford Hill y clasificacion coste-utilidad.

## Decision

Crear el workflow `epidemiology_support_v1` y exponerlo mediante:

- `POST /api/v1/care-tasks/{task_id}/epidemiology/recommendation`

Persistir trazas en `agent_runs/agent_steps` con `run_output.epidemiology_support`.

Agregar metricas Prometheus:

- `epidemiology_support_runs_total`
- `epidemiology_support_runs_completed_total`
- `epidemiology_support_critical_alerts_total`

## Consecuencias

### Positivas

- Estandariza calculos epidemiologicos de uso frecuente en una salida trazable.
- Reduce errores de magnitud en NNT al forzar riesgos en escala `0..1`.
- Refuerza comunicacion causal prudente mediante formulacion en condicional.
- No requiere cambios de esquema en base de datos.

### Riesgos

- Riesgo de sobreinterpretar RR como causal sin calidad metodologica suficiente.
- Dependencia de calidad del dato de entrada (riesgos, denominadores, persona-tiempo).
- Variabilidad institucional para interpretar utilidades/costos en evaluacion economica.

## Mitigaciones

- Advertencia explicita de no diagnostico en salida.
- Validacion humana obligatoria.
- Bloques de seguridad para temporalidad ausente, RR no calculable y NNT no interpretable.
