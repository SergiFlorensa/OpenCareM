# Guia Operativa de Prueba MCP

Este documento define como validar rapidamente que las tools MCP siguen operativas.

## Objetivo

- Verificar roundtrip completo del MCP contra la API real.
- Detectar roturas de contrato de forma temprana.

## Script oficial

- Archivo: `mcp_server/smoke.py`
- Comando: `python -m mcp_server.smoke`

## Prerrequisitos

1. API levantada (`uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`).
2. Variable `TASK_API_BASE_URL` correcta (por defecto `http://localhost:8000/api/v1`).

## Que valida el smoke

1. `create_task`
2. `list_tasks`
3. `get_task`
4. `update_task`
5. `tasks_stats_count`
6. `openapi_schema`
7. `delete_task`

Si todo sale bien, imprime `MCP smoke OK`.

## Validacion automatizada en tests

- Test: `app/tests/test_mcp_smoke.py`
- Comando: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_mcp_smoke.py`

## Riesgos pendientes

- El smoke manual depende de API en ejecucion.
- Aun no hay smoke remoto contra entorno staging.


