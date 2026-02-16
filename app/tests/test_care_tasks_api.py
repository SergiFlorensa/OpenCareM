def test_create_and_get_care_task(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Review abnormal lab queue",
            "description": "Pending analysis backlog",
            "clinical_priority": "high",
            "specialty": "lab",
            "sla_target_minutes": 60,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["title"] == "Review abnormal lab queue"
    assert created["clinical_priority"] == "high"
    assert created["specialty"] == "lab"
    task_id = created["id"]

    get_response = client.get(f"/api/v1/care-tasks/{task_id}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["id"] == task_id
    assert fetched["sla_target_minutes"] == 60


def test_list_filter_stats_update_delete_care_task(client):
    client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Case A",
            "clinical_priority": "critical",
            "specialty": "emergency",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Case B",
            "clinical_priority": "medium",
            "specialty": "cardiology",
            "sla_target_minutes": 180,
            "human_review_required": False,
            "completed": True,
        },
    )

    list_response = client.get("/api/v1/care-tasks/?clinical_priority=critical")
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 1
    assert items[0]["clinical_priority"] == "critical"

    stats_response = client.get("/api/v1/care-tasks/stats/count?completed=true")
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["total"] == 1
    assert stats["filtered"] == 1

    target_id = items[0]["id"]
    update_response = client.put(
        f"/api/v1/care-tasks/{target_id}",
        json={"completed": True, "clinical_priority": "high"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["completed"] is True
    assert updated["clinical_priority"] == "high"

    delete_response = client.delete(f"/api/v1/care-tasks/{target_id}")
    assert delete_response.status_code == 204

    get_deleted_response = client.get(f"/api/v1/care-tasks/{target_id}")
    assert get_deleted_response.status_code == 404


def test_reject_invalid_clinical_priority(client):
    response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Bad priority",
            "clinical_priority": "urgent-now",
            "specialty": "general",
            "sla_target_minutes": 90,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert response.status_code == 400
    assert "prioridad clinica invalido" in response.json()["detail"]


def test_triage_care_task_creates_agent_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Escalar caso con riesgo de caida",
            "description": "Paciente con movilidad reducida en espera de traslado",
            "clinical_priority": "high",
            "specialty": "geriatria",
            "sla_target_minutes": 45,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    triage_response = client.post(f"/api/v1/care-tasks/{task_id}/triage")
    assert triage_response.status_code == 200
    payload = triage_response.json()

    assert payload["care_task_id"] == task_id
    assert payload["workflow_name"] == "care_task_triage_v1"
    assert payload["agent_run_id"] > 0
    assert payload["triage"]["priority"] in {"low", "medium", "high"}
    assert payload["triage"]["source"] in {"rules", "llm", "rules_fallback"}

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "care_task_triage_v1"
    assert run.run_input["care_task_id"] == task_id
    assert run.run_input["specialty"] == "geriatria"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "triage_care_task"


def test_triage_care_task_returns_404_when_task_not_found(client):
    response = client.post("/api/v1/care-tasks/999999/triage")
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_approve_care_task_triage_success_and_update(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso para aprobacion humana",
            "description": "Triaje inicial",
            "clinical_priority": "medium",
            "specialty": "general",
            "sla_target_minutes": 120,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    run_response = client.post(f"/api/v1/care-tasks/{task_id}/triage")
    assert run_response.status_code == 200
    run_id = run_response.json()["agent_run_id"]

    approve_response = client.post(
        f"/api/v1/care-tasks/{task_id}/triage/approve",
        json={
            "agent_run_id": run_id,
            "approved": True,
            "reviewer_note": "Validado por operacion clinica.",
            "reviewed_by": "supervisor_guardia",
        },
    )
    assert approve_response.status_code == 200
    payload = approve_response.json()
    assert payload["care_task_id"] == task_id
    assert payload["agent_run_id"] == run_id
    assert payload["approved"] is True
    assert payload["reviewed_by"] == "supervisor_guardia"

    update_response = client.post(
        f"/api/v1/care-tasks/{task_id}/triage/approve",
        json={
            "agent_run_id": run_id,
            "approved": False,
            "reviewer_note": "Se rechaza por contexto asistencial actualizado.",
            "reviewed_by": "supervisor_noche",
        },
    )
    assert update_response.status_code == 200
    updated_payload = update_response.json()
    assert updated_payload["review_id"] == payload["review_id"]
    assert updated_payload["approved"] is False
    assert updated_payload["reviewed_by"] == "supervisor_noche"


def test_approve_care_task_triage_returns_404_when_run_not_found(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso sin run",
            "description": "Sin ejecucion de agente",
            "clinical_priority": "low",
            "specialty": "general",
            "sla_target_minutes": 240,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/triage/approve",
        json={"agent_run_id": 999999, "approved": True},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Ejecucion de agente no encontrada."


def test_approve_care_task_triage_returns_400_when_run_belongs_to_other_task(client):
    first_task = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Primer caso",
            "description": "Caso A",
            "clinical_priority": "medium",
            "specialty": "general",
            "sla_target_minutes": 90,
            "human_review_required": True,
            "completed": False,
        },
    )
    second_task = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Segundo caso",
            "description": "Caso B",
            "clinical_priority": "high",
            "specialty": "emergency",
            "sla_target_minutes": 45,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert first_task.status_code == 201
    assert second_task.status_code == 201

    first_task_id = first_task.json()["id"]
    second_task_id = second_task.json()["id"]

    run_response = client.post(f"/api/v1/care-tasks/{first_task_id}/triage")
    assert run_response.status_code == 200
    run_id = run_response.json()["agent_run_id"]

    response = client.post(
        f"/api/v1/care-tasks/{second_task_id}/triage/approve",
        json={"agent_run_id": run_id, "approved": True},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "La ejecucion de agente no pertenece al CareTask indicado."


def test_create_triage_audit_and_summary_with_under_triage(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso auditado",
            "description": "Seguimiento para auditoria",
            "clinical_priority": "medium",
            "specialty": "general",
            "sla_target_minutes": 90,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    run_response = client.post(f"/api/v1/care-tasks/{task_id}/triage")
    assert run_response.status_code == 200
    run_id = run_response.json()["agent_run_id"]

    audit_response = client.post(
        f"/api/v1/care-tasks/{task_id}/triage/audit",
        json={
            "agent_run_id": run_id,
            "human_validated_level": 1,
            "reviewed_by": "medico_supervisor",
            "reviewer_note": "Se eleva prioridad por riesgo neurologico.",
        },
    )
    assert audit_response.status_code == 200
    audit_payload = audit_response.json()
    assert audit_payload["care_task_id"] == task_id
    assert audit_payload["agent_run_id"] == run_id
    assert audit_payload["ai_recommended_level"] in {1, 2, 3, 4, 5}
    assert audit_payload["human_validated_level"] == 1
    assert audit_payload["classification"] in {"under_triage", "match", "over_triage"}

    list_response = client.get(f"/api/v1/care-tasks/{task_id}/triage/audit")
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 1
    assert items[0]["audit_id"] == audit_payload["audit_id"]

    summary_response = client.get(f"/api/v1/care-tasks/{task_id}/triage/audit/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["total_audits"] == 1
    assert summary["matches"] + summary["under_triage"] + summary["over_triage"] == 1


def test_create_triage_audit_returns_404_when_run_not_found(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso sin run audit",
            "description": "Prueba run inexistente",
            "clinical_priority": "low",
            "specialty": "general",
            "sla_target_minutes": 120,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/triage/audit",
        json={
            "agent_run_id": 999999,
            "human_validated_level": 2,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Ejecucion de agente no encontrada."


def test_run_respiratory_protocol_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Disnea y fiebre en paciente mayor",
            "description": "Sospecha de infeccion respiratoria aguda",
            "clinical_priority": "high",
            "specialty": "emergency",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/respiratory-protocol/recommendation",
        json={
            "age_years": 82,
            "immunosuppressed": False,
            "comorbidities": ["insuficiencia_cardiaca"],
            "vaccination_updated_last_12_months": False,
            "symptom_onset_hours": 24,
            "hours_since_er_arrival": 2,
            "current_systolic_bp": 108,
            "baseline_systolic_bp": 160,
            "needs_oxygen": False,
            "pathogen_suspected": "covid",
            "antigen_result": "positivo",
            "oral_antiviral_contraindicated": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["care_task_id"] == task_id
    assert payload["workflow_name"] == "respiratory_protocol_v1"
    assert payload["recommendation"]["vulnerable_patient"] is True
    assert payload["recommendation"]["shock_relative_suspected"] is True
    assert any(
        "Nirmatrelvir/Ritonavir" in item for item in payload["recommendation"]["antiviral_plan"]
    )

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "respiratory_protocol_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "respiratory_protocol_assessment"


def test_run_respiratory_protocol_recommends_pcr_for_negative_antigen_in_vulnerable(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Sospecha VRS adulto",
            "description": "Antigeno negativo en vulnerable",
            "clinical_priority": "medium",
            "specialty": "general",
            "sla_target_minutes": 90,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/respiratory-protocol/recommendation",
        json={
            "age_years": 70,
            "immunosuppressed": False,
            "comorbidities": [],
            "vaccination_updated_last_12_months": True,
            "symptom_onset_hours": 72,
            "needs_oxygen": False,
            "pathogen_suspected": "vrs",
            "antigen_result": "negativo",
            "oral_antiviral_contraindicated": False,
        },
    )
    assert response.status_code == 200
    plans = response.json()["recommendation"]["diagnostic_plan"]
    assert any("PCR" in item for item in plans)
    assert any("muestra combinada" in item for item in plans)


def test_run_respiratory_protocol_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/respiratory-protocol/recommendation",
        json={
            "age_years": 40,
            "immunosuppressed": False,
            "comorbidities": [],
            "vaccination_updated_last_12_months": True,
            "symptom_onset_hours": 12,
            "needs_oxygen": False,
            "pathogen_suspected": "gripe",
            "antigen_result": "positivo",
            "oral_antiviral_contraindicated": False,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_humanization_protocol_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso pediatrico neuro-oncologico complejo",
            "description": "Familia con alta carga emocional y dudas de consentimiento",
            "clinical_priority": "high",
            "specialty": "pediatria",
            "sla_target_minutes": 60,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/humanization/recommendation",
        json={
            "patient_age_years": 9,
            "primary_context": "neuro_oncologia",
            "emotional_distress_level": 9,
            "family_understanding_level": 3,
            "family_present": True,
            "sibling_support_needed": True,
            "social_risk_flags": ["vivienda_inestable"],
            "needs_spiritual_support": True,
            "multidisciplinary_team": ["oncologia", "anestesia", "enfermeria"],
            "has_clinical_trial_option": True,
            "informed_consent_status": "pendiente",
            "professional_burnout_risk": "medium",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["care_task_id"] == task_id
    assert payload["workflow_name"] == "pediatric_neuro_onco_support_v1"
    assert payload["recommendation"]["human_validation_required"] is True
    assert len(payload["recommendation"]["communication_plan"]) > 0
    assert len(payload["recommendation"]["alerts"]) > 0

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "pediatric_neuro_onco_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "humanization_operational_assessment"


def test_run_humanization_protocol_emits_distress_alerts(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso pediatrico con estres familiar",
            "description": "Validar alertas por distres y comprension baja",
            "clinical_priority": "medium",
            "specialty": "pediatria",
            "sla_target_minutes": 90,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/humanization/recommendation",
        json={
            "patient_age_years": 6,
            "primary_context": "ensayo_clinico",
            "emotional_distress_level": 8,
            "family_understanding_level": 2,
            "family_present": False,
            "sibling_support_needed": False,
            "social_risk_flags": [],
            "needs_spiritual_support": False,
            "multidisciplinary_team": ["oncologia"],
            "has_clinical_trial_option": False,
            "informed_consent_status": "rechazado",
            "professional_burnout_risk": "high",
        },
    )
    assert response.status_code == 200
    alerts = response.json()["recommendation"]["alerts"]
    assert any("Distres emocional alto" in item for item in alerts)
    assert any("baja comprension" in item for item in alerts)
    assert any("clinico-legal" in item for item in alerts)


def test_run_humanization_protocol_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/humanization/recommendation",
        json={
            "patient_age_years": 12,
            "primary_context": "seguimiento",
            "emotional_distress_level": 2,
            "family_understanding_level": 8,
            "family_present": True,
            "sibling_support_needed": False,
            "social_risk_flags": [],
            "needs_spiritual_support": False,
            "multidisciplinary_team": [],
            "has_clinical_trial_option": False,
            "informed_consent_status": "explicado",
            "professional_burnout_risk": "low",
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_advanced_screening_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Paciente mayor con fiebre sin foco",
            "description": "Cribado operativo en triaje",
            "clinical_priority": "high",
            "specialty": "emergency",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/screening/recommendation",
        json={
            "age_years": 78,
            "sex": "m",
            "systolic_bp": 108,
            "can_walk_independently": False,
            "sodium_mmol_l": 128,
            "glucose_mg_dl": 262,
            "heart_rate_bpm": 122,
            "oxygen_saturation_percent": 90,
            "chief_complaints": ["fiebre sin foco", "malestar general"],
            "known_conditions": ["plaquetopenia"],
            "immunosuppressed": True,
            "persistent_positive_days": 15,
            "persistent_symptoms": True,
            "imaging_compatible_with_persistent_infection": True,
            "stable_after_acute_phase": True,
            "infection_context": "endocarditis",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_name"] == "advanced_screening_support_v1"
    assert payload["recommendation"]["geriatric_risk_level"] in {"medium", "high"}
    assert payload["recommendation"]["persistent_covid_suspected"] is True
    assert payload["recommendation"]["long_acting_candidate"] is True
    assert payload["recommendation"]["alerts_generated_total"] >= 1

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "advanced_screening_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "advanced_screening_assessment"


def test_run_advanced_screening_suppresses_alerts_by_fatigue_control(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso con muchas alertas",
            "description": "Validar supresion por fatiga",
            "clinical_priority": "medium",
            "specialty": "general",
            "sla_target_minutes": 90,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/screening/recommendation",
        json={
            "age_years": 86,
            "systolic_bp": 95,
            "can_walk_independently": False,
            "heart_rate_bpm": 125,
            "oxygen_saturation_percent": 88,
            "chief_complaints": ["neumonia", "fiebre sin foco"],
            "known_conditions": ["its", "plaquetopenia"],
            "immunosuppressed": True,
            "persistent_positive_days": 21,
            "persistent_symptoms": True,
            "imaging_compatible_with_persistent_infection": True,
            "stable_after_acute_phase": False,
            "infection_context": "no_aplica",
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    assert recommendation["alerts_generated_total"] >= len(recommendation["alerts"])
    assert recommendation["alerts_suppressed_total"] >= 0


def test_run_advanced_screening_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/screening/recommendation",
        json={
            "age_years": 40,
            "chief_complaints": [],
            "known_conditions": [],
            "stable_after_acute_phase": False,
            "infection_context": "no_aplica",
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_create_screening_audit_and_summary(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso para auditoria screening",
            "description": "Validar calidad IA vs humano",
            "clinical_priority": "high",
            "specialty": "emergency",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    run_response = client.post(
        f"/api/v1/care-tasks/{task_id}/screening/recommendation",
        json={
            "age_years": 79,
            "systolic_bp": 108,
            "can_walk_independently": False,
            "heart_rate_bpm": 122,
            "oxygen_saturation_percent": 90,
            "chief_complaints": ["fiebre sin foco"],
            "known_conditions": ["plaquetopenia"],
            "immunosuppressed": True,
            "persistent_positive_days": 16,
            "persistent_symptoms": True,
            "imaging_compatible_with_persistent_infection": True,
            "stable_after_acute_phase": True,
            "infection_context": "endocarditis",
        },
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["agent_run_id"]

    audit_response = client.post(
        f"/api/v1/care-tasks/{task_id}/screening/audit",
        json={
            "agent_run_id": run_id,
            "human_validated_risk_level": "high",
            "human_hiv_screening_suggested": True,
            "human_sepsis_route_suggested": True,
            "human_persistent_covid_suspected": True,
            "human_long_acting_candidate": True,
            "reviewed_by": "supervisor_guardia",
        },
    )
    assert audit_response.status_code == 200
    payload = audit_response.json()
    assert payload["care_task_id"] == task_id
    assert payload["agent_run_id"] == run_id
    assert payload["classification"] in {"match", "under_screening", "over_screening"}

    list_response = client.get(f"/api/v1/care-tasks/{task_id}/screening/audit")
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 1
    assert items[0]["audit_id"] == payload["audit_id"]

    summary_response = client.get(f"/api/v1/care-tasks/{task_id}/screening/audit/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["total_audits"] == 1
    assert summary["matches"] + summary["under_screening"] + summary["over_screening"] == 1
    assert "hiv_screening_match_rate_percent" in summary
    assert "sepsis_route_match_rate_percent" in summary


def test_create_screening_audit_returns_404_when_run_not_found(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso sin run screening",
            "description": "Error esperado",
            "clinical_priority": "medium",
            "specialty": "general",
            "sla_target_minutes": 90,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/screening/audit",
        json={
            "agent_run_id": 999999,
            "human_validated_risk_level": "medium",
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Ejecucion de agente no encontrada."


def test_run_chest_xray_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Paciente con disnea y dolor toracico",
            "description": "Soporte de lectura RX torax en urgencias",
            "clinical_priority": "high",
            "specialty": "emergency",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/chest-xray/interpretation-support",
        json={
            "projection": "ap",
            "inspiratory_quality": "suboptima",
            "pattern": "alveolar",
            "signs": ["broncograma_aereo", "cardiomegalia_aparente_ap"],
            "lesion_size_cm": 2.1,
            "clinical_context": "Fiebre y tos productiva de 48h",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_name"] == "chest_xray_support_v1"
    assert payload["recommendation"]["human_validation_required"] is True
    assert len(payload["recommendation"]["suspected_patterns"]) > 0
    assert len(payload["recommendation"]["projection_caveats"]) > 0

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "chest_xray_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "chest_xray_interpretation_assessment"


def test_run_chest_xray_support_detects_tension_pneumothorax_red_flag(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Trauma toracico con inestabilidad",
            "description": "Validar red flag critica",
            "clinical_priority": "critical",
            "specialty": "emergency",
            "sla_target_minutes": 15,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/chest-xray/interpretation-support",
        json={
            "projection": "pa",
            "inspiratory_quality": "adecuada",
            "pattern": "neumotorax",
            "signs": [
                "linea_pleural_visceral",
                "ausencia_trama_periferica",
                "desplazamiento_mediastinico",
            ],
            "clinical_context": "Hipotension y deterioro respiratorio brusco",
        },
    )
    assert response.status_code == 200
    red_flags = response.json()["recommendation"]["urgent_red_flags"]
    assert any("neumotorax a tension" in item.lower() for item in red_flags)


def test_run_chest_xray_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/chest-xray/interpretation-support",
        json={
            "projection": "pa",
            "inspiratory_quality": "adecuada",
            "pattern": "ninguno",
            "signs": [],
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_pityriasis_differential_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Lesiones maculares en tronco",
            "description": "Diferencial pitiriasis en consulta de urgencias",
            "clinical_priority": "medium",
            "specialty": "dermatologia",
            "sla_target_minutes": 120,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/pityriasis-differential/recommendation",
        json={
            "age_years": 26,
            "lesion_distribution": ["torax", "espalda", "areas_seborreicas"],
            "lesion_pigmentation": "hipocromica",
            "fine_scaling_present": True,
            "signo_unyada_positive": True,
            "herald_patch_present": False,
            "christmas_tree_pattern_present": False,
            "pruritus_intensity": 4,
            "viral_prodrome_present": False,
            "wood_lamp_result": "amarillo_naranja",
            "koh_result": "positivo_spaghetti_albondigas",
            "recurrent_course": True,
            "atopic_background": False,
            "sensory_loss_in_lesion": False,
            "deep_erythema_warmth_pain": False,
            "systemic_signs": False,
            "immunosuppressed": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_name"] == "pityriasis_differential_support_v1"
    assert payload["recommendation"]["most_likely_condition"] == "pitiriasis_versicolor"
    assert payload["recommendation"]["human_validation_required"] is True

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "pityriasis_differential_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "pityriasis_differential_assessment"


def test_run_pityriasis_differential_detects_red_flags(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Lesion hipocromica con alarma",
            "description": "Evaluar red flags dermatologicas",
            "clinical_priority": "high",
            "specialty": "dermatologia",
            "sla_target_minutes": 60,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/pityriasis-differential/recommendation",
        json={
            "age_years": 17,
            "lesion_distribution": ["cara"],
            "lesion_pigmentation": "hipocromica",
            "fine_scaling_present": True,
            "signo_unyada_positive": False,
            "herald_patch_present": False,
            "christmas_tree_pattern_present": False,
            "pruritus_intensity": 2,
            "viral_prodrome_present": False,
            "wood_lamp_result": "sin_fluorescencia",
            "koh_result": "negativo",
            "recurrent_course": False,
            "atopic_background": False,
            "sensory_loss_in_lesion": True,
            "deep_erythema_warmth_pain": True,
            "systemic_signs": True,
            "immunosuppressed": False,
        },
    )
    assert response.status_code == 200
    red_flags = response.json()["recommendation"]["urgent_red_flags"]
    assert any("lepra" in item.lower() for item in red_flags)
    assert any("celulitis" in item.lower() or "erisipela" in item.lower() for item in red_flags)


def test_run_pityriasis_differential_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/pityriasis-differential/recommendation",
        json={
            "age_years": 20,
            "lesion_distribution": ["tronco"],
            "lesion_pigmentation": "hipocromica",
            "fine_scaling_present": True,
            "signo_unyada_positive": False,
            "herald_patch_present": False,
            "christmas_tree_pattern_present": False,
            "pruritus_intensity": 1,
            "viral_prodrome_present": False,
            "wood_lamp_result": "no_realizada",
            "koh_result": "no_realizado",
            "recurrent_course": False,
            "atopic_background": False,
            "sensory_loss_in_lesion": False,
            "deep_erythema_warmth_pain": False,
            "systemic_signs": False,
            "immunosuppressed": False,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_acne_rosacea_differential_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Lesiones inflamatorias faciales",
            "description": "Diferencial acne vs rosacea",
            "clinical_priority": "medium",
            "specialty": "dermatologia",
            "sla_target_minutes": 120,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/acne-rosacea/recommendation",
        json={
            "age_years": 19,
            "sex": "masculino",
            "lesion_distribution": ["frente", "menton", "espalda"],
            "comedones_present": True,
            "lesion_pattern": "polimorfo",
            "flushing_present": False,
            "telangiectasias_present": False,
            "ocular_symptoms_present": False,
            "phymatous_changes_present": False,
            "photosensitivity_triggered": False,
            "vasodilatory_triggers_present": False,
            "severe_nodules_abscesses_present": False,
            "systemic_symptoms_present": False,
            "elevated_vsg_or_leukocytosis": False,
            "suspected_hyperandrogenism": False,
            "pediatric_patient": False,
            "pregnant_or_pregnancy_possible": False,
            "isotretinoin_candidate": False,
            "current_systemic_tetracycline": False,
            "current_retinoid_oral": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_name"] == "acne_rosacea_differential_support_v1"
    assert payload["recommendation"]["most_likely_condition"] == "acne"
    assert payload["recommendation"]["human_validation_required"] is True

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "acne_rosacea_differential_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "acne_rosacea_differential_assessment"


def test_run_acne_rosacea_differential_detects_fulminans_red_flag(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Acne severo con compromiso sistémico",
            "description": "Escenario de alarma",
            "clinical_priority": "high",
            "specialty": "dermatologia",
            "sla_target_minutes": 45,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/acne-rosacea/recommendation",
        json={
            "age_years": 17,
            "sex": "masculino",
            "lesion_distribution": ["mejillas", "espalda"],
            "comedones_present": True,
            "lesion_pattern": "nodulo_quistico",
            "flushing_present": False,
            "telangiectasias_present": False,
            "ocular_symptoms_present": False,
            "phymatous_changes_present": False,
            "photosensitivity_triggered": False,
            "vasodilatory_triggers_present": False,
            "severe_nodules_abscesses_present": True,
            "systemic_symptoms_present": True,
            "elevated_vsg_or_leukocytosis": True,
            "suspected_hyperandrogenism": False,
            "pediatric_patient": False,
            "pregnant_or_pregnancy_possible": False,
            "isotretinoin_candidate": True,
            "current_systemic_tetracycline": False,
            "current_retinoid_oral": False,
        },
    )
    assert response.status_code == 200
    red_flags = response.json()["recommendation"]["urgent_red_flags"]
    assert any("acne fulminans" in item.lower() for item in red_flags)
    checklist = response.json()["recommendation"]["isotretinoin_monitoring_checklist"]
    assert any("perfil lipidico" in item.lower() for item in checklist)


def test_run_acne_rosacea_differential_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/acne-rosacea/recommendation",
        json={
            "age_years": 32,
            "sex": "femenino",
            "lesion_distribution": ["mejillas", "nariz"],
            "comedones_present": False,
            "lesion_pattern": "papulo_pustuloso",
            "flushing_present": True,
            "telangiectasias_present": True,
            "ocular_symptoms_present": False,
            "phymatous_changes_present": False,
            "photosensitivity_triggered": True,
            "vasodilatory_triggers_present": True,
            "severe_nodules_abscesses_present": False,
            "systemic_symptoms_present": False,
            "elevated_vsg_or_leukocytosis": False,
            "suspected_hyperandrogenism": False,
            "pediatric_patient": False,
            "pregnant_or_pregnancy_possible": False,
            "isotretinoin_candidate": False,
            "current_systemic_tetracycline": False,
            "current_retinoid_oral": False,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_trauma_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Trauma cerrado de alta energia",
            "description": "Monitorizar curva trimodal y via aerea",
            "clinical_priority": "critical",
            "specialty": "urgencias",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/trauma/recommendation",
        json={
            "minutes_since_trauma": 45,
            "suspected_major_brain_injury": False,
            "suspected_major_vascular_injury": False,
            "epidural_hematoma_suspected": True,
            "massive_hemothorax_suspected": False,
            "splenic_rupture_suspected": False,
            "sepsis_signs_post_stabilization": False,
            "persistent_organ_dysfunction": False,
            "laryngeal_fracture_palpable": True,
            "hoarseness_present": True,
            "subcutaneous_emphysema_present": True,
            "agitation_present": True,
            "stupor_present": False,
            "intercostal_retractions_present": True,
            "accessory_muscle_use_present": True,
            "hyperthermia_present": True,
            "hypercapnia_present": False,
            "acidosis_present": False,
            "motor_loss_arms_more_than_legs": True,
            "motor_loss_global": False,
            "sensory_loss_global": False,
            "preserved_vibration_proprioception": False,
            "ipsilateral_motor_vibration_loss": False,
            "contralateral_pain_temperature_loss": False,
            "crush_injury_suspected": False,
            "hyperkalemia_risk": False,
            "hyperphosphatemia_present": False,
            "ecg_series_started": False,
            "patient_profile": "adulto",
            "left_lateral_decubitus_applied": False,
            "broselow_tape_used": False,
            "sniffing_position_applied": False,
            "core_temperature_celsius": 36.2,
            "osborn_j_wave_present": False,
            "open_fracture_wound_cm": 12,
            "high_energy_open_fracture": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_name"] == "trauma_support_v1"
    assert payload["recommendation"]["mortality_phase_risk"] == "early"
    assert payload["recommendation"]["laryngeal_trauma_triad_present"] is True
    assert payload["recommendation"]["airway_priority_level"] == "nivel_i"
    assert payload["recommendation"]["open_fracture_gustilo_grade"] == "grado_iii"
    assert payload["recommendation"]["human_validation_required"] is True
    assert len(payload["recommendation"]["condition_matrix"]) >= 2
    assert (
        payload["recommendation"]["condition_matrix"][0]["source"]
        == "CCM 2025 - Especialidad Urgencias"
    )

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "trauma_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "trauma_operational_assessment"


def test_run_trauma_support_detects_crush_risk_and_serial_ecg_requirement(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Aplastamiento en derrumbe",
            "description": "Riesgo de rabdomiolisis y FRA",
            "clinical_priority": "critical",
            "specialty": "urgencias",
            "sla_target_minutes": 15,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/trauma/recommendation",
        json={
            "minutes_since_trauma": 1300,
            "suspected_major_brain_injury": False,
            "suspected_major_vascular_injury": False,
            "epidural_hematoma_suspected": False,
            "massive_hemothorax_suspected": False,
            "splenic_rupture_suspected": False,
            "sepsis_signs_post_stabilization": True,
            "persistent_organ_dysfunction": True,
            "laryngeal_fracture_palpable": False,
            "hoarseness_present": False,
            "subcutaneous_emphysema_present": False,
            "agitation_present": False,
            "stupor_present": False,
            "intercostal_retractions_present": False,
            "accessory_muscle_use_present": False,
            "hyperthermia_present": False,
            "hypercapnia_present": True,
            "acidosis_present": True,
            "motor_loss_arms_more_than_legs": False,
            "motor_loss_global": False,
            "sensory_loss_global": False,
            "preserved_vibration_proprioception": False,
            "ipsilateral_motor_vibration_loss": True,
            "contralateral_pain_temperature_loss": True,
            "crush_injury_suspected": True,
            "hyperkalemia_risk": True,
            "hyperphosphatemia_present": True,
            "ecg_series_started": False,
            "patient_profile": "embarazada",
            "pregnancy_weeks": 28,
            "left_lateral_decubitus_applied": False,
            "broselow_tape_used": False,
            "sniffing_position_applied": False,
            "core_temperature_celsius": 27.5,
            "osborn_j_wave_present": True,
            "open_fracture_wound_cm": 0.5,
            "high_energy_open_fracture": False,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    assert recommendation["mortality_phase_risk"] == "late"
    assert recommendation["suspected_spinal_syndrome"] == "brown_sequard"
    assert recommendation["crush_syndrome_alert"] is True
    assert recommendation["renal_failure_risk_high"] is True
    assert recommendation["serial_ecg_required"] is True
    assert recommendation["hypothermia_stage"] == "severe"
    assert recommendation["open_fracture_gustilo_grade"] == "grado_i"
    assert any("ecg seriados" in item.lower() for item in recommendation["alerts"])
    assert (
        any(
            item["condition"] == "Taponamiento Cardiaco"
            for item in recommendation["condition_matrix"]
        )
        is False
    )


def test_run_trauma_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/trauma/recommendation",
        json={
            "minutes_since_trauma": 20,
            "patient_profile": "adulto",
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_trauma_support_detects_tension_pneumothorax_and_tamponade(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Trauma toracico inestable",
            "description": "Sospecha de choque obstructivo",
            "clinical_priority": "critical",
            "specialty": "urgencias",
            "sla_target_minutes": 10,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/trauma/recommendation",
        json={
            "minutes_since_trauma": 15,
            "dyspnea_present": True,
            "percussion_hyperresonance_present": True,
            "tracheal_deviation_present": True,
            "beck_hypotension_present": True,
            "beck_muffled_heart_sounds_present": True,
            "beck_jvd_present": True,
            "patient_profile": "adulto",
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    assert any("neumotorax a tension" in item.lower() for item in recommendation["alerts"])
    assert any("beck" in item.lower() for item in recommendation["alerts"])
    card_conditions = {item["condition"] for item in recommendation["condition_matrix"]}
    assert "Neumotorax a Tension" in card_conditions
    assert "Taponamiento Cardiaco" in card_conditions


def test_run_critical_ops_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso operativo critico transversal",
            "description": "Validar SLA y ruta respiratoria/TEP",
            "clinical_priority": "high",
            "specialty": "urgencias",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/critical-ops/recommendation",
        json={
            "non_traumatic_chest_pain": True,
            "door_to_ecg_minutes": 8,
            "suspected_septic_shock": False,
            "triage_level": "naranja",
            "respiratory_failure_severity": "moderada",
            "good_respiratory_mechanics": True,
            "suspected_pe": True,
            "wells_score": 3.0,
            "d_dimer_ng_ml": 850,
            "svr_dyn_s_cm5": 760,
            "cvp_mm_hg": 7,
            "lactate_mmol_l": 1.8,
            "lactate_interval_minutes": 90,
            "chest_xray_performed": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_name"] == "critical_ops_support_v1"
    assert payload["recommendation"]["respiratory_device_recommended"] == "mascarilla_venturi"
    assert payload["recommendation"]["hemodynamic_profile"] == "shock_distributivo_probable"
    assert any(
        "angio-tac" in item.lower() for item in payload["recommendation"]["chest_pain_pe_pathway"]
    )

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "critical_ops_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "critical_ops_operational_assessment"


def test_run_critical_ops_support_detects_sla_breaches_and_red_flags(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso con incumplimientos criticos",
            "description": "Validar banderas rojas y brechas de SLA",
            "clinical_priority": "critical",
            "specialty": "urgencias",
            "sla_target_minutes": 10,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/critical-ops/recommendation",
        json={
            "non_traumatic_chest_pain": True,
            "door_to_ecg_minutes": 22,
            "suspected_septic_shock": True,
            "sepsis_antibiotic_minutes": 120,
            "triage_level": "rojo",
            "triage_to_first_assessment_minutes": 14,
            "rapid_cutaneous_mucosal_symptoms": True,
            "respiratory_compromise": True,
            "on_beta_blocker": True,
            "anaphylaxis_refractory_to_im_adrenaline": True,
            "abrupt_anuria_present": True,
            "chest_tube_output_immediate_ml": 1800,
            "core_temperature_celsius": 27.0,
            "persistent_asystole": True,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    assert recommendation["severity_level"] == "critical"
    assert any("ecg" in item.lower() for item in recommendation["sla_breaches"])
    assert any("sepsis" in item.lower() for item in recommendation["sla_breaches"])
    assert any("triaje rojo" in item.lower() for item in recommendation["sla_breaches"])
    assert any("toracotomia" in item.lower() for item in recommendation["operational_red_flags"])
    assert any("anuria" in item.lower() for item in recommendation["operational_red_flags"])
    assert any(
        "adrenalina intramuscular" in item.lower() for item in recommendation["anaphylaxis_pathway"]
    )
    assert any(
        "no certificar muerte" in item.lower() or "recalentamiento" in item.lower()
        for item in recommendation["toxicology_reversal_actions"]
    )


def test_run_critical_ops_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/critical-ops/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_neurology_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso neurologico vascular",
            "description": "Validar HSA e ictus de inicio desconocido",
            "clinical_priority": "critical",
            "specialty": "neurologia",
            "sla_target_minutes": 15,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/neurology/recommendation",
        json={
            "sudden_severe_headache": True,
            "cranial_ct_subarachnoid_hyperdensity": True,
            "perimesencephalic_bleeding_pattern": True,
            "cerebral_angiography_result": "normal",
            "suspected_stroke": True,
            "symptom_onset_known": False,
            "wake_up_stroke": True,
            "ct_perfusion_performed": True,
            "salvageable_penumbra_present": True,
            "aspects_score": 9,
            "aneurysm_or_malformation_suspected": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_name"] == "neurology_support_v1"
    assert payload["recommendation"]["severity_level"] == "critical"
    assert any(
        "hemorragia subaracnoidea" in item.lower()
        for item in payload["recommendation"]["vascular_life_threat_alerts"]
    )
    assert any(
        "tac perfusion" in item.lower()
        for item in payload["recommendation"]["stroke_reperfusion_pathway"]
    )

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "neurology_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "neurology_operational_assessment"


def test_run_neurology_support_detects_contraindications_and_nmda_pattern(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Neurologia autoinmune y neuromuscular",
            "description": "SGB y anti-NMDA",
            "clinical_priority": "high",
            "specialty": "neurologia",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/neurology/recommendation",
        json={
            "rapidly_progressive_weakness": True,
            "areflexia_or_hyporeflexia": True,
            "csf_albuminocytologic_dissociation": True,
            "corticosteroids_planned": True,
            "young_woman": True,
            "acute_psychiatric_symptoms": True,
            "seizures_present": True,
            "orofacial_dyskinesias": True,
            "ovarian_teratoma_screening_done": False,
            "fluctuating_weakness": True,
            "ocular_ptosis_or_diplopia": True,
            "pupils_spared": True,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    assert any("sgb" in item.lower() for item in recommendation["autoimmune_neuromuscular_pathway"])
    assert any("corticoides" in item.lower() for item in recommendation["contraindication_alerts"])
    assert any(
        "teratoma ovarico" in item.lower()
        for item in recommendation["autoimmune_neuromuscular_pathway"]
    )


def test_run_neurology_support_prioritizes_wakeup_pathway(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Ictus wake-up",
            "description": "Priorizar ruta de inicio desconocido por wake-up stroke",
            "clinical_priority": "high",
            "specialty": "neurologia",
            "sla_target_minutes": 15,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/neurology/recommendation",
        json={
            "suspected_stroke": True,
            "wake_up_stroke": True,
            "symptom_onset_known": True,
            "hours_since_symptom_onset": 2,
            "ct_perfusion_performed": True,
            "salvageable_penumbra_present": True,
        },
    )
    assert response.status_code == 200
    pathway = response.json()["recommendation"]["stroke_reperfusion_pathway"]
    assert any("inicio desconocido" in item.lower() for item in pathway)
    assert any("trombectomia" in item.lower() for item in pathway)


def test_run_neurology_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/neurology/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_gastro_hepato_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso gastro-hepato critico",
            "description": "Validar trombosis portal y HDA en cirrosis",
            "clinical_priority": "critical",
            "specialty": "digestivo",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/gastro-hepato/recommendation",
        json={
            "abdominal_pain": True,
            "jaundice": True,
            "ascites": True,
            "portal_doppler_no_flow_silence": True,
            "portal_doppler_heterogeneous": True,
            "cirrhosis_known": True,
            "upper_gi_bleeding_suspected": True,
            "vasoactive_somatostatin_started": False,
            "endoscopy_performed": False,
            "portal_venous_gas_on_ct": True,
            "gastric_pneumatosis_on_ct": True,
            "hypotension_present": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_name"] == "gastro_hepato_support_v1"
    assert payload["recommendation"]["severity_level"] == "critical"
    assert any(
        "trombosis portal aguda" in item.lower()
        for item in payload["recommendation"]["critical_alerts"]
    )
    assert any(
        "somatostatina" in item.lower()
        for item in payload["recommendation"]["critical_alerts"]
    )

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "gastro_hepato_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "gastro_hepato_operational_assessment"


def test_run_gastro_hepato_support_flags_surgery_and_pharmacology(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso quirurgico digestivo",
            "description": "Validar criterios de cirugia y seguridad EII",
            "clinical_priority": "high",
            "specialty": "cirugia",
            "sla_target_minutes": 40,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/gastro-hepato/recommendation",
        json={
            "porcelain_gallbladder": True,
            "inguinal_hernia_repair_planned": True,
            "wants_non_mesh_technique": True,
            "planned_hernia_technique": "shouldice",
            "duodenal_adenocarcinoma_non_metastatic": True,
            "ibd_patient": True,
            "azathioprine_active": True,
            "infliximab_or_biologic_active": True,
            "gerd_preop_evaluation": True,
            "esophageal_manometry_done": False,
            "fap_suspected": True,
            "mandibular_osteomas": True,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    assert any(
        "vesicula en porcelana" in item.lower()
        for item in recommendation["surgical_decision_support"]
    )
    assert any(
        "shouldice" in item.lower() for item in recommendation["surgical_decision_support"]
    )
    assert any(
        "no melanocitico" in item.lower()
        for item in recommendation["pharmacology_safety_alerts"]
    )
    assert any("melanoma" in item.lower() for item in recommendation["pharmacology_safety_alerts"])
    assert any(
        "manometria esofagica" in item.lower()
        for item in recommendation["functional_genetic_guidance"]
    )


def test_run_gastro_hepato_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/gastro-hepato/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_rheum_immuno_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso reuma-inmuno critico",
            "description": "LES con disnea y riesgo trombotico",
            "clinical_priority": "critical",
            "specialty": "reumatologia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/rheum-immuno/recommendation",
        json={
            "lupus_known": True,
            "new_unexplained_dyspnea": True,
            "prior_aptt_prolonged": True,
            "systemic_sclerosis_known": True,
            "raynaud_phenomenon_active": True,
            "active_digital_ischemic_ulcers": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_name"] == "rheum_immuno_support_v1"
    assert payload["recommendation"]["severity_level"] == "critical"
    assert any("tep" in item.lower() for item in payload["recommendation"]["critical_alerts"])
    assert any(
        "dimero d" in item.lower() for item in payload["recommendation"]["diagnostic_actions"]
    )
    assert any(
        "prostaglandinas" in item.lower()
        for item in payload["recommendation"]["therapeutic_actions"]
    )

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "rheum_immuno_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "rheum_immuno_operational_assessment"


def test_run_rheum_immuno_support_flags_safety_maternal_and_data_domains(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso reuma-inmuno seguridad",
            "description": "Behcet neurologico y riesgo neonatal",
            "clinical_priority": "high",
            "specialty": "medicina_interna",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/rheum-immuno/recommendation",
        json={
            "recurrent_oral_aphthae": True,
            "ocular_inflammation_or_uveitis": True,
            "erythema_nodosum_present": True,
            "cerebral_parenchymal_involvement": True,
            "cyclosporine_planned": True,
            "pregnancy_ongoing": True,
            "anti_ro_positive": True,
            "fetal_conduction_or_myocardial_risk": True,
            "fluorinated_corticosteroids_started": False,
            "igg4_related_disease_suspected": True,
            "igg4_lymphoplasmacytic_infiltrate": True,
            "igg4_obliterative_phlebitis": False,
            "igg4_storiform_fibrosis": True,
            "aps_clinical_event_present": True,
            "aps_laboratory_criterion_present": True,
            "thrombocytopenia_present": True,
            "young_male_with_inflammatory_back_pain": True,
            "sacroiliitis_on_imaging": True,
            "peripheral_joint_involvement": False,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    assert any("ciclosporina" in item.lower() for item in recommendation["safety_alerts"])
    assert any(
        "corticoides fluorados" in item.lower()
        for item in recommendation["critical_alerts"]
    )
    assert any(
        "igg4" in item.lower() for item in recommendation["data_model_flags"]
    )
    assert any(
        "aines" in item.lower() for item in recommendation["therapeutic_actions"]
    )


def test_run_rheum_immuno_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/rheum-immuno/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_psychiatry_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso psiquiatria riesgo adolescente",
            "description": "Autolesiones y sintomas postraumaticos",
            "clinical_priority": "critical",
            "specialty": "psiquiatria",
            "sla_target_minutes": 15,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/psychiatry/recommendation",
        json={
            "age_years": 16,
            "traumatic_event_exposure": True,
            "days_since_traumatic_event": 45,
            "reexperiencing_symptoms": True,
            "avoidance_symptoms": True,
            "hyperarousal_symptoms": True,
            "self_harm_present": True,
            "prior_suicide_attempt": True,
            "family_history_suicide": True,
            "social_isolation": True,
            "male_sex": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_name"] == "psychiatry_support_v1"
    assert payload["recommendation"]["severity_level"] == "critical"
    assert any(
        "riesgo suicida" in item.lower() for item in payload["recommendation"]["critical_alerts"]
    )
    assert any(
        "prioridad operativa maxima" in item.lower()
        for item in payload["recommendation"]["triage_actions"]
    )
    assert any("tept" in item.lower() for item in payload["recommendation"]["diagnostic_support"])

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "psychiatry_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "psychiatry_operational_assessment"


def test_run_psychiatry_support_enforces_elderly_insomnia_safety_flow(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso insomnio geriatrico",
            "description": "Paciente anciano con posible dolor secundario",
            "clinical_priority": "high",
            "specialty": "geriatria",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/psychiatry/recommendation",
        json={
            "age_years": 90,
            "insomnia_present": True,
            "pain_secondary_cause_suspected": True,
            "hypnotic_planned": True,
            "benzodiazepine_planned": True,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    assert recommendation["severity_level"] == "high"
    assert any(
        "causas secundarias de dolor" in item.lower()
        for item in recommendation["triage_actions"]
    )
    assert any(
        "benzodiacepinas" in item.lower()
        for item in recommendation["pharmacologic_safety_alerts"]
    )


def test_run_psychiatry_support_flags_pregnancy_and_metabolic_risk(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso bipolar en embarazo",
            "description": "Seguridad farmacologica y medicina interna",
            "clinical_priority": "critical",
            "specialty": "psiquiatria",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/psychiatry/recommendation",
        json={
            "age_years": 34,
            "bipolar_disorder_known": True,
            "pregnancy_ongoing": True,
            "planned_mood_stabilizer": "valproato",
            "eating_disorder_suspected": True,
            "lanugo_present": True,
            "hypotension_present": True,
            "sinus_bradycardia_present": True,
            "purging_vomiting_present": True,
            "hypokalemia_present": True,
            "delusional_disorder_suspected": True,
            "defense_projection": True,
            "defense_regression": True,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    assert any(
        "valproato" in item.lower() for item in recommendation["critical_alerts"]
    )
    assert any(
        "lamotrigina" in item.lower() for item in recommendation["maternal_fetal_actions"]
    )
    assert any(
        "metabolica" in item.lower() for item in recommendation["critical_alerts"]
    )
    assert any(
        "lanugo" in item.lower() for item in recommendation["internal_medicine_alerts"]
    )
    assert any(
        "proyeccion" in item.lower() for item in recommendation["psychodynamic_flags"]
    )


def test_run_psychiatry_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/psychiatry/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_hematology_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso hematologia MAT",
            "description": "Hemolisis intravascular y sospecha TIH",
            "clinical_priority": "critical",
            "specialty": "hematologia",
            "sla_target_minutes": 15,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/hematology/recommendation",
        json={
            "mah_anemia_present": True,
            "thrombocytopenia_present": True,
            "organ_damage_present": True,
            "cold_exposure_trigger": True,
            "intravascular_hemolysis_sudden": True,
            "hemoglobinuria_present": True,
            "free_plasma_hemoglobin_high": True,
            "hypotension_present": True,
            "bloody_diarrhea_prodrome": True,
            "direct_coombs_negative": True,
            "schistocytes_percent": 12,
            "creatinine_elevated": True,
            "heparin_exposure_active": True,
            "days_since_heparin_start": 7,
            "platelet_drop_percent": 60,
            "major_orthopedic_postop_context": True,
            "renal_failure_present": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_name"] == "hematology_support_v1"
    assert payload["recommendation"]["severity_level"] == "critical"
    assert any("mat" in item.lower() for item in payload["recommendation"]["critical_alerts"])
    assert any(
        "shu tipico" in item.lower() for item in payload["recommendation"]["critical_alerts"]
    )
    assert any(
        "suspender heparina" in item.lower()
        for item in payload["recommendation"]["therapeutic_actions"]
    )
    assert any(
        "argatroban" in item.lower()
        for item in payload["recommendation"]["therapeutic_actions"]
    )

    from app.models.agent_run import AgentRun, AgentStep

    run = (
        db_session.query(AgentRun)
        .filter(AgentRun.id == payload["agent_run_id"])
        .first()
    )
    assert run is not None
    assert run.workflow_name == "hematology_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "hematology_operational_assessment"


def test_run_hematology_support_flags_hemophilia_and_splenectomy_safety(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso hemofilia con inhibidores",
            "description": "Sangrado agudo con Emicizumab y seguridad preoperatoria",
            "clinical_priority": "critical",
            "specialty": "hematologia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/hematology/recommendation",
        json={
            "hemophilia_a_severe": True,
            "high_titer_factor_viii_inhibitors": True,
            "acute_hemarthrosis": True,
            "on_emicizumab_prophylaxis": True,
            "prothrombin_complex_planned": True,
            "planned_splenectomy": True,
            "encapsulated_vaccines_completed_preop": False,
            "postsplenectomy_status": True,
            "active_bleeding": False,
            "thromboprophylaxis_started": False,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    assert any(
        "emicizumab" in item.lower()
        for item in recommendation["pharmacologic_safety_alerts"]
    )
    assert any("mat" in item.lower() for item in recommendation["critical_alerts"])
    assert any(
        "encapsulados" in item.lower() for item in recommendation["critical_alerts"]
    )
    assert any(
        "tromboprofilaxis" in item.lower() for item in recommendation["critical_alerts"]
    )


def test_run_hematology_support_flags_oncology_fanconi_and_transplant(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso oncohematologia y fallo medular",
            "description": "Clasificacion fenotipica y trasplante",
            "clinical_priority": "high",
            "specialty": "hematologia",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/hematology/recommendation",
        json={
            "fine_needle_aspirate_only": True,
            "biopsy_histology_available": False,
            "cd20_positive": True,
            "cd3_positive": False,
            "cd15_positive": True,
            "cd30_positive": True,
            "cd19_positive": True,
            "cd5_positive": True,
            "cd23_positive": False,
            "cyclin_d1_positive": True,
            "hhv8_positive": True,
            "ebv_positive": True,
            "htlv1_positive": True,
            "pediatric_patient": True,
            "short_stature": True,
            "cafe_au_lait_spots": True,
            "thumb_or_radius_hypoplasia": True,
            "renal_anomaly_present": True,
            "macrocytosis_present": True,
            "pancytopenia_present": True,
            "hsct_recipient": True,
            "recipient_male": True,
            "donor_karyotype_47xxy_detected": True,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    assert any(
        "biopsia histologica" in item.lower() for item in recommendation["diagnostic_actions"]
    )
    assert any(
        "lbdcg" in item.lower() for item in recommendation["oncology_immunophenotype_notes"]
    )
    assert any(
        "hodgkin" in item.lower() for item in recommendation["oncology_immunophenotype_notes"]
    )
    assert any(
        "fanconi" in item.lower()
        for item in recommendation["inherited_bone_marrow_failure_flags"]
    )
    assert any("klinefelter" in item.lower() for item in recommendation["transplant_flags"])


def test_run_hematology_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/hematology/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_endocrinology_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso endocrino metabolico critico",
            "description": "Hipoglucemia hipocetosica e incidentaloma suprarrenal",
            "clinical_priority": "critical",
            "specialty": "endocrinologia",
            "sla_target_minutes": 15,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/endocrinology/recommendation",
        json={
            "suspected_hypoglycemia": True,
            "fasting_context": True,
            "ketosis_present": False,
            "lactic_acidosis_present": True,
            "hyperammonemia_present": True,
            "dicarboxylic_acids_elevated": True,
            "adrenal_incidentaloma_present": True,
            "isolated_serum_cortisol_screening_planned": True,
            "hypertension_present": True,
            "aldosterone_renin_ratio_completed": False,
            "overnight_dexamethasone_1mg_test_completed": False,
            "urinary_metanephrines_24h_completed": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_name"] == "endocrinology_support_v1"
    assert payload["recommendation"]["severity_level"] == "critical"
    assert any(
        "hipoglucemia sin cetosis" in item.lower()
        for item in payload["recommendation"]["critical_alerts"]
    )
    assert any(
        "triada bioquimica" in item.lower()
        for item in payload["recommendation"]["critical_alerts"]
    )
    assert any(
        "cortisol serico aislado" in item.lower()
        for item in payload["recommendation"]["critical_alerts"]
    )
    assert any(
        "dicarboxilicos" in item.lower()
        for item in payload["recommendation"]["diagnostic_actions"]
    )

    from app.models.agent_run import AgentRun, AgentStep

    run = (
        db_session.query(AgentRun)
        .filter(AgentRun.id == payload["agent_run_id"])
        .first()
    )
    assert run is not None
    assert run.workflow_name == "endocrinology_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "endocrinology_operational_assessment"


def test_run_endocrinology_support_flags_thyroid_and_siadh_safety(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso tiroideo e hiponatremia",
            "description": "CMT preoperatorio y SIADH",
            "clinical_priority": "critical",
            "specialty": "endocrinologia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/endocrinology/recommendation",
        json={
            "pediatric_patient": True,
            "pediatric_growth_deceleration": True,
            "tsh_elevated": True,
            "anti_tpo_positive": True,
            "diffuse_firm_painless_goiter": True,
            "medullary_thyroid_carcinoma_suspected": True,
            "preop_urinary_metanephrines_completed": False,
            "thyroglobulin_followup_planned": True,
            "ret_genetic_study_completed": False,
            "hyponatremia_present": True,
            "plasma_hypoosmolarity_present": True,
            "inappropriately_concentrated_urine": True,
            "serum_sodium_mmol_l": 118,
            "neurologic_symptoms_present": True,
            "tolvaptan_planned": True,
            "water_restriction_planned": True,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    assert any(
        "metanefrinas urinarias preoperatorias" in item.lower()
        for item in recommendation["critical_alerts"]
    )
    assert any(
        "siadh grave" in item.lower() for item in recommendation["critical_alerts"]
    )
    assert any(
        "tiroglobulina no es marcador" in item.lower()
        for item in recommendation["pharmacologic_safety_alerts"]
    )
    assert any(
        "tolvaptan" in item.lower()
        for item in recommendation["pharmacologic_safety_alerts"]
    )


def test_run_endocrinology_support_flags_diabetes_and_confounders(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso diabetes y factores de confusion",
            "description": "Estadiaje DM1 y seguridad farmacologica",
            "clinical_priority": "high",
            "specialty": "endocrinologia",
            "sla_target_minutes": 25,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/endocrinology/recommendation",
        json={
            "hyperprolactinemia_present": True,
            "prolactin_ng_ml": 120,
            "pregnancy_ruled_out": True,
            "pituitary_mri_planned": False,
            "refractory_hypotension_present": True,
            "abdominal_pain_or_vomiting_present": True,
            "skin_mucosal_hyperpigmentation_present": True,
            "hyponatremia_present": True,
            "t1d_autoimmunity_positive": True,
            "prediabetes_range": True,
            "obesity_present": True,
            "high_cardiovascular_risk": True,
            "weight_loss_priority": True,
            "glp1_ra_planned": False,
            "pioglitazone_planned": True,
            "sulfonylurea_planned": True,
            "insulin_planned": True,
            "hypercalcemia_present": True,
            "thiazide_exposure": True,
            "chronic_alcohol_use": True,
            "hypertriglyceridemia_present": True,
            "hdl_low_present": True,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    assert any(
        "estadio 2" in item.lower() for item in recommendation["diabetes_staging_support"]
    )
    assert any("glp-1" in item.lower() for item in recommendation["therapeutic_actions"])
    assert any(
        "pioglitazona" in item.lower()
        for item in recommendation["pharmacologic_safety_alerts"]
    )
    assert any(
        "sulfonilureas" in item.lower()
        for item in recommendation["pharmacologic_safety_alerts"]
    )
    assert any(
        "tiazidas" in item.lower() for item in recommendation["metabolic_context_flags"]
    )
    assert any(
        "alcohol" in item.lower() for item in recommendation["metabolic_context_flags"]
    )


def test_run_endocrinology_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/endocrinology/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_nephrology_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso renopulmonar critico",
            "description": "FRA glomerular con hemorragia alveolar",
            "clinical_priority": "critical",
            "specialty": "nefrologia",
            "sla_target_minutes": 10,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/nephrology/recommendation",
        json={
            "acute_kidney_injury_present": True,
            "urine_sodium_mmol_l": 55,
            "proteinuria_present": True,
            "microhematuria_present": True,
            "dysmorphic_rbc_present": True,
            "bilateral_ground_glass_ct_present": True,
            "pulmonary_hemorrhage_present": True,
            "acute_anemization_present": True,
            "anti_gbm_positive": True,
            "platelet_count_typo_suspected": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_name"] == "nephrology_support_v1"
    assert payload["recommendation"]["severity_level"] == "critical"
    assert payload["recommendation"]["aki_classification"] == "parenchymal"
    assert any(
        "renopulmonar" in item.lower()
        for item in payload["recommendation"]["critical_alerts"]
    )
    assert any(
        "plasmaferesis obligatoria" in item.lower()
        for item in payload["recommendation"]["critical_alerts"]
    )
    assert any(
        "plaquetario dudoso" in item.lower()
        for item in payload["recommendation"]["interpretability_trace"]
    )

    from app.models.agent_run import AgentRun, AgentStep

    run = (
        db_session.query(AgentRun)
        .filter(AgentRun.id == payload["agent_run_id"])
        .first()
    )
    assert run is not None
    assert run.workflow_name == "nephrology_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "nephrology_operational_assessment"


def test_run_nephrology_support_flags_acid_base_and_aeiou(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso acido-base y AEIOU",
            "description": "Acidosis metabolica con sospecha de trastorno mixto",
            "clinical_priority": "critical",
            "specialty": "nefrologia",
            "sla_target_minutes": 15,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/nephrology/recommendation",
        json={
            "ph": 7.18,
            "hco3_mmol_l": 12,
            "pco2_mm_hg": 40,
            "refractory_metabolic_acidosis": True,
            "refractory_hyperkalemia_with_ecg_changes": True,
            "dialyzable_intoxication_lithium": True,
            "refractory_volume_overload_pulmonary_edema": True,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    assert any(
        "trastorno mixto" in item.lower() for item in recommendation["critical_alerts"]
    )
    assert any(
        "acidosis metabolica" in item.lower()
        for item in recommendation["acid_base_assessment"]
    )
    assert any("a:" in item.lower() for item in recommendation["dialysis_alerts"])
    assert any("i:" in item.lower() for item in recommendation["dialysis_alerts"])
    assert any(
        "dialisis urgente" in item.lower() for item in recommendation["critical_alerts"]
    )


def test_run_nephrology_support_flags_nephroprotection_and_interstitial_safety(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso nefroproteccion y glomerulopatias",
            "description": "IgA, NIA farmacologica y seguridad RAAS",
            "clinical_priority": "high",
            "specialty": "nefrologia",
            "sla_target_minutes": 25,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/nephrology/recommendation",
        json={
            "acute_kidney_injury_present": True,
            "urine_sodium_mmol_l": 15,
            "microhematuria_present": True,
            "dysmorphic_rbc_present": True,
            "iga_mesangial_deposits_biopsy": True,
            "c3_mesangial_deposits_biopsy": True,
            "proteinuria_g_24h": 1.4,
            "months_conservative_therapy": 6,
            "recent_drug_trigger_present": True,
            "suspected_drug_name": "amoxicilina-clavulanico",
            "fever_present": True,
            "rash_present": True,
            "eosinophilia_present": True,
            "no_improvement_after_48_72h": True,
            "diabetic_nephropathy_suspected": True,
            "proteinuric_ckd_present": True,
            "sglt2_planned": False,
            "acei_active": True,
            "arb_active": True,
            "diabetic_retinopathy_present": True,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    assert recommendation["aki_classification"] == "prerenal"
    assert any(
        "nefropatia iga" in item.lower()
        for item in recommendation["glomerular_interstitial_flags"]
    )
    assert any(
        "intersticial aguda" in item.lower()
        for item in recommendation["glomerular_interstitial_flags"]
    )
    assert any(
        "isglt2" in item.lower() for item in recommendation["nephroprotection_actions"]
    )
    assert any(
        "doble bloqueo" in item.lower()
        for item in recommendation["pharmacologic_safety_alerts"]
    )


def test_run_nephrology_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/nephrology/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_pneumology_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso neumologico integral",
            "description": "NOC con riesgo funcional para cirugia",
            "clinical_priority": "critical",
            "specialty": "neumologia",
            "sla_target_minutes": 10,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/pneumology/recommendation",
        json={
            "ct_peripheral_subpleural_consolidation": True,
            "air_bronchogram_present": True,
            "po2_low_detected": True,
            "pco2_high_detected": True,
            "respiratory_acidosis_present": True,
            "chronic_hypercapnia_days": 4,
            "renal_compensation_evidence": True,
            "copd_diagnosed": True,
            "persistent_frequent_exacerbator": True,
            "on_laba_lama": True,
            "eosinophils_per_ul": 220,
            "severe_asthma": True,
            "eosinophilic_phenotype": True,
            "chronic_rhinosinusitis_with_polyposis": True,
            "solitary_nodule_malignancy_suspected": True,
            "pet_positive": True,
            "vo2max_ml_kg_min": 8.5,
            "surgery_planned": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_name"] == "pneumology_support_v1"
    assert payload["recommendation"]["severity_level"] == "critical"
    assert any(
        "noc" in item.lower() for item in payload["recommendation"]["imaging_assessment"]
    )
    assert any(
        "bipap" in item.lower() for item in payload["recommendation"]["therapeutic_actions"]
    )
    assert any(
        "triple terapia" in item.lower()
        for item in payload["recommendation"]["therapeutic_actions"]
    )
    assert any(
        "mepolizumab" in item.lower() for item in payload["recommendation"]["biologic_strategy"]
    )
    assert any(
        "vo2 max < 10" in item.lower() for item in payload["recommendation"]["critical_alerts"]
    )

    from app.models.agent_run import AgentRun, AgentStep

    run = (
        db_session.query(AgentRun)
        .filter(AgentRun.id == payload["agent_run_id"])
        .first()
    )
    assert run is not None
    assert run.workflow_name == "pneumology_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "pneumology_operational_assessment"


def test_run_pneumology_support_flags_safety_and_lba_context(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso seguridad EPOC y LBA",
            "description": "Validar alertas de seguridad neumologica",
            "clinical_priority": "high",
            "specialty": "neumologia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/pneumology/recommendation",
        json={
            "copd_diagnosed": True,
            "on_laba_ics_without_lama": True,
            "bibasal_velcro_crackles_present": True,
            "digital_clubbing_present": True,
            "wheeze_present": True,
            "bal_performed": True,
            "sarcoidosis_suspected": True,
            "bal_cd4_cd8_high": True,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    assert recommendation["severity_level"] == "high"
    assert any(
        "laba+corticoide" in item.lower()
        for item in recommendation["procedural_safety_alerts"]
    )
    assert any("sibilancias" in item.lower() for item in recommendation["procedural_safety_alerts"])
    assert any("sarcoidosis" in item.lower() for item in recommendation["diagnostic_actions"])


def test_run_pneumology_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/pneumology/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_geriatrics_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso geriatrico con fragilidad",
            "description": "Inmovilidad con delirium infeccioso",
            "clinical_priority": "critical",
            "specialty": "geriatria",
            "sla_target_minutes": 15,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/geriatrics/recommendation",
        json={
            "patient_age_years": 87,
            "mesangial_matrix_expansion_present": True,
            "glomerular_basement_membrane_thickening_present": True,
            "nephrology_red_flags_present": False,
            "prolonged_immobility_present": True,
            "nitrogen_balance_negative": True,
            "high_protein_support_plan_active": False,
            "delirium_suspected": True,
            "infectious_trigger_suspected": True,
            "insomnia_present": True,
            "benzodiazepine_planned": True,
            "dementia_progression_assessment_planned_during_acute_event": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["workflow_name"] == "geriatrics_support_v1"
    assert payload["recommendation"]["severity_level"] == "critical"
    assert any(
        "mesangial" in item.lower()
        for item in payload["recommendation"]["aging_context_interpretation"]
    )
    assert any(
        "balance nitrogenado negativo" in item.lower()
        for item in payload["recommendation"]["critical_alerts"]
    )
    assert any(
        "benzodiacepinas" in item.lower() for item in payload["recommendation"]["safety_blocks"]
    )

    from app.models.agent_run import AgentRun, AgentStep

    run = (
        db_session.query(AgentRun)
        .filter(AgentRun.id == payload["agent_run_id"])
        .first()
    )
    assert run is not None
    assert run.workflow_name == "geriatrics_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "geriatrics_operational_assessment"


def test_run_geriatrics_support_flags_start_v3_and_tetanus_logic(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso START geriatria",
            "description": "Validar optimizacion farmacologica",
            "clinical_priority": "high",
            "specialty": "geriatria",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/geriatrics/recommendation",
        json={
            "symptomatic_atrophic_vaginitis": True,
            "topical_vaginal_estrogen_active": False,
            "lidocaine_patch_planned_for_general_joint_pain": True,
            "localized_neuropathic_pain_present": False,
            "copd_gold_stage": 2,
            "inhaled_corticosteroid_planned": True,
            "open_wound_present": True,
            "tetanus_booster_planned": True,
            "tetanus_doses_completed": True,
            "years_since_last_tetanus_dose": 3,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    assert recommendation["severity_level"] == "high"
    assert any(
        "estrogenos topicos" in item.lower()
        for item in recommendation["pharmacologic_optimization_actions"]
    )
    assert any("lidocaina" in item.lower() for item in recommendation["safety_blocks"])
    assert any("gold 1-2" in item.lower() for item in recommendation["safety_blocks"])
    assert any("antitetanico" in item.lower() for item in recommendation["safety_blocks"])


def test_run_geriatrics_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/geriatrics/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_oncology_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso oncologico critico en urgencias",
            "description": "irAE hepatica + neutropenia febril",
            "clinical_priority": "critical",
            "specialty": "oncologia",
            "sla_target_minutes": 10,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/oncology/recommendation",
        json={
            "checkpoint_inhibitor_class": "pd-1",
            "checkpoint_agent_name": "pembrolizumab",
            "metastatic_crc_unresectable": True,
            "first_line_setting": True,
            "dmmr_present": True,
            "immune_hepatotoxicity_suspected": True,
            "transaminases_multiple_uln": 6.4,
            "total_bilirubin_mg_dl": 2.8,
            "immunotherapy_suspended": False,
            "prednisone_mg_kg_day": 0.6,
            "refractory_to_steroids": True,
            "infliximab_considered": False,
            "trastuzumab_planned": True,
            "baseline_lvef_assessed": False,
            "temperature_c_single": 38.6,
            "absolute_neutrophil_count_mm3": 420,
            "perioperative_or_adjuvant_context": True,
            "bone_sarcoma_post_neoadjuvant_specimen_available": True,
            "necrosis_rate_percent": 92,
            "ewing_sarcoma_suspected": True,
            "ewsr1_rearrangement_documented": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    recommendation = payload["recommendation"]

    assert payload["workflow_name"] == "oncology_support_v1"
    assert recommendation["severity_level"] == "critical"
    assert any("pd-1" in item.lower() for item in recommendation["immunotherapy_mechanism_notes"])
    assert any("dmmr/msi-high" in item.lower() for item in recommendation["biomarker_strategy"])
    assert any(
        "neutropenia febril" in item.lower() for item in recommendation["critical_alerts"]
    )
    assert any("fevi basal" in item.lower() for item in recommendation["critical_alerts"])
    assert any("necrosis" in item.lower() for item in recommendation["sarcoma_response_actions"])
    assert any("ewsr1" in item.lower() for item in recommendation["sarcoma_response_actions"])

    from app.models.agent_run import AgentRun, AgentStep

    run = (
        db_session.query(AgentRun)
        .filter(AgentRun.id == payload["agent_run_id"])
        .first()
    )
    assert run is not None
    assert run.workflow_name == "oncology_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "oncology_operational_assessment"


def test_run_oncology_support_flags_cardio_and_sarcoma_branches(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso oncologico de ramas operativas",
            "description": "Cardio-onco + sarcoma post-neoadyuvancia",
            "clinical_priority": "high",
            "specialty": "oncologia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/oncology/recommendation",
        json={
            "checkpoint_inhibitor_class": "pd-l1",
            "checkpoint_agent_name": "atezolizumab",
            "immune_hepatotoxicity_suspected": True,
            "hepatic_toxicity_grade": 2,
            "refractory_to_steroids": True,
            "infliximab_considered": True,
            "rechallenge_considered_after_resolution": True,
            "anthracycline_planned": True,
            "baseline_lvef_percent": 45,
            "fever_over_38_more_than_1h": True,
            "absolute_neutrophil_count_mm3": 780,
            "anc_expected_to_drop_below_500": True,
            "palliative_later_line_context": True,
            "bone_sarcoma_post_neoadjuvant_specimen_available": True,
            "necrosis_rate_percent": 55,
            "ewing_sarcoma_suspected": True,
            "ewsr1_rearrangement_documented": True,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]

    assert recommendation["severity_level"] == "critical"
    assert any(
        "infliximab" in item.lower() for item in recommendation["toxicity_management_actions"]
    )
    assert any(
        "paliativo" in item.lower() for item in recommendation["febrile_neutropenia_actions"]
    )
    assert any("suboptima" in item.lower() for item in recommendation["sarcoma_response_actions"])
    assert any(
        "ewsr1 documentado" in item.lower() for item in recommendation["sarcoma_response_actions"]
    )
    assert any("fevi basal reducida" in item.lower() for item in recommendation["critical_alerts"])


def test_run_oncology_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/oncology/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_anesthesiology_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso anestesia urgente",
            "description": "ISR por obstruccion y dolor presacro refractario",
            "clinical_priority": "critical",
            "specialty": "anestesia",
            "sla_target_minutes": 10,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/anesthesiology/recommendation",
        json={
            "emergency_airway_needed": True,
            "intestinal_obstruction_present": True,
            "preoxygenation_minutes_planned": 3.5,
            "bag_mask_manual_ventilation_planned": True,
            "expected_intubation_seconds_after_iv": 55,
            "iv_route_confirmed": False,
            "inhaled_halogenated_induction_planned": True,
            "hypnotic_agent": "propofol",
            "neuromuscular_blocker_agent": "rocuronio",
            "sellick_maneuver_planned": True,
            "tube_position_verified": False,
            "cuff_inflated": False,
            "presacral_mass_present": True,
            "severe_perineal_or_pelvic_internal_pain": True,
            "neuropathic_pain_component": True,
            "opioid_response_insufficient": True,
            "perineal_pelvic_internal_pain": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    recommendation = payload["recommendation"]

    assert payload["workflow_name"] == "anesthesiology_support_v1"
    assert recommendation["severity_level"] == "critical"
    assert any(
        "kit de induccion" in item.lower()
        for item in recommendation["rapid_sequence_induction_actions"]
    )
    assert any(
        "evitar ventilacion manual" in item.lower() for item in recommendation["critical_alerts"]
    )
    assert any(
        "ganglio impar" in item.lower()
        for item in recommendation["sympathetic_block_recommendations"]
    )

    from app.models.agent_run import AgentRun, AgentStep

    run = (
        db_session.query(AgentRun)
        .filter(AgentRun.id == payload["agent_run_id"])
        .first()
    )
    assert run is not None
    assert run.workflow_name == "anesthesiology_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "anesthesiology_operational_assessment"


def test_run_anesthesiology_support_differential_blocks_and_safety(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso diferencial de bloqueos",
            "description": "Dolor con criterios anatomicos mixtos",
            "clinical_priority": "high",
            "specialty": "anestesia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/anesthesiology/recommendation",
        json={
            "emergency_airway_needed": True,
            "no_preop_fasting": True,
            "preoxygenation_minutes_planned": 2.0,
            "expected_intubation_seconds_after_iv": 80,
            "iv_route_confirmed": True,
            "hypnotic_agent": "propofol",
            "neuromuscular_blocker_agent": "rocuronio",
            "sellick_maneuver_planned": False,
            "upper_abdominal_visceral_pain": True,
            "pelvic_genital_autonomic_pain": True,
            "perineal_external_genital_pain": True,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]

    assert recommendation["severity_level"] == "high"
    assert any(
        "plexo celiaco" in item.lower()
        for item in recommendation["differential_block_recommendations"]
    )
    assert any(
        "esplacnicos" in item.lower()
        for item in recommendation["differential_block_recommendations"]
    )
    assert any(
        "pudendos" in item.lower()
        for item in recommendation["differential_block_recommendations"]
    )
    assert any("3 minutos" in item.lower() for item in recommendation["airway_safety_blocks"])
    assert any("45-60" in item.lower() for item in recommendation["airway_safety_blocks"])
    assert any("sellick" in item.lower() for item in recommendation["airway_safety_blocks"])


def test_run_anesthesiology_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/anesthesiology/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_palliative_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso paliativo terminal",
            "description": "Decision final de cuidados y seguridad opioide",
            "clinical_priority": "high",
            "specialty": "paliativos",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/palliative/recommendation",
        json={
            "patient_rejects_life_prolonging_treatment": True,
            "informed_consequences_documented": False,
            "effort_adequation_planned": True,
            "professional_futility_assessment_documented": True,
            "renal_failure_present": True,
            "morphine_active": True,
            "breakthrough_pain_present": True,
            "rapid_onset_rescue_opioid_planned": True,
            "transmucosal_fentanyl_planned": True,
            "advanced_dementia_present": True,
            "dysphagia_or_oral_intake_refusal": True,
            "enteral_tube_sng_or_peg_planned": True,
            "comfort_feeding_planned": False,
            "renal_function_deterioration_present": True,
            "intense_somnolence_present": True,
            "tactile_hallucinations_present": True,
            "delirium_present": True,
            "reversible_cause_addressed": False,
            "neuroleptic_planned": True,
            "persistent_delirium_after_cause_treatment": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    recommendation = payload["recommendation"]

    assert payload["workflow_name"] == "palliative_support_v1"
    assert recommendation["severity_level"] == "critical"
    assert any("morfina activa" in item.lower() for item in recommendation["critical_alerts"])
    assert any("sng/peg" in item.lower() for item in recommendation["critical_alerts"])
    assert any(
        "alimentacion de confort" in item.lower()
        for item in recommendation["dementia_comfort_actions"]
    )
    assert any(
        "rotacion opioide" in item.lower() for item in recommendation["opioid_safety_actions"]
    )

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "palliative_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "palliative_operational_assessment"


def test_run_palliative_support_flags_ethical_and_delirium_logic(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso paliativo legal",
            "description": "Circuito LO 3/2021 y delirium persistente",
            "clinical_priority": "high",
            "specialty": "paliativos",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/palliative/recommendation",
        json={
            "aid_in_dying_request_expressed": True,
            "aid_in_dying_request_reiterated": False,
            "aid_in_dying_process_formalized_per_lo_3_2021": False,
            "chronic_pain_baseline_present": True,
            "long_acting_opioid_active": False,
            "breakthrough_pain_present": True,
            "rapid_onset_rescue_opioid_planned": False,
            "delirium_present": True,
            "reversible_cause_addressed": True,
            "neuroleptic_planned": True,
            "persistent_delirium_after_cause_treatment": True,
            "steroid_psychosis_hyperactive_profile": True,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]

    assert recommendation["severity_level"] == "high"
    assert any("lo 3/2021" in item.lower() for item in recommendation["ethical_legal_actions"])
    assert any("formalizacion legal" in item.lower() for item in recommendation["safety_blocks"])
    assert any("delirium" in item.lower() for item in recommendation["delirium_management_actions"])
    assert any(
        "psicosis por corticoides" in item.lower()
        for item in recommendation["delirium_management_actions"]
    )


def test_run_palliative_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/palliative/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_urology_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso urologia critica",
            "description": "Gas urinario, FRA obstructivo y trauma genital",
            "clinical_priority": "critical",
            "specialty": "urologia",
            "sla_target_minutes": 10,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/urology/recommendation",
        json={
            "diabetes_mellitus_poor_control": True,
            "hypertension_present": True,
            "urinary_tract_gas_on_imaging": True,
            "urinary_obstruction_lithiasis_suspected": True,
            "urgent_urinary_diversion_planned": False,
            "colicky_flank_pain_present": True,
            "vomiting_present": True,
            "anuria_present": True,
            "creatinine_mg_dl": 8.1,
            "bilateral_pyelocaliceal_dilation_on_ultrasound": True,
            "urgent_ct_planned_before_diversion": True,
            "genital_trauma_during_erection": True,
            "penile_edema_or_expansive_hematoma_present": True,
            "flaccid_penis_after_trauma": True,
            "bladder_catheterization_planned": True,
            "urgent_surgical_review_planned": False,
            "cavernosal_blood_gas_planned": True,
            "localized_renal_tumor_suspected": True,
            "renal_mass_cm": 5.0,
            "solitary_functional_kidney": True,
            "contralateral_kidney_atrophy_present": True,
            "planned_partial_nephrectomy": False,
            "planned_radical_nephrectomy": True,
            "prostate_mri_anterior_lesion_present": True,
            "transrectal_biopsy_planned": True,
            "transperineal_fusion_biopsy_planned": False,
            "prostate_metastatic_high_volume": True,
            "gleason_score": 9,
            "bone_metastases_present": True,
            "liver_metastases_present": True,
            "lhrh_analog_planned": True,
            "docetaxel_planned": True,
            "novel_antiandrogen_name": "darolutamida",
            "local_curative_treatment_planned": True,
            "radiotherapy_planned": True,
            "low_volume_metastatic_profile": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    recommendation = payload["recommendation"]

    assert payload["workflow_name"] == "urology_support_v1"
    assert recommendation["severity_level"] == "critical"
    assert any(
        "pielonefritis enfisematosa" in item.lower()
        for item in recommendation["critical_alerts"]
    )
    assert any(
        "derivacion urinaria urgente antes de tac" in item.lower()
        for item in recommendation["obstruction_actions"]
    )
    assert any(
        "bloquear orden de sondaje vesical" in item.lower()
        for item in recommendation["safety_blocks"]
    )
    assert any(
        "nefrectomia parcial" in item.lower()
        for item in recommendation["oncologic_actions"]
    )
    assert any(
        "biopsia transperineal" in item.lower()
        for item in recommendation["oncologic_actions"]
    )

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "urology_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "urology_operational_assessment"


def test_run_urology_support_prioritizes_diversion_and_triple_therapy_safety(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso urologia onco-obstructiva",
            "description": "Priorizacion de derivacion y seguridad sistemica",
            "clinical_priority": "high",
            "specialty": "urologia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/urology/recommendation",
        json={
            "colicky_flank_pain_present": True,
            "anuria_present": True,
            "creatinine_mg_dl": 7.4,
            "bilateral_pyelocaliceal_dilation_on_ultrasound": True,
            "urgent_urinary_diversion_planned": True,
            "urgent_ct_planned_before_diversion": True,
            "prostate_metastatic_high_volume": True,
            "gleason_score": 9,
            "bone_metastases_present": True,
            "liver_metastases_present": True,
            "lhrh_analog_planned": False,
            "docetaxel_planned": True,
            "novel_antiandrogen_name": "enzalutamida",
            "local_curative_treatment_planned": True,
            "radiotherapy_planned": True,
            "low_volume_metastatic_profile": False,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]

    assert recommendation["severity_level"] == "critical"
    assert any(
        "falta analogo lhrh" in item.lower() for item in recommendation["critical_alerts"]
    )
    assert any(
        "antiandrogeno" in item.lower() for item in recommendation["critical_alerts"]
    )
    assert any(
        "bloquear secuencia tac previo" in item.lower() for item in recommendation["safety_blocks"]
    )
    assert any(
        "bloquear tratamiento local curativo" in item.lower()
        for item in recommendation["safety_blocks"]
    )
    assert any(
        "docetaxel-enzalutamida" in item.lower() for item in recommendation["safety_blocks"]
    )


def test_run_urology_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/urology/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_epidemiology_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso epidemiologia aplicada",
            "description": "Metricas de riesgo y causalidad",
            "clinical_priority": "high",
            "specialty": "salud_publica",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/epidemiology/recommendation",
        json={
            "requested_individual_risk_estimation": True,
            "requested_population_status_snapshot": True,
            "new_cases_count": 30,
            "population_at_risk_count": 1000,
            "person_time_at_risk": 5000,
            "existing_cases_count": 120,
            "population_total_count": 2000,
            "exposed_risk": 0.047,
            "unexposed_risk": 0.1,
            "control_event_risk": 0.044,
            "intervention_event_risk": 0.038,
            "hill_strength_of_association": True,
            "hill_temporality": True,
            "hill_biological_gradient": True,
            "economic_study_type": "coste-utilidad",
            "qaly_or_utility_outcomes_used": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    recommendation = payload["recommendation"]

    assert payload["workflow_name"] == "epidemiology_support_v1"
    assert recommendation["severity_level"] == "medium"
    assert recommendation["critical_alerts"] == []
    assert abs(recommendation["incidence_accumulated"] - 0.03) < 0.0001
    assert abs(recommendation["incidence_density"] - 0.006) < 0.0001
    assert abs(recommendation["prevalence"] - 0.06) < 0.0001
    assert abs(recommendation["risk_relative"] - 0.47) < 0.0001
    assert abs(recommendation["absolute_risk_reduction"] - 0.006) < 0.0001
    assert abs(recommendation["number_needed_to_treat"] - 166.6667) < 0.01
    assert any(
        "se reduciria un 53.0%" in item.lower()
        for item in recommendation["causal_inference_actions"]
    )
    assert any(
        "coste-utilidad" in item.lower() for item in recommendation["economic_evaluation_actions"]
    )

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "epidemiology_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "epidemiology_operational_assessment"


def test_run_epidemiology_support_flags_rr_and_nnt_safety_blocks(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso seguridad epidemiologia",
            "description": "RR no calculable y coste-utilidad inconsistente",
            "clinical_priority": "high",
            "specialty": "salud_publica",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/epidemiology/recommendation",
        json={
            "requested_individual_risk_estimation": True,
            "exposed_risk": 0.2,
            "unexposed_risk": 0.0,
            "control_event_risk": 0.1,
            "intervention_event_risk": 0.1,
            "hill_temporality": False,
            "economic_study_type": "coste-utilidad",
            "qaly_or_utility_outcomes_used": False,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]

    assert recommendation["severity_level"] == "critical"
    assert any(
        "rr potencialmente infinito" in item.lower() for item in recommendation["critical_alerts"]
    )
    assert any("rr no calculable" in item.lower() for item in recommendation["safety_blocks"])
    assert any("rar igual a 0" in item.lower() for item in recommendation["safety_blocks"])
    assert any("temporalidad" in item.lower() for item in recommendation["safety_blocks"])
    assert any(
        "coste-utilidad sin avac/qaly" in item.lower() for item in recommendation["safety_blocks"]
    )


def test_run_epidemiology_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/epidemiology/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_ophthalmology_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso oftalmologia vascular e IFIS",
            "description": "Perdida visual brusca con riesgo perioperatorio",
            "clinical_priority": "critical",
            "specialty": "oftalmologia",
            "sla_target_minutes": 10,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/ophthalmology/recommendation",
        json={
            "sudden_visual_loss": True,
            "fundus_flame_hemorrhages_present": True,
            "fundus_papilledema_present": True,
            "intraocular_pressure_mmhg": 28,
            "cataract_surgery_planned": True,
            "tamsulosin_or_alpha_blocker_active": True,
            "intracameral_phenylephrine_planned": False,
            "drusen_present": True,
            "neovascular_membrane_or_exudation_present": True,
            "anti_vegf_planned": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    recommendation = payload["recommendation"]

    assert payload["workflow_name"] == "ophthalmology_support_v1"
    assert recommendation["severity_level"] == "critical"
    assert any("ovcr" in item.lower() for item in recommendation["critical_alerts"])
    assert any("ifis" in item.lower() for item in recommendation["critical_alerts"])
    assert any(
        "fenilefrina intracamerular" in item.lower()
        for item in recommendation["safety_blocks"]
    )
    assert any("dmae humeda" in item.lower() for item in recommendation["critical_alerts"])

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "ophthalmology_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "ophthalmology_operational_assessment"


def test_run_ophthalmology_support_flags_neuro_and_anisocoria_logic(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso neuroftalmologia pupilar",
            "description": "Anisocoria y DPAR en urgencias",
            "clinical_priority": "high",
            "specialty": "oftalmologia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/ophthalmology/recommendation",
        json={
            "anisocoria_present": True,
            "anisocoria_worse_in_darkness": True,
            "anisocoria_worse_in_bright_light": True,
            "relative_afferent_pupillary_defect_present": True,
            "optic_nerve_disease_suspected": False,
            "extensive_retinal_disease_suspected": False,
            "posterior_communicating_aneurysm_suspected": True,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]

    assert recommendation["severity_level"] == "critical"
    assert any(
        "disfuncion simpatica" in item.lower()
        for item in recommendation["neuro_ophthalmology_actions"]
    )
    assert any(
        "disfuncion parasimpatica" in item.lower()
        for item in recommendation["neuro_ophthalmology_actions"]
    )
    assert any(
        "patrones simpatico y parasimpatico simultaneos" in item.lower()
        for item in recommendation["safety_blocks"]
    )
    assert any("dpar sin sospecha" in item.lower() for item in recommendation["safety_blocks"])
    assert any("iii par" in item.lower() for item in recommendation["critical_alerts"])


def test_run_ophthalmology_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/ophthalmology/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_immunology_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso inmunodeficiencia humoral critica",
            "description": "Sospecha Bruton con infecciones sinopulmonares recurrentes",
            "clinical_priority": "critical",
            "specialty": "inmunologia",
            "sla_target_minutes": 10,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/immunology/recommendation",
        json={
            "patient_male": True,
            "age_months": 14,
            "btk_mutation_confirmed": True,
            "peripheral_cd19_cd20_b_cells_absent": True,
            "igg_low_or_absent": True,
            "iga_low_or_absent": True,
            "igm_low_or_absent": True,
            "recurrent_sinopulmonary_bacterial_infections": True,
            "lower_respiratory_infection_active": True,
            "alveolar_macrophage_dysfunction_suspected": True,
            "monocyte_function_abnormal_reported": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    recommendation = payload["recommendation"]

    assert payload["workflow_name"] == "immunology_support_v1"
    assert recommendation["severity_level"] == "critical"
    assert any("bruton" in item.lower() for item in recommendation["critical_alerts"])
    assert any("macrofago alveolar" in item.lower() for item in recommendation["critical_alerts"])
    assert any("funcion monocitaria" in item.lower() for item in recommendation["safety_blocks"])
    assert any("cd19/cd20" in item.lower() for item in recommendation["interpretability_trace"])

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "immunology_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "immunology_operational_assessment"


def test_run_immunology_support_differential_profiles_and_safety_blocks(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso diferencial humoral mixto",
            "description": "Patron analitico inconsistente en inmunoglobulinas",
            "clinical_priority": "high",
            "specialty": "inmunologia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/immunology/recommendation",
        json={
            "igg_low_or_absent": True,
            "iga_low_or_absent": True,
            "igm_low_or_absent": True,
            "igm_elevated": True,
            "peripheral_cd19_cd20_b_cells_absent": False,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]

    assert recommendation["severity_level"] == "critical"
    assert any("hiper-igm" in item.lower() for item in recommendation["critical_alerts"])
    assert any(
        "igm marcada simultaneamente" in item.lower()
        for item in recommendation["safety_blocks"]
    )
    assert any(
        "multiples perfiles humorales" in item.lower()
        for item in recommendation["safety_blocks"]
    )


def test_run_immunology_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/immunology/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_genetic_recurrence_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Recurrencia OI tipo II",
            "description": "Dos gestaciones afectadas con padres fenotipicamente sanos",
            "clinical_priority": "critical",
            "specialty": "genetica",
            "sla_target_minutes": 15,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/genetic-recurrence/recommendation",
        json={
            "gestational_age_weeks": 26,
            "autosomal_dominant_condition_suspected": True,
            "oi_type_ii_suspected": True,
            "col1a1_or_col1a2_involved": True,
            "previous_pregnancy_with_same_condition": True,
            "recurrent_affected_pregnancies_count": 2,
            "parents_phenotypically_unaffected": True,
            "de_novo_hypothesis_active": True,
            "molecular_confirmation_available": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    recommendation = payload["recommendation"]

    assert payload["workflow_name"] == "genetic_recurrence_support_v1"
    assert recommendation["severity_level"] == "critical"
    assert recommendation["mosaicism_alert_active"] is True
    assert "mosaicismo_germinal" in recommendation["prioritized_recurrence_mechanism"]
    assert any("mosaicismo" in item.lower() for item in recommendation["critical_alerts"])
    assert any("de novo aislado" in item.lower() for item in recommendation["safety_blocks"])

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "genetic_recurrence_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "genetic_recurrence_operational_assessment"


def test_run_genetic_recurrence_support_handles_mosaicism_fraction_and_consistency(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Recurrencia genetica con datos inconsistentes",
            "description": "Validar bloqueos de seguridad en consejo genetico",
            "clinical_priority": "high",
            "specialty": "genetica",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/genetic-recurrence/recommendation",
        json={
            "autosomal_dominant_condition_suspected": True,
            "recurrent_affected_pregnancies_count": 3,
            "parents_phenotypically_unaffected": True,
            "mother_phenotypically_affected": True,
            "germline_mosaicism_confirmed": True,
            "somatic_mosaicism_only_confirmed": True,
            "estimated_mutated_gamete_fraction_percent": 40,
            "molecular_confirmation_available": False,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]

    assert recommendation["mosaicism_alert_active"] is True
    assert (
        recommendation["prioritized_recurrence_mechanism"]
        == "mosaicismo_germinal_confirmado"
    )
    assert recommendation["estimated_recurrence_risk_percent"] == 40
    assert any(
        "inconsistencia fenotipica parental" in item.lower()
        for item in recommendation["safety_blocks"]
    )
    assert any(
        "sin confirmacion molecular" in item.lower()
        for item in recommendation["safety_blocks"]
    )
    assert any(
        "normalizar clasificacion" in item.lower()
        for item in recommendation["safety_blocks"]
    )


def test_run_genetic_recurrence_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/genetic-recurrence/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_gynecology_obstetrics_support_returns_recommendation_and_trace(
    client, db_session
):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso GO urgente con ectopico y preeclampsia",
            "description": "Validar alertas criticas gineco-obstetricas",
            "clinical_priority": "critical",
            "specialty": "ginecologia_obstetricia",
            "sla_target_minutes": 10,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/gynecology-obstetrics/recommendation",
        json={
            "reproductive_age_with_abdominal_pain_or_bleeding": True,
            "pregnancy_test_positive": True,
            "severe_abdominal_pain": True,
            "vaginal_spotting_present": True,
            "free_intraperitoneal_fluid_on_ultrasound": True,
            "dilated_or_violaceous_tube_on_ultrasound": True,
            "postpartum_preeclampsia_suspected": True,
            "systolic_bp_mm_hg": 168,
            "severe_features_present": True,
            "iv_antihypertensive_started": False,
            "magnesium_sulfate_started": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    recommendation = payload["recommendation"]

    assert payload["workflow_name"] == "gynecology_obstetrics_support_v1"
    assert recommendation["severity_level"] == "critical"
    assert any("ectopica" in item.lower() for item in recommendation["critical_alerts"])
    assert any("sistolica >=160" in item.lower() for item in recommendation["critical_alerts"])
    assert any("antihipertensivo iv" in item.lower() for item in recommendation["safety_blocks"])
    assert any("sulfato de magnesio" in item.lower() for item in recommendation["safety_blocks"])

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "gynecology_obstetrics_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "gynecology_obstetrics_operational_assessment"


def test_run_gynecology_obstetrics_support_blocks_unsafe_pharmacology(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso GO seguridad farmacologica",
            "description": "Validar bloqueos en linfedema y anticoncepcion",
            "clinical_priority": "high",
            "specialty": "ginecologia_obstetricia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/gynecology-obstetrics/recommendation",
        json={
            "oral_contraception_planned": True,
            "baseline_history_completed": False,
            "baseline_bp_recorded": False,
            "baseline_bmi_recorded": False,
            "routine_cytology_required_before_ocp": True,
            "routine_thrombophilia_panel_required_before_ocp": True,
            "progestin_generation": "third",
            "chronic_lymphedema_post_oncologic_surgery": True,
            "diuretic_prescription_requested": True,
            "fetal_neuroprotection_magnesium_requested": True,
            "ruptured_membranes_present": True,
            "cervix_long_without_contractions": True,
            "gestational_age_weeks": 30,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]

    assert recommendation["severity_level"] == "high"
    assert any(
        "bloqueo de diureticos" in item.lower()
        for item in recommendation["safety_blocks"]
    )
    assert any(
        "fisioterapia descongestiva" in item.lower()
        for item in recommendation["pharmacology_prevention_actions"]
    )
    assert any("citologia rutinaria" in item.lower() for item in recommendation["safety_blocks"])
    assert any("trombofilia rutinaria" in item.lower() for item in recommendation["safety_blocks"])
    assert any("no indicada en rpm" in item.lower() for item in recommendation["safety_blocks"])


def test_run_gynecology_obstetrics_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/gynecology-obstetrics/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_pediatrics_neonatology_support_returns_recommendation_and_trace(
    client, db_session
):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso pediatrico exantematico y neonatal",
            "description": "Validar aislamiento respiratorio y soporte neonatal",
            "clinical_priority": "critical",
            "specialty": "pediatria_neonatologia",
            "sla_target_minutes": 10,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/pediatrics-neonatology/recommendation",
        json={
            "patient_age_months": 10,
            "high_fever_present": True,
            "photophobia_present": True,
            "cough_present": True,
            "koplik_spots_present": True,
            "respiratory_isolation_started": False,
            "mmr_doses_received": 0,
            "apgar_minute_1": 8,
            "apgar_minute_5": 9,
            "neonatal_heart_rate_bpm": 120,
            "spontaneous_breathing_present": True,
            "neonatal_respiratory_distress_present": True,
            "neonatal_cyanosis_present": True,
            "minute_of_life": 3,
            "oxygen_saturation_percent": 70,
            "oxygen_increase_requested": True,
            "cpap_started": False,
            "gestational_age_weeks": 38,
            "fio2_percent": 21,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    recommendation = payload["recommendation"]

    assert payload["workflow_name"] == "pediatrics_neonatology_support_v1"
    assert recommendation["severity_level"] == "critical"
    assert any("sarampion" in item.lower() for item in recommendation["critical_alerts"])
    assert any(
        "aislamiento respiratorio" in item.lower()
        for item in recommendation["safety_blocks"]
    )
    assert any(
        "no aumentar o2" in item.lower() for item in recommendation["safety_blocks"]
    )
    assert any(
        "susceptible" in item.lower()
        for item in recommendation["infectious_exanthem_actions"]
    )
    assert any(
        "cpap" in item.lower()
        for item in recommendation["neonatal_resuscitation_actions"]
    )

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "pediatrics_neonatology_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "pediatrics_neonatology_operational_assessment"


def test_run_pediatrics_neonatology_support_flags_critical_branches(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso pediatrico critico mixto",
            "description": "Validar tosferina, invaginacion y sifilis congenita",
            "clinical_priority": "high",
            "specialty": "pediatria_neonatologia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/pediatrics-neonatology/recommendation",
        json={
            "patient_age_months": 12,
            "confirmed_pertussis_case": True,
            "household_contact": True,
            "macrolide_prophylaxis_started": False,
            "intermittent_colicky_abdominal_pain": True,
            "asymptomatic_intervals_between_pain": True,
            "hutchinson_teeth_present": True,
            "interstitial_keratitis_present": True,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]

    assert recommendation["severity_level"] == "critical"
    assert any("tosferina" in item.lower() for item in recommendation["critical_alerts"])
    assert any(
        "invaginacion" in item.lower() for item in recommendation["critical_alerts"]
    )
    assert any(
        "sifilis congenita" in item.lower()
        for item in recommendation["critical_alerts"]
    )
    assert any(
        "azitromicina" in item.lower()
        for item in recommendation["pertussis_contact_actions"]
    )


def test_run_pediatrics_neonatology_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/pediatrics-neonatology/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_anisakis_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso sospecha anisakis alergico",
            "description": "Urticaria y compromiso respiratorio tras ingesta de pescado",
            "clinical_priority": "critical",
            "specialty": "urgencias",
            "sla_target_minutes": 10,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/anisakis/recommendation",
        json={
            "fish_ingestion_last_hours": 4.0,
            "raw_or_undercooked_fish_exposure": True,
            "insufficient_cooking_suspected": True,
            "urticaria_present": True,
            "respiratory_compromise_present": True,
            "specific_ige_requested": False,
            "freezing_temperature_c": -10,
            "freezing_duration_hours": 24,
            "cooking_temperature_c": 50,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    recommendation = payload["recommendation"]

    assert payload["workflow_name"] == "anisakis_support_v1"
    assert recommendation["severity_level"] == "critical"
    assert any(
        "sospecha de alergia a anisakis" in item.lower()
        for item in recommendation["critical_alerts"]
    )
    assert any("anafilaxia grave" in item.lower() for item in recommendation["critical_alerts"])
    assert any("ige especifica" in item.lower() for item in recommendation["safety_blocks"])
    assert any(
        "congelacion previa insuficiente" in item.lower()
        for item in recommendation["safety_blocks"]
    )
    assert any(
        "-20 c" in item.lower() for item in recommendation["discharge_prevention_actions"]
    )
    assert any(
        "por encima de 60 c" in item.lower()
        for item in recommendation["discharge_prevention_actions"]
    )

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "anisakis_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "anisakis_operational_assessment"


def test_run_anisakis_support_handles_digestive_profile_without_anaphylaxis(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso perfil digestivo anisakis",
            "description": "Sintomas digestivos sin anafilaxia",
            "clinical_priority": "medium",
            "specialty": "urgencias",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/anisakis/recommendation",
        json={
            "fish_ingestion_last_hours": 12,
            "raw_or_undercooked_fish_exposure": True,
            "digestive_symptoms_present": True,
            "deep_sea_eviscerated_or_ultrafrozen_fish_consumed": False,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]

    assert recommendation["severity_level"] == "medium"
    assert any(
        "cuadro digestivo sin fenotipo alergico" in item.lower()
        for item in recommendation["diagnostic_actions"]
    )
    assert any(
        "ultracongelado/eviscerado en altamar" in item.lower()
        for item in recommendation["discharge_prevention_actions"]
    )
    assert recommendation["critical_alerts"] == []


def test_run_anisakis_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/anisakis/recommendation",
        json={},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_medicolegal_ops_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso medico-legal de guardia",
            "description": "Validar soporte legal en urgencias",
            "clinical_priority": "high",
            "specialty": "emergency",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/medicolegal/recommendation",
        json={
            "triage_wait_minutes": 8,
            "first_medical_contact_minutes": 35,
            "patient_age_years": 42,
            "patient_has_decision_capacity": True,
            "invasive_procedure_planned": True,
            "informed_consent_documented": False,
            "intoxication_forensic_context": True,
            "chain_of_custody_started": False,
            "suspected_crime_injuries": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["care_task_id"] == task_id
    assert payload["workflow_name"] == "medicolegal_ops_support_v1"
    assert payload["agent_run_id"] > 0
    assert payload["recommendation"]["human_validation_required"] is True
    assert payload["recommendation"]["legal_risk_level"] in {"low", "medium", "high"}
    assert len(payload["recommendation"]["critical_legal_alerts"]) >= 1
    assert payload["recommendation"]["life_preserving_override_recommended"] is False
    assert payload["recommendation"]["urgency_summary"] != ""

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "medicolegal_ops_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "medicolegal_operational_assessment"


def test_run_medicolegal_ops_detects_non_natural_death_red_flag(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso fallecimiento sospechoso",
            "description": "Escenario para alerta medico-legal critica",
            "clinical_priority": "critical",
            "specialty": "emergency",
            "sla_target_minutes": 15,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/medicolegal/recommendation",
        json={
            "patient_age_years": 67,
            "patient_has_decision_capacity": False,
            "non_natural_death_suspected": True,
        },
    )
    assert response.status_code == 200
    alerts = response.json()["recommendation"]["critical_legal_alerts"]
    assert any("muerte no natural" in item.lower() for item in alerts)


def test_run_medicolegal_ops_pediatric_life_saving_conflict_prioritizes_protection(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Conflicto bioetico pediatrico en criticos",
            "description": "Menor con hemorragia y conflicto de representacion",
            "clinical_priority": "critical",
            "specialty": "pediatria",
            "sla_target_minutes": 5,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/medicolegal/recommendation",
        json={
            "patient_age_years": 8,
            "patient_has_decision_capacity": False,
            "legal_representative_present": False,
            "legal_representatives_deceased": True,
            "parental_religious_refusal_life_saving_treatment": True,
            "life_threatening_condition": True,
            "blood_transfusion_indicated": True,
            "immediate_judicial_authorization_available": False,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]

    assert recommendation["legal_risk_level"] == "high"
    assert recommendation["life_preserving_override_recommended"] is True
    assert any(
        "interes superior del menor" in item.lower()
        for item in recommendation["ethical_legal_basis"]
    )
    assert any(
        "interes superior del menor" in item.lower()
        for item in recommendation["critical_legal_alerts"]
    )
    assert any(
        "estado de necesidad terapeutica" in item.lower()
        for item in recommendation["required_documents"]
    )
    assert any(
        "no demorar medida de soporte vital indicada" in item.lower()
        for item in recommendation["operational_actions"]
    )
    assert any(
        "imposibilidad de autorizacion judicial inmediata" in item.lower()
        for item in recommendation["compliance_checklist"]
    )
    assert "riesgo vital inminente" in recommendation["urgency_summary"].lower()


def test_run_medicolegal_ops_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/medicolegal/recommendation",
        json={
            "patient_age_years": 30,
            "patient_has_decision_capacity": True,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_create_medicolegal_audit_and_summary(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso auditoria medico-legal",
            "description": "Validar calidad del motor medico-legal",
            "clinical_priority": "high",
            "specialty": "emergency",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    run_response = client.post(
        f"/api/v1/care-tasks/{task_id}/medicolegal/recommendation",
        json={
            "triage_wait_minutes": 8,
            "first_medical_contact_minutes": 35,
            "patient_age_years": 44,
            "invasive_procedure_planned": True,
            "informed_consent_documented": False,
            "intoxication_forensic_context": True,
            "chain_of_custody_started": False,
            "suspected_crime_injuries": True,
        },
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["agent_run_id"]

    audit_response = client.post(
        f"/api/v1/care-tasks/{task_id}/medicolegal/audit",
        json={
            "agent_run_id": run_id,
            "human_validated_legal_risk_level": "high",
            "human_consent_required": True,
            "human_judicial_notification_required": True,
            "human_chain_of_custody_required": True,
            "reviewed_by": "supervisor_legal",
        },
    )
    assert audit_response.status_code == 200
    audit_payload = audit_response.json()
    assert audit_payload["care_task_id"] == task_id
    assert audit_payload["agent_run_id"] == run_id
    assert audit_payload["classification"] in {"match", "under_legal_risk", "over_legal_risk"}

    list_response = client.get(f"/api/v1/care-tasks/{task_id}/medicolegal/audit")
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 1
    assert items[0]["audit_id"] == audit_payload["audit_id"]

    summary_response = client.get(f"/api/v1/care-tasks/{task_id}/medicolegal/audit/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["total_audits"] == 1
    assert summary["matches"] + summary["under_legal_risk"] + summary["over_legal_risk"] == 1


def test_create_medicolegal_audit_returns_404_when_run_not_found(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso sin run medico-legal",
            "description": "Prueba run inexistente",
            "clinical_priority": "medium",
            "specialty": "general",
            "sla_target_minutes": 90,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/medicolegal/audit",
        json={
            "agent_run_id": 999999,
            "human_validated_legal_risk_level": "medium",
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Ejecucion de agente no encontrada."


def test_run_sepsis_protocol_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso sospecha sepsis urgencias",
            "description": "Paciente con hipotension y taquipnea",
            "clinical_priority": "high",
            "specialty": "emergency",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/sepsis/recommendation",
        json={
            "suspected_infection": True,
            "respiratory_rate_rpm": 26,
            "systolic_bp": 92,
            "altered_mental_status": True,
            "lactate_mmol_l": 4.2,
            "map_mmhg": 60,
            "blood_cultures_collected": False,
            "antibiotics_started": False,
            "fluid_bolus_ml_per_kg": 10,
            "vasopressor_started": True,
            "time_since_detection_minutes": 80,
            "probable_focus": "pulmonar",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["care_task_id"] == task_id
    assert payload["workflow_name"] == "sepsis_protocol_support_v1"
    assert payload["agent_run_id"] > 0
    assert payload["recommendation"]["qsofa_score"] >= 2
    assert payload["recommendation"]["high_sepsis_risk"] is True
    assert payload["recommendation"]["septic_shock_suspected"] is True

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "sepsis_protocol_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "sepsis_operational_assessment"


def test_run_sepsis_protocol_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/sepsis/recommendation",
        json={
            "suspected_infection": True,
            "respiratory_rate_rpm": 24,
            "systolic_bp": 98,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_scasest_protocol_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso dolor toracico sospecha SCASEST",
            "description": "Paciente con cambios ECG y troponina positiva",
            "clinical_priority": "critical",
            "specialty": "cardiology",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/scasest/recommendation",
        json={
            "chest_pain_typical": True,
            "dyspnea": True,
            "ecg_st_depression": True,
            "troponin_positive": True,
            "hemodynamic_instability": True,
            "refractory_angina": True,
            "grace_score": 160,
            "oxygen_saturation_percent": 88,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["care_task_id"] == task_id
    assert payload["workflow_name"] == "scasest_protocol_support_v1"
    assert payload["agent_run_id"] > 0
    assert payload["recommendation"]["scasest_suspected"] is True
    assert payload["recommendation"]["high_risk_scasest"] is True

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "scasest_protocol_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "scasest_operational_assessment"


def test_run_scasest_protocol_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/scasest/recommendation",
        json={
            "chest_pain_typical": True,
            "ecg_st_depression": True,
            "troponin_positive": True,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_create_scasest_audit_and_summary(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso auditoria SCASEST",
            "description": "Validar calidad del soporte SCASEST",
            "clinical_priority": "critical",
            "specialty": "cardiology",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    run_response = client.post(
        f"/api/v1/care-tasks/{task_id}/scasest/recommendation",
        json={
            "chest_pain_typical": True,
            "ecg_st_depression": True,
            "troponin_positive": True,
            "hemodynamic_instability": True,
            "grace_score": 155,
        },
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["agent_run_id"]

    audit_response = client.post(
        f"/api/v1/care-tasks/{task_id}/scasest/audit",
        json={
            "agent_run_id": run_id,
            "human_validated_high_risk_scasest": True,
            "human_escalation_required": True,
            "human_immediate_antiischemic_strategy": True,
            "reviewed_by": "cardiologia_guardia",
        },
    )
    assert audit_response.status_code == 200
    payload = audit_response.json()
    assert payload["care_task_id"] == task_id
    assert payload["agent_run_id"] == run_id
    assert payload["classification"] in {"match", "under_scasest_risk", "over_scasest_risk"}

    list_response = client.get(f"/api/v1/care-tasks/{task_id}/scasest/audit")
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 1
    assert items[0]["audit_id"] == payload["audit_id"]

    summary_response = client.get(f"/api/v1/care-tasks/{task_id}/scasest/audit/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["total_audits"] == 1
    assert summary["matches"] + summary["under_scasest_risk"] + summary["over_scasest_risk"] == 1
    assert "escalation_required_match_rate_percent" in summary
    assert "immediate_antiischemic_strategy_match_rate_percent" in summary


def test_create_scasest_audit_returns_404_when_run_not_found(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso sin run SCASEST",
            "description": "Prueba run inexistente",
            "clinical_priority": "medium",
            "specialty": "general",
            "sla_target_minutes": 90,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/scasest/audit",
        json={
            "agent_run_id": 999999,
            "human_validated_high_risk_scasest": True,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Ejecucion de agente no encontrada."


def test_run_cardio_risk_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso riesgo cardiovascular",
            "description": "Paciente para estratificacion operativa",
            "clinical_priority": "high",
            "specialty": "cardiology",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/cardio-risk/recommendation",
        json={
            "age_years": 67,
            "sex": "male",
            "smoker": True,
            "systolic_bp": 158,
            "non_hdl_mg_dl": 210,
            "apob_mg_dl": 132,
            "triglycerides_mg_dl": 210,
            "diabetes": True,
            "chronic_kidney_disease": False,
            "established_atherosclerotic_cvd": False,
            "family_history_premature_cvd": True,
            "chronic_inflammatory_state": False,
            "on_lipid_lowering_therapy": False,
            "statin_intolerance": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["care_task_id"] == task_id
    assert payload["workflow_name"] == "cardio_risk_support_v1"
    assert payload["agent_run_id"] > 0
    assert payload["recommendation"]["risk_level"] in {"low", "moderate", "high", "very_high"}
    assert payload["recommendation"]["human_validation_required"] is True

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "cardio_risk_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "cardio_risk_operational_assessment"


def test_run_cardio_risk_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/cardio-risk/recommendation",
        json={
            "age_years": 60,
            "sex": "female",
            "smoker": False,
            "systolic_bp": 132,
            "non_hdl_mg_dl": 145,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_create_cardio_risk_audit_and_summary(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso auditoria cardiovascular",
            "description": "Validar calidad del soporte de riesgo cardio",
            "clinical_priority": "high",
            "specialty": "cardiology",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    run_response = client.post(
        f"/api/v1/care-tasks/{task_id}/cardio-risk/recommendation",
        json={
            "age_years": 72,
            "sex": "male",
            "smoker": True,
            "systolic_bp": 165,
            "non_hdl_mg_dl": 230,
            "apob_mg_dl": 145,
            "diabetes": True,
            "chronic_kidney_disease": True,
            "family_history_premature_cvd": True,
        },
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["agent_run_id"]

    audit_response = client.post(
        f"/api/v1/care-tasks/{task_id}/cardio-risk/audit",
        json={
            "agent_run_id": run_id,
            "human_validated_risk_level": "very_high",
            "human_non_hdl_target_required": True,
            "human_pharmacologic_strategy_suggested": True,
            "human_intensive_lifestyle_required": True,
            "reviewed_by": "cardio_guardia",
        },
    )
    assert audit_response.status_code == 200
    payload = audit_response.json()
    assert payload["care_task_id"] == task_id
    assert payload["agent_run_id"] == run_id
    assert payload["classification"] in {"match", "under_cardio_risk", "over_cardio_risk"}

    list_response = client.get(f"/api/v1/care-tasks/{task_id}/cardio-risk/audit")
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 1
    assert items[0]["audit_id"] == payload["audit_id"]

    summary_response = client.get(f"/api/v1/care-tasks/{task_id}/cardio-risk/audit/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["total_audits"] == 1
    assert summary["matches"] + summary["under_cardio_risk"] + summary["over_cardio_risk"] == 1
    assert "non_hdl_target_required_match_rate_percent" in summary
    assert "pharmacologic_strategy_match_rate_percent" in summary
    assert "intensive_lifestyle_match_rate_percent" in summary


def test_create_cardio_risk_audit_returns_404_when_run_not_found(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso cardio sin run",
            "description": "Prueba run inexistente",
            "clinical_priority": "medium",
            "specialty": "general",
            "sla_target_minutes": 90,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/cardio-risk/audit",
        json={
            "agent_run_id": 999999,
            "human_validated_risk_level": "high",
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Ejecucion de agente no encontrada."


def test_run_resuscitation_support_returns_recommendation_and_trace(client, db_session):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso de paro cardiorrespiratorio en box vital",
            "description": "Escenario para soporte operativo de reanimacion",
            "clinical_priority": "critical",
            "specialty": "emergency",
            "sla_target_minutes": 5,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/resuscitation/recommendation",
        json={
            "context_type": "cardiac_arrest",
            "rhythm": "vf",
            "has_pulse": False,
            "compression_depth_cm": 5.5,
            "compression_rate_per_min": 110,
            "interruption_seconds": 8,
            "etco2_mm_hg": 18,
            "door_ecg_minutes": 12,
            "symptom_onset_minutes": 45,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["care_task_id"] == task_id
    assert payload["workflow_name"] == "resuscitation_protocol_support_v1"
    assert payload["agent_run_id"] > 0
    assert payload["recommendation"]["severity_level"] == "critical"
    assert payload["recommendation"]["shock_recommended"] is True
    assert payload["recommendation"]["human_validation_required"] is True

    from app.models.agent_run import AgentRun, AgentStep

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "resuscitation_protocol_support_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "resuscitation_operational_assessment"


def test_run_resuscitation_support_recommends_synchronized_cardioversion(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "FA inestable en area de criticos",
            "description": "Validar energia y sedoanalgesia de cardioversion sincronizada",
            "clinical_priority": "critical",
            "specialty": "emergency",
            "sla_target_minutes": 10,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/resuscitation/recommendation",
        json={
            "context_type": "tachyarrhythmia_with_pulse",
            "rhythm": "af",
            "has_pulse": True,
            "hypotension": True,
            "shock_signs": True,
            "systolic_bp_mm_hg": 82,
            "diastolic_bp_mm_hg": 60,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]

    assert recommendation["shock_recommended"] is True
    assert any(
        "120-200 j bifasico" in item.lower() for item in recommendation["electrical_therapy_plan"]
    )
    assert any(
        "marcas de onda r visibles" in item.lower()
        for item in recommendation["pre_shock_safety_checklist"]
    )
    assert any(
        "etomidato 0.1-0.15 mg/kg" in item.lower() for item in recommendation["sedoanalgesia_plan"]
    )
    assert any("presion de pulso estrecha" in item.lower() for item in recommendation["alerts"])


def test_run_resuscitation_support_returns_404_when_task_not_found(client):
    response = client.post(
        "/api/v1/care-tasks/999999/resuscitation/recommendation",
        json={
            "context_type": "post_rosc",
            "rhythm": "brady_advanced",
            "has_pulse": True,
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_run_resuscitation_support_obstetric_critical_window_actions(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Paro obstetrico en sala de partos",
            "description": "Validar acciones 4-5 min y compresion aortocava",
            "clinical_priority": "critical",
            "specialty": "obstetricia",
            "sla_target_minutes": 5,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/resuscitation/recommendation",
        json={
            "context_type": "cardiac_arrest",
            "rhythm": "pea",
            "has_pulse": False,
            "pregnant": True,
            "gestational_weeks": 32,
            "uterine_fundus_at_or_above_umbilicus": True,
            "minutes_since_arrest": 5,
            "access_above_diaphragm_secured": False,
            "fetal_monitor_connected": True,
            "magnesium_infusion_active": True,
            "magnesium_toxicity_suspected": True,
        },
    )
    assert response.status_code == 200
    recommendation = response.json()["recommendation"]
    special_actions = recommendation["special_situation_actions"]
    alerts = recommendation["alerts"]
    reversible = recommendation["reversible_causes_checklist"]

    assert any("histerotomia resucitativa" in action for action in special_actions)
    assert any("minuto 5" in action for action in special_actions)
    assert any("toxicidad por magnesio" in action for action in special_actions)
    assert any("ventana critica 4-5 min" in alert.lower() for alert in alerts)
    assert any(
        "acceso vascular por encima del diafragma pendiente" in alert.lower() for alert in alerts
    )
    assert any("hemorragia obstetrica masiva" in item.lower() for item in reversible)


def test_create_resuscitation_audit_and_summary(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso auditoria reanimacion",
            "description": "Validar calidad del soporte de reanimacion",
            "clinical_priority": "critical",
            "specialty": "emergency",
            "sla_target_minutes": 5,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    run_response = client.post(
        f"/api/v1/care-tasks/{task_id}/resuscitation/recommendation",
        json={
            "context_type": "cardiac_arrest",
            "rhythm": "asystole",
            "has_pulse": False,
            "compression_depth_cm": 4.0,
            "compression_rate_per_min": 90,
            "interruption_seconds": 12,
            "etco2_mm_hg": 8,
        },
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["agent_run_id"]

    audit_response = client.post(
        f"/api/v1/care-tasks/{task_id}/resuscitation/audit",
        json={
            "agent_run_id": run_id,
            "human_validated_severity_level": "critical",
            "human_shock_recommended": False,
            "human_reversible_causes_completed": True,
            "human_airway_plan_adequate": True,
            "reviewed_by": "supervisor_criticos",
        },
    )
    assert audit_response.status_code == 200
    payload = audit_response.json()
    assert payload["care_task_id"] == task_id
    assert payload["agent_run_id"] == run_id
    assert payload["classification"] in {
        "match",
        "under_resuscitation_risk",
        "over_resuscitation_risk",
    }

    list_response = client.get(f"/api/v1/care-tasks/{task_id}/resuscitation/audit")
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 1
    assert items[0]["audit_id"] == payload["audit_id"]

    summary_response = client.get(f"/api/v1/care-tasks/{task_id}/resuscitation/audit/summary")
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["total_audits"] == 1
    assert (
        summary["matches"]
        + summary["under_resuscitation_risk"]
        + summary["over_resuscitation_risk"]
        == 1
    )
    assert "shock_recommended_match_rate_percent" in summary
    assert "reversible_causes_match_rate_percent" in summary
    assert "airway_plan_match_rate_percent" in summary


def test_create_resuscitation_audit_returns_404_when_run_not_found(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso reanimacion sin run",
            "description": "Prueba run inexistente",
            "clinical_priority": "high",
            "specialty": "general",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/resuscitation/audit",
        json={
            "agent_run_id": 999999,
            "human_validated_severity_level": "high",
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Ejecucion de agente no encontrada."


def test_quality_scorecard_returns_zero_without_audits(client):
    response = client.get("/api/v1/care-tasks/quality/scorecard")
    assert response.status_code == 200
    payload = response.json()

    assert payload["total_audits"] == 0
    assert payload["matches"] == 0
    assert payload["under_events"] == 0
    assert payload["over_events"] == 0
    assert payload["under_rate_percent"] == 0.0
    assert payload["over_rate_percent"] == 0.0
    assert payload["match_rate_percent"] == 0.0
    assert payload["quality_status"] == "sin_datos"
    assert payload["domains"]["triage"]["total_audits"] == 0
    assert payload["domains"]["screening"]["total_audits"] == 0
    assert payload["domains"]["medicolegal"]["total_audits"] == 0
    assert payload["domains"]["scasest"]["total_audits"] == 0
    assert payload["domains"]["cardio_risk"]["total_audits"] == 0
    assert payload["domains"]["resuscitation"]["total_audits"] == 0


def test_quality_scorecard_aggregates_all_audit_domains(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso scorecard global",
            "description": "Consolidar auditorias de todos los dominios",
            "clinical_priority": "high",
            "specialty": "emergency",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    triage_run = client.post(f"/api/v1/care-tasks/{task_id}/triage")
    assert triage_run.status_code == 200
    triage_run_id = triage_run.json()["agent_run_id"]
    triage_audit = client.post(
        f"/api/v1/care-tasks/{task_id}/triage/audit",
        json={
            "agent_run_id": triage_run_id,
            "human_validated_level": 2,
            "reviewed_by": "supervisor_triaje",
        },
    )
    assert triage_audit.status_code == 200

    screening_run = client.post(
        f"/api/v1/care-tasks/{task_id}/screening/recommendation",
        json={
            "age_years": 79,
            "systolic_bp": 108,
            "can_walk_independently": False,
            "heart_rate_bpm": 112,
            "oxygen_saturation_percent": 92,
            "chief_complaints": ["fiebre sin foco"],
            "known_conditions": ["plaquetopenia"],
            "immunosuppressed": True,
            "persistent_positive_days": 14,
            "persistent_symptoms": True,
            "imaging_compatible_with_persistent_infection": True,
            "stable_after_acute_phase": True,
            "infection_context": "osteomielitis",
        },
    )
    assert screening_run.status_code == 200
    screening_run_id = screening_run.json()["agent_run_id"]
    screening_audit = client.post(
        f"/api/v1/care-tasks/{task_id}/screening/audit",
        json={
            "agent_run_id": screening_run_id,
            "human_validated_risk_level": "high",
            "human_hiv_screening_suggested": True,
            "human_sepsis_route_suggested": True,
            "human_persistent_covid_suspected": True,
            "human_long_acting_candidate": True,
            "reviewed_by": "supervisor_screening",
        },
    )
    assert screening_audit.status_code == 200

    medicolegal_run = client.post(
        f"/api/v1/care-tasks/{task_id}/medicolegal/recommendation",
        json={
            "triage_wait_minutes": 9,
            "first_medical_contact_minutes": 35,
            "patient_age_years": 47,
            "patient_has_decision_capacity": True,
            "invasive_procedure_planned": True,
            "informed_consent_documented": False,
            "intoxication_forensic_context": True,
            "chain_of_custody_started": False,
        },
    )
    assert medicolegal_run.status_code == 200
    medicolegal_run_id = medicolegal_run.json()["agent_run_id"]
    medicolegal_audit = client.post(
        f"/api/v1/care-tasks/{task_id}/medicolegal/audit",
        json={
            "agent_run_id": medicolegal_run_id,
            "human_validated_legal_risk_level": "high",
            "human_consent_required": True,
            "human_judicial_notification_required": True,
            "human_chain_of_custody_required": True,
            "reviewed_by": "supervisor_legal",
        },
    )
    assert medicolegal_audit.status_code == 200

    scasest_run = client.post(
        f"/api/v1/care-tasks/{task_id}/scasest/recommendation",
        json={
            "chest_pain_typical": True,
            "ecg_st_depression": True,
            "troponin_positive": True,
            "hemodynamic_instability": True,
            "grace_score": 148,
        },
    )
    assert scasest_run.status_code == 200
    scasest_run_id = scasest_run.json()["agent_run_id"]
    scasest_audit = client.post(
        f"/api/v1/care-tasks/{task_id}/scasest/audit",
        json={
            "agent_run_id": scasest_run_id,
            "human_validated_high_risk_scasest": True,
            "human_escalation_required": True,
            "human_immediate_antiischemic_strategy": True,
            "reviewed_by": "supervisor_cardiologia",
        },
    )
    assert scasest_audit.status_code == 200

    cardio_run = client.post(
        f"/api/v1/care-tasks/{task_id}/cardio-risk/recommendation",
        json={
            "age_years": 70,
            "sex": "male",
            "smoker": True,
            "systolic_bp": 162,
            "non_hdl_mg_dl": 225,
            "apob_mg_dl": 135,
            "diabetes": True,
            "chronic_kidney_disease": True,
        },
    )
    assert cardio_run.status_code == 200
    cardio_run_id = cardio_run.json()["agent_run_id"]
    cardio_audit = client.post(
        f"/api/v1/care-tasks/{task_id}/cardio-risk/audit",
        json={
            "agent_run_id": cardio_run_id,
            "human_validated_risk_level": "very_high",
            "human_non_hdl_target_required": True,
            "human_pharmacologic_strategy_suggested": True,
            "human_intensive_lifestyle_required": True,
            "reviewed_by": "supervisor_prevencion",
        },
    )
    assert cardio_audit.status_code == 200

    resuscitation_run = client.post(
        f"/api/v1/care-tasks/{task_id}/resuscitation/recommendation",
        json={
            "context_type": "cardiac_arrest",
            "rhythm": "vf",
            "has_pulse": False,
            "compression_depth_cm": 5.3,
            "compression_rate_per_min": 112,
            "interruption_seconds": 9,
            "etco2_mm_hg": 16,
        },
    )
    assert resuscitation_run.status_code == 200
    resuscitation_run_id = resuscitation_run.json()["agent_run_id"]
    resuscitation_audit = client.post(
        f"/api/v1/care-tasks/{task_id}/resuscitation/audit",
        json={
            "agent_run_id": resuscitation_run_id,
            "human_validated_severity_level": "critical",
            "human_shock_recommended": True,
            "human_reversible_causes_completed": True,
            "human_airway_plan_adequate": True,
            "reviewed_by": "supervisor_reanimacion",
        },
    )
    assert resuscitation_audit.status_code == 200

    scorecard_response = client.get("/api/v1/care-tasks/quality/scorecard")
    assert scorecard_response.status_code == 200
    scorecard = scorecard_response.json()

    assert scorecard["domains"]["triage"]["total_audits"] == 1
    assert scorecard["domains"]["screening"]["total_audits"] == 1
    assert scorecard["domains"]["medicolegal"]["total_audits"] == 1
    assert scorecard["domains"]["scasest"]["total_audits"] == 1
    assert scorecard["domains"]["cardio_risk"]["total_audits"] == 1
    assert scorecard["domains"]["resuscitation"]["total_audits"] == 1
    assert scorecard["total_audits"] == 6
    assert scorecard["matches"] + scorecard["under_events"] + scorecard["over_events"] == 6
    assert scorecard["quality_status"] in {"estable", "atencion", "degradado"}


def test_create_care_task_chat_message_persists_message_and_trace(client, db_session):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "chat_profesional_1",
            "password": "StrongPass123",
            "specialty": "cardiology",
        },
    )
    assert register_response.status_code == 200
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "chat_profesional_1", "password": "StrongPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso para chat clinico",
            "description": "Se requiere soporte operativo interactivo",
            "clinical_priority": "high",
            "specialty": "emergency",
            "patient_reference": "PAC-001",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    chat_response = client.post(
        f"/api/v1/care-tasks/{task_id}/chat/messages",
        json={
            "query": "Sospecha de sepsis con lactato 4 mmol/l y TAS 85 mmHg. "
            "Necesito ruta operativa inicial.",
            "session_id": "guardia-manana",
            "clinician_id": "medico_guardia_1",
            "max_history_messages": 10,
            "include_protocol_catalog": True,
            "persist_extracted_facts": True,
        },
        headers=auth_headers,
    )
    assert chat_response.status_code == 200
    payload = chat_response.json()
    assert payload["care_task_id"] == task_id
    assert payload["workflow_name"] == "care_task_clinical_chat_v1"
    assert payload["agent_run_id"] > 0
    assert payload["message_id"] > 0
    assert payload["session_id"] == "guardia-manana"
    assert payload["effective_specialty"] == "cardiology"
    assert payload["matched_domains"]
    assert "/api/v1/care-tasks/" in payload["matched_endpoints"][0]
    assert isinstance(payload["knowledge_sources"], list)
    assert payload["non_diagnostic_warning"].startswith("Soporte operativo no diagnostico")

    from app.models.agent_run import AgentRun, AgentStep
    from app.models.care_task_chat_message import CareTaskChatMessage

    message = (
        db_session.query(CareTaskChatMessage)
        .filter(CareTaskChatMessage.id == payload["message_id"])
        .first()
    )
    assert message is not None
    assert message.care_task_id == task_id
    assert message.session_id == "guardia-manana"
    assert message.clinician_id == "medico_guardia_1"
    assert message.effective_specialty == "cardiology"

    run = db_session.query(AgentRun).filter(AgentRun.id == payload["agent_run_id"]).first()
    assert run is not None
    assert run.workflow_name == "care_task_clinical_chat_v1"
    step = db_session.query(AgentStep).filter(AgentStep.run_id == run.id).first()
    assert step is not None
    assert step.step_name == "clinical_chat_assessment"


def test_list_care_task_chat_messages_and_memory_summary(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "chat_profesional_2",
            "password": "StrongPass123",
            "specialty": "cardiology",
        },
    )
    assert register_response.status_code == 200
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "chat_profesional_2", "password": "StrongPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso con memoria de chat",
            "description": "Seguimiento de dudas operativas",
            "clinical_priority": "medium",
            "specialty": "cardiology",
            "patient_reference": "PAC-002",
            "sla_target_minutes": 60,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    first_chat = client.post(
        f"/api/v1/care-tasks/{task_id}/chat/messages",
        json={
            "query": "Paciente con dolor toracico y troponina elevada, valorar ruta SCASEST.",
            "session_id": "session-main",
            "clinician_id": "medico_a",
        },
        headers=auth_headers,
    )
    second_chat = client.post(
        f"/api/v1/care-tasks/{task_id}/chat/messages",
        json={
            "query": "Mantiene dolor y TAS < 90 mmHg, revisar escalado y alertas criticas.",
            "session_id": "session-main",
            "clinician_id": "medico_a",
        },
        headers=auth_headers,
    )
    assert first_chat.status_code == 200
    assert second_chat.status_code == 200

    history_response = client.get(
        f"/api/v1/care-tasks/{task_id}/chat/messages?session_id=session-main&limit=10",
        headers=auth_headers,
    )
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) == 2
    assert history[0]["session_id"] == "session-main"
    assert history[1]["session_id"] == "session-main"
    assert history[0]["created_at"] >= history[1]["created_at"]

    memory_response = client.get(
        f"/api/v1/care-tasks/{task_id}/chat/memory?session_id=session-main",
        headers=auth_headers,
    )
    assert memory_response.status_code == 200
    memory = memory_response.json()
    assert memory["care_task_id"] == task_id
    assert memory["session_id"] == "session-main"
    assert memory["interactions_count"] == 2
    assert len(memory["top_domains"]) >= 1
    assert memory["patient_reference"] == "PAC-002"
    assert memory["patient_interactions_count"] >= 2
    assert "scasest" in memory["top_domains"] or "critical_ops" in memory["top_domains"]


def test_chat_continuity_filters_control_facts_from_memory(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "chat_profesional_5",
            "password": "StrongPass123",
            "specialty": "emergency",
        },
    )
    assert register_response.status_code == 200
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "chat_profesional_5", "password": "StrongPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    auth_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso continuidad de chat",
            "clinical_priority": "high",
            "specialty": "emergency",
            "patient_reference": "PAC-CTX-001",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    first_chat = client.post(
        f"/api/v1/care-tasks/{task_id}/chat/messages",
        json={
            "query": "Paciente con sepsis y lactato 4 mmol/l.",
            "session_id": "session-continuidad",
            "conversation_mode": "general",
            "tool_mode": "chat",
        },
        headers=auth_headers,
    )
    assert first_chat.status_code == 200

    second_chat = client.post(
        f"/api/v1/care-tasks/{task_id}/chat/messages",
        json={
            "query": "Ahora prioriza acciones de la primera hora con TAS 85 mmHg.",
            "session_id": "session-continuidad",
            "conversation_mode": "clinical",
            "tool_mode": "treatment",
        },
        headers=auth_headers,
    )
    assert second_chat.status_code == 200
    payload = second_chat.json()

    assert all(
        not fact.startswith("modo_respuesta:")
        for fact in payload["memory_facts_used"]
    )
    assert all(
        not fact.startswith("herramienta:")
        for fact in payload["memory_facts_used"]
    )
    assert payload["response_mode"] == "clinical"


def test_chat_follow_up_query_reuses_previous_context_for_domain_matching(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "chat_profesional_6",
            "password": "StrongPass123",
            "specialty": "emergency",
        },
    )
    assert register_response.status_code == 200
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "chat_profesional_6", "password": "StrongPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    auth_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso follow up contextual",
            "clinical_priority": "high",
            "specialty": "emergency",
            "patient_reference": "PAC-CTX-002",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    first_chat = client.post(
        f"/api/v1/care-tasks/{task_id}/chat/messages",
        json={
            "query": "Paciente con sepsis, lactato 4.5 y TAS 85.",
            "session_id": "session-followup",
            "conversation_mode": "clinical",
            "tool_mode": "chat",
        },
        headers=auth_headers,
    )
    assert first_chat.status_code == 200

    follow_up_chat = client.post(
        f"/api/v1/care-tasks/{task_id}/chat/messages",
        json={
            "query": "y ahora que hago?",
            "session_id": "session-followup",
            "conversation_mode": "auto",
            "tool_mode": "chat",
        },
        headers=auth_headers,
    )
    assert follow_up_chat.status_code == 200
    payload = follow_up_chat.json()

    assert "sepsis" in payload["matched_domains"]
    assert any("query_expanded=1" in item for item in payload["interpretability_trace"])


def test_create_care_task_chat_message_returns_404_when_task_not_found(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "chat_profesional_3",
            "password": "StrongPass123",
            "specialty": "emergency",
        },
    )
    assert register_response.status_code == 200
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "chat_profesional_3", "password": "StrongPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/care-tasks/999999/chat/messages",
        json={"query": "Necesito validar ruta operativa de sepsis."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "CareTask no encontrado"


def test_chat_endpoints_require_authentication(client):
    create_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso privado chat",
            "clinical_priority": "high",
            "specialty": "emergency",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    create_chat = client.post(
        f"/api/v1/care-tasks/{task_id}/chat/messages",
        json={"query": "Necesito ruta de soporte operativo."},
    )
    list_chat = client.get(f"/api/v1/care-tasks/{task_id}/chat/messages")
    memory_chat = client.get(f"/api/v1/care-tasks/{task_id}/chat/memory")

    assert create_chat.status_code == 401
    assert list_chat.status_code == 401
    assert memory_chat.status_code == 401


def test_chat_memory_aggregates_patient_history_across_tasks(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "chat_profesional_4",
            "password": "StrongPass123",
            "specialty": "emergency",
        },
    )
    assert register_response.status_code == 200
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "chat_profesional_4", "password": "StrongPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    auth_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    first_task = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Visita previa",
            "clinical_priority": "medium",
            "specialty": "emergency",
            "patient_reference": "PAC-003",
            "sla_target_minutes": 60,
            "human_review_required": True,
            "completed": False,
        },
    )
    second_task = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Visita actual",
            "clinical_priority": "high",
            "specialty": "emergency",
            "patient_reference": "PAC-003",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert first_task.status_code == 201
    assert second_task.status_code == 201

    first_id = first_task.json()["id"]
    second_id = second_task.json()["id"]

    first_chat = client.post(
        f"/api/v1/care-tasks/{first_id}/chat/messages",
        json={"query": "Consulta previa por dolor toracico."},
        headers=auth_headers,
    )
    second_chat = client.post(
        f"/api/v1/care-tasks/{second_id}/chat/messages",
        json={"query": "Reconsulta con empeoramiento y disnea."},
        headers=auth_headers,
    )
    assert first_chat.status_code == 200
    assert second_chat.status_code == 200

    memory_response = client.get(
        f"/api/v1/care-tasks/{second_id}/chat/memory",
        headers=auth_headers,
    )
    assert memory_response.status_code == 200
    memory = memory_response.json()
    assert memory["patient_reference"] == "PAC-003"
    assert memory["patient_interactions_count"] >= 2


def test_chat_message_supports_general_conversation_mode(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "chat_profesional_5",
            "password": "StrongPass123",
            "specialty": "emergency",
        },
    )
    assert register_response.status_code == 200
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "chat_profesional_5", "password": "StrongPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    auth_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    create_task = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Conversacion general en guardia",
            "clinical_priority": "medium",
            "specialty": "emergency",
            "sla_target_minutes": 60,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task.status_code == 201
    task_id = create_task.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/chat/messages",
        json={
            "query": "Ayudame a estructurar un plan breve para organizar turnos de guardia.",
            "conversation_mode": "general",
            "tool_mode": "chat",
            "session_id": "session-general",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["response_mode"] == "general"
    assert payload["tool_mode"] == "chat"
    assert any(item == "conversation_mode=general" for item in payload["interpretability_trace"])
    assert any(item == "llm_enabled=false" for item in payload["interpretability_trace"])


def test_chat_message_forces_clinical_mode_with_medication_tool(client):
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "chat_profesional_6",
            "password": "StrongPass123",
            "specialty": "general",
        },
    )
    assert register_response.status_code == 200
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "chat_profesional_6", "password": "StrongPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    auth_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    create_task = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Consulta de medicacion",
            "clinical_priority": "high",
            "specialty": "emergency",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task.status_code == 201
    task_id = create_task.json()["id"]

    response = client.post(
        f"/api/v1/care-tasks/{task_id}/chat/messages",
        json={
            "query": "Tengo dudas sobre ajuste de dosis en paciente fragil.",
            "conversation_mode": "auto",
            "tool_mode": "medication",
            "session_id": "session-medication",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["response_mode"] == "clinical"
    assert payload["tool_mode"] == "medication"
    assert "herramienta:medication" in payload["extracted_facts"]
