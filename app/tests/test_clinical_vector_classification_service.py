from app.core.config import settings
from app.services.clinical_chat_service import ClinicalChatService
from app.services.clinical_vector_classification_service import (
    ClinicalVectorClassificationService,
)


def test_vector_rocchio_prioritizes_oncology_query():
    assessment = ClinicalVectorClassificationService.analyze_query(
        query="Paciente oncologico con neutropenia febril tras quimioterapia",
        domain_catalog=ClinicalChatService._DOMAIN_CATALOG,  # noqa: SLF001
        matched_domains=["critical_ops"],
        effective_specialty="emergency",
    )
    assert assessment["enabled"] is True
    assert assessment["top_domain"] == "oncology"
    assert float(assessment["top_probability"]) > 0.0


def test_vector_knn_prioritizes_nephrology_query(monkeypatch):
    monkeypatch.setattr(settings, "CLINICAL_CHAT_VECTOR_METHOD", "knn")
    monkeypatch.setattr(settings, "CLINICAL_CHAT_VECTOR_K", 5)
    assessment = ClinicalVectorClassificationService.analyze_query(
        query="Oliguria con hiperkalemia y creatinina en ascenso",
        domain_catalog=ClinicalChatService._DOMAIN_CATALOG,  # noqa: SLF001
        matched_domains=["critical_ops"],
        effective_specialty="emergency",
    )
    assert assessment["enabled"] is True
    assert assessment["top_domain"] == "nephrology"
    assert assessment["trace"]["vector_method"] == "knn"


def test_vector_evaluation_includes_confusion_matrix_and_macro_micro():
    metrics = ClinicalVectorClassificationService.evaluate_predictions(
        y_true=["oncology", "oncology", "nephrology", "critical_ops"],
        y_pred=["oncology", "critical_ops", "nephrology", "critical_ops"],
        labels=["oncology", "nephrology", "critical_ops"],
    )
    assert metrics["support"] == 4
    assert metrics["macro_precision"] == 0.8333
    assert metrics["micro_f1"] == 0.75
    assert metrics["confusion_matrix"]["oncology"]["critical_ops"] == 1
