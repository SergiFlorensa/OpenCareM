# Referencia de Herramientas MCP

Referencia de herramientas expuestas por `mcp_server/server.py`.

## Tabla de mapeo

- `list_tasks(skip=0, limit=100, completed=None)`
  - HTTP: `GET /tasks/`
  - Uso: listar tareas con filtros.
- `create_task(title, description=None, completed=False)`
  - HTTP: `POST /tasks/`
  - Uso: crear tarea.
- `get_task(task_id)`
  - HTTP: `GET /tasks/{task_id}`
  - Uso: leer una tarea puntual.
- `update_task(task_id, title=None, description=None, completed=None)`
  - HTTP: `PUT /tasks/{task_id}`
  - Uso: actualizar campos enviados.
- `delete_task(task_id)`
  - HTTP: `DELETE /tasks/{task_id}`
  - Uso: eliminar tarea por id.
- `tasks_stats_count()`
  - HTTP: `GET /tasks/stats/count`
  - Uso: totales y conteos por estado.
- `openapi_schema()`
  - HTTP: `GET /openapi.json`
  - Uso: inspeccionar contrato OpenAPI actual.

## Reglas de operacion

- Todas las herramientas dependen de `TASK_API_BASE_URL`.
- `openapi_schema` usa:
  - `TASK_API_ROOT_URL` si existe.
  - Si no existe, deriva desde `TASK_API_BASE_URL`.
- Los errores HTTP se elevan como `RuntimeError` con estado y cuerpo.

## Buenas practicas

- Antes de ejecutar lotes, usar `tasks_stats_count`.
- Para actualizaciones, enviar solo campos necesarios.
- Usar `openapi_schema` al cambiar contratos de API.




