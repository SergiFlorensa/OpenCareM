# ADR-0067: Soporte Operativo de Pediatria y Neonatologia para Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

Faltaba una capa operativa trazable para urgencias pediatrico-neonatales con
reglas de alto impacto: sarampion, reanimacion neonatal, contactos de tosferina,
invaginacion intestinal y estigmas tardios de sifilis congenita.

Se necesitaba:

- un endpoint especializado sobre `CareTask`,
- trazabilidad completa en `agent_runs/agent_steps`,
- metricas observables para ejecucion y alertas criticas,
- cero cambios de esquema en base de datos.

## Decision

Crear el workflow `pediatrics_neonatology_support_v1` y exponerlo mediante:

- `POST /api/v1/care-tasks/{task_id}/pediatrics-neonatology/recommendation`

Persistir trazas en `agent_runs/agent_steps` con
`run_output.pediatrics_neonatology_support`.

Agregar metricas Prometheus:

- `pediatrics_neonatology_support_runs_total`
- `pediatrics_neonatology_support_runs_completed_total`
- `pediatrics_neonatology_support_critical_alerts_total`

## Consecuencias

### Positivas

- Estandariza reglas criticas pediatrico-neonatales en un flujo unico.
- Mejora seguridad operacional con bloqueos explicitos (aislamiento sarampion,
  Apgar obligatorio, hiperoxia neonatal y uso racional de O2).
- Incrementa trazabilidad y auditabilidad de decisiones operativas.

### Riesgos

- Riesgo de sobreinterpretacion si la temporalidad o el registro clinico son incompletos.
- Variabilidad institucional en protocolos de aislamiento/reanimacion/cirugia pediatrica.
- Necesidad de validacion humana obligatoria para acciones de alto impacto.

## Mitigaciones

- Salida marcada como no diagnostica con validacion humana requerida.
- Bloqueos de seguridad explicitados en respuesta estructurada.
- Cobertura de pruebas API/metricas para evitar deriva funcional en regresiones.
