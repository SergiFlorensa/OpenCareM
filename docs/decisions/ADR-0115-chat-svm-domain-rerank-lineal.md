# ADR-0115: Clasificacion SVM lineal OVA para rerank de dominio clinico

## Estado
Aceptado

## Contexto
El chat ya contaba con capas de enrutado por reglas, inferencia matematica, Naive Bayes y clasificacion vectorial.
Faltaba una capa SVM supervisada que maximizara margen para robustez ante ruido en consultas clinicas.

En la primera version del SVM OVA, el `bias` del hiperplano dominaba el score de inferencia por desbalance de clases (pocos positivos por dominio), causando priorizacion incorrecta de `critical_ops`.

## Decision
Se integra `ClinicalSVMDomainService` con:
- entrenamiento SVM lineal one-vs-rest,
- regularizacion configurable (`C`, `L2`, `epochs`),
- trazabilidad operativa `svm_domain_*`,
- evaluacion con matriz de confusion y metricas macro/micro.

Para inferencia, se adopta:
- score basado en componente discriminativa `w·x` (sin sumar `bias` al ranking),
- prior suave por dominio/especialidad para desempates,
- calibracion de logits con escala fija para estabilizar probabilidad top y gating de rerank.

## Alternativas consideradas
1. Mantener solo Naive Bayes + vectorial.
- Rechazada por menor control del margen de separacion.

2. Usar SVM con kernel no lineal.
- Rechazada por coste/latencia superior y menor interpretabilidad operativa.

3. Conservar `bias` completo en inferencia.
- Rechazada por sesgo sistematico en catalogo pseudo-etiquetado desbalanceado.

## Consecuencias
- Mejora el rerank en consultas clinicas con terminologia especifica (ej. oncologia/neutropenia).
- Se reduce deriva a dominios generales por sesgo de intercepto.
- La calibracion requiere revisarse si cambia sustancialmente el catalogo de dominios.

## Validacion
- `./venv/Scripts/python.exe -m ruff check app/services/clinical_svm_domain_service.py app/tests/test_clinical_svm_domain_service.py app/tests/test_clinical_chat_operational.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_svm_domain_service.py app/tests/test_clinical_chat_operational.py -k "svm_domain" -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -k "svm_domain" -o addopts=""`

## Riesgos pendientes
- El entrenamiento sigue pseudo-supervisado sobre catalogo interno; puede requerir calibracion por dominio al crecer la base.
- La escala fija de logits puede necesitar ajuste para mantener estabilidad de probabilidades en escenarios multiclase mas grandes.
