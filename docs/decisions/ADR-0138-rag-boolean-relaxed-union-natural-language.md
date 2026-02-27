# ADR-0138: RAG boolean relaxed union for natural-language queries

- Fecha: 2026-02-26
- Estado: aceptada
- Ambito: `app/services/rag_retriever.py`

## Contexto

El parser booleano de candidatos FTS inserta `AND` implicitos entre operandos.
En consultas naturales largas (sin operadores booleanos explicitos), esta
interseccion estricta puede dejar `candidate_ids=0` y provocar
`rag_status=failed_retrieval`, aunque existan chunks relevantes por terminos
parciales.

Se observo en benchmark con queries tipo:

- `Neutropenia febril oncologica: pasos 0-10...`
- `Oliguria con hiperkalemia y QRS ancho...`
- `Paciente pediatrico con sospecha de sarampion...`

## Decision

Aplicar fallback de union relajada cuando:

1. `candidate_ids` queda vacio.
2. Hay terminos candidatos.
3. La consulta no es booleana explicita (o hubo error de parseo).

Implementacion:

- usar `legacy_include`/`legacy_optional` como terminos de union.
- mantener modo estricto para consultas con `AND/OR/NOT` explicitos.
- si sigue vacio y no es booleana explicita, usar `full_scan_fallback`.

Nuevas trazas:

- `candidate_boolean_relaxed_union`
- `candidate_boolean_relaxed_union_terms`
- `candidate_strategy=fts_boolean_relaxed_union`

## Consecuencias

- Mejora recall y reduce `failed_retrieval` en lenguaje natural.
- Puede introducir algo mas de ruido en consultas ambiguas.
- Las consultas booleanas explicitas mantienen semantica estricta.

## Validacion

- `ruff check app/services/rag_retriever.py app/tests/test_rag_retriever.py`
- `pytest -q app/tests/test_rag_retriever.py -k "fetch_candidate_chunks_relaxes_non_explicit_boolean_when_intersection_is_empty or fetch_candidate_chunks_keeps_strict_no_match_for_explicit_boolean" -o addopts=""`

