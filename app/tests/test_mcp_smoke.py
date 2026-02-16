import pytest

from mcp_server import client as mcp_client


@pytest.mark.asyncio
async def test_mcp_tools_smoke(client, monkeypatch):
    async def fake_request(method, path, *, params=None, json=None):
        response = client.request(method, f"/api/v1{path}", params=params, json=json)
        if response.status_code >= 400:
            raise RuntimeError(f"API error {response.status_code}: {response.text}")
        if response.status_code == 204:
            return None
        return response.json()

    monkeypatch.setattr(mcp_client, "request", fake_request)

    async def fake_openapi_schema():
        response = client.get("/openapi.json")
        if response.status_code >= 400:
            raise RuntimeError(f"API error {response.status_code}: {response.text}")
        return response.json()

    monkeypatch.setattr(mcp_client, "openapi_schema", fake_openapi_schema)

    created = await mcp_client.create_task(title="MCP task", description="smoke", completed=False)
    assert created["title"] == "MCP task"
    task_id = created["id"]

    listed = await mcp_client.list_tasks()
    assert any(item["id"] == task_id for item in listed)

    updated = await mcp_client.update_task(task_id=task_id, completed=True)
    assert updated["completed"] is True

    stats = await mcp_client.tasks_stats_count()
    assert stats["total"] >= 1

    schema = await mcp_client.openapi_schema()
    assert "openapi" in schema
    assert "/api/v1/tasks/" in schema["paths"]

    deleted = await mcp_client.delete_task(task_id=task_id)
    assert deleted is True
