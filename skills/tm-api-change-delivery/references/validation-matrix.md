# Matriz de Validacion

## Minimo

- `.\venv\Scripts\python.exe -m pytest -q <tests-dirigidos>`

## Completo

- `.\venv\Scripts\python.exe -m ruff check app mcp_server alembic`
- `.\venv\Scripts\python.exe -m black --check app mcp_server alembic`
- `.\venv\Scripts\python.exe -m mypy app mcp_server`
- `.\venv\Scripts\python.exe -m pytest -q`

Ejecuta primero el minimo para iterar rapido y el completo antes de cerrar tarea.

