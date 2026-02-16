from __future__ import annotations

import os
from typing import Any, Optional

import httpx


def base_url() -> str:
    base = os.getenv("TASK_API_BASE_URL", "http://localhost:8000/api/v1")
    return base.rstrip("/")


def url(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return f"{base_url()}{path}"


async def request(
    method: str, path: str, *, params: dict[str, Any] | None = None, json: Any = None
) -> Any:
    async with httpx.AsyncClient(timeout=15.0) as http_client:
        response = await http_client.request(
            method,
            url(path),
            params=params,
            json=json,
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text
            raise RuntimeError(
                f"Error de API {exc.response.status_code} llamando a {path}: {detail}"
            ) from exc
        if response.status_code == 204:
            return None
        return response.json()


async def list_tasks(
    skip: int = 0,
    limit: int = 100,
    completed: Optional[bool] = None,
) -> Any:
    params: dict[str, Any] = {"skip": skip, "limit": limit}
    if completed is not None:
        params["completed"] = completed
    return await request("GET", "/tasks/", params=params)


async def create_task(
    title: str, description: Optional[str] = None, completed: bool = False
) -> Any:
    payload = {"title": title, "description": description, "completed": completed}
    return await request("POST", "/tasks/", json=payload)


async def get_task(task_id: int) -> Any:
    return await request("GET", f"/tasks/{task_id}")


async def update_task(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    completed: Optional[bool] = None,
) -> Any:
    payload: dict[str, Any] = {}
    if title is not None:
        payload["title"] = title
    if description is not None:
        payload["description"] = description
    if completed is not None:
        payload["completed"] = completed
    return await request("PUT", f"/tasks/{task_id}", json=payload)


async def delete_task(task_id: int) -> bool:
    await request("DELETE", f"/tasks/{task_id}")
    return True


async def tasks_stats_count() -> Any:
    return await request("GET", "/tasks/stats/count")


async def openapi_schema() -> Any:
    api_root_url = os.getenv("TASK_API_ROOT_URL")
    if not api_root_url:
        base = base_url()
        if base.endswith("/api/v1"):
            api_root_url = base[: -len("/api/v1")]
        else:
            api_root_url = base
    api_root_url = api_root_url.rstrip("/")
    async with httpx.AsyncClient(timeout=15.0) as http_client:
        response = await http_client.get(f"{api_root_url}/openapi.json")
        response.raise_for_status()
        return response.json()
