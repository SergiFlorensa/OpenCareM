# ADR-0050: Soporte Operativo Reuma-Inmuno para Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

El proyecto disponia de motores clinico-operativos, pero faltaba una capa
reuma-inmuno para:

- detectar escenarios vitales de base autoinmune/trombotica,
- estandarizar diferenciales y alertas de seguridad terapeutica,
- incorporar reglas materno-fetales y de clasificacion especifica (IgG4/SAF),
- mantener trazabilidad para auditoria y mejora continua.

## Decision

Crear el workflow `rheum_immuno_support_v1` y exponerlo mediante:

- `POST /api/v1/care-tasks/{task_id}/rheum-immuno/recommendation`

Persistir trazas en `agent_runs/agent_steps` con `run_output.rheum_immuno_support`.

Agregar metricas Prometheus:

- `rheum_immuno_support_runs_total`
- `rheum_immuno_support_runs_completed_total`
- `rheum_immuno_support_critical_alerts_total`

## Consecuencias

### Positivas

- Estandariza decisiones operativas reuma-inmunologicas en urgencias.
- Mejora priorizacion en escenarios de alta morbilidad (TEP, isquemia digital, riesgo fetal).
- Incrementa observabilidad con trazas y metricas dedicadas.
- No requiere migraciones de BD (reutiliza trazas existentes).

### Riesgos

- Riesgo de mal uso si se interpreta como diagnostico definitivo.
- Sensibilidad/especificidad depende de calibracion local y perfil del centro.
- Dependencia de disponibilidad de pruebas de imagen/laboratorio/medicina fetal.

## Mitigaciones

- Mantener advertencia de no diagnostico en la salida del motor.
- Validacion humana obligatoria en todos los escenarios.
- Revisiones periodicas de reglas y ajuste por comite clinico local.
