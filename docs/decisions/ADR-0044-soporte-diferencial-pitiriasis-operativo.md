# ADR-0044: Soporte diferencial operativo de pitiriasis en CareTask

- Fecha: 2026-02-13
- Estado: aceptada
- Ambito: API/servicios/observabilidad (sin cambios de esquema SQL)

## Contexto

El proyecto incorpora protocolos operativos por dominio clinico. Faltaba una pieza para diferenciar de forma estructurada pitiriasis versicolor, rosada y alba, incorporando señales de alarma para descartar diagnósticos alternativos de mayor riesgo.

Se requiere:

1. Endpoint trazable por `CareTask`.
2. Reglas explicables (sin caja negra).
3. Metricas operativas para observabilidad.

## Decision

Implementar un workflow nuevo:

- Endpoint:
  - `POST /api/v1/care-tasks/{task_id}/pityriasis-differential/recommendation`
- Workflow:
  - `pityriasis_differential_support_v1`
- Paso de traza:
  - `pityriasis_differential_assessment`

Salida operativa con:

- condicion mas probable (`most_likely_condition`)
- diferenciales y hallazgos de soporte
- pruebas sugeridas y manejo inicial
- `urgent_red_flags`
- marca de validacion humana obligatoria

Metricas Prometheus:

- `pityriasis_differential_runs_total`
- `pityriasis_differential_runs_completed_total`
- `pityriasis_differential_red_flags_total`

## Consecuencias

### Positivas

- Cobertura de un nuevo bloque clinico con salida interpretable.
- Trazabilidad completa en `agent_runs/agent_steps`.
- Observabilidad operativa desde `/metrics`.

### Negativas / trade-offs

- Reglas heuristicas pueden requerir recalibracion por contexto local.
- No hay auditoria IA vs humano especifica en esta fase (solo recomendacion y traza).

## Riesgos pendientes

- Riesgo de sobreconfianza si se usa como diagnostico definitivo.
- Variabilidad clinica regional en criterios de derivacion dermatologica.

## Mitigaciones

- Mensaje no diagnostico obligatorio en respuesta.
- `human_validation_required=true` en todas las recomendaciones.
- Documentacion de red flags con escalado presencial.
