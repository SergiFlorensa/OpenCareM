# ADR-0030: Motor Operativo de Sepsis en Urgencias

## Estado

Aprobado

## Contexto

Dentro del pivot clinico-operativo, sepsis es un caso de alto impacto:

- ventana terapeutica corta,
- alta variabilidad operativa en guardia,
- riesgo de empeoramiento rapido si se retrasa el bundle inicial.

## Decision

Implementar un workflow especifico:

- `sepsis_protocol_support_v1`
- endpoint `POST /api/v1/care-tasks/{id}/sepsis/recommendation`

El motor no diagnostica: organiza riesgo, bundle de 1 hora y escalado.

## Consecuencias

### Positivas

- estandariza deteccion operativa temprana por qSOFA,
- reduce omisiones del bundle inicial,
- mejora trazabilidad de decisiones en `agent_runs/agent_steps`,
- habilita observabilidad con metricas especificas.

### Riesgos / Costes

- requiere ajuste continuo segun protocolos locales,
- no debe usarse como sustituto de juicio clinico.

## Validacion

- tests API (exito y 404),
- tests de metricas `sepsis_protocol_*`,
- regresion completa de `app/tests`.
