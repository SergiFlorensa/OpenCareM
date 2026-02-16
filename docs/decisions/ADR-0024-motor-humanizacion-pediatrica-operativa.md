# ADR-0024 - Motor de Humanizacion Pediatrica Operativa

## Estado

Aprobado

## Contexto

El proyecto ya incluye:

- trazabilidad de agentes por corrida y pasos,
- workflows operativos para triaje y protocolo respiratorio,
- auditoria y observabilidad con Prometheus/Grafana.

Faltaba un flujo centrado en humanizacion pediatrica para casos de alta complejidad
con foco en comunicacion, familia, soporte integral y coordinacion de equipo.

## Decision

Implementar un motor de reglas de humanizacion pediatrica con:

1. endpoint: `POST /api/v1/care-tasks/{id}/humanization/recommendation`;
2. servicio dedicado: `HumanizationProtocolService`;
3. trazabilidad en workflow `pediatric_neuro_onco_support_v1`;
4. metricas especificas para este workflow en `/metrics`.

La recomendacion es operativa, no diagnostica, y exige validacion humana.

## Consecuencias

### Positivas

- Se refuerza el enfoque human-in-the-loop en situaciones vulnerables.
- Se estandariza la coordinacion familia-equipo sin perder trazabilidad.
- Se habilita medicion de madurez operativa en humanizacion pediatrica.

### Trade-offs

- Mayor complejidad de contrato API y pruebas.
- Reglas iniciales simplificadas que requieren calibracion con especialistas.
- Riesgo de sobreautomatizacion si no se mantiene la revision humana.

## Alternativas consideradas

- Dejar el flujo solo como documento sin endpoint: descartado por baja auditabilidad.
- Resolverlo con prompts LLM en tiempo real: descartado en esta fase por coste y variabilidad.
- Mezclarlo con workflow respiratorio existente: descartado por acoplamiento de dominios.
