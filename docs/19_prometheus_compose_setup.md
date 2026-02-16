# Configuracion de Prometheus en Compose

Guia para levantar Prometheus junto a la API usando Docker Compose.

## Objetivo

- Tener scraping continuo de metricas sin hacerlo manual en Postman.
- Ver estado de targets y consultas en la UI de Prometheus.

## Archivos implicados

- `docker-compose.yml`
- `ops/prometheus/prometheus.yml`

## Que se levanta

- `api` en `http://localhost:8000`
- `prometheus` en `http://localhost:9090`
- `grafana` en `http://localhost:3000`

Prometheus scrapea:

- target interno: `api:8000`
- endpoint: `/metrics`

## Arranque paso a paso

1. Levantar stack:
   - `docker compose up --build`
2. Comprobar API:
   - `http://127.0.0.1:8000/health`
3. Entrar a Prometheus:
   - `http://127.0.0.1:9090`
4. Ver targets:
   - `http://127.0.0.1:9090/targets`
   - Esperado: job `task_manager_api` en `UP`.

## Primera consulta recomendada

En `http://127.0.0.1:9090/graph`:

- `http_requests_total`
- `rate(http_requests_total[1m])`
- `http_request_duration_seconds_sum`

## Diagnostico rapido

Si target sale `DOWN`:

1. Revisar logs API:
   - `docker compose logs -f api`
2. Revisar logs Prometheus:
   - `docker compose logs -f prometheus`
3. Confirmar que `/metrics` responde dentro del contenedor API.

## Riesgos pendientes

- Falta almacenamiento persistente dedicado para Prometheus.
- Falta dashboard de Grafana y alertas.


