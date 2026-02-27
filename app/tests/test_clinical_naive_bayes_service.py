from app.services.clinical_chat_service import ClinicalChatService
from app.services.clinical_naive_bayes_service import ClinicalNaiveBayesService


def test_naive_bayes_multinomial_prioritizes_oncology_query():
    assessment = ClinicalNaiveBayesService.analyze_query(
        query="Paciente oncologico con neutropenia febril tras quimioterapia",
        domain_catalog=ClinicalChatService._DOMAIN_CATALOG,  # noqa: SLF001
        matched_domains=["oncology"],
        effective_specialty="oncology",
    )
    assert assessment["enabled"] is True
    assert assessment["top_domain"] == "oncology"
    assert float(assessment["top_probability"]) > 0.0
    assert assessment["trace"]["nb_model"] in {"multinomial", "bernoulli"}


def test_naive_bayes_trace_contains_operational_fields():
    assessment = ClinicalNaiveBayesService.analyze_query(
        query="Gestante con cefalea intensa y fosfenos en urgencias",
        domain_catalog=ClinicalChatService._DOMAIN_CATALOG,  # noqa: SLF001
        matched_domains=["gynecology_obstetrics"],
        effective_specialty="gynecology_obstetrics",
    )
    trace = assessment["trace"]
    for key in (
        "nb_enabled",
        "nb_top_domain",
        "nb_top_probability",
        "nb_margin_top2",
        "nb_entropy",
        "nb_features_selected",
        "nb_rerank_recommended",
    ):
        assert key in trace


def test_naive_bayes_evaluation_supports_macro_and_micro_averaging():
    metrics = ClinicalNaiveBayesService.evaluate_predictions(
        y_true=["oncology", "oncology", "nephrology", "critical_ops"],
        y_pred=["oncology", "critical_ops", "nephrology", "critical_ops"],
        labels=["oncology", "nephrology", "critical_ops"],
    )

    assert metrics["support"] == 4
    assert metrics["macro_precision"] == 0.8333
    assert metrics["macro_recall"] == 0.8333
    assert metrics["macro_f1"] == 0.7778
    assert metrics["micro_precision"] == 0.75
    assert metrics["micro_recall"] == 0.75
    assert metrics["micro_f1"] == 0.75
    assert metrics["per_class"]["oncology"]["recall"] == 0.5
