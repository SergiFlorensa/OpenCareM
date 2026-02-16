from app.services.clinical_chat_service import ClinicalChatService
from app.services.llm_chat_provider import LLMChatProvider


def _auth_headers(client, username: str):
    register = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": "StrongPass123", "specialty": "emergency"},
    )
    assert register.status_code == 200
    login = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": "StrongPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_follow_up_query_expansion_uses_previous_context():
    effective, expanded = ClinicalChatService._compose_effective_query(
        query="y ahora?",
        recent_dialogue=[
            {
                "user_query": "Paciente con sepsis y TAS 85, prioriza bundle.",
                "assistant_answer": "Activa bundle 1 hora y monitoriza MAP.",
            }
        ],
    )
    assert expanded is True
    assert "Seguimiento: y ahora?" in effective


def test_llm_provider_prefers_ollama_chat_endpoint(monkeypatch):
    called: list[str] = []

    def fake_request(*, endpoint, payload):
        called.append(endpoint)
        if endpoint == "api/chat":
            return {"message": {"content": "Respuesta desde chat"}}
        return {"response": "fallback"}

    monkeypatch.setattr("app.services.llm_chat_provider.settings.CLINICAL_CHAT_LLM_ENABLED", True)
    monkeypatch.setattr(LLMChatProvider, "_request_ollama_json", staticmethod(fake_request))

    answer, trace = LLMChatProvider.generate_answer(
        query="resume el plan",
        response_mode="clinical",
        effective_specialty="emergency",
        tool_mode="chat",
        matched_domains=["sepsis"],
        matched_endpoints=["/api/v1/care-tasks/1/sepsis/recommendation"],
        memory_facts_used=["termino:sepsis"],
        patient_summary=None,
        patient_history_facts_used=[],
        knowledge_sources=[],
        web_sources=[],
        recent_dialogue=[],
        endpoint_results=[],
    )

    assert answer == "Respuesta desde chat"
    assert called[0] == "api/chat"
    assert trace["llm_endpoint"] == "chat"


def test_chat_e2e_three_turns_continuity_and_trace(client, monkeypatch):
    headers = _auth_headers(client, "chat_trace_user")
    create_task = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso continuidad 3 turnos",
            "clinical_priority": "high",
            "specialty": "emergency",
            "patient_reference": "PAC-TRACE-1",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task.status_code == 201
    task_id = create_task.json()["id"]

    def fake_generate_answer(**kwargs):
        return (
            "Plan contextual con recomendaciones internas y validacion humana.",
            {
                "llm_used": "true",
                "llm_model": "llama3.1:8b",
                "llm_endpoint": "chat",
                "llm_latency_ms": "12.5",
            },
        )

    monkeypatch.setattr(LLMChatProvider, "generate_answer", staticmethod(fake_generate_answer))

    first = client.post(
        f"/api/v1/care-tasks/{task_id}/chat/messages",
        json={"query": "Sospecha de sepsis con lactato 4", "session_id": "session-e2e"},
        headers=headers,
    )
    second = client.post(
        f"/api/v1/care-tasks/{task_id}/chat/messages",
        json={"query": "resume", "session_id": "session-e2e", "tool_mode": "chat"},
        headers=headers,
    )
    third = client.post(
        f"/api/v1/care-tasks/{task_id}/chat/messages",
        json={"query": "y ahora?", "session_id": "session-e2e", "tool_mode": "treatment"},
        headers=headers,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 200

    payload = third.json()
    assert payload["answer"] != ""
    assert any(item == "query_expanded=1" for item in payload["interpretability_trace"])
    assert any(item == "llm_endpoint=chat" for item in payload["interpretability_trace"])
    assert any(item.startswith("matched_endpoints=") for item in payload["interpretability_trace"])
