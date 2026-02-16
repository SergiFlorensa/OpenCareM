# ADR-0043: Fundamento etico-legal estructurado en respuesta medico-legal

- Fecha: 2026-02-13
- Estado: aceptada

## Contexto

Tras TM-067, el motor medico-legal identificaba conflicto pediatrico critico,
pero la salida no separaba explicitamente:

- recomendacion de override vital
- base etico-legal de la decision
- resumen de urgencia util para operacion en tiempo real

Esto dificultaba consumo en frontend, auditoria y defensa documental.

## Decision

Se extiende `MedicolegalOpsRecommendation` con:

- `life_preserving_override_recommended: bool`
- `ethical_legal_basis: list[str]`
- `urgency_summary: str`

La logica activa estos campos especialmente cuando existe conflicto pediatrico
con riesgo vital y limitaciones de representacion/autorizacion inmediata.

## Consecuencias

### Positivas

- Mejor explicabilidad de decisiones en escenarios de alta carga etica.
- Mayor trazabilidad para auditoria clinico-juridica.
- Mejor interoperabilidad con frontend para mostrar rationale.

### Trade-offs

- Contrato de salida mas amplio en endpoint medico-legal.
- Mayor mantenimiento de mensajes base y consistencia semantica.

## Alternativas consideradas

1. Mantener justificacion dentro de texto libre en `context_notes`.
   - Rechazada: baja estructura y auditabilidad.
2. Generar documento externo fuera del endpoint.
   - Rechazada: rompe flujo de decision en tiempo real.
3. Incluir campos estructurados en respuesta del motor.
   - Elegida.
