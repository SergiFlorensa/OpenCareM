# ADR-0153: Regression Set de Chat para Continual Learning Offline

## Estado

Aprobado

## Contexto

El sistema necesita aprendizaje continuo sin coste y sin reentrenar modelos en caliente.
La forma mas segura y reproducible es evaluar periodicamente el comportamiento del chat
contra un conjunto de regresion derivado del historico validado.

## Decision

1. Añadir export de Regression Set desde `care_task_chat_messages`:
   - script `build_chat_regression_set.py`.
   - filtra respuestas con baja señal (sin fuentes, muy cortas o con leakage interno).
2. Añadir evaluacion automatica del set contra backend actual:
   - script `evaluate_chat_regression.py`.
   - metricas: `token_f1_avg`, `domain_hit_rate`, `must_include_rate`,
     `forbidden_leak_rate`, `latency_p95_ms`.
3. Mantener enfoque determinista y auditable:
   - sin cambios de schema DB.
   - artefactos en `tmp/` para ejecucion local/CI.

## Consecuencias

- Permite detectar regresiones funcionales sin depender de proveedores externos.
- Facilita ciclo de mejora incremental (regenerar set, reevaluar, ajustar reglas).
- Riesgo: sesgo temporal del dataset si no se renueva; se recomienda regeneracion periodica.
