# ADR-0004: Prometheus en Docker Compose para scraping local

## Contexto

La API ya exponia `/metrics`, pero el scraping era manual.
Faltaba una forma reproducible de observabilidad continua en entorno local.

## Decision

Integrar un servicio `prometheus` en `docker-compose.yml` usando:

- imagen `prom/prometheus`
- configuracion en `ops/prometheus/prometheus.yml`
- scrape de `api:8000/metrics`

## Consecuencias

Beneficios:

- Observabilidad local continua sin pasos manuales.
- Base lista para evolucionar a dashboards y alertas.
- Flujo de validacion mas parecido a entorno real.

Coste:

- Un servicio extra en Compose.
- Necesidad de mantener la configuracion de scrape.

## Validacion

- `docker compose config`
- `http://127.0.0.1:9090/targets` con job `task_manager_api` en `UP`



