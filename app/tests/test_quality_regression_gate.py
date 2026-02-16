from fastapi.testclient import TestClient


def _create_care_task(client: TestClient, title: str) -> int:
    response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": title,
            "description": "Caso de evaluacion continua para gate de calidad.",
            "clinical_priority": "high",
            "specialty": "cardiology",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def _run_scasest_case(client: TestClient, task_id: int, *, high_risk_case: bool) -> dict:
    if high_risk_case:
        payload = {
            "chest_pain_typical": True,
            "dyspnea": True,
            "ecg_st_depression": True,
            "troponin_positive": True,
            "hemodynamic_instability": True,
            "grace_score": 160,
            "oxygen_saturation_percent": 88,
        }
    else:
        payload = {
            "chest_pain_typical": False,
            "dyspnea": False,
            "ecg_st_depression": False,
            "troponin_positive": False,
            "hemodynamic_instability": False,
            "grace_score": 62,
            "oxygen_saturation_percent": 97,
        }

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/scasest/recommendation",
        json=payload,
    )
    assert response.status_code == 200
    return response.json()


def _audit_scasest_case(
    client: TestClient,
    task_id: int,
    run_payload: dict,
    *,
    human_high_risk: bool,
) -> dict:
    response = client.post(
        f"/api/v1/care-tasks/{task_id}/scasest/audit",
        json={
            "agent_run_id": run_payload["agent_run_id"],
            "human_validated_high_risk_scasest": human_high_risk,
            "human_escalation_required": human_high_risk,
            "human_immediate_antiischemic_strategy": human_high_risk,
            "reviewed_by": "gate_ci",
            "reviewer_note": "Caso sintetico para evaluacion continua.",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_quality_gate_thresholds_hold_in_controlled_mix(client):
    for index in range(5):
        task_id = _create_care_task(client, f"Gate quality high-risk match #{index + 1}")
        run_payload = _run_scasest_case(client, task_id, high_risk_case=True)
        ai_high_risk = bool(run_payload["recommendation"]["high_risk_scasest"])
        assert ai_high_risk is True
        audit_payload = _audit_scasest_case(
            client,
            task_id,
            run_payload,
            human_high_risk=True,
        )
        assert audit_payload["classification"] == "match"

    for index in range(5):
        task_id = _create_care_task(client, f"Gate quality low-risk match #{index + 1}")
        run_payload = _run_scasest_case(client, task_id, high_risk_case=False)
        ai_high_risk = bool(run_payload["recommendation"]["high_risk_scasest"])
        assert ai_high_risk is False
        audit_payload = _audit_scasest_case(
            client,
            task_id,
            run_payload,
            human_high_risk=False,
        )
        assert audit_payload["classification"] == "match"

    under_task_id = _create_care_task(client, "Gate quality forced under-risk")
    under_run_payload = _run_scasest_case(client, under_task_id, high_risk_case=False)
    assert bool(under_run_payload["recommendation"]["high_risk_scasest"]) is False
    under_audit_payload = _audit_scasest_case(
        client,
        under_task_id,
        under_run_payload,
        human_high_risk=True,
    )
    assert under_audit_payload["classification"] == "under_scasest_risk"

    over_task_id = _create_care_task(client, "Gate quality forced over-risk")
    over_run_payload = _run_scasest_case(client, over_task_id, high_risk_case=True)
    assert bool(over_run_payload["recommendation"]["high_risk_scasest"]) is True
    over_audit_payload = _audit_scasest_case(
        client,
        over_task_id,
        over_run_payload,
        human_high_risk=False,
    )
    assert over_audit_payload["classification"] == "over_scasest_risk"

    scorecard_response = client.get("/api/v1/care-tasks/quality/scorecard")
    assert scorecard_response.status_code == 200
    scorecard = scorecard_response.json()

    assert scorecard["total_audits"] == 12
    assert scorecard["matches"] == 10
    assert scorecard["under_events"] == 1
    assert scorecard["over_events"] == 1
    assert scorecard["under_rate_percent"] <= 10.0
    assert scorecard["over_rate_percent"] <= 20.0
    assert scorecard["match_rate_percent"] >= 80.0
    assert scorecard["quality_status"] == "atencion"


def test_quality_gate_detects_degradation_when_under_rate_is_high(client):
    for index in range(12):
        task_id = _create_care_task(client, f"Gate quality degradation #{index + 1}")
        run_payload = _run_scasest_case(client, task_id, high_risk_case=False)
        assert bool(run_payload["recommendation"]["high_risk_scasest"]) is False
        audit_payload = _audit_scasest_case(
            client,
            task_id,
            run_payload,
            human_high_risk=True,
        )
        assert audit_payload["classification"] == "under_scasest_risk"

    scorecard_response = client.get("/api/v1/care-tasks/quality/scorecard")
    assert scorecard_response.status_code == 200
    scorecard = scorecard_response.json()

    assert scorecard["total_audits"] == 12
    assert scorecard["under_events"] == 12
    assert scorecard["under_rate_percent"] > 10.0
    assert scorecard["quality_status"] == "degradado"
