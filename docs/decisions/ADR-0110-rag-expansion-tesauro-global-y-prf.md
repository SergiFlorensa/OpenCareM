# ADR-0110: Expansion de consultas con tesauro global y pseudo-relevance feedback

- Fecha: 2026-02-24
- Estado: Aprobado

## Contexto

El retrieval necesitaba mejorar recall ante sinonimia clinica y variaciones terminologicas sin reentrenamiento ni servicios de pago.

## Decision

Se incorpora una estrategia dual de expansion:

1. Expansion global (thesaurus-based):
   - tesauro local en JSON (`docs/clinical_thesaurus_es_en.json`), cacheado con TTL.
2. Expansion local (blind relevance feedback):
   - PRF tipo Rocchio simplificado sobre top-k pseudo-relevante.
   - ponderacion configurable via `PRF_BETA/GAMMA`.

## Implementacion

- `app/services/rag_retriever.py`
  - carga/cache de tesauro global.
  - `expand_query_for_retrieval_details` con desglose local/global/especialidad.
  - `derive_prf_terms` y `expand_query_with_feedback` para segunda pasada.
  - integracion en `search_keyword` y `search_hybrid`.
- `app/core/config.py`
  - settings nuevos de tesauro y PRF.
- `.env` / `.env.example`
  - defaults nuevos.
- `docs/clinical_thesaurus_es_en.json`
  - base inicial de sinonimos clinicos.

## Consecuencias

### Positivas

- mejor recall semantico en consultas con sinonimos y variantes ES/EN.
- menor necesidad de knowledge manual por parte del usuario final.

### Riesgos

- PRF puede generar query drift si el top-k inicial es ruidoso.
- tesauro requiere mantenimiento para evitar expansiones ambiguas.

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""`
