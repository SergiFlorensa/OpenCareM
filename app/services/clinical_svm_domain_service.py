"""
Clasificacion de dominio clinico con SVM lineal (one-vs-rest).

Objetivo:
- maximizar margen de separacion por dominio sobre vectores tf-idf
- mantener coste cero y trazabilidad en runtime
- exponer senal adicional de enrutado para chat clinico
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from typing import Any

from app.core.config import settings


class ClinicalSVMDomainService:
    """SVM lineal OVA para priorizacion de dominio clinico."""

    _TOKEN_PATTERN = re.compile(r"[a-z0-9]{3,}", flags=re.IGNORECASE)
    _INFERENCE_LOGIT_SCALE = 4.0

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
    def _dot(left: dict[str, float], right: dict[str, float]) -> float:
        if not left or not right:
            return 0.0
        if len(left) > len(right):
            left, right = right, left
        return sum(float(value) * float(right.get(term, 0.0)) for term, value in left.items())

    @staticmethod
    def _l2_normalize(vector: dict[str, float]) -> dict[str, float]:
        if not vector:
            return {}
        norm = math.sqrt(sum(float(value) ** 2 for value in vector.values()))
        if norm <= 0:
            return {}
        return {term: float(value) / norm for term, value in vector.items()}

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
    def _train_ova_linear_svm(
        cls,
        *,
        sample_vectors: list[dict[str, float]],
        sample_labels: list[str],
        classes: list[str],
        c_value: float,
        l2_value: float,
        epochs: int,
    ) -> dict[str, dict[str, Any]]:
        models: dict[str, dict[str, Any]] = {}

        for class_label in classes:
            weights: dict[str, float] = {}
            bias = 0.0
            t = 0

            for _ in range(max(1, epochs)):
                for vector, label in zip(sample_vectors, sample_labels, strict=True):
                    y = 1.0 if label == class_label else -1.0
                    t += 1
                    eta = 1.0 / (float(l2_value) * float(t))

                    # Regularizacion L2 (margen blando).
                    shrink = max(0.0, 1.0 - (eta * float(l2_value)))
                    if weights and shrink != 1.0:
                        for term in list(weights.keys()):
                            new_value = float(weights[term]) * shrink
                            if abs(new_value) < 1e-10:
                                weights.pop(term, None)
                            else:
                                weights[term] = new_value

                    margin = y * (cls._dot(weights, vector) + bias)
                    if margin < 1.0:
                        step = eta * float(c_value) * y
                        for term, value in vector.items():
                            weights[term] = float(weights.get(term, 0.0)) + (step * float(value))
                        bias += step

            # Vectores de soporte aproximados: muestras dentro o violando margen.
            support_count = 0
            hinge_sum = 0.0
            for vector, label in zip(sample_vectors, sample_labels, strict=True):
                y = 1.0 if label == class_label else -1.0
                signed_distance = y * (cls._dot(weights, vector) + bias)
                if signed_distance <= 1.0 + 1e-9:
                    support_count += 1
                hinge_sum += max(0.0, 1.0 - signed_distance)
            avg_hinge = cls._safe_div(hinge_sum, float(len(sample_vectors)))

            models[class_label] = {
                "weights": weights,
                "bias": bias,
                "support_vectors": support_count,
                "avg_hinge_loss": avg_hinge,
            }

        return models

    @classmethod
    def _extract_support_terms(
        cls,
        *,
        query_vector: dict[str, float],
        top_weights: dict[str, float],
        max_terms: int = 5,
    ) -> list[str]:
        scored: list[tuple[float, str]] = []
        for term, q_value in query_vector.items():
            weight = float(top_weights.get(term, 0.0))
            contribution = float(q_value) * weight
            if contribution > 0:
                scored.append((contribution, term))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [term for _, term in scored[:max_terms]]

    @classmethod
    def analyze_query(
        cls,
        *,
        query: str,
        domain_catalog: list[dict[str, object]],
        matched_domains: list[str],
        effective_specialty: str,
    ) -> dict[str, Any]:
        method = "linear_ova"
        c_value = float(settings.CLINICAL_CHAT_SVM_DOMAIN_C)
        l2_value = float(settings.CLINICAL_CHAT_SVM_DOMAIN_L2)
        epochs = int(settings.CLINICAL_CHAT_SVM_DOMAIN_EPOCHS)
        if not settings.CLINICAL_CHAT_SVM_DOMAIN_ENABLED:
            return {
                "enabled": False,
                "method": method,
                "top_domain": "none",
                "top_probability": 0.0,
                "margin_top2": 0.0,
                "entropy": 0.0,
                "avg_hinge_loss": 0.0,
                "probabilities": [],
                "trace": {
                    "svm_domain_enabled": "0",
                    "svm_domain_method": method,
                    "svm_domain_c": f"{c_value:.3f}",
                    "svm_domain_l2": f"{l2_value:.4f}",
                    "svm_domain_epochs": str(epochs),
                    "svm_domain_top_domain": "none",
                    "svm_domain_top_probability": "0.0",
                    "svm_domain_margin_top2": "0.0",
                    "svm_domain_entropy": "0.0",
                    "svm_domain_support_vectors": "0",
                    "svm_domain_avg_hinge_loss": "0.0",
                    "svm_domain_vocab_size": "0",
                    "svm_domain_classes": "0",
                    "svm_domain_training_docs": "0",
                    "svm_domain_rerank_recommended": "0",
                    "svm_domain_support_terms": "none",
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
                "avg_hinge_loss": 0.0,
                "probabilities": [],
                "trace": {
                    "svm_domain_enabled": "0",
                    "svm_domain_method": method,
                    "svm_domain_c": f"{c_value:.3f}",
                    "svm_domain_l2": f"{l2_value:.4f}",
                    "svm_domain_epochs": str(epochs),
                    "svm_domain_top_domain": "none",
                    "svm_domain_top_probability": "0.0",
                    "svm_domain_margin_top2": "0.0",
                    "svm_domain_entropy": "0.0",
                    "svm_domain_support_vectors": "0",
                    "svm_domain_avg_hinge_loss": "0.0",
                    "svm_domain_vocab_size": "0",
                    "svm_domain_classes": "0",
                    "svm_domain_training_docs": "0",
                    "svm_domain_rerank_recommended": "0",
                    "svm_domain_support_terms": "none",
                },
                "memory_facts": [],
            }

        idf = cls._compute_idf(samples=samples)
        sample_vectors = [cls._vectorize_tokens(tokens=tokens, idf=idf) for _, tokens in samples]
        sample_labels = [label for label, _ in samples]
        classes = sorted(set(sample_labels))
        priors = cls._class_priors(
            classes=classes,
            matched_domains=matched_domains,
            effective_specialty=effective_specialty,
        )
        models = cls._train_ova_linear_svm(
            sample_vectors=sample_vectors,
            sample_labels=sample_labels,
            classes=classes,
            c_value=c_value,
            l2_value=max(1e-6, l2_value),
            epochs=max(1, epochs),
        )

        query_tokens = cls._tokenize(query)
        query_vector = cls._vectorize_tokens(tokens=query_tokens, idf=idf)
        raw_scores: dict[str, float] = {}
        support_counts: list[int] = []
        hinge_values: list[float] = []
        for class_label in classes:
            model = models.get(class_label, {})
            weights = model.get("weights", {})
            # En catalogo pseudo-etiquetado y altamente desbalanceado por clase,
            # el bias del OVA puede dominar el score. Para inferencia usamos la
            # parte discriminativa (w·x) y mantenemos un prior suave para desempates.
            margin = cls._dot(query_vector, weights)
            raw_scores[class_label] = float(margin) + (0.10 * float(priors.get(class_label, 0.0)))
            support_counts.append(int(model.get("support_vectors", 0)))
            hinge_values.append(float(model.get("avg_hinge_loss", 0.0)))

        calibrated_scores = {
            class_label: float(score) * float(cls._INFERENCE_LOGIT_SCALE)
            for class_label, score in raw_scores.items()
        }
        probabilities = cls._softmax(calibrated_scores)
        ranked = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
        top_domain = ranked[0][0] if ranked else "none"
        top_probability = float(ranked[0][1]) if ranked else 0.0
        second_probability = float(ranked[1][1]) if len(ranked) > 1 else 0.0
        margin_top2 = max(0.0, top_probability - second_probability)
        entropy = cls._entropy(probabilities)
        support_vectors = max(support_counts) if support_counts else 0
        avg_hinge_loss = cls._safe_div(sum(hinge_values), float(len(hinge_values)))
        rerank_recommended = (
            1 if top_probability >= float(settings.CLINICAL_CHAT_SVM_DOMAIN_MIN_CONFIDENCE) else 0
        )
        top_weights = dict(models.get(top_domain, {}).get("weights", {}))
        support_terms = cls._extract_support_terms(
            query_vector=query_vector,
            top_weights=top_weights,
            max_terms=5,
        )

        trace = {
            "svm_domain_enabled": "1",
            "svm_domain_method": method,
            "svm_domain_c": f"{c_value:.3f}",
            "svm_domain_l2": f"{l2_value:.4f}",
            "svm_domain_epochs": str(epochs),
            "svm_domain_top_domain": top_domain,
            "svm_domain_top_probability": f"{top_probability:.4f}",
            "svm_domain_margin_top2": f"{margin_top2:.4f}",
            "svm_domain_entropy": f"{entropy:.4f}",
            "svm_domain_support_vectors": str(int(support_vectors)),
            "svm_domain_avg_hinge_loss": f"{avg_hinge_loss:.4f}",
            "svm_domain_vocab_size": str(len(idf)),
            "svm_domain_classes": str(len(classes)),
            "svm_domain_training_docs": str(len(samples)),
            "svm_domain_rerank_recommended": str(rerank_recommended),
            "svm_domain_support_terms": ",".join(support_terms) if support_terms else "none",
        }

        return {
            "enabled": True,
            "method": method,
            "top_domain": top_domain,
            "top_probability": round(top_probability, 4),
            "margin_top2": round(margin_top2, 4),
            "entropy": round(entropy, 4),
            "support_vectors": int(support_vectors),
            "avg_hinge_loss": round(avg_hinge_loss, 4),
            "support_terms": support_terms,
            "probabilities": [
                {"domain": domain, "probability": round(probability, 4)}
                for domain, probability in ranked[:5]
            ],
            "trace": trace,
            "memory_facts": [
                f"svm_domain_top:{top_domain}",
                f"svm_domain_probability:{round(top_probability, 4)}",
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
