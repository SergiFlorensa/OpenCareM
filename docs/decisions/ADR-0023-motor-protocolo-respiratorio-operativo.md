# ADR-0023 - Motor de Protocolo Respiratorio Operativo

## Estado

Aprobado

## Contexto

El proyecto ya dispone de:

- `CareTask` como unidad operativa,
- trazabilidad de workflows de agente (`AgentRun`/`AgentStep`),
- observabilidad en Prometheus/Grafana.

Faltaba un flujo concreto, util y reusable para urgencias respiratorias que permitiera:

- priorizar acciones tempranas,
- medir ejecuciones y resultados,
- mantener supervision humana obligatoria.

## Decision

Implementar un motor de recomendaciones operativas respiratorias basado en reglas con:

1. endpoint dedicado:  
   `POST /api/v1/care-tasks/{id}/respiratory-protocol/recommendation`
2. servicio de reglas desacoplado (`RespiratoryProtocolService`);
3. persistencia de traza en workflow `respiratory_protocol_v1`;
4. metricas dedicadas en `/metrics`.

El motor no emite diagnostico medico final y devuelve advertencia explicita de validacion clinica humana.

## Consecuencias

### Positivas

- Se obtiene un caso de uso real para entrenar practicas de IA operativa en salud.
- El flujo queda auditable y medible desde API, base de datos y observabilidad.
- Permite evolucionar a evaluaciones de calidad por protocolo y por ventana temporal.

### Negativas o trade-offs

- Reglas iniciales simplificadas: requieren calibracion clinica continua.
- Riesgo de sobreconfianza si no se mantiene el human-in-the-loop.
- Mayor complejidad de contratos API y pruebas.

## Alternativas consideradas

- Reglas embebidas directamente en endpoint: descartado por baja mantenibilidad.
- Integrar directamente proveedor LLM para esta logica: descartado en esta fase por coste, latencia y reproducibilidad.
- No trazar en `AgentRun`: descartado por perdida de auditabilidad.
