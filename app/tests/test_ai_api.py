from app.core.config import settings
from app.schemas.ai import TaskTriageResponse
from app.services.llm_triage_provider import LLMTriageProvider


def test_ai_triage_bug_goes_high_priority(client):
    response = client.post(
        "/api/v1/ai/triage-task",
        json={
            "title": "Fix production bug in auth",
            "description": "Critical error when users login",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["category"] == "bug"
    assert payload["priority"] == "high"
    assert payload["confidence"] >= 0.8
    assert payload["source"] in {"rules", "rules_fallback"}


def test_ai_triage_docs_goes_low_priority(client):
    response = client.post(
        "/api/v1/ai/triage-task",
        json={
            "title": "Update docs for docker setup",
            "description": "Improve onboarding guide",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["category"] == "docs"
    assert payload["priority"] == "low"
    assert payload["source"] in {"rules", "rules_fallback"}


def test_ai_triage_general_returns_safe_defaults(client):
    response = client.post(
        "/api/v1/ai/triage-task",
        json={
            "title": "Review pending work",
            "description": "Check status and align next steps",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["category"] in {"general", "analysis", "dev"}
    assert payload["priority"] in {"low", "medium", "high"}
    assert 0 <= payload["confidence"] <= 1
    assert isinstance(payload["reason"], str)
    assert payload["source"] in {"rules", "rules_fallback"}


def test_ai_triage_hybrid_mode_uses_llm_when_available(client, monkeypatch):
    monkeypatch.setattr(settings, "AI_TRIAGE_MODE", "hybrid")

    def fake_llm(title: str, description: str | None = None):
        return TaskTriageResponse(
            priority="medium",
            category="analysis",
            confidence=0.91,
            reason="Mocked LLM result.",
            source="llm",
        )

    monkeypatch.setattr(LLMTriageProvider, "suggest_task_metadata", fake_llm)

    response = client.post(
        "/api/v1/ai/triage-task",
        json={"title": "Investigate vector embeddings", "description": "Check RAG quality"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "llm"
    assert payload["reason"] == "Mocked LLM result."


def test_ai_triage_hybrid_mode_falls_back_to_rules(client, monkeypatch):
    monkeypatch.setattr(settings, "AI_TRIAGE_MODE", "hybrid")
    monkeypatch.setattr(
        LLMTriageProvider,
        "suggest_task_metadata",
        lambda title, description=None: None,
    )

    response = client.post(
        "/api/v1/ai/triage-task",
        json={"title": "Update docs", "description": "Add onboarding details"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "rules_fallback"
    assert "Fallback de modo hibrido" in payload["reason"]
