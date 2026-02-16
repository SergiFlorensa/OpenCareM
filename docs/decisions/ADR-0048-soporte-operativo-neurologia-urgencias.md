# ADR-0048: Soporte Operativo de Neurologia para Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

El proyecto disponia de motores en dominios de urgencias, pero faltaba una capa neurologica unificada para:

- priorizar emergencias vasculares tiempo-dependientes (HSA/ictus),
- mejorar diferenciales criticos en triaje,
- emitir alertas de seguridad terapeutica (p. ej., corticoides en SGB),
- mantener trazabilidad operativa para auditoria.

## Decision

Crear el workflow `neurology_support_v1` y exponerlo mediante:

- `POST /api/v1/care-tasks/{task_id}/neurology/recommendation`

Persistir trazas en `agent_runs/agent_steps` con `run_output.neurology_support`.

Agregar metricas Prometheus:

- `neurology_support_runs_total`
- `neurology_support_runs_completed_total`
- `neurology_support_critical_alerts_total`

## Consecuencias

### Positivas

- Estandariza reglas neurologicas de urgencias en un motor interpretable.
- Reduce variabilidad operativa en escenarios de alto riesgo vascular.
- Mejora observabilidad y capacidad de drill con metricas dedicadas.
- No requiere migraciones de BD (reutiliza trazas existentes).

### Riesgos

- Uso fuera de alcance si se interpreta como diagnostico definitivo.
- Sensibilidad/especificidad de reglas depende de calibracion local.
- Dependencia de acceso real a TAC perfusion, angiografia y biomarcadores.

## Mitigaciones

- Mantener aviso de no diagnostico en respuesta del motor.
- Validacion humana obligatoria en todos los escenarios.
- Revisiones periodicas de reglas y tuning por centro.
