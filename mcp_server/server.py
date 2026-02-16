"""
Servidor MCP para la API de gestion de tareas.

Expone un conjunto de herramientas MCP que llaman por HTTP al servicio FastAPI activo.

Entorno:
  - TASK_API_BASE_URL (default: http://localhost:8000/api/v1)
"""

from __future__ import annotations

from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from mcp_server import client

mcp = FastMCP(
    name="task-manager-api",
    instructions=(
        "Herramientas para gestionar tareas. Requiere la API en ejecucion. "
        "Configura TASK_API_BASE_URL si la API usa otro host o puerto."
    ),
)


@mcp.tool(
    description="Lista tareas con paginacion opcional y filtro por completadas.",
)
async def list_tasks(
    skip: int = 0,
    limit: int = 100,
    completed: Optional[bool] = None,
) -> Any:
    return await client.list_tasks(skip=skip, limit=limit, completed=completed)


@mcp.tool(
    description="Crea una tarea nueva.",
)
async def create_task(
    title: str,
    description: Optional[str] = None,
    completed: bool = False,
) -> Any:
    return await client.create_task(title=title, description=description, completed=completed)


@mcp.tool(
    description="Obtiene una tarea por ID.",
)
async def get_task(task_id: int) -> Any:
    return await client.get_task(task_id=task_id)


@mcp.tool(
    description="Actualiza una tarea. Solo se modifican los campos enviados.",
)
async def update_task(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    completed: Optional[bool] = None,
) -> Any:
    return await client.update_task(
        task_id=task_id,
        title=title,
        description=description,
        completed=completed,
    )


@mcp.tool(
    description="Elimina una tarea por ID. Devuelve true si se elimina.",
)
async def delete_task(task_id: int) -> bool:
    return await client.delete_task(task_id=task_id)


@mcp.tool(
    description="Obtiene contadores de tareas (total/completadas/pendientes).",
)
async def tasks_stats_count() -> Any:
    return await client.tasks_stats_count()


@mcp.tool(
    description="Obtiene el esquema OpenAPI de la API (openapi.json).",
)
async def openapi_schema() -> Any:
    return await client.openapi_schema()


if __name__ == "__main__":
    mcp.run()
