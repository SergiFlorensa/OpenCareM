# ADR-0111: Retrieval probabilistico BM25 + BIM en scorer lexical RAG

## Estado
Aceptado

## Contexto
El retrieval lexical del chat clinico ya soportaba tf-idf por zonas, normalizacion pivotada, poda por idf y ranking por niveles.
Para consultas clinicas con incertidumbre lexical (sinonimos, terminos repetidos, chunks de distinta longitud) se necesitaba una capa probabilistica sin coste adicional y sin servicios externos.

## Decision
Se adopta un scoring hibrido lexical con:
- Base tf-idf por zonas (title, section, body, keywords, custom_questions).
- Componente probabilistico BM25 configurable:
  - CLINICAL_CHAT_RAG_BM25_ENABLED
  - CLINICAL_CHAT_RAG_BM25_K1
  - CLINICAL_CHAT_RAG_BM25_B
  - CLINICAL_CHAT_RAG_BM25_BLEND
- Bonus BIM (Binary Independence Model) opcional:
  - CLINICAL_CHAT_RAG_BIM_BINARY_BONUS_ENABLED
  - CLINICAL_CHAT_RAG_BIM_BINARY_BONUS_WEIGHT

Se mantiene compatibilidad de API (sin cambios de payload) y se agregan trazas de observabilidad:
- keyword_search_bm25_top_avg
- keyword_search_bim_top_avg
- trazas de configuracion BM25/BIM incluso cuando no hay candidatos.

## Alternativas consideradas
1. Mantener solo tf-idf por zonas.
- Rechazada por menor robustez ante variaciones de frecuencia y longitud.

2. Migrar a un ranker externo neuronal.
- Rechazada por coste/latencia y dependencia de infraestructura adicional.

## Consecuencias
- Mejora esperada en ordenacion de chunks relevantes cuando hay variacion fuerte de longitud/frecuencia.
- Mayor control operativo via parametros, con riesgo de sobreajuste si blend y bim_bonus_weight se configuran alto.
- Score probabilistico relativo al candidate pool (no al corpus global completo), priorizando latencia.

## Validacion
- ./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py
- ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py app/tests/test_evaluate_rag_retrieval.py -o addopts=""
- ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""

## Riesgos pendientes
- El score BM25/BIM depende de la calidad del candidate pool lexical.
- Requiere calibracion por especialidad para evitar sesgo hacia chunks largos o muy repetitivos.
