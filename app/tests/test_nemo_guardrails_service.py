from app.services.nemo_guardrails_service import NeMoGuardrailsService


def test_guardrails_service_skips_when_disabled(monkeypatch):
    monkeypatch.setattr(
        "app.services.nemo_guardrails_service.settings.CLINICAL_CHAT_GUARDRAILS_ENABLED",
        False,
    )
    answer, trace = NeMoGuardrailsService.apply_output_guardrails(
        query="Paciente con sepsis",
        answer="Plan inicial.",
        response_mode="clinical",
        effective_specialty="emergency",
        tool_mode="chat",
        knowledge_sources=[],
        web_sources=[],
    )
    assert answer == "Plan inicial."
    assert trace["guardrails_status"] == "skipped_disabled"


def test_guardrails_service_fails_open_when_config_missing(monkeypatch):
    monkeypatch.setattr(
        "app.services.nemo_guardrails_service.settings.CLINICAL_CHAT_GUARDRAILS_ENABLED",
        True,
    )
    monkeypatch.setattr(
        "app.services.nemo_guardrails_service.settings.CLINICAL_CHAT_GUARDRAILS_CONFIG_PATH",
        "app/guardrails_missing_for_test",
    )
    monkeypatch.setattr(
        "app.services.nemo_guardrails_service.settings.CLINICAL_CHAT_GUARDRAILS_FAIL_OPEN",
        True,
    )
    answer, trace = NeMoGuardrailsService.apply_output_guardrails(
        query="Paciente con sepsis",
        answer="Plan inicial.",
        response_mode="clinical",
        effective_specialty="emergency",
        tool_mode="chat",
        knowledge_sources=[],
        web_sources=[],
    )
    assert answer == "Plan inicial."
    assert trace["guardrails_status"] == "fallback_unavailable"
    assert trace["guardrails_fail_mode"] == "open"
