from types import SimpleNamespace

from app.scripts.evaluate_rag_retrieval import (
    _average_precision,
    _cohen_kappa_from_pairs,
    _dcg,
    _evaluate_acceptance,
    _f1,
    _parse_acceptance_thresholds,
    _parse_precision_ks,
    _precision_at_k,
    _recall_at_k,
    _resolve_relevance_lists,
)


def test_precision_recall_and_f1_basic():
    rels = [1, 0, 1, 0, 0]
    precision = _precision_at_k(rels, 5)
    recall = _recall_at_k(rels, total_relevant=4, k=5)
    f1 = _f1(precision, recall)
    assert round(precision, 4) == 0.4
    assert round(recall, 4) == 0.5
    assert round(f1, 4) == 0.4444


def test_average_precision_uses_relevant_ranks():
    rels = [1, 0, 1, 1]
    # precisiones en relevantes: 1/1, 2/3, 3/4 -> AP = (1 + 0.6667 + 0.75) / 3
    value = _average_precision(rels, total_relevant=3)
    assert round(value, 4) == 0.8056


def test_dcg_prefers_early_relevance():
    better = _dcg([3, 2, 0, 0])
    worse = _dcg([0, 3, 2, 0])
    assert better > worse


def test_kappa_from_pairs_perfect_and_none_cases():
    perfect = _cohen_kappa_from_pairs([(1, 1), (0, 0), (1, 1), (0, 0)])
    assert perfect is not None
    assert round(perfect, 4) == 1.0

    empty = _cohen_kappa_from_pairs([])
    assert empty is None


def test_parse_precision_ks_with_invalid_values():
    parsed = _parse_precision_ks("1,3,foo,5,3,-1")
    assert parsed == [1, 3, 5]


def test_parse_precision_ks_defaults_when_empty():
    parsed = _parse_precision_ks("")
    assert parsed == [1, 3, 5]


def test_resolve_relevance_lists_terms_fallback_caps_total_relevant():
    row = {"expected_terms": ["neutropenia", "fiebre"]}
    chunks = [
        SimpleNamespace(id=1, chunk_text="neutropenia febril"),
        SimpleNamespace(id=2, chunk_text="fiebre y cultivos"),
        SimpleNamespace(id=3, chunk_text="sin match"),
    ]
    binary, graded, total = _resolve_relevance_lists(row=row, chunks=chunks)
    assert binary == [1, 1, 0]
    assert graded == [1.0, 1.0, 0.0]
    assert total == 2


def test_parse_acceptance_thresholds_ignores_invalid_pairs():
    parsed = _parse_acceptance_thresholds("precision_at_k=0.4,foo,ndcg=a,p@1=0.2")
    assert parsed == {"precision_at_k": 0.4, "p@1": 0.2}


def test_evaluate_acceptance_detects_missing_and_low_metrics():
    summary = {"precision_at_k": 0.33, "context_relevance": 0.21}
    thresholds = {"precision_at_k": 0.35, "context_relevance": 0.2, "ndcg": 0.3}
    failures = _evaluate_acceptance(summary, thresholds)
    assert "precision_at_k:0.3300<0.3500" in failures
    assert "ndcg:missing" in failures
    assert all("context_relevance" not in item for item in failures)
