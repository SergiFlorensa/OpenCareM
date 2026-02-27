# ADR-0108: Ranking lexical acelerado con idf pruning, proximidad y calidad estatica

- Fecha: 2026-02-24
- Estado: Aprobado

## Contexto

Tras introducir `tf-idf` por zonas, se requiere reducir latencia y reforzar relevancia de top-K en consultas clinicas con candidate pools amplios.

## Decision

Se incorpora una capa adicional de optimizacion lexical:

1. Poda por `idf` (inexact retrieval):
   - se priorizan terminos de mayor poder discriminativo.
   - se mantiene un minimo configurable de terminos para evitar sobre-poda.
2. Bonus de proximidad:
   - se calcula ventana minima en `chunk_text` que contiene terminos activos.
   - menor ventana => mayor bonus.
3. Calidad estatica `g(d)`:
   - heuristica local basada en metadata de documento/zona para priorizar fuentes mas operativas.
4. Ranking por niveles:
   - tier1: docs con calidad estatica sobre umbral.
   - tier2: resto de candidatos para completar cobertura.

## Implementacion

- `app/services/rag_retriever.py`
  - `_minimum_window_span`
  - `_estimate_static_quality`
  - integracion en `_score_keyword_candidates`.
- `app/core/config.py`
  - nuevos settings de `idf`, proximidad, calidad estatica y tiering.
- `.env` / `.env.example`
  - defaults para tuning.
- tests:
  - `app/tests/test_rag_retriever.py`
  - `app/tests/test_settings_security.py`

## Consecuencias

### Positivas

- menos ruido por terminos comunes en ranking lexical.
- mejor orden en top-K para consultas donde contexto cercano importa.
- priorizacion de fuentes internas de mayor valor operativo.

### Riesgos

- `g(d)` es heuristica y debe calibrarse con evaluacion offline y feedback real.
- proximidad basada en tokenizacion simple puede infraestimar sinonimos/parafrasis.

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""`
