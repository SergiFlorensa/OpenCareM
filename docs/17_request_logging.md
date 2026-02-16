# Request Logging

Este documento define el logging estructurado por request en la API.

## Objetivo

- Tener trazabilidad por peticion HTTP.
- Facilitar diagnostico con un identificador unico (`request_id`).
- Medir latencia por endpoint sin herramientas externas.

## Implementacion

- Middleware HTTP en `app/main.py`.
- Campos registrados en cada request:
  - `event`: `http_request`
  - `request_id`
  - `method`
  - `path`
  - `status_code`
  - `duration_ms`

## Header de trazabilidad

La API devuelve `X-Request-ID` en cada respuesta:

- Si el cliente envia `X-Request-ID`, se conserva.
- Si no lo envia, la API genera uno automaticamente.

## Ejemplo de uso

1. Cliente hace request a `/health`.
2. API responde con `X-Request-ID`.
3. En logs queda una linea con ese mismo `request_id`.
4. Se puede correlacionar request-respuesta-log rapidamente.

## Validacion

- Test: `app/tests/test_request_logging.py`
- Comando:
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_request_logging.py`

## Riesgos pendientes

- Aun no se exportan logs en formato JSON nativo para agregadores.
- No hay inclusion de `request_id` en respuestas de error personalizadas.


