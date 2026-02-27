# ADR-0148: RAG Query-Aware Snippet Ranking y Metricas de Safety

## Estado

Aprobado

## Contexto

El modo extractivo mostraba fragmentos tecnicos o poco alineados con la consulta
(cabeceras de documento y texto no accionable), degradando la utilidad clinica.
Adicionalmente faltaba una metrica explicita de fuga interna en benchmark.

## Decision

1. En `RAGOrchestrator._build_extractive_answer`:
   - ranking de candidatos por solape con tokens de la consulta (query-aware),
   - mezcla con score de retrieval como factor secundario,
   - descarte de snippets sin solape cuando hay tokens de consulta.
2. En limpiadores de snippet (`rag_orchestrator` y `clinical_chat_service`):
   - filtrado de patrones de ruido documental (`motor operativo`, `documento >`, `validacion -`).
3. En benchmark:
   - nuevas metricas proxy de validacion y safety:
     - `proxy_token_f1_avg`,
     - `proxy_exact_match_rate`,
     - `internal_leak_rate`,
     - `abstention_rate`.
   - criterio de aceptacion adicional: `internal_leak_rate <= 0.0`.

## Consecuencias

- Respuestas extractivas mas orientadas a la pregunta y menos "plantilla documental".
- Mejor capacidad de deteccion temprana de fugas de trazas internas.
- Metricas proxy no sustituyen evaluacion clinica humana ni gold labels formales.
