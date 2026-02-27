"""
Clasificador Naive Bayes ligero para enrutado clinico de dominios.

Objetivo:
- aportar una senal supervisada de texto (multinomial/bernoulli)
- mantener coste computacional bajo (sin dependencias externas)
- exponer trazabilidad operativa para auditoria
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from typing import Any

from app.core.config import settings


class ClinicalNaiveBayesService:
    """Clasificador NB para priorizar dominio clinico de la consulta."""

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
    def _safe_log(value: float) -> float:
        return math.log(max(1e-12, float(value)))

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
    def _build_training_docs(
        cls,
        *,
        domain_catalog: list[dict[str, object]],
    ) -> dict[str, list[str]]:
        docs_by_class: dict[str, list[str]] = {}
        for item in domain_catalog:
            key = str(item.get("key") or "").strip()
            if not key:
                continue
            label = str(item.get("label") or "")
            summary = str(item.get("summary") or "")
            keywords = " ".join(str(token) for token in (item.get("keywords") or []))
            training_text = f"{key} {label} {summary} {keywords}"
            tokens = cls._tokenize(training_text)
            if tokens:
                docs_by_class[key] = tokens
        return docs_by_class

    @classmethod
    def _term_class_association_scores(
        cls,
        *,
        docs_by_class: dict[str, list[str]],
        method: str,
    ) -> dict[str, float]:
        if not docs_by_class:
            return {}
        class_labels = list(docs_by_class.keys())
        total_docs = len(class_labels)
        term_presence_by_class: dict[str, set[str]] = {}
        for class_label, tokens in docs_by_class.items():
            for term in set(tokens):
                term_presence_by_class.setdefault(term, set()).add(class_label)

        scores: dict[str, float] = {}
        epsilon = 1e-12
        for term, present_classes in term_presence_by_class.items():
            best_score = 0.0
            term_docs = len(present_classes)
            for class_label in class_labels:
                class_positive = 1
                class_negative = total_docs - class_positive
                n11 = 1 if class_label in present_classes else 0
                n10 = term_docs - n11
                n01 = class_positive - n11
                n00 = class_negative - n10

                if method == "mi":
                    # Informacion mutua binaria termino/clase.
                    n = float(total_docs)
                    p_t = (n11 + n10) / n
                    p_not_t = 1.0 - p_t
                    p_c = class_positive / n
                    p_not_c = 1.0 - p_c
                    p_tc = n11 / n
                    p_t_not_c = n10 / n
                    p_not_t_c = n01 / n
                    p_not_t_not_c = n00 / n
                    score = 0.0
                    if p_tc > 0:
                        score += p_tc * math.log((p_tc + epsilon) / ((p_t * p_c) + epsilon))
                    if p_t_not_c > 0:
                        score += p_t_not_c * math.log(
                            (p_t_not_c + epsilon) / ((p_t * p_not_c) + epsilon)
                        )
                    if p_not_t_c > 0:
                        score += p_not_t_c * math.log(
                            (p_not_t_c + epsilon) / ((p_not_t * p_c) + epsilon)
                        )
                    if p_not_t_not_c > 0:
                        score += p_not_t_not_c * math.log(
                            (p_not_t_not_c + epsilon) / ((p_not_t * p_not_c) + epsilon)
                        )
                else:
                    # Chi-cuadrado sobre tabla 2x2.
                    n = float(total_docs)
                    numerator = ((n11 * n00) - (n10 * n01)) ** 2 * n
                    denominator = max(
                        epsilon,
                        float(n11 + n01) * float(n11 + n10) * float(n10 + n00) * float(n01 + n00),
                    )
                    score = numerator / denominator
                if score > best_score:
                    best_score = float(score)
            scores[term] = best_score
        return scores

    @classmethod
    def _select_features(
        cls,
        *,
        docs_by_class: dict[str, list[str]],
    ) -> set[str]:
        method = str(settings.CLINICAL_CHAT_NB_FEATURE_METHOD).strip().lower()
        max_features = int(settings.CLINICAL_CHAT_NB_MAX_FEATURES)
        if method == "none":
            all_terms: set[str] = set()
            for tokens in docs_by_class.values():
                all_terms.update(tokens)
            return all_terms
        metric = "mi" if method == "mi" else "chi2"
        scores = cls._term_class_association_scores(docs_by_class=docs_by_class, method=metric)
        ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return {term for term, _ in ordered[:max_features]}

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
        return {label: value / total for label, value in base.items()}

    @classmethod
    def _predict_multinomial(
        cls,
        *,
        query_tokens: list[str],
        docs_by_class: dict[str, list[str]],
        priors: dict[str, float],
        alpha: float,
        features: set[str],
    ) -> dict[str, float]:
        vocabulary = set(features)
        if not vocabulary:
            for tokens in docs_by_class.values():
                vocabulary.update(tokens)
        vocab_size = max(1, len(vocabulary))
        query_counts = Counter(token for token in query_tokens if token in vocabulary)
        if not query_counts:
            return {label: cls._safe_log(priors.get(label, 1e-12)) for label in docs_by_class}

        class_scores: dict[str, float] = {}
        for class_label, tokens in docs_by_class.items():
            token_counts = Counter(token for token in tokens if token in vocabulary)
            token_total = float(sum(token_counts.values()))
            denom = token_total + (alpha * vocab_size)
            score = cls._safe_log(priors.get(class_label, 1e-12))
            for term, tf_query in query_counts.items():
                prob = (float(token_counts.get(term, 0.0)) + alpha) / denom
                score += float(tf_query) * cls._safe_log(prob)
            class_scores[class_label] = score
        return class_scores

    @classmethod
    def _predict_bernoulli(
        cls,
        *,
        query_tokens: list[str],
        docs_by_class: dict[str, list[str]],
        priors: dict[str, float],
        alpha: float,
        features: set[str],
    ) -> dict[str, float]:
        vocabulary = set(features)
        if not vocabulary:
            for tokens in docs_by_class.values():
                vocabulary.update(tokens)
        if not vocabulary:
            return {label: cls._safe_log(priors.get(label, 1e-12)) for label in docs_by_class}

        query_presence = set(token for token in query_tokens if token in vocabulary)
        class_scores: dict[str, float] = {}
        for class_label, tokens in docs_by_class.items():
            class_presence = set(token for token in tokens if token in vocabulary)
            # En este esquema ligero cada clase se modela como un documento etiquetado.
            n_class_docs = 1.0
            score = cls._safe_log(priors.get(class_label, 1e-12))
            for term in vocabulary:
                n_ct = 1.0 if term in class_presence else 0.0
                p_term = (n_ct + alpha) / (n_class_docs + (2.0 * alpha))
                if term in query_presence:
                    score += cls._safe_log(p_term)
                else:
                    score += cls._safe_log(1.0 - p_term)
            class_scores[class_label] = score
        return class_scores

    @classmethod
    def analyze_query(
        cls,
        *,
        query: str,
        domain_catalog: list[dict[str, object]],
        matched_domains: list[str],
        effective_specialty: str,
    ) -> dict[str, Any]:
        if not settings.CLINICAL_CHAT_NB_ENABLED:
            return {
                "enabled": False,
                "top_domain": "none",
                "top_probability": 0.0,
                "margin_top2": 0.0,
                "entropy": 0.0,
                "probabilities": [],
                "trace": {
                    "nb_enabled": "0",
                    "nb_model": str(settings.CLINICAL_CHAT_NB_MODEL),
                    "nb_top_domain": "none",
                    "nb_top_probability": "0.0",
                    "nb_margin_top2": "0.0",
                    "nb_entropy": "0.0",
                    "nb_tokens": "0",
                    "nb_vocab_size": "0",
                    "nb_classes": "0",
                    "nb_features_selected": "0",
                    "nb_rerank_recommended": "0",
                },
                "memory_facts": [],
            }

        docs_by_class = cls._build_training_docs(domain_catalog=domain_catalog)
        if not docs_by_class:
            return {
                "enabled": False,
                "top_domain": "none",
                "top_probability": 0.0,
                "margin_top2": 0.0,
                "entropy": 0.0,
                "probabilities": [],
                "trace": {
                    "nb_enabled": "0",
                    "nb_model": str(settings.CLINICAL_CHAT_NB_MODEL),
                    "nb_top_domain": "none",
                    "nb_top_probability": "0.0",
                    "nb_margin_top2": "0.0",
                    "nb_entropy": "0.0",
                    "nb_tokens": "0",
                    "nb_vocab_size": "0",
                    "nb_classes": "0",
                    "nb_features_selected": "0",
                    "nb_rerank_recommended": "0",
                },
                "memory_facts": [],
            }

        model = str(settings.CLINICAL_CHAT_NB_MODEL).strip().lower()
        alpha = max(1e-6, float(settings.CLINICAL_CHAT_NB_ALPHA))
        query_tokens = cls._tokenize(query)
        classes = list(docs_by_class.keys())
        priors = cls._class_priors(
            classes=classes,
            matched_domains=matched_domains,
            effective_specialty=effective_specialty,
        )
        features = cls._select_features(docs_by_class=docs_by_class)

        if model == "bernoulli":
            class_log_scores = cls._predict_bernoulli(
                query_tokens=query_tokens,
                docs_by_class=docs_by_class,
                priors=priors,
                alpha=alpha,
                features=features,
            )
        else:
            class_log_scores = cls._predict_multinomial(
                query_tokens=query_tokens,
                docs_by_class=docs_by_class,
                priors=priors,
                alpha=alpha,
                features=features,
            )

        probabilities = cls._softmax(class_log_scores)
        ranked = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
        top_domain = ranked[0][0] if ranked else "none"
        top_probability = float(ranked[0][1]) if ranked else 0.0
        second_probability = float(ranked[1][1]) if len(ranked) > 1 else 0.0
        margin_top2 = max(0.0, top_probability - second_probability)
        entropy = cls._entropy(probabilities)
        rerank_recommended = (
            1 if top_probability >= float(settings.CLINICAL_CHAT_NB_MIN_CONFIDENCE) else 0
        )

        trace = {
            "nb_enabled": "1",
            "nb_model": model,
            "nb_alpha": f"{alpha:.3f}",
            "nb_top_domain": top_domain,
            "nb_top_probability": f"{top_probability:.4f}",
            "nb_margin_top2": f"{margin_top2:.4f}",
            "nb_entropy": f"{entropy:.4f}",
            "nb_tokens": str(len(query_tokens)),
            "nb_vocab_size": str(len(features)),
            "nb_classes": str(len(classes)),
            "nb_features_selected": str(len(features)),
            "nb_rerank_recommended": str(rerank_recommended),
        }
        return {
            "enabled": True,
            "model": model,
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
                f"nb_top_domain:{top_domain}",
                f"nb_top_probability:{round(top_probability, 4)}",
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
        """Calcula metricas por clase y agregados macro/micro para clasificacion."""
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
            }

        if labels is None:
            labels = sorted({str(value) for value in y_true} | {str(value) for value in y_pred})

        def _safe_div(num: float, den: float) -> float:
            return float(num) / float(den) if den else 0.0

        per_class: dict[str, dict[str, float]] = {}
        macro_precision_values: list[float] = []
        macro_recall_values: list[float] = []
        macro_f1_values: list[float] = []
        tp_total = 0
        fp_total = 0
        fn_total = 0

        for label in labels:
            tp = 0
            fp = 0
            fn = 0
            support = 0
            for truth, pred in zip(y_true, y_pred, strict=True):
                truth_label = str(truth)
                pred_label = str(pred)
                if truth_label == label:
                    support += 1
                if truth_label == label and pred_label == label:
                    tp += 1
                elif truth_label != label and pred_label == label:
                    fp += 1
                elif truth_label == label and pred_label != label:
                    fn += 1

            precision = _safe_div(tp, tp + fp)
            recall = _safe_div(tp, tp + fn)
            f1 = _safe_div(2.0 * precision * recall, precision + recall)

            per_class[label] = {
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

        macro_precision = _safe_div(sum(macro_precision_values), len(macro_precision_values))
        macro_recall = _safe_div(sum(macro_recall_values), len(macro_recall_values))
        macro_f1 = _safe_div(sum(macro_f1_values), len(macro_f1_values))
        micro_precision = _safe_div(tp_total, tp_total + fp_total)
        micro_recall = _safe_div(tp_total, tp_total + fn_total)
        micro_f1 = _safe_div(2.0 * micro_precision * micro_recall, micro_precision + micro_recall)

        return {
            "support": int(len(y_true)),
            "macro_precision": round(macro_precision, 4),
            "macro_recall": round(macro_recall, 4),
            "macro_f1": round(macro_f1, 4),
            "micro_precision": round(micro_precision, 4),
            "micro_recall": round(micro_recall, 4),
            "micro_f1": round(micro_f1, 4),
            "per_class": per_class,
        }
