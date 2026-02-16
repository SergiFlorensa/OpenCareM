# ADR-0066: Soporte Operativo de Ginecologia y Obstetricia para Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

Faltaba una capa operativa trazable para casos gineco-obstetricos de alto
riesgo en urgencias: oncogenetica hereditaria, ectopico/rotura, preeclampsia
grave y bloqueos de seguridad farmacologica.

Se necesitaba:

- un endpoint especializado sobre `CareTask`,
- trazabilidad completa en `agent_runs/agent_steps`,
- metricas observables para ejecucion y alertas criticas,
- mantener cero cambios de esquema en base de datos.

## Decision

Crear el workflow `gynecology_obstetrics_support_v1` y exponerlo mediante:

- `POST /api/v1/care-tasks/{task_id}/gynecology-obstetrics/recommendation`

Persistir trazas en `agent_runs/agent_steps` con
`run_output.gynecology_obstetrics_support`.

Agregar metricas Prometheus:

- `gynecology_obstetrics_support_runs_total`
- `gynecology_obstetrics_support_runs_completed_total`
- `gynecology_obstetrics_support_critical_alerts_total`

## Consecuencias

### Positivas

- Estandariza reglas criticas de urgencias gineco-obstetricas en un flujo unico.
- Mejora la seguridad con bloqueos explicitos (preeclampsia grave, diureticos en
  linfedema, vacunas vivas en embarazo).
- Incrementa trazabilidad y auditabilidad de decisiones operativas.

### Riesgos

- Riesgo de sobreinterpretacion si los datos de entrada son incompletos.
- Variabilidad de protocolos institucionales para manejo definitivo.
- Necesidad de validacion humana obligatoria para todas las acciones de alto impacto.

## Mitigaciones

- Salida marcada como no diagnostica con validacion humana requerida.
- Bloqueos de seguridad explicitados en respuesta estructurada.
- Documentacion de reglas y pruebas de regresion para evitar deriva funcional.
