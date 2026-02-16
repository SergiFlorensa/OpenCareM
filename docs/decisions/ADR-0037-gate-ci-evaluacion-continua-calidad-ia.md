# ADR-0037: Gate CI de evaluacion continua para calidad IA clinica

- Fecha: 2026-02-12
- Estado: aceptada

## Contexto

El proyecto ya dispone de scorecard global y alertas en Prometheus/Grafana, pero esa deteccion ocurre en runtime.
Necesitamos una barrera previa en CI para evitar desplegar regresiones de calidad.

## Decision

Se introduce un gate de evaluacion continua en CI basado en una suite dedicada:

- `app/tests/test_quality_regression_gate.py`
- runner: `app/scripts/run_quality_gate.py`
- step en CI: `python app/scripts/run_quality_gate.py`

La suite valida:

- escenario controlado con umbrales operativos
- escenario degradado para verificar deteccion de riesgo

## Consecuencias

### Positivas

- Se bloquean regresiones antes de despliegue.
- Se estandariza un criterio minimo de calidad global.
- Se refuerza trazabilidad tecnica y clinica en auditoria interna.

### Costes / trade-offs

- Incremento del tiempo de CI por una suite adicional.
- Mantenimiento de tests cuando evolucionen reglas de auditoria.

## Alternativas consideradas

1. Solo alertas en runtime
   - Rechazada: detecta tarde y con coste operativo.
2. Revisiones manuales ad hoc
   - Rechazada: no escalable ni reproducible.
3. Gate automatizado en CI
   - Elegida: reproducible, auditable y preventiva.
