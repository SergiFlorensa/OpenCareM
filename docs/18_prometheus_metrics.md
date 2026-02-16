# Metricas de Prometheus

Este documento explica que es Prometheus, para que sirve y como lo usamos en este proyecto.

## Que es Prometheus (aterrizado)

Prometheus es un sistema que:

1. Entra a una URL de metricas (por ejemplo `/metrics`).
2. Lee numeros de estado del sistema (peticiones, latencia, errores, etc.).
3. Guarda esos datos en el tiempo para poder consultarlos y alertar.

En resumen:

- Logs te cuentan *historias* (texto de eventos).
- Metricas te dan *numeros* para ver salud y tendencia.

## Que problema resuelve

Sin metricas, puedes saber que algo fallo, pero no:

- cuantas veces falla,
- desde cuando empezo,
- si la latencia subio de forma sostenida.

Con Prometheus puedes responder eso en segundos.

## Implementacion en este proyecto

Se instrumenta FastAPI en `app/main.py` con `prometheus-fastapi-instrumentator` y se expone:

- `GET /metrics`

Ese endpoint devuelve texto en formato Prometheus.

## Que metricas HTTP obtienes aqui

En esta fase, Prometheus recoge metricas de trÃ¡fico HTTP de la API, por ejemplo:

- volumen de requests,
- distribucion de codigos HTTP,
- duracion/latencia de requests.

## Como practicarlo paso a paso (manual)

1. Levanta API:
   - `python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
2. Genera trafico:
   - `GET /health`
   - `GET /api/v1/tasks/`
3. Abre metricas:
   - `http://127.0.0.1:8000/metrics`
4. Busca lineas con `http_requests_total` o `http_request_duration_seconds`.

## Ejemplo real de uso operativo

Si un cliente reporta lentitud:

1. Revisas `http_request_duration_seconds`.
2. Filtras por ruta/estado.
3. Confirmas si la latencia subio en los ultimos minutos.
4. Cruzas con logs usando `X-Request-ID` para casos puntuales.

## Pruebas en este repo

- `app/tests/test_metrics_endpoint.py`

Valida que:

- `/metrics` existe y responde `200`.
- El body contiene series Prometheus de HTTP.

## Relacion con lo que ya tenemos

- `docs/17_request_logging.md` -> trazabilidad por request individual.
- `docs/18_prometheus_metrics.md` -> salud agregada en el tiempo.

Ambos se complementan: logs para detalle, metricas para panorama.

## Riesgos pendientes

- Aun no hay servidor Prometheus levantado para scraping continuo.
- Aun no hay dashboard (ej. Grafana) ni alertas.


