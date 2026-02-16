def test_create_and_get_task(client):
    create_response = client.post(
        "/api/v1/tasks/",
        json={"title": "Test API", "description": "Create and get", "completed": False},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["title"] == "Test API"
    assert created["completed"] is False
    assert "id" in created

    task_id = created["id"]
    get_response = client.get(f"/api/v1/tasks/{task_id}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["id"] == task_id
    assert fetched["title"] == "Test API"


def test_list_filter_and_stats(client):
    client.post("/api/v1/tasks/", json={"title": "Pending task", "completed": False})
    client.post("/api/v1/tasks/", json={"title": "Done task", "completed": True})

    all_response = client.get("/api/v1/tasks/")
    assert all_response.status_code == 200
    assert len(all_response.json()) == 2

    completed_response = client.get("/api/v1/tasks/?completed=true")
    assert completed_response.status_code == 200
    completed_items = completed_response.json()
    assert len(completed_items) == 1
    assert completed_items[0]["completed"] is True

    stats_response = client.get("/api/v1/tasks/stats/count")
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["total"] == 2
    assert stats["completed"] == 1
    assert stats["pending"] == 1


def test_update_delete_and_not_found(client):
    create_response = client.post(
        "/api/v1/tasks/",
        json={"title": "To update", "completed": False},
    )
    task_id = create_response.json()["id"]

    update_response = client.put(
        f"/api/v1/tasks/{task_id}", json={"completed": True, "title": "Updated"}
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["completed"] is True
    assert updated["title"] == "Updated"

    delete_response = client.delete(f"/api/v1/tasks/{task_id}")
    assert delete_response.status_code == 204

    get_deleted_response = client.get(f"/api/v1/tasks/{task_id}")
    assert get_deleted_response.status_code == 404
