# ADR-0151: HAM Ligero y Ranking Hibrido Query-Aware

## Estado

Aprobado

## Contexto

El seguimiento conversacional y la calidad extractiva mejoraron, pero faltaba:

- seleccionar historial relevante en multi-turno sin procesar todo,
- combinar fidelidad extractiva con fluidez local sin depender de LLM generativo.

## Decision

1. Reescritura contextual con HAM ligero (`ClinicalChatService`):
   - score por turno = overlap con consulta + recencia exponencial + foco clinico.
   - seleccion de top turnos para construir `effective_query`.

2. Ranking hibrido en extractivo (`RAGOrchestrator`):
   - overlap con escala logaritmica (estabilidad en consultas largas),
   - score extractivo + proxy generativo (tau=0.6, delta=0.4),
   - integrado en pipeline coarse-to-fine y MMR.

## Consecuencias

- Mejora de coherencia en turnos de seguimiento con baja latencia.
- Respuestas mas accionables sin introducir dependencia de modelos pesados.
- Mantiene modo evidence-first y safety gates existentes.
