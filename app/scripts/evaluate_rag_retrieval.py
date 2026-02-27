"""
Evaluacion offline de retrieval RAG (sin servicios externos).

Formato JSONL soportado por fila:
{
  "query": "Neutropenia febril ...",
  "specialty": "oncology",
  "domains": ["oncology"],
  "expected_terms": ["neutropenia", "fiebre"],             # opcional
  "expected_doc_ids": [123, 456],                          # opcional
  "graded_relevance": [{"doc_id": 123, "grade": 3}],       # opcional
  "assessor_labels": [{"a": 1, "b": 1}, {"a": 1, "b": 0}]  # opcional (kappa)
}

Notas:
- Si hay `graded_relevance`, se usa para nDCG graduado y binarizacion (>0) para MAP/MRR.
- Si hay `expected_doc_ids`, se usa relevancia binaria por doc_id.
- Si no hay doc_ids/graded, se usa fallback por `expected_terms` en chunk_text.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from app.core.database import SessionLocal
from app.models.document_chunk import DocumentChunk
from app.services.rag_retriever import HybridRetriever


def _load_dataset(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw:
            continue
        item = json.loads(raw)
        if "query" not in item:
            continue
        rows.append(item)
    return rows


def _dcg(relevances: list[float]) -> float:
    score = 0.0
    for idx, rel in enumerate(relevances, start=1):
        if rel <= 0:
            continue
        score += float(rel) / math.log2(idx + 1)
    return score


def _safe_div(num: float, den: float) -> float:
    if den <= 0:
        return 0.0
    return num / den


def _precision_at_k(binary_rels: list[int], k: int) -> float:
    top = binary_rels[: max(1, k)]
    return _safe_div(sum(top), max(1, k))


def _recall_at_k(binary_rels: list[int], total_relevant: int, k: int) -> float:
    return _safe_div(sum(binary_rels[: max(1, k)]), max(1, total_relevant))


def _f1(precision: float, recall: float) -> float:
    return _safe_div(2.0 * precision * recall, precision + recall)


def _average_precision(binary_rels: list[int], total_relevant: int) -> float:
    if total_relevant <= 0:
        return 0.0
    precisions: list[float] = []
    running_hits = 0
    for idx, rel in enumerate(binary_rels, start=1):
        if rel <= 0:
            continue
        running_hits += 1
        precisions.append(_safe_div(running_hits, idx))
    if not precisions:
        return 0.0
    return _safe_div(sum(precisions), total_relevant)


def _first_relevant_rank(binary_rels: list[int]) -> int | None:
    for idx, rel in enumerate(binary_rels, start=1):
        if rel > 0:
            return idx
    return None


def _token_overlap_ratio(query: str, chunk_text: str) -> float:
    query_tokens = {token for token in query.lower().split() if len(token) > 3}
    if not query_tokens:
        return 0.0
    chunk_tokens = {
        token.strip(".,;:()[]{}")
        for token in str(chunk_text or "").lower().split()
        if len(token.strip(".,;:()[]{}")) > 3
    }
    return _safe_div(len(query_tokens.intersection(chunk_tokens)), len(query_tokens))


def _is_relevant_by_terms(chunk_text: str, expected_terms: list[str]) -> bool:
    if not expected_terms:
        return False
    text = str(chunk_text or "").lower()
    return any(str(term).lower() in text for term in expected_terms if str(term).strip())


def _build_graded_lookup(row: dict[str, Any]) -> dict[int, float]:
    graded = row.get("graded_relevance") or []
    lookup: dict[int, float] = {}
    for item in graded:
        if not isinstance(item, dict):
            continue
        doc_id = item.get("doc_id")
        grade = item.get("grade")
        if doc_id is None or grade is None:
            continue
        try:
            lookup[int(doc_id)] = float(grade)
        except (TypeError, ValueError):
            continue
    return lookup


def _resolve_relevance_lists(
    *,
    row: dict[str, Any],
    chunks: list[DocumentChunk],
) -> tuple[list[int], list[float], int]:
    graded_lookup = _build_graded_lookup(row)
    expected_doc_ids = {int(x) for x in (row.get("expected_doc_ids") or [])}
    expected_terms = [str(item) for item in (row.get("expected_terms") or []) if str(item).strip()]

    binary_rels: list[int] = []
    graded_rels: list[float] = []
    for chunk in chunks:
        chunk_id = int(getattr(chunk, "id", 0) or 0)
        text_value = str(getattr(chunk, "chunk_text", "") or "")
        if graded_lookup:
            grade = float(graded_lookup.get(chunk_id, 0.0))
            graded_rels.append(grade)
            binary_rels.append(1 if grade > 0 else 0)
            continue
        if expected_doc_ids:
            rel = 1 if chunk_id in expected_doc_ids else 0
            binary_rels.append(rel)
            graded_rels.append(float(rel))
            continue
        rel = 1 if _is_relevant_by_terms(text_value, expected_terms) else 0
        binary_rels.append(rel)
        graded_rels.append(float(rel))

    if graded_lookup:
        total_relevant = sum(1 for grade in graded_lookup.values() if grade > 0)
    elif expected_doc_ids:
        total_relevant = len(expected_doc_ids)
    else:
        # Fallback sin gold doc_id: acotar a lo observable en top-k para mantener
        # metricas dentro de [0,1] y evitar sobreestimar recall/AP.
        total_relevant = max(1, sum(binary_rels))
    return binary_rels, graded_rels, total_relevant


def _cohen_kappa_from_pairs(pairs: list[tuple[int, int]]) -> float | None:
    if not pairs:
        return None
    normalized: list[tuple[int, int]] = []
    for left, right in pairs:
        if left not in {0, 1} or right not in {0, 1}:
            continue
        normalized.append((left, right))
    if not normalized:
        return None

    total = len(normalized)
    agree = sum(1 for left, right in normalized if left == right)
    p_a = _safe_div(agree, total)

    left_pos = _safe_div(sum(1 for left, _ in normalized if left == 1), total)
    left_neg = 1.0 - left_pos
    right_pos = _safe_div(sum(1 for _, right in normalized if right == 1), total)
    right_neg = 1.0 - right_pos
    p_e = (left_pos * right_pos) + (left_neg * right_neg)

    if abs(1.0 - p_e) < 1e-9:
        return None
    return (p_a - p_e) / (1.0 - p_e)


def _collect_assessor_pairs(rows: list[dict[str, Any]]) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    for row in rows:
        values = row.get("assessor_labels") or []
        if not isinstance(values, list):
            continue
        for item in values:
            if not isinstance(item, dict):
                continue
            try:
                pairs.append((int(item.get("a")), int(item.get("b"))))
            except (TypeError, ValueError):
                continue
    return pairs


def _extract_kwic_snippet(query: str, text: str, window: int = 14) -> str:
    tokens = str(text or "").split()
    if not tokens:
        return ""
    query_tokens = [term.lower() for term in query.split() if len(term) > 3]
    if not query_tokens:
        return " ".join(tokens[: min(len(tokens), window * 2)])
    lower_tokens = [token.lower().strip(".,;:()[]{}") for token in tokens]
    hit_index = None
    for idx, token in enumerate(lower_tokens):
        if any(term in token for term in query_tokens):
            hit_index = idx
            break
    if hit_index is None:
        return " ".join(tokens[: min(len(tokens), window * 2)])
    start = max(0, hit_index - window)
    end = min(len(tokens), hit_index + window + 1)
    return " ".join(tokens[start:end])


def _search_with_strategy(
    *,
    retriever: HybridRetriever,
    db: Any,
    row: dict[str, Any],
    k: int,
    strategy: str,
) -> tuple[list[DocumentChunk], dict[str, str]]:
    query = str(row.get("query") or "").strip()
    specialty = str(row.get("specialty") or "").strip().lower() or None
    domains = [str(item) for item in (row.get("domains") or []) if str(item).strip()]

    strategy_norm = strategy.lower().strip()
    if strategy_norm == "domain":
        if domains:
            return retriever.search_by_domain(domains, db, query=query, k=k)
        return retriever.search_hybrid(query, db, k=k, specialty_filter=specialty)
    if strategy_norm == "hybrid":
        return retriever.search_hybrid(query, db, k=k, specialty_filter=specialty)

    # auto
    if domains:
        return retriever.search_by_domain(domains, db, query=query, k=k)
    return retriever.search_hybrid(query, db, k=k, specialty_filter=specialty)


def evaluate(
    *,
    dataset_path: Path,
    k: int,
    precision_ks: list[int],
    strategy: str = "auto",
    emit_report_path: Path | None = None,
    acceptance_thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    db = SessionLocal()
    retriever = HybridRetriever()
    try:
        rows = _load_dataset(dataset_path)
        if not rows:
            empty = {
                "queries": 0.0,
                "precision_at_k": 0.0,
                "recall_at_k": 0.0,
                "f1_at_k": 0.0,
                "map": 0.0,
                "mrr": 0.0,
                "ndcg": 0.0,
                "context_relevance": 0.0,
                "kappa": None,
                "strategy": strategy,
            }
            for metric_k in precision_ks:
                empty[f"p@{metric_k}"] = 0.0
            return empty

        per_query_report: list[dict[str, Any]] = []
        precision_sum = 0.0
        recall_sum = 0.0
        f1_sum = 0.0
        map_sum = 0.0
        reciprocal_sum = 0.0
        ndcg_sum = 0.0
        context_relevance_sum = 0.0
        precision_at_k_sums = {value: 0.0 for value in precision_ks}
        specialty_agg: dict[str, dict[str, Any]] = {}

        for row in rows:
            query = str(row.get("query") or "").strip()
            if not query:
                continue
            chunks, trace = _search_with_strategy(
                retriever=retriever,
                db=db,
                row=row,
                k=k,
                strategy=strategy,
            )
            binary_rels, graded_rels, total_relevant = _resolve_relevance_lists(
                row=row,
                chunks=chunks,
            )

            precision_k = _precision_at_k(binary_rels, k)
            recall_k = _recall_at_k(binary_rels, total_relevant, k)
            f1_k = _f1(precision_k, recall_k)
            ap = _average_precision(binary_rels, total_relevant)
            first_rank = _first_relevant_rank(binary_rels)
            reciprocal = (1.0 / first_rank) if first_rank else 0.0
            ideal_graded = sorted(graded_rels, reverse=True)
            dcg = _dcg(graded_rels)
            idcg = _dcg(ideal_graded)
            ndcg = _safe_div(dcg, idcg) if idcg > 0 else 0.0

            best_overlap = 0.0
            for chunk in chunks:
                overlap = _token_overlap_ratio(query, str(getattr(chunk, "chunk_text", "") or ""))
                if overlap > best_overlap:
                    best_overlap = overlap

            precision_sum += precision_k
            recall_sum += recall_k
            f1_sum += f1_k
            map_sum += ap
            reciprocal_sum += reciprocal
            ndcg_sum += ndcg
            context_relevance_sum += best_overlap

            for metric_k in precision_ks:
                precision_at_k_sums[metric_k] += _precision_at_k(binary_rels, metric_k)

            specialty = str(row.get("specialty") or "unknown").strip().lower() or "unknown"
            aggregate = specialty_agg.setdefault(
                specialty,
                {
                    "queries": 0,
                    "precision_sum": 0.0,
                    "recall_sum": 0.0,
                    "f1_sum": 0.0,
                    "map_sum": 0.0,
                    "mrr_sum": 0.0,
                    "ndcg_sum": 0.0,
                    "context_relevance_sum": 0.0,
                    "precision_at_k_sums": {value: 0.0 for value in precision_ks},
                },
            )
            aggregate["queries"] += 1
            aggregate["precision_sum"] += precision_k
            aggregate["recall_sum"] += recall_k
            aggregate["f1_sum"] += f1_k
            aggregate["map_sum"] += ap
            aggregate["mrr_sum"] += reciprocal
            aggregate["ndcg_sum"] += ndcg
            aggregate["context_relevance_sum"] += best_overlap
            for metric_k in precision_ks:
                aggregate["precision_at_k_sums"][metric_k] += _precision_at_k(binary_rels, metric_k)

            top_chunk = chunks[0] if chunks else None
            kwic = (
                _extract_kwic_snippet(
                    query,
                    str(getattr(top_chunk, "chunk_text", "") or ""),
                )
                if top_chunk is not None
                else ""
            )
            per_query_report.append(
                {
                    "query": query,
                    "strategy": strategy,
                    "total_relevant": total_relevant,
                    "precision_at_k": round(precision_k, 4),
                    "recall_at_k": round(recall_k, 4),
                    "f1_at_k": round(f1_k, 4),
                    "average_precision": round(ap, 4),
                    "reciprocal_rank": round(reciprocal, 4),
                    "ndcg": round(ndcg, 4),
                    "retrieved_doc_ids": [int(getattr(chunk, "id", 0) or 0) for chunk in chunks],
                    "retrieved_scores": [
                        round(float(getattr(chunk, "_rag_score", 0.0) or 0.0), 6)
                        for chunk in chunks
                    ],
                    "kwic_top1": kwic,
                    "trace": trace,
                }
            )

        total_queries = max(1, len(per_query_report))
        summary: dict[str, Any] = {
            "queries": float(len(per_query_report)),
            "strategy": strategy,
            "precision_at_k": round(precision_sum / total_queries, 4),
            "recall_at_k": round(recall_sum / total_queries, 4),
            "f1_at_k": round(f1_sum / total_queries, 4),
            "map": round(map_sum / total_queries, 4),
            "mrr": round(reciprocal_sum / total_queries, 4),
            "ndcg": round(ndcg_sum / total_queries, 4),
            "context_relevance": round(context_relevance_sum / total_queries, 4),
        }
        for metric_k in precision_ks:
            summary[f"p@{metric_k}"] = round(
                precision_at_k_sums[metric_k] / total_queries,
                4,
            )

        kappa_pairs = _collect_assessor_pairs(rows)
        kappa_value = _cohen_kappa_from_pairs(kappa_pairs)
        summary["kappa"] = round(kappa_value, 4) if kappa_value is not None else None

        by_specialty: dict[str, dict[str, Any]] = {}
        for specialty, aggregate in specialty_agg.items():
            specialty_queries = max(1, int(aggregate.get("queries", 0) or 0))
            specialty_summary: dict[str, Any] = {
                "queries": float(aggregate.get("queries", 0) or 0),
                "precision_at_k": round(
                    float(aggregate.get("precision_sum", 0.0) or 0.0) / specialty_queries,
                    4,
                ),
                "recall_at_k": round(
                    float(aggregate.get("recall_sum", 0.0) or 0.0) / specialty_queries,
                    4,
                ),
                "f1_at_k": round(
                    float(aggregate.get("f1_sum", 0.0) or 0.0) / specialty_queries,
                    4,
                ),
                "map": round(
                    float(aggregate.get("map_sum", 0.0) or 0.0) / specialty_queries,
                    4,
                ),
                "mrr": round(
                    float(aggregate.get("mrr_sum", 0.0) or 0.0) / specialty_queries,
                    4,
                ),
                "ndcg": round(
                    float(aggregate.get("ndcg_sum", 0.0) or 0.0) / specialty_queries,
                    4,
                ),
                "context_relevance": round(
                    float(aggregate.get("context_relevance_sum", 0.0) or 0.0) / specialty_queries,
                    4,
                ),
            }
            specialty_p_sums = aggregate.get("precision_at_k_sums", {})
            for metric_k in precision_ks:
                specialty_summary[f"p@{metric_k}"] = round(
                    float(specialty_p_sums.get(metric_k, 0.0) or 0.0) / specialty_queries,
                    4,
                )
            by_specialty[specialty] = specialty_summary
        summary["by_specialty"] = by_specialty

        if acceptance_thresholds:
            failures = _evaluate_acceptance(summary, acceptance_thresholds)
            summary["acceptance_thresholds"] = acceptance_thresholds
            summary["acceptance_failures"] = failures
            summary["acceptance_passed"] = len(failures) == 0
            for specialty in by_specialty:
                specialty_failures = _evaluate_acceptance(
                    by_specialty[specialty],
                    acceptance_thresholds,
                )
                by_specialty[specialty]["acceptance_failures"] = specialty_failures
                by_specialty[specialty]["acceptance_passed"] = len(specialty_failures) == 0

        if emit_report_path is not None:
            emit_report_path.parent.mkdir(parents=True, exist_ok=True)
            emit_report_path.write_text(
                json.dumps(
                    {"summary": summary, "per_query": per_query_report},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

        return summary
    finally:
        db.close()


def _parse_precision_ks(raw_value: str) -> list[int]:
    parts = [item.strip() for item in str(raw_value or "").split(",")]
    values: list[int] = []
    for part in parts:
        if not part:
            continue
        try:
            number = int(part)
        except ValueError:
            continue
        if number > 0 and number not in values:
            values.append(number)
    if not values:
        values = [1, 3, 5]
    return sorted(values)


def _compute_delta(
    *,
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, float]:
    keys = {
        "precision_at_k",
        "recall_at_k",
        "f1_at_k",
        "map",
        "mrr",
        "ndcg",
        "context_relevance",
    }
    keys.update(key for key in baseline if key.startswith("p@"))
    keys.update(key for key in candidate if key.startswith("p@"))
    delta: dict[str, float] = {}
    for key in sorted(keys):
        left = float(baseline.get(key, 0.0) or 0.0)
        right = float(candidate.get(key, 0.0) or 0.0)
        delta[key] = round(right - left, 4)
    return delta


def _parse_acceptance_thresholds(raw_value: str) -> dict[str, float]:
    thresholds: dict[str, float] = {}
    parts = [item.strip() for item in str(raw_value or "").split(",")]
    for part in parts:
        if not part or "=" not in part:
            continue
        metric, value = part.split("=", maxsplit=1)
        key = str(metric).strip()
        if not key:
            continue
        try:
            thresholds[key] = float(value)
        except ValueError:
            continue
    return thresholds


def _evaluate_acceptance(summary: dict[str, Any], thresholds: dict[str, float]) -> list[str]:
    failures: list[str] = []
    for metric, expected_min in thresholds.items():
        value = summary.get(metric)
        if value is None:
            failures.append(f"{metric}:missing")
            continue
        try:
            value_float = float(value)
        except (TypeError, ValueError):
            failures.append(f"{metric}:invalid")
            continue
        if value_float < float(expected_min):
            failures.append(f"{metric}:{value_float:.4f}<{float(expected_min):.4f}")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Evalua retrieval RAG con dataset JSONL.")
    parser.add_argument("--dataset", required=True, help="Ruta al dataset JSONL.")
    parser.add_argument("--k", type=int, default=8, help="Top-K de recuperacion.")
    parser.add_argument(
        "--precision-ks",
        default="1,3,5",
        help="Lista separada por comas para P@k (ej: 1,3,5,10).",
    )
    parser.add_argument(
        "--strategy",
        default="auto",
        choices=["auto", "hybrid", "domain"],
        help="Estrategia principal de retrieval.",
    )
    parser.add_argument(
        "--ab-strategy",
        default="",
        choices=["", "auto", "hybrid", "domain"],
        help="Estrategia alternativa para comparativa A/B offline.",
    )
    parser.add_argument(
        "--report-out",
        default="",
        help="Ruta opcional para guardar reporte detallado JSON.",
    )
    parser.add_argument(
        "--acceptance-thresholds",
        default="",
        help=(
            "Umbrales minimos como metric=value separados por coma. "
            "Ej: precision_at_k=0.35,context_relevance=0.22,ndcg=0.30,p@1=0.4"
        ),
    )
    parser.add_argument(
        "--fail-on-acceptance",
        action="store_true",
        help="Devuelve exit code 1 cuando no se cumplen umbrales de aceptacion.",
    )
    args = parser.parse_args()

    precision_ks = _parse_precision_ks(args.precision_ks)
    report_path = Path(args.report_out) if str(args.report_out or "").strip() else None
    acceptance_thresholds = _parse_acceptance_thresholds(args.acceptance_thresholds)

    baseline = evaluate(
        dataset_path=Path(args.dataset),
        k=max(1, args.k),
        precision_ks=precision_ks,
        strategy=args.strategy,
        emit_report_path=report_path,
        acceptance_thresholds=acceptance_thresholds or None,
    )

    if not args.ab_strategy:
        print(json.dumps(baseline, ensure_ascii=False, indent=2))
        if args.fail_on_acceptance and acceptance_thresholds:
            failures = baseline.get("acceptance_failures") or []
            if failures:
                raise SystemExit(1)
        return

    ab_summary = evaluate(
        dataset_path=Path(args.dataset),
        k=max(1, args.k),
        precision_ks=precision_ks,
        strategy=args.ab_strategy,
        emit_report_path=None,
        acceptance_thresholds=acceptance_thresholds or None,
    )
    payload = (
        json.dumps(
            {
                "baseline": baseline,
                "candidate": ab_summary,
                "delta_candidate_minus_baseline": _compute_delta(
                    baseline=baseline,
                    candidate=ab_summary,
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    print(payload)
    if args.fail_on_acceptance and acceptance_thresholds:
        failures = ab_summary.get("acceptance_failures") or []
        if failures:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
