# ADR-0015: Alertas baseline para salud de agentes

## Contexto

Ya existen metricas y dashboards de agentes, pero faltaba deteccion automatica de degradacion.

## Decision

Agregar reglas de Prometheus para:

- detectar corridas fallidas (`agent_runs_failed_total > 0`)
- detectar degradacion por fallback alto (`agent_fallback_rate_percent > 10`)

## Consecuencias

Beneficios:

- Detecta incidentes sin inspeccion manual.
- Mejora tiempos de respuesta operativa.

Costes:

- Posibles alertas ruido en entornos de prueba.
- Requiere ajuste de umbrales al crecer el sistema.

## Validacion

- `docker compose config`
- `http://127.0.0.1:9090/rules`



