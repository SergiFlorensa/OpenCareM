from types import SimpleNamespace

from app.scripts.build_chat_regression_set import (
    _derive_must_include_terms,
    _has_forbidden_leak,
    _is_regression_candidate,
    _message_to_regression_item,
)


def test_derive_must_include_terms_filters_stopwords_and_limits():
    terms = _derive_must_include_terms(
        "Paciente con dolor toracico y troponina positiva en urgencias",
        max_terms=3,
    )
    assert len(terms) == 3
    assert "troponina" in terms


def test_has_forbidden_leak_detects_internal_tokens():
    assert _has_forbidden_leak("Endpoint interno /api/v1/care-tasks") is True
    assert _has_forbidden_leak("Resumen operativo basado en evidencia interna.") is False


def test_is_regression_candidate_requires_sources_and_quality():
    message = SimpleNamespace(
        user_query="Dolor toracico con cambios ECG",
        assistant_answer="Resumen operativo con acciones iniciales y escalado seguro.",
        knowledge_sources=[{"title": "SCASEST"}],
    )
    assert (
        _is_regression_candidate(
            message,
            min_query_chars=10,
            min_answer_chars=20,
        )
        is True
    )


def test_message_to_regression_item_maps_expected_fields():
    message = SimpleNamespace(
        id=12,
        care_task_id=5,
        session_id="s-1",
        user_query="Sospecha de sepsis con lactato alto",
        assistant_answer="Plan operativo en fases temporales.",
        matched_domains=["sepsis", "critical_ops"],
    )
    row = _message_to_regression_item(message)
    assert row["id"] == "chatmsg-12"
    assert row["care_task_id"] == 5
    assert row["expected_domains"][0] == "sepsis"
    assert "must_include_terms" in row
