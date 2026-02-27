# ADR-0149: CQU Effective Query Conectada a RAG

## Estado

Aprobado

## Contexto

El sistema ya realizaba reescritura contextual de consultas (`effective_query`), pero
la llamada a `RAGOrchestrator` seguia usando `safe_query`. Esto dejaba la CQU fuera
del retrieval real en varios turnos.

## Decision

En `ClinicalChatService.create_message`, la invocacion de:

- `RAGOrchestrator.process_query_with_rag(query=...)`

pasa a usar `effective_query`.

## Consecuencias

- Mejor recuperación en consultas elípticas/correferenciales.
- Menor ambigüedad en turnos de seguimiento.
- Se mantiene sanitización de entrada en etapas previas.
