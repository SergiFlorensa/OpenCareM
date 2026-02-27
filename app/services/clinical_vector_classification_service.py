"""
Clasificacion vectorial ligera para enrutado clinico por dominio.

Incluye:
- Rocchio (centroides por clase)
- kNN (votacion ponderada por similitud)
- modo hibrido (promedio de probabilidades)
- evaluacion con matriz de confusion + macro/micro averaging
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter, defaultdict
from typing import Any

from app.core.config import settings


class ClinicalVectorClassificationService:
    """Clasificador vectorial de dominio clinico (Rocchio/kNN)."""

    _TOKEN_PATTERN = re.compile(r"[a-z0-9]{3,}", flags=re.IGNORECASE)

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", str(text or ""))
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        return normalized.lower().strip()

    @classmethod
    def _tokenize(cls, text: str) -> list[str]:
        return [token for token in cls._TOKEN_PATTERN.findall(cls._normalize(text))]

    @staticmethod
    def _safe_div(num: float, den: float) -> float:
        return float(num) / float(den) if den else 0.0

    @staticmethod
    def _l2_normalize(vector: dict[str, float]) -> dict[str, float]:
        if not vector:
            return {}
        norm = math.sqrt(sum(float(value) ** 2 for value in vector.values()))
        if norm <= 0:
            return {}
        return {term: float(value) / norm for term, value in vector.items()}

    @staticmethod
    def _dot(left: dict[str, float], right: dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        if len(left) > len(right):
            left, right = right, left
        return sum(float(value) * float(right.get(term, 0.0)) for term, value in left.items())

    @staticmethod
    def _softmax(scores: dict[str, float]) -> dict[str, float]:
        if not scores:
            return {}
        max_score = max(scores.values())
        exps = {label: math.exp(score - max_score) for label, score in scores.items()}
        denom = sum(exps.values()) or 1.0
        return {label: value / denom for label, value in exps.items()}

    @staticmethod
    def _entropy(probabilities: dict[str, float]) -> float:
        entropy = 0.0
        for value in probabilities.values():
            if value <= 0:
                continue
            entropy -= float(value) * math.log(float(value))
        return entropy

    @classmethod
    def _build_training_samples(
        cls,
        *,
        domain_catalog: list[dict[str, object]],
    ) -> list[tuple[str, list[str]]]:
        samples: list[tuple[str, list[str]]] = []
        for item in domain_catalog:
            label = str(item.get("key") or "").strip()
            if not label:
                continue
            title = str(item.get("label") or "")
            summary = str(item.get("summary") or "")
            keywords = [str(token) for token in (item.get("keywords") or [])]
            keyword_text = " ".join(keywords)
            sample_texts = [
                f"{label} {title} {summary}",
                keyword_text,
                f"{title} {keyword_text}",
            ]
            for text in sample_texts:
                tokens = cls._tokenize(text)
                if tokens:
                    samples.append((label, tokens))
        return samples

    @classmethod
    def _compute_idf(
        cls,
        *,
        samples: list[tuple[str, list[str]]],
    ) -> dict[str, float]:
        if not samples:
            return {}
        doc_count = len(samples)
        df = Counter()
        for _, tokens in samples:
            for term in set(tokens):
                df[term] += 1
        return {
            term: math.log((1.0 + float(doc_count)) / (1.0 + float(freq))) + 1.0
            for term, freq in df.items()
        }

    @classmethod
    def _vectorize_tokens(
        cls,
        *,
        tokens: list[str],
        idf: dict[str, float],
    ) -> dict[str, float]:
        if not tokens or not idf:
            return {}
        tf = Counter(token for token in tokens if token in idf)
        weighted = {
            term: (1.0 + math.log(float(freq))) * float(idf.get(term, 0.0))
            for term, freq in tf.items()
            if freq > 0
        }
        return cls._l2_normalize(weighted)

    @classmethod
    def _build_centroids(
        cls,
        *,
        samples: list[tuple[str, list[str]]],
        sample_vectors: list[dict[str, float]],
    ) -> dict[str, dict[str, float]]:
        centroid_sums: dict[str, dict[str, float]] = defaultdict(dict)
        class_counts: dict[str, int] = defaultdict(int)
        for (label, _), vector in zip(samples, sample_vectors, strict=True):
            class_counts[label] += 1
            for term, value in vector.items():
                centroid_sums[label][term] = (
                    float(centroid_sums[label].get(term, 0.0)) + float(value)
                )

        centroids: dict[str, dict[str, float]] = {}
        for label, vector_sum in centroid_sums.items():
            count = max(1, class_counts.get(label, 1))
            averaged = {term: float(value) / float(count) for term, value in vector_sum.items()}
            centroids[label] = cls._l2_normalize(averaged)
        return centroids

    @classmethod
    def _class_priors(
        cls,
        *,
        classes: list[str],
        matched_domains: list[str],
        effective_specialty: str,
    ) -> dict[str, float]:
        if not classes:
            return {}
        base = {class_label: 1.0 for class_label in classes}
        normalized_specialty = cls._normalize(effective_specialty)
        for class_label in classes:
            if cls._normalize(class_label) == normalized_specialty:
                base[class_label] += 0.35
        for domain in matched_domains:
            normalized_domain = cls._normalize(domain)
            for class_label in classes:
                if cls._normalize(class_label) == normalized_domain:
                    base[class_label] += 0.20
        total = sum(base.values()) or 1.0
        return {label: float(value) / float(total) for label, value in base.items()}

    @classmethod
    def _predict_rocchio(
        cls,
        *,
        query_vector: dict[str, float],
        centroids: dict[str, dict[str, float]],
        priors: dict[str, float],
    ) -> dict[str, float]:
        raw_scores: dict[str, float] = {}
        for label, centroid in centroids.items():
            similarity = cls._dot(query_vector, centroid)
            raw_scores[label] = float(similarity) + (0.12 * float(priors.get(label, 0.0)))
        return cls._softmax(raw_scores)

    @classmethod
    def _predict_knn(
        cls,
        *,
        query_vector: dict[str, float],
        sample_vectors: list[dict[str, float]],
        sample_labels: list[str],
        priors: dict[str, float],
        k: int,
    ) -> dict[str, float]:
        if not sample_vectors or not sample_labels:
            return {}
        scored = [
            (cls._dot(query_vector, vector), label)
            for vector, label in zip(sample_vectors, sample_labels, strict=True)
        ]
        scored.sort(key=lambda item: item[0], reverse=True)
        top_k = scored[: max(1, min(k, len(scored)))]

        votes: dict[str, float] = defaultdict(float)
        for similarity, label in top_k:
            votes[label] += max(0.0, float(similarity))

        vote_total = float(sum(votes.values()))
        if vote_total <= 0:
            return dict(priors)

        normalized_votes = {
            label: float(value) / vote_total for label, value in votes.items()
        }
        blended: dict[str, float] = {}
        for label in priors:
            blended[label] = (0.90 * float(normalized_votes.get(label, 0.0))) + (
                0.10 * float(priors.get(label, 0.0))
            )
        norm = float(sum(blended.values())) or 1.0
        return {label: float(value) / norm for label, value in blended.items()}

    @classmethod
    def analyze_query(
        cls,
        *,
        query: str,
        domain_catalog: list[dict[str, object]],
        matched_domains: list[str],
        effective_specialty: str,
    ) -> dict[str, Any]:
        method = str(settings.CLINICAL_CHAT_VECTOR_METHOD).strip().lower()
        k = int(settings.CLINICAL_CHAT_VECTOR_K)
        if not settings.CLINICAL_CHAT_VECTOR_ENABLED:
            return {
                "enabled": False,
                "method": method,
                "top_domain": "none",
                "top_probability": 0.0,
                "margin_top2": 0.0,
                "entropy": 0.0,
                "probabilities": [],
                "trace": {
                    "vector_enabled": "0",
                    "vector_method": method,
                    "vector_k": str(k),
                    "vector_top_domain": "none",
                    "vector_top_probability": "0.0",
                    "vector_margin_top2": "0.0",
                    "vector_entropy": "0.0",
                    "vector_tokens": "0",
                    "vector_vocab_size": "0",
                    "vector_classes": "0",
                    "vector_training_docs": "0",
                    "vector_rerank_recommended": "0",
                },
                "memory_facts": [],
            }

        samples = cls._build_training_samples(domain_catalog=domain_catalog)
        if not samples:
            return {
                "enabled": False,
                "method": method,
                "top_domain": "none",
                "top_probability": 0.0,
                "margin_top2": 0.0,
                "entropy": 0.0,
                "probabilities": [],
                "trace": {
                    "vector_enabled": "0",
                    "vector_method": method,
                    "vector_k": str(k),
                    "vector_top_domain": "none",
                    "vector_top_probability": "0.0",
                    "vector_margin_top2": "0.0",
                    "vector_entropy": "0.0",
                    "vector_tokens": "0",
                    "vector_vocab_size": "0",
                    "vector_classes": "0",
                    "vector_training_docs": "0",
                    "vector_rerank_recommended": "0",
                },
                "memory_facts": [],
            }

        idf = cls._compute_idf(samples=samples)
        sample_vectors = [
            cls._vectorize_tokens(tokens=tokens, idf=idf)
            for _, tokens in samples
        ]
        sample_labels = [label for label, _ in samples]
        classes = sorted(set(sample_labels))
        priors = cls._class_priors(
            classes=classes,
            matched_domains=matched_domains,
            effective_specialty=effective_specialty,
        )

        query_tokens = cls._tokenize(query)
        query_vector = cls._vectorize_tokens(tokens=query_tokens, idf=idf)
        centroids = cls._build_centroids(samples=samples, sample_vectors=sample_vectors)
        rocchio_probs = cls._predict_rocchio(
            query_vector=query_vector,
            centroids=centroids,
            priors=priors,
        )
        knn_probs = cls._predict_knn(
            query_vector=query_vector,
            sample_vectors=sample_vectors,
            sample_labels=sample_labels,
            priors=priors,
            k=k,
        )

        if method == "knn":
            probabilities = knn_probs
        elif method == "hybrid":
            merged_labels = set(rocchio_probs.keys()) | set(knn_probs.keys())
            probabilities = {
                label: (0.5 * float(rocchio_probs.get(label, 0.0)))
                + (0.5 * float(knn_probs.get(label, 0.0)))
                for label in merged_labels
            }
            normalizer = float(sum(probabilities.values())) or 1.0
            probabilities = {
                label: float(value) / normalizer for label, value in probabilities.items()
            }
        else:
            probabilities = rocchio_probs

        ranked = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
        top_domain = ranked[0][0] if ranked else "none"
        top_probability = float(ranked[0][1]) if ranked else 0.0
        second_probability = float(ranked[1][1]) if len(ranked) > 1 else 0.0
        margin_top2 = max(0.0, top_probability - second_probability)
        entropy = cls._entropy(probabilities)
        rerank_recommended = (
            1 if top_probability >= float(settings.CLINICAL_CHAT_VECTOR_MIN_CONFIDENCE) else 0
        )

        trace = {
            "vector_enabled": "1",
            "vector_method": method,
            "vector_k": str(k),
            "vector_top_domain": top_domain,
            "vector_top_probability": f"{top_probability:.4f}",
            "vector_margin_top2": f"{margin_top2:.4f}",
            "vector_entropy": f"{entropy:.4f}",
            "vector_tokens": str(len(query_tokens)),
            "vector_vocab_size": str(len(idf)),
            "vector_classes": str(len(classes)),
            "vector_training_docs": str(len(samples)),
            "vector_rerank_recommended": str(rerank_recommended),
        }
        return {
            "enabled": True,
            "method": method,
            "top_domain": top_domain,
            "top_probability": round(top_probability, 4),
            "margin_top2": round(margin_top2, 4),
            "entropy": round(entropy, 4),
            "probabilities": [
                {"domain": domain, "probability": round(probability, 4)}
                for domain, probability in ranked[:5]
            ],
            "trace": trace,
            "memory_facts": [
                f"vector_top_domain:{top_domain}",
                f"vector_top_probability:{round(top_probability, 4)}",
            ],
        }

    @classmethod
    def evaluate_predictions(
        cls,
        *,
        y_true: list[str],
        y_pred: list[str],
        labels: list[str] | None = None,
    ) -> dict[str, Any]:
        """Evalua clasificacion con matriz de confusion y macro/micro averaging."""
        if len(y_true) != len(y_pred):
            raise ValueError("y_true y y_pred deben tener la misma longitud.")
        if not y_true:
            return {
                "support": 0,
                "macro_precision": 0.0,
                "macro_recall": 0.0,
                "macro_f1": 0.0,
                "micro_precision": 0.0,
                "micro_recall": 0.0,
                "micro_f1": 0.0,
                "per_class": {},
                "confusion_matrix": {},
            }

        if labels is None:
            labels = sorted({str(value) for value in y_true} | {str(value) for value in y_pred})

        confusion_matrix: dict[str, dict[str, int]] = {
            str(true_label): {str(pred_label): 0 for pred_label in labels}
            for true_label in labels
        }
        for truth, pred in zip(y_true, y_pred, strict=True):
            truth_label = str(truth)
            pred_label = str(pred)
            confusion_matrix.setdefault(
                truth_label, {str(pred_label_inner): 0 for pred_label_inner in labels}
            )
            for label in labels:
                confusion_matrix[truth_label].setdefault(str(label), 0)
            confusion_matrix[truth_label][pred_label] = (
                int(confusion_matrix[truth_label].get(pred_label, 0)) + 1
            )

        per_class: dict[str, dict[str, float]] = {}
        macro_precision_values: list[float] = []
        macro_recall_values: list[float] = []
        macro_f1_values: list[float] = []
        tp_total = 0
        fp_total = 0
        fn_total = 0

        for label in labels:
            label_key = str(label)
            tp = int(confusion_matrix.get(label_key, {}).get(label_key, 0))
            fp = sum(
                int(confusion_matrix.get(other_label, {}).get(label_key, 0))
                for other_label in labels
                if other_label != label_key
            )
            fn = sum(
                int(confusion_matrix.get(label_key, {}).get(other_label, 0))
                for other_label in labels
                if other_label != label_key
            )
            support = sum(int(value) for value in confusion_matrix.get(label_key, {}).values())

            precision = cls._safe_div(tp, tp + fp)
            recall = cls._safe_div(tp, tp + fn)
            f1 = cls._safe_div(2.0 * precision * recall, precision + recall)

            per_class[label_key] = {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "support": float(support),
            }
            macro_precision_values.append(precision)
            macro_recall_values.append(recall)
            macro_f1_values.append(f1)
            tp_total += tp
            fp_total += fp
            fn_total += fn

        macro_precision = cls._safe_div(sum(macro_precision_values), len(macro_precision_values))
        macro_recall = cls._safe_div(sum(macro_recall_values), len(macro_recall_values))
        macro_f1 = cls._safe_div(sum(macro_f1_values), len(macro_f1_values))
        micro_precision = cls._safe_div(tp_total, tp_total + fp_total)
        micro_recall = cls._safe_div(tp_total, tp_total + fn_total)
        micro_f1 = cls._safe_div(
            2.0 * micro_precision * micro_recall,
            micro_precision + micro_recall,
        )

        return {
            "support": int(len(y_true)),
            "macro_precision": round(macro_precision, 4),
            "macro_recall": round(macro_recall, 4),
            "macro_f1": round(macro_f1, 4),
            "micro_precision": round(micro_precision, 4),
            "micro_recall": round(micro_recall, 4),
            "micro_f1": round(micro_f1, 4),
            "per_class": per_class,
            "confusion_matrix": confusion_matrix,
        }
