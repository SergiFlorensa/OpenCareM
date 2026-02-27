# ADR-0147: Reescritura Contextual de Consulta para CIR

## Estado

Aprobado

## Contexto

El chat conversacional en varios turnos recibia preguntas elipticas o con correferencia
(por ejemplo: "y ahora?", "y su dosis?") que llegaban al retrieval con poco contexto.
Eso reducia relevancia y provocaba respuestas menos utiles.

## Decision

Se incorpora reescritura contextual en `ClinicalChatService._compose_effective_query`:

- Detecta consulta dependiente de contexto por:
  - baja longitud de tokens,
  - patrones de seguimiento,
  - pistas de correferencia,
  - forma interrogativa + foco clinico.
- Reescribe a consulta descontextualizada:
  - `Contexto clinico previo: <ultima consulta>. Consulta de seguimiento: <consulta actual>`.

## Consecuencias

- Mejora la recuperacion en multi-turno sin cambiar infraestructura de retriever.
- Mantiene compatibilidad con flujo actual (solo se activa en queries contextuales).
- Riesgo residual: sobre-expansion de contexto en consultas ambiguas; mitigado por umbrales
  de activacion y limites de longitud.
