# ADR-0117: Clustering jerarquico (HAC/divisive/buckshot) para rerank de dominio clinico

## Estado
Aceptado

## Contexto
El chat ya contaba con rerank por capa matematica, clasificadores supervisados y clustering plano.
Faltaba una capa jerarquica para capturar estructura multinivel entre dominios y ofrecer una alternativa robusta cuando el agrupamiento plano no separa bien consultas ambiguas.

## Decision
Se integra `ClinicalHierarchicalClusteringService` con:
- metodos `hac_single`, `hac_complete`, `hac_average`, `divisive`, `buckshot`,
- seleccion de K por objetivo de calidad ponderado en rango configurable (`purity`, `nmi`, `f_measure`),
- etiquetado diferencial basico por cluster,
- trazas operativas `hcluster_*`,
- rerank condicional en chat por confianza minima y gate opcional de incertidumbre matematica.

## Alternativas consideradas
1. Mantener solo clustering plano.
- Rechazada por menor capacidad de representar estructura jerarquica y por sensibilidad a geometria fija de centroides.

2. Usar solo HAC average.
- Rechazada para permitir flexibilidad operativa y control de coste (divisive/buckshot en escenarios de mayor volumen).

3. Learning-to-rank adicional inmediato.
- Rechazada en esta fase por coste de entrenamiento/curacion; se mantiene roadmap incremental.

## Consecuencias
- Mejora la priorizacion de dominios en consultas ambiguas con una capa no supervisada adicional.
- Aumenta auditabilidad del enrutado con señales de linkage/estrategia y calidad del cluster.
- Introduce nuevos hiperparametros que requieren calibracion periodica.

## Validacion
- `./venv/Scripts/python.exe -m ruff check app/services/clinical_hierarchical_clustering_service.py app/services/clinical_chat_service.py app/services/__init__.py app/core/config.py app/tests/test_clinical_hierarchical_clustering_service.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_hierarchical_clustering_service.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py -k "hcluster or hierarchical" -o addopts=""`

## Riesgos pendientes
- HAC completo puede crecer en coste si aumenta significativamente el numero de muestras de entrenamiento.
- El etiquetado diferencial de cluster es heuristico y no sustituye validacion clinica experta.
