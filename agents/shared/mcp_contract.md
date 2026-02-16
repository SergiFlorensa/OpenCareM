# Notas de Contrato MCP

## Servidor

- Archivo: `mcp_server/server.py`
- Transporte: `stdio`
- Variable principal: `TASK_API_BASE_URL`

## Herramientas actuales

- `list_tasks`
- `create_task`
- `get_task`
- `update_task`
- `delete_task`
- `tasks_stats_count`
- `openapi_schema`

## Reglas de versionado

- Cada cambio de endpoint debe reflejarse en tools afectadas.
- Si hay cambio rompedor, registrar decision en `docs/decisions/`.

## Validacion operativa

- Smoke manual oficial: `python -m mcp_server.smoke`.
- Smoke en tests: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_mcp_smoke.py`.


