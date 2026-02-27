from app.services.clinical_chat_service import ClinicalChatService
from app.services.clinical_svm_domain_service import ClinicalSVMDomainService


def test_svm_domain_prioritizes_oncology_query():
    assessment = ClinicalSVMDomainService.analyze_query(
        query="Paciente oncologico con neutropenia febril tras quimioterapia",
        domain_catalog=ClinicalChatService._DOMAIN_CATALOG,  # noqa: SLF001
        matched_domains=["critical_ops"],
        effective_specialty="emergency",
    )
    assert assessment["enabled"] is True
    assert assessment["top_domain"] == "oncology"
    assert float(assessment["top_probability"]) > 0.0
    assert "svm_domain_support_vectors" in assessment["trace"]


def test_svm_domain_trace_contains_margin_and_hinge():
    assessment = ClinicalSVMDomainService.analyze_query(
        query="Oliguria con hiperkalemia y creatinina en ascenso",
        domain_catalog=ClinicalChatService._DOMAIN_CATALOG,  # noqa: SLF001
        matched_domains=["critical_ops"],
        effective_specialty="emergency",
    )
    trace = assessment["trace"]
    assert "svm_domain_margin_top2" in trace
    assert "svm_domain_avg_hinge_loss" in trace
    assert "svm_domain_top_probability" in trace


def test_svm_domain_evaluation_includes_confusion_matrix_and_macro_micro():
    metrics = ClinicalSVMDomainService.evaluate_predictions(
        y_true=["oncology", "oncology", "nephrology", "critical_ops"],
        y_pred=["oncology", "critical_ops", "nephrology", "critical_ops"],
        labels=["oncology", "nephrology", "critical_ops"],
    )
    assert metrics["support"] == 4
    assert metrics["macro_precision"] == 0.8333
    assert metrics["micro_f1"] == 0.75
    assert metrics["confusion_matrix"]["oncology"]["critical_ops"] == 1
