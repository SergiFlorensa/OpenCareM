---
name: tm-observability-ops
description: "Opera y resuelve problemas de la pila local de observabilidad de este repositorio (metricas API, scraping de Prometheus, dashboards de Grafana) usando docker compose. Usar cuando se pregunte por /metrics, targets caidos, paneles Grafana, validacion de telemetria o cambios de configuracion Prometheus/Grafana."
---

# TM Operaciones de Observabilidad

## Vision general

Usa esta skill para mantener la observabilidad accionable y reproducible entre sesiones.

## Flujo operativo

1. Carga `references/stack-commands.md` y empieza por chequeos de salud.
2. Valida scraping (`/metrics`, targets de Prometheus).
3. Valida visualizacion (datasource y paneles de Grafana).
4. Si aparecen fallos, carga `references/troubleshooting.md`.
5. Registra evidencia en task board y notas de despliegue.

## Flujo de consultas

Carga `references/dashboard-queries.md` para consultas practicas de Prometheus.
Prioriza chequeos pequenos (`up`, tasa de peticiones, cuantiles de latencia, ratio 5xx).

## Regla de cambios

Si editas compose o configuracion de observabilidad:

- ejecuta `docker compose config`,
- actualiza docs en `docs/07_*`, `docs/19_*`, `docs/20_*`,
- registra riesgos/notas en `agents/shared/deploy_notes.md`.

