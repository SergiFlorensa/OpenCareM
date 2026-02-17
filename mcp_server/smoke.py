"""
Script ejecutable de prueba rapida MCP para verificacion local.

Uso:
  python -m mcp_server.smoke
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from mcp_server import client


def _unique_title() -> str:
    """Genera un titulo unico para evitar colisiones en ejecuciones repetidas."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"mcp-smoke-{timestamp}"


async def run_smoke() -> None:
    """Ejecuta un recorrido completo de herramientas MCP y falla si algo rompe."""
    title = _unique_title()
    created = await client.create_task(title=title, description="mcp smoke", completed=False)
    task_id = created["id"]

    listed = await client.list_tasks()
    if not any(item["id"] == task_id for item in listed):
        raise RuntimeError("Prueba MCP fallida: la tarea creada no aparece en list_tasks.")

    fetched = await client.get_task(task_id=task_id)
    if fetched["title"] != title:
        raise RuntimeError("Prueba MCP fallida: get_task devolvio un titulo inesperado.")

    updated = await client.update_task(task_id=task_id, completed=True)
    if updated["completed"] is not True:
        raise RuntimeError("Prueba MCP fallida: update_task no establecio completed=True.")

    stats = await client.tasks_stats_count()
    required_keys = {"total", "completed", "pending"}
    if not required_keys.issubset(stats.keys()):
        raise RuntimeError(
            "Prueba MCP fallida: la forma de respuesta de tasks_stats_count " "es invalida."
        )

    schema = await client.openapi_schema()
    if "paths" not in schema:
        raise RuntimeError("Prueba MCP fallida: openapi_schema no devolvio rutas.")

    await client.delete_task(task_id=task_id)
    print("Prueba MCP OK")


def main() -> None:
    """Punto de entrada CLI para ejecutar la prueba MCP manualmente."""
    asyncio.run(run_smoke())


if __name__ == "__main__":
    main()
