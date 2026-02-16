# ADR-0029: Auditoria de Calidad Medico-Legal

## Estado

Aprobado

## Contexto

Ya existe el motor `medicolegal_ops_support_v1`, pero faltaba medir su calidad real
frente a revision humana en escenarios operativos de urgencias.

Sin auditoria:

- no se detecta under-risk legal,
- no se cuantifica precision de reglas clave,
- no hay base objetiva para mejora continua del motor.

## Decision

Agregar auditoria persistida IA vs humano para medico-legal:

- tabla `care_task_medicolegal_audit_logs`,
- endpoints de registro/listado/resumen por `CareTask`,
- metricas Prometheus de volumen, desviacion y match por regla.

## Consecuencias

### Positivas

- trazabilidad de calidad del motor medico-legal,
- deteccion temprana de under/over en riesgo legal,
- priorizacion de mejoras por regla concreta (consentimiento, judicial, custodia).

### Costes / Riesgos

- aumento de complejidad de datos y paneles,
- necesidad de mantener criterios humanos consistentes para evitar sesgo de auditoria.

## Validacion

- tests de API para `POST/GET/GET summary`,
- tests de metricas `medicolegal_audit_*` en `/metrics`,
- regresion completa de `app/tests`.
