# ADR-0130: Priorizacion de fuentes RAG por score + gate local de aceptacion benchmark

- Fecha: 2026-02-25
- Estado: Aprobada

## Contexto
El diagnostico tecnico indica brecha principal en calidad (`answer_relevance`, `context_relevance`) y observabilidad insuficiente del benchmark (p95 incoherente y sin criterio de aceptacion automatico).

## Decision
1. En `RAGOrchestrator`, ordenar `rag_sources` por score de retrieval (relevancia) y usar tipo de fuente solo como desempate.
2. En fallback evidence-first, incluir `Consulta objetivo` en respuesta para mayor alineacion auditable.
3. Corregir p95 del benchmark (`nearest-rank`) y generar resumen JSON persistente.
4. Agregar script `check_acceptance.py` para gate automatico local/CI.

## Consecuencias
- Mejora esperada de relevancia contextual al priorizar chunks verdaderamente top-score.
- p95 reportado deja de subestimar outliers en muestras pequenas.
- El pipeline de evaluacion ahora falla explicitamente cuando no cumple criterios.

## Riesgos pendientes
- La mejora de calidad aun depende de subir `context_relevance` en retrieval real (reranker/chunking por seccion en siguiente iteracion).
