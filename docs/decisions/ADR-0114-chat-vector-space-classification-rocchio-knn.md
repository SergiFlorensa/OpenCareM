# ADR-0114: Clasificacion vectorial (Rocchio + kNN) para enrutado clinico

## Estado
Aceptado

## Contexto
El enrutado de dominio del chat ya incorporaba reglas keyword, capa matematica y Naive Bayes.
Faltaba una capa de clasificacion en espacio vectorial para capturar similitud semantica con la hipotesis de contiguidad y mejorar el enrutado en consultas ambiguas.

## Decision
Se integra un clasificador vectorial local con tres modos:
- `rocchio`: centroides tf-idf normalizados por clase (default).
- `knn`: vecinos mas cercanos con votacion ponderada por similitud.
- `hybrid`: promedio de probabilidades Rocchio+kNN.

Se agrega rerank de dominios en chat condicionado por:
- umbral de confianza (`CLINICAL_CHAT_VECTOR_MIN_CONFIDENCE`),
- gating por incertidumbre matematica (`CLINICAL_CHAT_VECTOR_RERANK_WHEN_MATH_UNCERTAIN_ONLY`).

Ademas, el servicio incorpora evaluacion de clasificacion con:
- matriz de confusion,
- precision/recall/F1 por clase,
- macro/micro averaging.

## Alternativas consideradas
1. Mantener solo Naive Bayes + capa matematica.
- Rechazada por menor capacidad para modelar fronteras semanticas no lineales.

2. Sustituir por modelos neuronales de embedding clasificador.
- Rechazada por coste, latencia y mayor complejidad operativa.

## Consecuencias
- Mejora del enrutado semantico con coste cero en infraestructura externa.
- `rocchio` ofrece menor varianza y latencia mas estable.
- `knn` captura mejor formas complejas, con coste de inferencia mayor.

## Validacion
- ./venv/Scripts/python.exe -m ruff check app/services/clinical_vector_classification_service.py app/services/clinical_chat_service.py app/services/__init__.py app/core/config.py app/tests/test_clinical_vector_classification_service.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py
- ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_vector_classification_service.py -o addopts=""
- ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "vector_when_math_uncertain" -o addopts=""
- ./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -k "vector_" -o addopts=""

## Riesgos pendientes
- El entrenamiento pseudo-supervisado depende del catalogo interno; requiere dataset etiquetado para calibracion clinica robusta.
- `knn` puede degradar latencia si aumenta el conjunto de muestras sin indexacion adicional.
