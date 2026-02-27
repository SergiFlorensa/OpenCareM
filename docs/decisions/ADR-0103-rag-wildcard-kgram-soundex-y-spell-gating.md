# ADR-0103: RAG candidate retrieval con wildcard, filtro k-gram/Jaccard y fallback Soundex

## Estado

Aprobada

## Contexto

El candidate retrieval ya soportaba parser booleano, frases, proximidad (`/k`) y correccion ortografica por Levenshtein.
Quedaban dos huecos para consultas reales de clinica:

- busquedas por prefijo/variantes mediante comodines (`psicot*`);
- mayor robustez de correccion para typos y terminos foneticos.

Ademas, el trigger de correccion ortografica era muy agresivo (solo `0 postings`) y convenia hacerlo configurable.

## Decision

Se extiende `HybridRetriever` con:

1. Soporte wildcard `*` en tokenizacion booleana.
2. Expansion wildcard sobre `document_chunks_fts_vocab` (FTS5) con limite configurable.
3. Filtro de candidatos por similitud `k-gram + Jaccard` antes de aplicar Levenshtein.
4. Fallback fonetico Soundex para candidatos sin match aceptable por distancia de edicion.
5. Gating de spell correction por postings (`<= CLINICAL_CHAT_RAG_SPELL_TRIGGER_MAX_POSTINGS`).

Se agregan settings:

- `CLINICAL_CHAT_RAG_SPELL_TRIGGER_MAX_POSTINGS`
- `CLINICAL_CHAT_RAG_WILDCARD_ENABLED`
- `CLINICAL_CHAT_RAG_WILDCARD_MAX_EXPANSIONS`
- `CLINICAL_CHAT_RAG_KGRAM_SIZE`
- `CLINICAL_CHAT_RAG_KGRAM_JACCARD_MIN`
- `CLINICAL_CHAT_RAG_SOUNDEX_ENABLED`

## Consecuencias

### Positivas

- mejor recall para consultas con prefijos y variantes de termino;
- menor coste de correccion por prefiltrado k-gram/Jaccard;
- mejor tolerancia a entradas foneticas en nombres/terminos.

### Riesgos

- wildcard corto puede introducir ruido si expande demasiados terminos;
- Soundex puede colisionar terminos tecnicos no equivalentes;
- requiere calibrar umbrales segun corpus clinico real.

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""`
