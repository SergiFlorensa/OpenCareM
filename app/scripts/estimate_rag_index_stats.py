"""
Estimador rapido de dimensionamiento IR sobre `document_chunks`.

Calcula:
- Tokens totales (T) y vocabulario distinto (M)
- Ajuste log-log de Ley de Heaps: M = k * T^b
- Resumen de Zipf (top términos y estabilidad de cf_i * i)

Uso:
    ./venv/Scripts/python.exe -m app.scripts.estimate_rag_index_stats --specialty oncology
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter

from app.core.database import SessionLocal
from app.models.document_chunk import DocumentChunk

TOKEN_PATTERN = re.compile(r"[a-z0-9#\-\+/]+", flags=re.IGNORECASE)


def _linear_regression(points: list[tuple[float, float]]) -> tuple[float, float]:
    """Retorna (slope, intercept) para y = slope*x + intercept."""
    n = float(len(points))
    if n < 2:
        return 0.0, 0.0
    sum_x = sum(x for x, _ in points)
    sum_y = sum(y for _, y in points)
    sum_xx = sum(x * x for x, _ in points)
    sum_xy = sum(x * y for x, y in points)
    denominator = (n * sum_xx) - (sum_x * sum_x)
    if abs(denominator) < 1e-12:
        return 0.0, 0.0
    slope = ((n * sum_xy) - (sum_x * sum_y)) / denominator
    intercept = (sum_y - (slope * sum_x)) / n
    return slope, intercept


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimador Heaps/Zipf para corpus RAG local")
    parser.add_argument("--specialty", type=str, default="", help="Filtra por especialidad")
    parser.add_argument(
        "--chunk-limit",
        type=int,
        default=0,
        help="Limite de chunks a analizar (0 = todos)",
    )
    parser.add_argument("--top", type=int, default=25, help="Top términos Zipf")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        query = db.query(DocumentChunk.chunk_text)
        specialty = str(args.specialty or "").strip().lower()
        if specialty:
            query = query.filter(DocumentChunk.specialty == specialty)
        if int(args.chunk_limit) > 0:
            query = query.limit(int(args.chunk_limit))
        rows = query.all()

        token_counter: Counter[str] = Counter()
        total_tokens = 0
        vocab: set[str] = set()
        heaps_points: list[tuple[float, float]] = []

        sample_every = max(50, int(len(rows) / 40) if rows else 50)
        for index, (chunk_text,) in enumerate(rows, start=1):
            text_value = str(chunk_text or "").lower()
            tokens = TOKEN_PATTERN.findall(text_value)
            if not tokens:
                continue
            total_tokens += len(tokens)
            token_counter.update(tokens)
            vocab.update(tokens)
            if index % sample_every == 0:
                heaps_points.append((float(total_tokens), float(len(vocab))))

        if total_tokens > 0 and (not heaps_points or heaps_points[-1][0] != float(total_tokens)):
            heaps_points.append((float(total_tokens), float(len(vocab))))

        log_points = [
            (math.log(max(1.0, t)), math.log(max(1.0, m)))
            for t, m in heaps_points
            if t > 0 and m > 0
        ]
        slope_b, intercept_logk = _linear_regression(log_points)
        heaps_k = math.exp(intercept_logk) if log_points else 0.0

        top_n = max(5, int(args.top))
        top_terms = token_counter.most_common(top_n)
        zipf_pairs = []
        zipf_products = []
        for rank, (term, freq) in enumerate(top_terms, start=1):
            product = int(freq) * rank
            zipf_products.append(float(product))
            zipf_pairs.append(
                {
                    "rank": rank,
                    "term": term,
                    "cf": int(freq),
                    "cf_times_rank": product,
                }
            )
        zipf_product_avg = (
            sum(zipf_products) / len(zipf_products) if zipf_products else 0.0
        )
        zipf_product_std = (
            math.sqrt(
                sum((value - zipf_product_avg) ** 2 for value in zipf_products)
                / len(zipf_products)
            )
            if zipf_products
            else 0.0
        )

        output = {
            "chunks_analyzed": len(rows),
            "specialty_filter": specialty or None,
            "T_total_tokens": int(total_tokens),
            "M_vocabulary_size": int(len(vocab)),
            "heaps_estimate": {
                "k": round(float(heaps_k), 4),
                "b": round(float(slope_b), 4),
                "formula": "M = k * T^b",
            },
            "zipf_snapshot": {
                "top_terms": zipf_pairs,
                "cf_times_rank_avg": round(zipf_product_avg, 2),
                "cf_times_rank_std": round(zipf_product_std, 2),
            },
            "recommendations": {
                "vocab_cache_max_terms_min": int(min(len(vocab), 2000000)),
                "suggested_postings_encoding": "vb",
            },
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
