# ADR-0118: LSI (SVD truncada) en retrieval lexical RAG

## Estado
Aceptado

## Contexto
El retriever ya combinaba tf-idf por zonas, BM25, QLM y bonus BIM. Faltaba una señal semántica latente para reducir el gap terminológico en consultas con sinonimia clínica.

## Decision
Se integra una capa LSI local en `HybridRetriever._score_keyword_candidates`:
- construcción de matriz término-documento ponderada por zonas sobre el candidate pool,
- descomposición SVD truncada (`numpy.linalg.svd`),
- proyección de consulta por folding-in,
- similitud coseno en espacio latente y normalización min-max por chunk,
- mezcla por `CLINICAL_CHAT_RAG_LSI_BLEND` con el score lexical existente.

Se agregan parámetros runtime:
- `CLINICAL_CHAT_RAG_LSI_ENABLED`
- `CLINICAL_CHAT_RAG_LSI_K`
- `CLINICAL_CHAT_RAG_LSI_BLEND`
- `CLINICAL_CHAT_RAG_LSI_MAX_VOCAB_TERMS`
- `CLINICAL_CHAT_RAG_LSI_MIN_DOCS`

Y trazas operativas `keyword_search_lsi_*`.

## Alternativas consideradas
1. No incorporar LSI.
- Rechazada por menor capacidad de captar co-ocurrencias latentes.

2. Reemplazar totalmente scoring lexical por LSI.
- Rechazada para preservar control y robustez de señales existentes.

3. Factorización global persistente.
- Rechazada en esta fase por coste operativo y complejidad de refresco continuo.

## Consecuencias
- Mejora potencial en recuperación semántica de consultas ambiguas.
- Incremento de coste CPU por consulta (SVD sobre pool candidato).
- Necesidad de calibrar `k`, `blend` y tamaño de vocabulario para latencia estable.

## Validacion
- `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -k "lsi or qlm or bm25 or tfidf" -o addopts=""`

## Riesgos pendientes
- Al calcularse sobre candidate pool, la geometría latente es local y puede variar por consulta.
- Si el pool crece, el coste de SVD puede afectar SLA de latencia.
