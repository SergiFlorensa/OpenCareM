# Puertas de Calidad

Usa estos comandos como puertas estandar de validacion.

## Primero dirigido

- `.\venv\Scripts\python.exe -m pytest -q <tests-dirigidos>`

## Puertas completas

- `.\venv\Scripts\python.exe -m ruff check app mcp_server alembic`
- `.\venv\Scripts\python.exe -m black --check app mcp_server alembic`
- `.\venv\Scripts\python.exe -m mypy app mcp_server`
- `.\venv\Scripts\python.exe -m pytest -q`

## Politica de evidencia

Registrar comando + resumen del resultado en `agents/shared/test_plan.md`.

