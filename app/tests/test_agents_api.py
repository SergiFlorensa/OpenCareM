from datetime import datetime, timedelta, timezone

from app.models.agent_run import AgentRun, AgentStep
from app.schemas.ai import TaskTriageResponse
from app.services.ai_triage_service import AITriageService


def test_agents_run_persists_run_and_step_trace(client, db_session):
    response = client.post(
        "/api/v1/agents/run",
        json={
            "workflow_name": "task_triage_v1",
            "title": "Fix bug in login flow",
            "description": "Users fail with auth error in production",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["workflow_name"] == "task_triage_v1"
    assert len(payload["steps"]) == 1
    assert payload["steps"][0]["step_name"] == "triage_task"
    assert payload["steps"][0]["decision"] in {"use_model_output", "fallback_safe_defaults"}

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["id"]).first()
    assert run is not None
    assert run.run_input["title"] == "Fix bug in login flow"
    steps = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).all()
    assert len(steps) == 1
    assert steps[0].step_input["title"] == "Fix bug in login flow"


def test_agents_run_applies_fallback_when_confidence_is_low(client, monkeypatch):
    def low_confidence_triage(title: str, description: str | None = None):
        return TaskTriageResponse(
            priority="low",
            category="docs",
            confidence=0.40,
            reason="Low confidence test scenario.",
            source="rules",
        )

    monkeypatch.setattr(AITriageService, "suggest_task_metadata", low_confidence_triage)

    response = client.post(
        "/api/v1/agents/run",
        json={
            "workflow_name": "task_triage_v1",
            "title": "Any title",
            "description": "Any description",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    step = payload["steps"][0]
    assert step["fallback_used"] is True
    assert step["decision"] == "fallback_safe_defaults"
    triage_output = payload["run_output"]["triage"]
    assert triage_output["priority"] == "medium"
    assert triage_output["category"] == "general"


def test_agents_run_rejects_unknown_workflow(client):
    response = client.post(
        "/api/v1/agents/run",
        json={
            "workflow_name": "unknown_workflow",
            "title": "Task title",
            "description": "Task description",
        },
    )
    assert response.status_code == 422


def test_agents_runs_list_returns_recent_runs(client):
    for index in range(2):
        response = client.post(
            "/api/v1/agents/run",
            json={
                "workflow_name": "task_triage_v1",
                "title": f"Investigate vector embeddings {index}",
                "description": "Evaluate prompt strategy and model behavior",
            },
        )
        assert response.status_code == 200

    response = client.get("/api/v1/agents/runs?limit=1")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["workflow_name"] == "task_triage_v1"
    assert payload[0]["status"] == "completed"


def test_agents_run_detail_returns_steps(client):
    create_response = client.post(
        "/api/v1/agents/run",
        json={
            "workflow_name": "task_triage_v1",
            "title": "Investigate vector embeddings for RAG",
            "description": "Evaluate prompt strategy and model behavior",
        },
    )
    assert create_response.status_code == 200
    run_id = create_response.json()["id"]

    detail_response = client.get(f"/api/v1/agents/runs/{run_id}")
    assert detail_response.status_code == 200
    payload = detail_response.json()
    assert payload["id"] == run_id
    assert len(payload["steps"]) == 1
    assert payload["steps"][0]["step_name"] == "triage_task"


def test_agents_run_detail_returns_404_for_unknown_id(client):
    response = client.get("/api/v1/agents/runs/999999")
    assert response.status_code == 404


def test_agents_runs_list_filters_by_status_and_workflow(client, db_session):
    now = datetime.now(timezone.utc)
    run_failed = AgentRun(
        workflow_name="task_triage_v1",
        status="failed",
        run_input={"title": "a", "description": None},
        run_output=None,
        error_message="test failure",
        total_cost_usd=0.0,
        total_latency_ms=10,
        created_at=now - timedelta(minutes=10),
        updated_at=now - timedelta(minutes=10),
    )
    run_other_workflow = AgentRun(
        workflow_name="other_workflow",
        status="completed",
        run_input={"title": "b", "description": None},
        run_output={"triage": {"priority": "low"}},
        error_message=None,
        total_cost_usd=0.0,
        total_latency_ms=11,
        created_at=now - timedelta(minutes=5),
        updated_at=now - timedelta(minutes=5),
    )
    db_session.add(run_failed)
    db_session.add(run_other_workflow)
    db_session.commit()

    response = client.get("/api/v1/agents/runs?status=failed&workflow_name=task_triage_v1")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["status"] == "failed"
    assert payload[0]["workflow_name"] == "task_triage_v1"


def test_agents_runs_list_filters_by_created_window(client, db_session):
    now = datetime.now(timezone.utc)
    old_run = AgentRun(
        workflow_name="task_triage_v1",
        status="completed",
        run_input={"title": "old", "description": None},
        run_output={"triage": {"priority": "low"}},
        error_message=None,
        total_cost_usd=0.0,
        total_latency_ms=10,
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=2),
    )
    new_run = AgentRun(
        workflow_name="task_triage_v1",
        status="completed",
        run_input={"title": "new", "description": None},
        run_output={"triage": {"priority": "high"}},
        error_message=None,
        total_cost_usd=0.0,
        total_latency_ms=12,
        created_at=now - timedelta(minutes=1),
        updated_at=now - timedelta(minutes=1),
    )
    db_session.add(old_run)
    db_session.add(new_run)
    db_session.commit()

    created_from = (now - timedelta(hours=1)).isoformat()
    response = client.get("/api/v1/agents/runs", params={"created_from": created_from})
    assert response.status_code == 200
    payload = response.json()
    returned_ids = [item["id"] for item in payload]
    assert new_run.id in returned_ids
    assert old_run.id not in returned_ids


def test_agents_ops_summary_returns_aggregated_metrics(client, db_session):
    run_completed = AgentRun(
        workflow_name="task_triage_v1",
        status="completed",
        run_input={"title": "completed", "description": None},
        run_output={"triage": {"priority": "low"}},
        error_message=None,
        total_cost_usd=0.0,
        total_latency_ms=10,
    )
    run_failed = AgentRun(
        workflow_name="task_triage_v1",
        status="failed",
        run_input={"title": "failed", "description": None},
        run_output=None,
        error_message="boom",
        total_cost_usd=0.0,
        total_latency_ms=11,
    )
    db_session.add(run_completed)
    db_session.add(run_failed)
    db_session.commit()

    fallback_step = AgentStep(
        run_id=run_completed.id,
        step_order=1,
        step_name="triage_task",
        status="completed",
        step_input={"title": "completed"},
        step_output={"priority": "medium"},
        decision="fallback_safe_defaults",
        fallback_used=True,
        error_message=None,
        step_cost_usd=0.0,
        step_latency_ms=1,
    )
    db_session.add(fallback_step)
    db_session.commit()

    response = client.get("/api/v1/agents/ops/summary?workflow_name=task_triage_v1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_runs"] == 2
    assert payload["completed_runs"] == 1
    assert payload["failed_runs"] == 1
    assert payload["fallback_steps"] == 1
    assert payload["fallback_rate_percent"] == 50.0
