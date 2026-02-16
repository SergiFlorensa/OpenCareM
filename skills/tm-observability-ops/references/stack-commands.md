# Comandos de la Pila

## Arrancar pila

- `docker compose up --build`

## Validar servicios

- API: `http://127.0.0.1:8000/health`
- Metricas: `http://127.0.0.1:8000/metrics`
- UI Prometheus: `http://127.0.0.1:9090`
- Targets Prometheus: `http://127.0.0.1:9090/targets`
- UI Grafana: `http://127.0.0.1:3000`

## Logs

- `docker compose logs -f api`
- `docker compose logs -f prometheus`
- `docker compose logs -f grafana`

