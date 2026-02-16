# Consultas de Dashboard

Usa estas consultas en Prometheus/Grafana.

## Tasa de peticiones

- `sum(rate(http_requests_total[1m])) by (handler, method, status)`

## Latencia p95

- `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, handler, method))`

## Ratio 5xx

- `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))`

## Disponibilidad del objetivo

- `up`

