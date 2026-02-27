# ADR-0113: Clasificacion supervisada Naive Bayes para rerank de dominio en chat clinico

## Estado
Aceptado

## Contexto
El enrutado de dominio del chat ya disponia de reglas keyword y capa matematica local.
En consultas ambiguas o con variacion terminologica, la seleccion de dominio podia degradarse y caer en rutas genericas.
Se necesitaba una capa probabilistica supervisada, local y sin coste, para reforzar validez del dominio top antes del retrieval/respuesta.

## Decision
Se incorpora un clasificador Naive Bayes local en `clinical_chat_service` para estimar dominio probable de consulta y reordenar candidatos.

- Modelos soportados:
  - multinomial
  - bernoulli
- Entrenamiento:
  - pseudo-supervisado sobre catalogo de dominios interno (`_DOMAIN_CATALOG`) usando `key`, `label`, `summary`, `keywords`.
- Seguridad numerica:
  - scoring en log-probabilidades.
  - smoothing Laplace (`alpha`) configurable.
- Seleccion de features configurable:
  - `chi2`
  - `mi`
  - `none`
- Rerank:
  - aplica cuando `nb_top_probability` supera umbral (`CLINICAL_CHAT_NB_MIN_CONFIDENCE`).
  - por defecto solo cuando la capa matematica esta incierta (`CLINICAL_CHAT_NB_RERANK_WHEN_MATH_UNCERTAIN_ONLY=true`).
- Observabilidad:
  - trazas `nb_*` en `interpretability_trace`.
  - evaluacion de clasificacion con precision/recall/F1 por clase y agregados macro/micro.

## Alternativas consideradas
1. Mantener solo reglas + capa matematica existente.
- Rechazada por menor robustez ante sinonimia y consultas clinicas ambiguas.

2. Sustituir por modelo neuronal de clasificacion.
- Rechazada por coste/latencia y dependencia de entrenamiento etiquetado adicional.

## Consecuencias
- Mejora esperada de precision de enrutado en consultas con senal semantica difusa.
- Configuracion sensible a umbral de confianza en escenario multiclase.
- La calidad depende del mantenimiento del catalogo y futuros datasets etiquetados.

## Validacion
- ./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/clinical_naive_bayes_service.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_naive_bayes_service.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py
- ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_naive_bayes_service.py -o addopts=""
- ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "test_chat_domain_rerank_uses_naive_bayes_when_math_uncertain" -o addopts=""
- ./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -k "nb_ or naive_bayes or invalid_nb" -o addopts=""
- ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_naive_bayes_service.py -o addopts=""

## Riesgos pendientes
- Entrenamiento pseudo-supervisado puede introducir sesgo de keywords; requiere calibracion futura con gold etiquetado por especialidad.
- Si el umbral de confianza es alto, el rerank no dispara; si es muy bajo, puede sobre-rerank. Default ajustado a 0.25.
