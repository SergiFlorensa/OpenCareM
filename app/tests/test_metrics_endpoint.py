def test_metrics_endpoint_is_exposed(client):
    """Expose Prometheus metrics endpoint for scraping by observability tools."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")


def test_metrics_endpoint_contains_http_metrics(client):
    """Return HTTP metric series so latency and request volume can be monitored."""
    client.get("/health")
    response = client.get("/metrics")
    body = response.text
    assert "# HELP" in body
    assert "http_requests_total" in body or "http_request_duration_seconds" in body


def test_metrics_endpoint_contains_agent_ops_metrics(client):
    client.post(
        "/api/v1/agents/run",
        json={
            "workflow_name": "task_triage_v1",
            "title": "Investigate vector embeddings",
            "description": "Evaluate prompt strategy and model behavior",
        },
    )
    response = client.get("/metrics")
    body = response.text
    assert "agent_runs_total" in body
    assert "agent_runs_completed_total" in body
    assert "agent_runs_failed_total" in body
    assert "agent_steps_fallback_total" in body
    assert "agent_fallback_rate_percent" in body


def test_metrics_endpoint_contains_triage_audit_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas auditoria",
            "description": "Caso para verificar series Prometheus",
            "clinical_priority": "medium",
            "specialty": "general",
            "sla_target_minutes": 90,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    run_response = client.post(f"/api/v1/care-tasks/{task_id}/triage")
    assert run_response.status_code == 200
    run_id = run_response.json()["agent_run_id"]

    audit_response = client.post(
        f"/api/v1/care-tasks/{task_id}/triage/audit",
        json={
            "agent_run_id": run_id,
            "human_validated_level": 2,
            "reviewed_by": "supervisor",
        },
    )
    assert audit_response.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "triage_audit_total" in body
    assert "triage_audit_match_total" in body
    assert "triage_audit_under_total" in body
    assert "triage_audit_over_total" in body
    assert "triage_audit_under_rate_percent" in body
    assert "triage_audit_over_rate_percent" in body


def test_metrics_endpoint_contains_respiratory_protocol_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso respiratorio metricas",
            "description": "Verificar series respiratorias",
            "clinical_priority": "medium",
            "specialty": "general",
            "sla_target_minutes": 90,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_protocol = client.post(
        f"/api/v1/care-tasks/{task_id}/respiratory-protocol/recommendation",
        json={
            "age_years": 72,
            "immunosuppressed": False,
            "comorbidities": ["epoc"],
            "vaccination_updated_last_12_months": False,
            "symptom_onset_hours": 24,
            "hours_since_er_arrival": 1,
            "current_systolic_bp": 130,
            "baseline_systolic_bp": 150,
            "needs_oxygen": True,
            "pathogen_suspected": "gripe",
            "antigen_result": "positivo",
            "oral_antiviral_contraindicated": False,
        },
    )
    assert response_protocol.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "respiratory_protocol_runs_total" in body
    assert "respiratory_protocol_runs_completed_total" in body


def test_metrics_endpoint_contains_pediatric_humanization_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso humanizacion metricas",
            "description": "Verificar series de humanizacion pediatrica",
            "clinical_priority": "high",
            "specialty": "pediatria",
            "sla_target_minutes": 45,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_humanization = client.post(
        f"/api/v1/care-tasks/{task_id}/humanization/recommendation",
        json={
            "patient_age_years": 10,
            "primary_context": "neuro_oncologia",
            "emotional_distress_level": 7,
            "family_understanding_level": 5,
            "family_present": True,
            "sibling_support_needed": False,
            "social_risk_flags": [],
            "needs_spiritual_support": False,
            "multidisciplinary_team": ["oncologia", "anestesia"],
            "has_clinical_trial_option": True,
            "informed_consent_status": "explicado",
            "professional_burnout_risk": "low",
        },
    )
    assert response_humanization.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "pediatric_humanization_runs_total" in body
    assert "pediatric_humanization_runs_completed_total" in body


def test_metrics_endpoint_contains_advanced_screening_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso screening metricas",
            "description": "Verificar series screening",
            "clinical_priority": "high",
            "specialty": "emergency",
            "sla_target_minutes": 45,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_screening = client.post(
        f"/api/v1/care-tasks/{task_id}/screening/recommendation",
        json={
            "age_years": 75,
            "systolic_bp": 110,
            "can_walk_independently": False,
            "heart_rate_bpm": 115,
            "oxygen_saturation_percent": 91,
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
    assert response_screening.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "advanced_screening_runs_total" in body
    assert "advanced_screening_runs_completed_total" in body
    assert "advanced_screening_alerts_generated_total" in body
    assert "advanced_screening_alerts_suppressed_total" in body


def test_metrics_endpoint_contains_screening_audit_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas auditoria screening",
            "description": "Validar series de precision por regla",
            "clinical_priority": "high",
            "specialty": "emergency",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    run_response = client.post(
        f"/api/v1/care-tasks/{task_id}/screening/recommendation",
        json={
            "age_years": 80,
            "systolic_bp": 110,
            "can_walk_independently": False,
            "heart_rate_bpm": 118,
            "oxygen_saturation_percent": 91,
            "chief_complaints": ["neumonia"],
            "known_conditions": ["plaquetopenia"],
            "immunosuppressed": True,
            "persistent_positive_days": 14,
            "persistent_symptoms": True,
            "imaging_compatible_with_persistent_infection": True,
            "stable_after_acute_phase": True,
            "infection_context": "osteomielitis",
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
        },
    )
    assert audit_response.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "screening_audit_total" in body
    assert "screening_audit_match_total" in body
    assert "screening_audit_under_total" in body
    assert "screening_audit_over_total" in body
    assert "screening_audit_under_rate_percent" in body
    assert "screening_audit_over_rate_percent" in body
    assert "screening_rule_hiv_match_rate_percent" in body
    assert "screening_rule_sepsis_match_rate_percent" in body
    assert "screening_rule_persistent_covid_match_rate_percent" in body
    assert "screening_rule_long_acting_match_rate_percent" in body


def test_metrics_endpoint_contains_chest_xray_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas rx torax",
            "description": "Verificar series de soporte radiografico",
            "clinical_priority": "high",
            "specialty": "emergency",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
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
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "chest_xray_support_runs_total" in body
    assert "chest_xray_support_runs_completed_total" in body
    assert "chest_xray_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_pityriasis_differential_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas pitiriasis",
            "description": "Verificar series del diferencial dermatologico",
            "clinical_priority": "medium",
            "specialty": "dermatologia",
            "sla_target_minutes": 90,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/pityriasis-differential/recommendation",
        json={
            "age_years": 19,
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
            "atopic_background": True,
            "sensory_loss_in_lesion": True,
            "deep_erythema_warmth_pain": False,
            "systemic_signs": False,
            "immunosuppressed": False,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "pityriasis_differential_runs_total" in body
    assert "pityriasis_differential_runs_completed_total" in body
    assert "pityriasis_differential_red_flags_total" in body


def test_metrics_endpoint_contains_acne_rosacea_differential_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas acne-rosacea",
            "description": "Verificar series diferencial acne/rosacea",
            "clinical_priority": "medium",
            "specialty": "dermatologia",
            "sla_target_minutes": 90,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/acne-rosacea/recommendation",
        json={
            "age_years": 34,
            "sex": "femenino",
            "lesion_distribution": ["mejillas", "nariz"],
            "comedones_present": False,
            "lesion_pattern": "papulo_pustuloso",
            "flushing_present": True,
            "telangiectasias_present": True,
            "ocular_symptoms_present": True,
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
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "acne_rosacea_differential_runs_total" in body
    assert "acne_rosacea_differential_runs_completed_total" in body
    assert "acne_rosacea_differential_red_flags_total" in body


def test_metrics_endpoint_contains_critical_ops_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas critical ops",
            "description": "Verificar series workflow critico transversal",
            "clinical_priority": "critical",
            "specialty": "urgencias",
            "sla_target_minutes": 15,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/critical-ops/recommendation",
        json={
            "non_traumatic_chest_pain": True,
            "door_to_ecg_minutes": 18,
            "suspected_septic_shock": True,
            "sepsis_antibiotic_minutes": 95,
            "triage_level": "rojo",
            "triage_to_first_assessment_minutes": 8,
            "abrupt_anuria_present": True,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "critical_ops_support_runs_total" in body
    assert "critical_ops_support_runs_completed_total" in body
    assert "critical_ops_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_neurology_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas neurologia",
            "description": "Verificar series workflow neurologico",
            "clinical_priority": "high",
            "specialty": "neurologia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/neurology/recommendation",
        json={
            "sudden_severe_headache": True,
            "cranial_ct_subarachnoid_hyperdensity": True,
            "suspected_stroke": True,
            "symptom_onset_known": False,
            "wake_up_stroke": True,
            "ct_perfusion_performed": True,
            "salvageable_penumbra_present": True,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "neurology_support_runs_total" in body
    assert "neurology_support_runs_completed_total" in body
    assert "neurology_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_gastro_hepato_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas gastro-hepato",
            "description": "Verificar series workflow gastro-hepato",
            "clinical_priority": "critical",
            "specialty": "digestivo",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/gastro-hepato/recommendation",
        json={
            "abdominal_pain": True,
            "jaundice": True,
            "ascites": True,
            "portal_doppler_no_flow_silence": True,
            "portal_doppler_heterogeneous": True,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "gastro_hepato_support_runs_total" in body
    assert "gastro_hepato_support_runs_completed_total" in body
    assert "gastro_hepato_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_rheum_immuno_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas reuma-inmuno",
            "description": "Verificar series workflow reuma-inmuno",
            "clinical_priority": "high",
            "specialty": "reumatologia",
            "sla_target_minutes": 25,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/rheum-immuno/recommendation",
        json={
            "lupus_known": True,
            "new_unexplained_dyspnea": True,
            "prior_aptt_prolonged": True,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "rheum_immuno_support_runs_total" in body
    assert "rheum_immuno_support_runs_completed_total" in body
    assert "rheum_immuno_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_psychiatry_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas psiquiatria",
            "description": "Verificar series workflow psiquiatria",
            "clinical_priority": "high",
            "specialty": "psiquiatria",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/psychiatry/recommendation",
        json={
            "age_years": 16,
            "self_harm_present": True,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "psychiatry_support_runs_total" in body
    assert "psychiatry_support_runs_completed_total" in body
    assert "psychiatry_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_hematology_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas hematologia",
            "description": "Verificar series workflow hematologia",
            "clinical_priority": "critical",
            "specialty": "hematologia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/hematology/recommendation",
        json={
            "mah_anemia_present": True,
            "thrombocytopenia_present": True,
            "organ_damage_present": True,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "hematology_support_runs_total" in body
    assert "hematology_support_runs_completed_total" in body
    assert "hematology_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_endocrinology_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas endocrinologia",
            "description": "Verificar series workflow endocrino-metabolico",
            "clinical_priority": "critical",
            "specialty": "endocrinologia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/endocrinology/recommendation",
        json={
            "suspected_hypoglycemia": True,
            "ketosis_present": False,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "endocrinology_support_runs_total" in body
    assert "endocrinology_support_runs_completed_total" in body
    assert "endocrinology_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_nephrology_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas nefrologia",
            "description": "Verificar series workflow nefrologico",
            "clinical_priority": "critical",
            "specialty": "nefrologia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/nephrology/recommendation",
        json={
            "ph": 7.2,
            "hco3_mmol_l": 16,
            "pco2_mm_hg": 36,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "nephrology_support_runs_total" in body
    assert "nephrology_support_runs_completed_total" in body
    assert "nephrology_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_pneumology_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas neumologia",
            "description": "Verificar series workflow neumologico",
            "clinical_priority": "critical",
            "specialty": "neumologia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/pneumology/recommendation",
        json={
            "ct_peripheral_subpleural_consolidation": True,
            "air_bronchogram_present": True,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "pneumology_support_runs_total" in body
    assert "pneumology_support_runs_completed_total" in body
    assert "pneumology_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_geriatrics_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas geriatria",
            "description": "Verificar series workflow geriatrico",
            "clinical_priority": "high",
            "specialty": "geriatria",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/geriatrics/recommendation",
        json={
            "prolonged_immobility_present": True,
            "nitrogen_balance_negative": True,
            "high_protein_support_plan_active": False,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "geriatrics_support_runs_total" in body
    assert "geriatrics_support_runs_completed_total" in body
    assert "geriatrics_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_oncology_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas oncologia",
            "description": "Verificar series workflow oncologico",
            "clinical_priority": "high",
            "specialty": "oncologia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/oncology/recommendation",
        json={
            "checkpoint_inhibitor_class": "pd-1",
            "immune_hepatotoxicity_suspected": True,
            "transaminases_multiple_uln": 6.0,
            "temperature_c_single": 38.5,
            "absolute_neutrophil_count_mm3": 450,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "oncology_support_runs_total" in body
    assert "oncology_support_runs_completed_total" in body
    assert "oncology_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_anesthesiology_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas anestesia",
            "description": "Verificar series workflow anestesiologico",
            "clinical_priority": "critical",
            "specialty": "anestesia",
            "sla_target_minutes": 10,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/anesthesiology/recommendation",
        json={
            "emergency_airway_needed": True,
            "acute_hematemesis_present": True,
            "iv_route_confirmed": False,
            "bag_mask_manual_ventilation_planned": True,
            "presacral_mass_present": True,
            "severe_perineal_or_pelvic_internal_pain": True,
            "opioid_escalation_not_tolerated": True,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "anesthesiology_support_runs_total" in body
    assert "anesthesiology_support_runs_completed_total" in body
    assert "anesthesiology_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_palliative_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas paliativos",
            "description": "Verificar series workflow paliativo",
            "clinical_priority": "high",
            "specialty": "paliativos",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/palliative/recommendation",
        json={
            "renal_failure_present": True,
            "morphine_active": True,
            "advanced_dementia_present": True,
            "dysphagia_or_oral_intake_refusal": True,
            "enteral_tube_sng_or_peg_planned": True,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "palliative_support_runs_total" in body
    assert "palliative_support_runs_completed_total" in body
    assert "palliative_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_urology_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas urologia",
            "description": "Verificar series workflow urologico",
            "clinical_priority": "critical",
            "specialty": "urologia",
            "sla_target_minutes": 10,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/urology/recommendation",
        json={
            "urinary_tract_gas_on_imaging": True,
            "diabetes_mellitus_poor_control": True,
            "urinary_obstruction_lithiasis_suspected": True,
            "urgent_urinary_diversion_planned": False,
            "genital_trauma_during_erection": True,
            "penile_edema_or_expansive_hematoma_present": True,
            "bladder_catheterization_planned": True,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "urology_support_runs_total" in body
    assert "urology_support_runs_completed_total" in body
    assert "urology_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_ophthalmology_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas oftalmologia",
            "description": "Verificar series workflow oftalmologico",
            "clinical_priority": "high",
            "specialty": "oftalmologia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/ophthalmology/recommendation",
        json={
            "sudden_visual_loss": True,
            "fundus_flame_hemorrhages_present": True,
            "cataract_surgery_planned": True,
            "tamsulosin_or_alpha_blocker_active": True,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "ophthalmology_support_runs_total" in body
    assert "ophthalmology_support_runs_completed_total" in body
    assert "ophthalmology_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_immunology_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas inmunologia",
            "description": "Verificar series workflow inmunologico",
            "clinical_priority": "high",
            "specialty": "inmunologia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/immunology/recommendation",
        json={
            "patient_male": True,
            "age_months": 18,
            "peripheral_cd19_cd20_b_cells_absent": True,
            "igg_low_or_absent": True,
            "iga_low_or_absent": True,
            "igm_low_or_absent": True,
            "lower_respiratory_infection_active": True,
            "alveolar_macrophage_dysfunction_suspected": True,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "immunology_support_runs_total" in body
    assert "immunology_support_runs_completed_total" in body
    assert "immunology_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_genetic_recurrence_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas recurrencia genetica",
            "description": "Verificar series workflow de recurrencia genetica",
            "clinical_priority": "high",
            "specialty": "genetica",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/genetic-recurrence/recommendation",
        json={
            "autosomal_dominant_condition_suspected": True,
            "oi_type_ii_suspected": True,
            "col1a1_or_col1a2_involved": True,
            "recurrent_affected_pregnancies_count": 2,
            "parents_phenotypically_unaffected": True,
            "previous_pregnancy_with_same_condition": True,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "genetic_recurrence_support_runs_total" in body
    assert "genetic_recurrence_support_runs_completed_total" in body
    assert "genetic_recurrence_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_gynecology_obstetrics_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas gineco-obstetricia",
            "description": "Verificar series workflow gineco-obstetrico",
            "clinical_priority": "high",
            "specialty": "ginecologia_obstetricia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/gynecology-obstetrics/recommendation",
        json={
            "reproductive_age_with_abdominal_pain_or_bleeding": True,
            "pregnancy_test_positive": True,
            "severe_abdominal_pain": True,
            "vaginal_spotting_present": True,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "gynecology_obstetrics_support_runs_total" in body
    assert "gynecology_obstetrics_support_runs_completed_total" in body
    assert "gynecology_obstetrics_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_pediatrics_neonatology_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas pediatria-neonatologia",
            "description": "Verificar series workflow pediatrico-neonatal",
            "clinical_priority": "high",
            "specialty": "pediatria_neonatologia",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/pediatrics-neonatology/recommendation",
        json={
            "high_fever_present": True,
            "photophobia_present": True,
            "cough_present": True,
            "koplik_spots_present": True,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "pediatrics_neonatology_support_runs_total" in body
    assert "pediatrics_neonatology_support_runs_completed_total" in body
    assert "pediatrics_neonatology_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_epidemiology_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas epidemiologia",
            "description": "Verificar series workflow epidemiologico",
            "clinical_priority": "high",
            "specialty": "salud_publica",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/epidemiology/recommendation",
        json={
            "requested_individual_risk_estimation": True,
            "new_cases_count": 15,
            "population_at_risk_count": 1000,
            "control_event_risk": 0.05,
            "intervention_event_risk": 0.04,
            "exposed_risk": 0.05,
            "unexposed_risk": 0.1,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "epidemiology_support_runs_total" in body
    assert "epidemiology_support_runs_completed_total" in body
    assert "epidemiology_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_anisakis_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas anisakis",
            "description": "Verificar series workflow anisakis",
            "clinical_priority": "high",
            "specialty": "urgencias",
            "sla_target_minutes": 15,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/anisakis/recommendation",
        json={
            "fish_ingestion_last_hours": 5,
            "raw_or_undercooked_fish_exposure": True,
            "urticaria_present": True,
            "anaphylaxis_present": True,
            "specific_ige_requested": False,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "anisakis_support_runs_total" in body
    assert "anisakis_support_runs_completed_total" in body
    assert "anisakis_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_trauma_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas trauma",
            "description": "Verificar series workflow trauma",
            "clinical_priority": "critical",
            "specialty": "urgencias",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_support = client.post(
        f"/api/v1/care-tasks/{task_id}/trauma/recommendation",
        json={
            "minutes_since_trauma": 30,
            "epidural_hematoma_suspected": True,
            "laryngeal_fracture_palpable": True,
            "hoarseness_present": True,
            "subcutaneous_emphysema_present": True,
            "agitation_present": True,
            "intercostal_retractions_present": True,
            "accessory_muscle_use_present": True,
            "patient_profile": "adulto",
            "open_fracture_wound_cm": 14,
            "high_energy_open_fracture": True,
        },
    )
    assert response_support.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "trauma_support_runs_total" in body
    assert "trauma_support_runs_completed_total" in body
    assert "trauma_support_critical_alerts_total" in body


def test_metrics_endpoint_contains_medicolegal_ops_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas medico-legales",
            "description": "Validar series del workflow medico-legal",
            "clinical_priority": "high",
            "specialty": "emergency",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_medicolegal = client.post(
        f"/api/v1/care-tasks/{task_id}/medicolegal/recommendation",
        json={
            "triage_wait_minutes": 7,
            "first_medical_contact_minutes": 31,
            "patient_age_years": 55,
            "patient_has_decision_capacity": True,
            "invasive_procedure_planned": True,
            "informed_consent_documented": False,
            "intoxication_forensic_context": True,
            "chain_of_custody_started": False,
        },
    )
    assert response_medicolegal.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "medicolegal_ops_runs_total" in body
    assert "medicolegal_ops_runs_completed_total" in body
    assert "medicolegal_ops_critical_alerts_total" in body


def test_metrics_endpoint_contains_medicolegal_audit_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas auditoria medico-legal",
            "description": "Validar series de precision medico-legal",
            "clinical_priority": "high",
            "specialty": "emergency",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    run_response = client.post(
        f"/api/v1/care-tasks/{task_id}/medicolegal/recommendation",
        json={
            "triage_wait_minutes": 8,
            "patient_age_years": 50,
            "invasive_procedure_planned": True,
            "informed_consent_documented": False,
            "intoxication_forensic_context": True,
            "chain_of_custody_started": False,
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
            "human_judicial_notification_required": False,
            "human_chain_of_custody_required": True,
        },
    )
    assert audit_response.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "medicolegal_audit_total" in body
    assert "medicolegal_audit_match_total" in body
    assert "medicolegal_audit_under_total" in body
    assert "medicolegal_audit_over_total" in body
    assert "medicolegal_audit_under_rate_percent" in body
    assert "medicolegal_audit_over_rate_percent" in body
    assert "medicolegal_rule_consent_match_rate_percent" in body
    assert "medicolegal_rule_judicial_notification_match_rate_percent" in body
    assert "medicolegal_rule_chain_of_custody_match_rate_percent" in body


def test_metrics_endpoint_contains_sepsis_protocol_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas sepsis",
            "description": "Verificar series workflow sepsis",
            "clinical_priority": "critical",
            "specialty": "emergency",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_sepsis = client.post(
        f"/api/v1/care-tasks/{task_id}/sepsis/recommendation",
        json={
            "suspected_infection": True,
            "respiratory_rate_rpm": 25,
            "systolic_bp": 95,
            "altered_mental_status": True,
            "lactate_mmol_l": 3.4,
            "blood_cultures_collected": False,
            "antibiotics_started": False,
            "fluid_bolus_ml_per_kg": 10,
            "time_since_detection_minutes": 75,
        },
    )
    assert response_sepsis.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "sepsis_protocol_runs_total" in body
    assert "sepsis_protocol_runs_completed_total" in body
    assert "sepsis_protocol_critical_alerts_total" in body


def test_metrics_endpoint_contains_scasest_protocol_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas SCASEST",
            "description": "Verificar series workflow SCASEST",
            "clinical_priority": "critical",
            "specialty": "cardiology",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_scasest = client.post(
        f"/api/v1/care-tasks/{task_id}/scasest/recommendation",
        json={
            "chest_pain_typical": True,
            "ecg_st_depression": True,
            "troponin_positive": True,
            "hemodynamic_instability": True,
            "grace_score": 145,
        },
    )
    assert response_scasest.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "scasest_protocol_runs_total" in body
    assert "scasest_protocol_runs_completed_total" in body
    assert "scasest_protocol_critical_alerts_total" in body


def test_metrics_endpoint_contains_scasest_audit_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas auditoria SCASEST",
            "description": "Validar series de calidad SCASEST",
            "clinical_priority": "critical",
            "specialty": "cardiology",
            "sla_target_minutes": 20,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    run_response = client.post(
        f"/api/v1/care-tasks/{task_id}/scasest/recommendation",
        json={
            "chest_pain_typical": True,
            "ecg_st_depression": True,
            "troponin_positive": True,
            "hemodynamic_instability": True,
            "grace_score": 150,
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
        },
    )
    assert audit_response.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "scasest_audit_total" in body
    assert "scasest_audit_match_total" in body
    assert "scasest_audit_under_total" in body
    assert "scasest_audit_over_total" in body
    assert "scasest_audit_under_rate_percent" in body
    assert "scasest_audit_over_rate_percent" in body
    assert "scasest_rule_escalation_match_rate_percent" in body
    assert "scasest_rule_immediate_antiischemic_match_rate_percent" in body


def test_metrics_endpoint_contains_cardio_risk_support_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas riesgo cardiovascular",
            "description": "Verificar series workflow cardiovascular",
            "clinical_priority": "high",
            "specialty": "cardiology",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_cardio = client.post(
        f"/api/v1/care-tasks/{task_id}/cardio-risk/recommendation",
        json={
            "age_years": 68,
            "sex": "male",
            "smoker": True,
            "systolic_bp": 158,
            "non_hdl_mg_dl": 205,
            "apob_mg_dl": 128,
            "diabetes": True,
        },
    )
    assert response_cardio.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "cardio_risk_support_runs_total" in body
    assert "cardio_risk_support_runs_completed_total" in body
    assert "cardio_risk_support_alerts_total" in body


def test_metrics_endpoint_contains_cardio_risk_audit_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas auditoria cardiovascular",
            "description": "Validar series de calidad cardiovascular",
            "clinical_priority": "high",
            "specialty": "cardiology",
            "sla_target_minutes": 30,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    run_response = client.post(
        f"/api/v1/care-tasks/{task_id}/cardio-risk/recommendation",
        json={
            "age_years": 74,
            "sex": "female",
            "smoker": True,
            "systolic_bp": 172,
            "non_hdl_mg_dl": 235,
            "apob_mg_dl": 142,
            "diabetes": True,
            "chronic_kidney_disease": True,
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
        },
    )
    assert audit_response.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "cardio_risk_audit_total" in body
    assert "cardio_risk_audit_match_total" in body
    assert "cardio_risk_audit_under_total" in body
    assert "cardio_risk_audit_over_total" in body
    assert "cardio_risk_audit_under_rate_percent" in body
    assert "cardio_risk_audit_over_rate_percent" in body
    assert "cardio_risk_rule_non_hdl_target_match_rate_percent" in body
    assert "cardio_risk_rule_pharmacologic_strategy_match_rate_percent" in body
    assert "cardio_risk_rule_intensive_lifestyle_match_rate_percent" in body


def test_metrics_endpoint_contains_resuscitation_protocol_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas reanimacion",
            "description": "Verificar series workflow de reanimacion",
            "clinical_priority": "critical",
            "specialty": "emergency",
            "sla_target_minutes": 5,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    response_resuscitation = client.post(
        f"/api/v1/care-tasks/{task_id}/resuscitation/recommendation",
        json={
            "context_type": "cardiac_arrest",
            "rhythm": "vf",
            "has_pulse": False,
            "compression_depth_cm": 5.4,
            "compression_rate_per_min": 108,
            "interruption_seconds": 9,
            "etco2_mm_hg": 17,
        },
    )
    assert response_resuscitation.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "resuscitation_protocol_runs_total" in body
    assert "resuscitation_protocol_runs_completed_total" in body
    assert "resuscitation_protocol_alerts_total" in body


def test_metrics_endpoint_contains_resuscitation_audit_metrics(client):
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Caso metricas auditoria reanimacion",
            "description": "Validar series de calidad de reanimacion",
            "clinical_priority": "critical",
            "specialty": "emergency",
            "sla_target_minutes": 5,
            "human_review_required": True,
            "completed": False,
        },
    )
    assert create_task_response.status_code == 201
    task_id = create_task_response.json()["id"]

    run_response = client.post(
        f"/api/v1/care-tasks/{task_id}/resuscitation/recommendation",
        json={
            "context_type": "cardiac_arrest",
            "rhythm": "asystole",
            "has_pulse": False,
            "compression_depth_cm": 4.2,
            "compression_rate_per_min": 92,
            "interruption_seconds": 12,
            "etco2_mm_hg": 7,
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
        },
    )
    assert audit_response.status_code == 200

    response = client.get("/metrics")
    body = response.text
    assert "resuscitation_audit_total" in body
    assert "resuscitation_audit_match_total" in body
    assert "resuscitation_audit_under_total" in body
    assert "resuscitation_audit_over_total" in body
    assert "resuscitation_audit_under_rate_percent" in body
    assert "resuscitation_audit_over_rate_percent" in body
    assert "resuscitation_rule_shock_match_rate_percent" in body
    assert "resuscitation_rule_reversible_causes_match_rate_percent" in body
    assert "resuscitation_rule_airway_plan_match_rate_percent" in body


def test_metrics_endpoint_contains_global_quality_scorecard_metrics(client):
    response = client.get("/metrics")
    body = response.text
    assert "care_task_quality_audit_total" in body
    assert "care_task_quality_audit_match_total" in body
    assert "care_task_quality_audit_under_total" in body
    assert "care_task_quality_audit_over_total" in body
    assert "care_task_quality_audit_under_rate_percent" in body
    assert "care_task_quality_audit_over_rate_percent" in body
    assert "care_task_quality_audit_match_rate_percent" in body
