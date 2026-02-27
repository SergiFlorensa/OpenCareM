# ADR-0112: Query Likelihood Model con smoothing en retrieval lexical RAG

## Estado
Aceptado

## Contexto
El retrieval lexical ya combinaba tf-idf por zonas, BM25 y bonus BIM.
Se necesitaba reforzar robustez frente a terminos ausentes o variacion terminologica en consultas clinicas (problema de probabilidades cero en matching literal).

## Decision
Se incorpora un Query Likelihood Model (QLM) unigrama para estimar P(q|d) por documento candidato.

- Suavizado soportado:
  - Dirichlet prior (`CLINICAL_CHAT_RAG_QLM_DIRICHLET_MU`)
  - Jelinek-Mercer (`CLINICAL_CHAT_RAG_QLM_JM_LAMBDA`)
- Activacion y blend configurables:
  - `CLINICAL_CHAT_RAG_QLM_ENABLED`
  - `CLINICAL_CHAT_RAG_QLM_BLEND`
  - `CLINICAL_CHAT_RAG_QLM_SMOOTHING`

El score QLM se normaliza y se mezcla con el score lexical existente sin cambios de contrato API.

## Alternativas consideradas
1. Mantener solo BM25/BIM.
- Rechazada por menor capacidad para modelar probabilidad de generacion de consulta.

2. Reemplazar ranking por LTR neuronal.
- Rechazada por mayor coste operativo y dependencia de entrenamiento/datos etiquetados.

## Consecuencias
- Mejora esperada en recall para consultas con mismatch terminologico moderado.
- Mayor sensibilidad a calibracion de `mu/lambda/blend`.
- Estimacion probabilistica relativa al candidate pool (no a todo el corpus).

## Validacion
- ./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py
- ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py app/tests/test_evaluate_rag_retrieval.py -o addopts=""
- ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""

## Riesgos pendientes
- Si el candidate pool inicial trae ruido, QLM puede reforzar distribuciones no ideales.
- Un blend alto puede diluir señales de coincidencia exacta en consultas de alta especificidad.
