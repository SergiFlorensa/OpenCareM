# ADR-0026 - Auditoria de Calidad de Screening Avanzado

## Estado

Aprobado

## Contexto

El workflow `advanced_screening_support_v1` ya genera recomendaciones operativas,
pero faltaba un mecanismo persistente para medir calidad real frente a decision humana.

Sin auditoria:

- no se puede cuantificar under/over-screening,
- no se puede calibrar reglas especificas (VIH, sepsis, COVID persistente, long-acting),
- no se puede cerrar el bucle de mejora continua.

## Decision

Implementar auditoria de screening con:

1. tabla `care_task_screening_audit_logs`;
2. endpoints de registro/listado/resumen por `CareTask`;
3. metrica de calidad global y por regla en Prometheus;
4. clasificacion global `match|under_screening|over_screening`.

## Consecuencias

### Positivas

- Trazabilidad completa IA vs humano para screening avanzado.
- Señales cuantitativas para calibrar reglas sin perder interpretabilidad.
- Base sólida para gates de calidad en CI y observabilidad en Grafana.

### Trade-offs

- Mayor complejidad de datos y mantenimiento de contratos.
- Necesidad de disciplina operativa para registrar validaciones humanas.

## Alternativas consideradas

- Validacion ad-hoc sin persistencia: descartado por baja auditabilidad.
- Solo metrica agregada global: descartado por falta de detalle por regla.
