# ADR-0102: Proximidad (/k) y skip pointers en candidate retrieval

- Fecha: 2026-02-24
- Estado: Aprobado

## Contexto

Tras TM-145, el retrieval booleando ya soportaba precedencia, parentesis,
frases y spell local. Faltaba cubrir dos puntos de IR clasico:

- operadores de proximidad tipo `/k` para consultas clinicas compuestas;
- aceleracion de intersecciones grandes con skip pointers.

## Decision

Se extiende `HybridRetriever` con:

- tokenizacion de `/k` y colapso a operando NEAR binario;
- resolucion de proximidad sobre FTS5 via `NEAR(left right, k)`;
- interseccion alternativa con skip pointers (`sqrt(P)`) en listas largas;
- flags de configuracion:
  - `CLINICAL_CHAT_RAG_SKIP_POINTERS_ENABLED`
  - `CLINICAL_CHAT_RAG_SKIP_POINTERS_MIN_LIST`

Adicionalmente, se ajusta fallback booleando:

- si una expresion booleana valida no arroja coincidencias, se reporta
  `candidate_strategy=fts_boolean_no_match` en lugar de expandir por union.

## Consecuencias

### Positivas

- mayor precision para consultas con cercania semantica de terminos;
- menor costo de interseccion en postings largos;
- trazabilidad explicita de uso de skip pointers.

### Riesgos

- `/k` se implementa como proximidad binaria por pares (no n-aria compleja);
- beneficio de skip pointers depende del tamano real de listas.

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""`
