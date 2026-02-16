# ADR-0028: Soporte Operativo Medico-Legal en Urgencias

## Estado

Aprobado

## Contexto

El proyecto ya cubre triaje, humanizacion, screening y soporte radiografico.
Faltaba una capa operativa medico-legal para escenarios de:

- retrasos criticos de triaje/valoracion,
- consentimiento en procedimientos invasivos,
- cadena de custodia en contexto forense,
- sospecha de muerte no natural y judicializacion.

En guardia, estas omisiones tienen impacto asistencial y riesgo legal.

## Decision

Implementar un workflow especifico `medicolegal_ops_support_v1` expuesto en:

- `POST /api/v1/care-tasks/{id}/medicolegal/recommendation`

La salida incluye:

- alertas legales criticas,
- documentos requeridos,
- acciones operativas,
- checklist de cumplimiento.

Siempre requiere validacion humana.

## Consecuencias

### Positivas

- Mejora estandarizacion de cumplimiento medico-legal en urgencias.
- Reduce riesgo de omisiones documentales bajo saturacion.
- Incrementa trazabilidad y auditabilidad con `agent_runs`/`agent_steps`.
- Permite observabilidad con metricas `medicolegal_ops_*`.

### Costes / Riesgos

- Puede aumentar carga de revision si se sobregeneran alertas.
- Requiere mantenimiento de reglas conforme a cambios normativos.
- No debe confundirse con asesoria legal ni dictamen forense.

## Validacion

- Tests API de exito, alerta critica y 404.
- Tests de metricas en `/metrics`.
- Regresion completa de `app/tests`.
