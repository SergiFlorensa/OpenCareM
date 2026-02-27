# ADR-0152: CIR de Ambiguedad con Clarificacion Proactiva y NQP-lite

## Estado

Aprobado

## Contexto

El chat clinico ya tenia reescritura contextual y fallback extractivo, pero faltaba un control
determinista para consultas ambiguas (muy cortas o sin datos clinicos clave). En esos turnos, la
respuesta final podia ser prematura o poco util.

## Decision

1. Introducir un gate heuristico de ambiguedad en `ClinicalChatService`:
   - variables: shortness, estructura numerica, señal de dominio y terminos ambiguos.
   - activacion con umbral `score >= 0.62`.
2. Cuando el gate dispara:
   - responder con pregunta de clarificacion (sin cambiar schema externo),
   - usar banco de preguntas por dominio/intencion.
3. Añadir NQP-lite:
   - sugerencias de siguientes consultas utiles por dominio/intencion,
   - reutilizable en aclaracion y en modo conversacional general.
4. Trazabilidad:
   - `clarification_gate_triggered`, `clarification_gate_score`,
     `clarification_gate_reason`, `clarification_suggestions`.

## Consecuencias

- Mejora de seguridad operativa en consultas de bajo contexto.
- Mejor UX conversacional sin dependencia de modelos adicionales.
- Coste computacional bajo (determinista, CPU-friendly).
- Sin ruptura de contrato API (solo cambia contenido de `answer` y trazas opcionales).
