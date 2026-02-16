# ADR-0045: Soporte diferencial operativo de acne y rosacea en CareTask

- Fecha: 2026-02-13
- Estado: aceptada
- Ambito: API/servicios/observabilidad (sin migraciones SQL)

## Contexto

El sistema ya cubre workflows clinicos por dominio. Faltaba un bloque de dermatologia operativa para diferenciar acne vs rosacea e incluir controles de seguridad farmacologica cuando se contempla isotretinoina.

## Decision

Agregar workflow dedicado:

- Endpoint:
  - `POST /api/v1/care-tasks/{task_id}/acne-rosacea/recommendation`
- Workflow:
  - `acne_rosacea_differential_support_v1`
- Paso trazable:
  - `acne_rosacea_differential_assessment`

La salida incluye:

- condicion mas probable,
- subtipo y severidad operativa,
- manejo inicial,
- consideraciones farmacologicas,
- checklist de monitorizacion de isotretinoina,
- red flags urgentes.

Metricas:

- `acne_rosacea_differential_runs_total`
- `acne_rosacea_differential_runs_completed_total`
- `acne_rosacea_differential_red_flags_total`

## Consecuencias

### Positivas

- Cubre diferencial frecuente con salida interpretable.
- Refuerza seguridad farmacoterapeutica en escenarios de retinoides sistemicos.
- Mantiene trazabilidad y observabilidad estandar del proyecto.

### Trade-offs

- Reglas heuristicas pueden requerir ajuste por contexto asistencial.
- No incorpora en esta fase auditoria IA vs humano especifica del dominio.

## Riesgos pendientes

- Riesgo de sobreuso fuera de su ambito (soporte operativo, no diagnostico).
- Necesidad de validacion local del escalado de severidad y subtipos.

## Mitigaciones

- `human_validation_required=true` en todas las respuestas.
- `non_diagnostic_warning` obligatorio.
- Documentacion explicita de limites y uso seguro.
