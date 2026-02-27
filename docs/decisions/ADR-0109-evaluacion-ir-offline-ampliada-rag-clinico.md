# ADR-0109: Evaluacion IR offline ampliada para RAG clinico

- Fecha: 2026-02-24
- Estado: Aprobado

## Contexto

El sistema necesitaba una evaluacion auditable que cubra metrica base, ranking y acuerdo humano, sin servicios de pago.

## Decision

Se amplía `app.scripts.evaluate_rag_retrieval` para incluir:

1. Metricas base y ranking:
   - `precision_at_k`, `recall_at_k`, `f1_at_k`
   - `p@k` configurable
   - `map`, `mrr`, `ndcg`, `context_relevance`
2. Relevancia flexible:
   - binaria por `expected_doc_ids`
   - graduada por `graded_relevance`
   - fallback por `expected_terms` para smoke.
3. Acuerdo entre evaluadores:
   - `kappa` opcional desde `assessor_labels`.
4. Comparativa A/B offline:
   - `--strategy` y `--ab-strategy`.
5. Transparencia:
   - `kwic_top1` en reporte por consulta.

## Implementacion

- `app/scripts/evaluate_rag_retrieval.py`
- `app/tests/test_evaluate_rag_retrieval.py`

## Consecuencias

### Positivas

- evaluacion reproducible y trazable sin coste.
- base cuantitativa para iterar ranking y retrieval.
- soporte directo para gold binario y graduado.

### Riesgos

- fallback por `expected_terms` no sustituye un gold por doc_id.
- kappa depende de calidad/cobertura de etiquetado humano.

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/scripts/evaluate_rag_retrieval.py app/tests/test_evaluate_rag_retrieval.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_evaluate_rag_retrieval.py -o addopts=""`
- `./venv/Scripts/python.exe -m app.scripts.evaluate_rag_retrieval --dataset tmp/rag_eval.jsonl --k 8 --precision-ks 1,3,5 --strategy auto`
