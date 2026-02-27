from app.services.clinical_chat_service import ClinicalChatService
from app.services.clinical_hierarchical_clustering_service import (
    ClinicalHierarchicalClusteringService,
)


def test_hierarchical_clustering_prioritizes_oncology_cluster_candidates():
    assessment = ClinicalHierarchicalClusteringService.analyze_query(
        query="Paciente oncologico con neutropenia febril tras quimioterapia",
        domain_catalog=ClinicalChatService._DOMAIN_CATALOG,  # noqa: SLF001
        matched_domains=["critical_ops"],
        effective_specialty="emergency",
    )
    assert assessment["enabled"] is True
    assert assessment["candidate_domains"]
    assert assessment["candidate_domains"][0] == "oncology"
    assert float(assessment["top_confidence"]) > 0.0


def test_hierarchical_clustering_trace_contains_quality_and_model_fields():
    assessment = ClinicalHierarchicalClusteringService.analyze_query(
        query="Oliguria con hiperkalemia y creatinina en ascenso",
        domain_catalog=ClinicalChatService._DOMAIN_CATALOG,  # noqa: SLF001
        matched_domains=["critical_ops"],
        effective_specialty="emergency",
    )
    trace = assessment["trace"]
    assert "hcluster_method" in trace
    assert "hcluster_k_selected" in trace
    assert "hcluster_purity" in trace
    assert "hcluster_nmi" in trace
    assert "hcluster_rand_index" in trace
    assert "hcluster_f_measure" in trace


def test_hierarchical_clustering_evaluation_metrics_are_computed():
    metrics = ClinicalHierarchicalClusteringService.evaluate_predictions(
        true_labels=["a", "a", "b", "b"],
        cluster_ids=[0, 0, 1, 1],
        beta=1.0,
    )
    assert metrics["purity"] == 1.0
    assert metrics["nmi"] == 1.0
    assert metrics["rand_index"] == 1.0
    assert metrics["f_measure"] == 1.0
