# ADR-0105: Cache de diccionario FTS en memoria para reducir I/O en retrieval

## Estado

Aprobada

## Contexto

El candidate retrieval usa `document_chunks_fts_vocab` para wildcard y spell correction.
En consultas repetidas, ese acceso a SQLite puede introducir latencia evitable por I/O.

## Decision

Se incorpora cache en memoria del vocabulario FTS (`term -> doc_freq`) con:

1. Carga inicial acotada por `CLINICAL_CHAT_RAG_VOCAB_CACHE_MAX_TERMS`.
2. Reuso en lookups wildcard/spell.
3. Recarga por TTL (`CLINICAL_CHAT_RAG_VOCAB_CACHE_TTL_SECONDS`).
4. Fallback automatico a DB si la cache no esta disponible.

Se añade lookup por prefijo sobre estructura ordenada (`bisect`) para patrones simples `prefijo*`.

## Consecuencias

### Positivas

- menor latencia en consultas repetidas con wildcard/typos;
- menor carga de I/O sobre SQLite en runtime.

### Riesgos

- cache puede quedar temporalmente stale hasta vencer TTL;
- si `MAX_TERMS` es muy bajo, puede perder recall en vocabularios muy grandes.

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""`
