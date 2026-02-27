# ADR-0104: Correccion ortografica contextual en RAG candidate retrieval

## Estado

Aprobada

## Contexto

La correccion ortografica local ya usaba Levenshtein, filtro k-gram/Jaccard y fallback Soundex.
Faltaba priorizar sugerencias cuando varias opciones tienen distancia similar, usando contexto de la propia consulta.

## Decision

Se añade re-ranking contextual en `HybridRetriever._suggest_term_correction`:

1. Construir contexto vecino por operando (izquierda/derecha) a partir de la consulta booleana.
2. Puntuar candidatos por soporte de bigramas en corpus local FTS:
   - `left_term candidate`
   - `candidate right_term`
3. Resolver empates por:
   - menor distancia de edicion;
   - mayor soporte contextual;
   - mayor frecuencia de documento.
4. Limitar candidatos evaluados en modo contextual para controlar latencia.

Nuevos settings:

- `CLINICAL_CHAT_RAG_CONTEXTUAL_SPELL_ENABLED`
- `CLINICAL_CHAT_RAG_CONTEXTUAL_SPELL_MAX_CANDIDATES`

## Consecuencias

### Positivas

- mejor precision de sugerencias en consultas multi-termino;
- menor probabilidad de correcciones lexicales plausibles pero clinicamente fuera de contexto.

### Riesgos

- el sesgo estadistico del corpus local puede priorizar terminologia dominante;
- en corpus pequeno, el soporte contextual puede ser insuficiente y prevalece la regla de distancia/frecuencia.

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""`
