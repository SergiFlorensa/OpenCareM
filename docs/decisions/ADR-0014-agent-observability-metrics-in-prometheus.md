# ADR-0014: Metricas de agentes en Prometheus para dashboard operativo

## Contexto

Ya existian endpoints de historial y summary JSON, pero faltaba integracion directa con Prometheus/Grafana para observacion continua.

## Decision

Exportar metricas agregadas de agentes en `/metrics`:

- `agent_runs_total`
- `agent_runs_completed_total`
- `agent_runs_failed_total`
- `agent_steps_fallback_total`
- `agent_fallback_rate_percent`

Y agregar paneles dedicados en dashboard Grafana principal.

## Consecuencias

Beneficios:

- Visibilidad operativa continua sin llamadas manuales.
- Deteccion mas rapida de degradacion por fallback/fallos.

Costes:

- Consultas agregadas a DB en cada scrape de Prometheus.
- Necesidad de ajustar umbrales a medida que crece volumen.

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py`



