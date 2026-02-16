def test_emergency_episode_happy_path_end_to_end(client):
    create_response = client.post(
        "/api/v1/emergency-episodes/",
        json={"origin": "walk_in", "notes": "Paciente llega por su pie"},
    )
    assert create_response.status_code == 201
    episode = create_response.json()
    episode_id = episode["id"]
    assert episode["current_stage"] == "admission"

    transitions = [
        {"next_stage": "nursing_triage"},
        {"next_stage": "immediate_care", "priority_risk": "time_dependent"},
        {"next_stage": "medical_evaluation"},
        {"next_stage": "diagnostics_ordered"},
        {"next_stage": "treatment_observation"},
        {"next_stage": "disposition_decision"},
        {"next_stage": "bed_request_transfer"},
        {"next_stage": "episode_closed"},
    ]
    for payload in transitions:
        response = client.post(
            f"/api/v1/emergency-episodes/{episode_id}/transition",
            json=payload,
        )
        assert response.status_code == 200

    final_response = client.get(f"/api/v1/emergency-episodes/{episode_id}")
    assert final_response.status_code == 200
    final_episode = final_response.json()
    assert final_episode["current_stage"] == "episode_closed"
    assert final_episode["disposition"] == "admission"
    assert final_episode["closed_at"] is not None

    kpi_response = client.get(f"/api/v1/emergency-episodes/{episode_id}/kpis")
    assert kpi_response.status_code == 200
    kpis = kpi_response.json()
    assert kpis["final_stage"] == "episode_closed"
    assert kpis["disposition"] == "admission"
    assert kpis["minutes_arrival_to_triage"] is not None


def test_emergency_episode_invalid_transition_returns_400(client):
    create_response = client.post(
        "/api/v1/emergency-episodes/",
        json={"origin": "ambulance_prealert"},
    )
    assert create_response.status_code == 201
    episode_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/emergency-episodes/{episode_id}/transition",
        json={"next_stage": "medical_evaluation"},
    )
    assert response.status_code == 400
    assert "Transicion invalida" in response.json()["detail"]


def test_emergency_episode_requires_priority_at_triage_exit(client):
    create_response = client.post(
        "/api/v1/emergency-episodes/",
        json={"origin": "walk_in"},
    )
    assert create_response.status_code == 201
    episode_id = create_response.json()["id"]

    triage_response = client.post(
        f"/api/v1/emergency-episodes/{episode_id}/transition",
        json={"next_stage": "nursing_triage"},
    )
    assert triage_response.status_code == 200

    response = client.post(
        f"/api/v1/emergency-episodes/{episode_id}/transition",
        json={"next_stage": "immediate_care"},
    )
    assert response.status_code == 400
    assert "priority_risk" in response.json()["detail"]
