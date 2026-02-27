from app.scripts.evaluate_chat_regression import (
    _contains_all_terms,
    _contains_any_forbidden,
    _summarize,
    _token_f1,
)


def test_token_f1_returns_overlap_signal():
    score = _token_f1(
        "bundle sepsis primera hora con hemocultivos y antibiotico",
        "sepsis bundle primera hora antibiotico",
    )
    assert score > 0.4


def test_contains_all_terms_behaves_as_expected():
    text = "Plan operativo: activar bundle de sepsis y monitorizar lactato."
    assert _contains_all_terms(text, ["sepsis", "lactato"]) is True
    assert _contains_all_terms(text, ["sepsis", "troponina"]) is False


def test_contains_any_forbidden_detects_internal_leak():
    text = "Se uso endpoint /api/v1/care-tasks interno."
    assert _contains_any_forbidden(text, ["/api/v1", "workflow"]) is True


def test_summarize_aggregates_metrics():
    rows = [
        {
            "token_f1": 0.6,
            "domain_hit": True,
            "must_include_ok": True,
            "forbidden_hit": False,
            "latency_ms": 1000,
            "error": None,
        },
        {
            "token_f1": 0.4,
            "domain_hit": False,
            "must_include_ok": True,
            "forbidden_hit": False,
            "latency_ms": 1200,
            "error": None,
        },
    ]
    summary = _summarize(rows)
    assert summary["rows_total"] == 2
    assert summary["ok"] == 2
    assert summary["token_f1_avg"] == 0.5
    assert summary["domain_hit_rate"] == 0.5
