# ADR-0116: Clustering plano (k-means + EM) para rerank de dominio clinico

## Estado
Aceptado

## Contexto
El chat ya integraba rerank por capa matematica, clasificacion vectorial, Naive Bayes y SVM.
Faltaba una capa no supervisada para agrupar dominios por similitud semantica y reducir el espacio candidato bajo incertidumbre, siguiendo la hipotesis de clustering.

## Decision
Se integra `ClinicalFlatClusteringService` con:
- k-means sobre vectores tf-idf (seleccion de K por AIC aproximado: `RSS + 2*M*K`),
- refinamiento EM opcional para asignacion blanda,
- metricas de calidad externa frente a etiquetas base del catalogo: `purity`, `nmi`, `rand_index`, `f_measure(beta)`,
- deteccion de singleton clusters para trazabilidad de outliers,
- trazas operativas `cluster_*` y rerank condicional de dominios en chat.

El rerank por clustering se aplica cuando:
- `CLINICAL_CHAT_CLUSTER_ENABLED=true`,
- confianza del cluster top supera umbral,
- y (por defecto) la capa matematica esta en incertidumbre no baja.

## Alternativas consideradas
1. No incorporar clustering y mantener solo clasificadores supervisados.
- Rechazada por menor capacidad de descubrir vecindades semanticas no etiquetadas.

2. Clustering jerarquico completo.
- Rechazada por mayor coste computacional y menor simplicidad operativa para latencia objetivo.

3. EM puro sin inicializacion.
- Rechazada por sensibilidad a optimos locales; se prefiere inicializacion por k-means.

## Consecuencias
- Mejora la priorizacion de dominios semanticos en consultas ambiguas.
- Aporta auditabilidad cuantitativa del agrupamiento sin coste externo.
- Introduce nuevos hiperparametros de clustering que requieren calibracion operativa periodica.

## Validacion
- `./venv/Scripts/python.exe -m ruff check app/services/clinical_flat_clustering_service.py app/services/clinical_chat_service.py app/core/config.py app/tests/test_clinical_flat_clustering_service.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_flat_clustering_service.py app/tests/test_clinical_chat_operational.py -k "cluster" -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -k "cluster" -o addopts=""`

## Riesgos pendientes
- El clustering se basa en catalogo pseudo-etiquetado de dominios; requiere recalibracion al crecer o cambiar el catalogo.
- K seleccionado por AIC aproximado puede no ser optimo en distribuciones muy no isotropicas; conviene monitorizar `cluster_nmi` y `cluster_f_measure` en regresion.
