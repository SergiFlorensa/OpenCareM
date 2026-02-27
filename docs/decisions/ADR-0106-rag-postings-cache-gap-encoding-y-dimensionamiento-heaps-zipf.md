# ADR-0106: Cache de postings comprimida (gaps) y script de dimensionamiento Heaps/Zipf

## Estado

Aprobada

## Contexto

El candidate retrieval ya tenia FTS + parser booleano + caches de vocabulario.
La latencia residual se concentraba en consultas repetidas de postings y en falta de visibilidad
cuantitativa para dimensionar memoria/caches con base estadistica del corpus.

## Decision

Se añade:

1. Cache de postings en memoria con TTL y LRU, clave por `kind|specialty|limit|query`.
2. Compresion de postings en cache via codificacion por gaps:
   - `vb` (default, orientado a velocidad)
   - `gamma` (opcional, orientado a ratio de compresion).
3. Trazas de observabilidad para hits/miss/evictions de cache de postings.
4. Script `estimate_rag_index_stats` para estimar:
   - Heaps (`M = k * T^b`)
   - snapshot Zipf (`cf_i * i`) y top terminos.

Nuevos settings:

- `CLINICAL_CHAT_RAG_POSTINGS_CACHE_ENABLED`
- `CLINICAL_CHAT_RAG_POSTINGS_CACHE_MAX_ENTRIES`
- `CLINICAL_CHAT_RAG_POSTINGS_CACHE_TTL_SECONDS`
- `CLINICAL_CHAT_RAG_POSTINGS_CACHE_ENCODING`

## Consecuencias

### Positivas

- menor I/O repetido sobre SQLite para consultas frecuentes;
- menor huella efectiva de cache de postings;
- mejor capacidad de tuning basado en estadisticas reales del corpus.

### Riesgos

- `gamma` puede penalizar CPU respecto a `vb`;
- TTL/límites de cache mal calibrados pueden degradar recall efectivo o memoria.

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/scripts/estimate_rag_index_stats.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""`
- `./venv/Scripts/python.exe -m app.scripts.estimate_rag_index_stats --chunk-limit 200 --top 10`
