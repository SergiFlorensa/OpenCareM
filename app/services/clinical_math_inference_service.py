"""
Capa matematica ligera para soporte de inferencia clinica local.

Incluye:
- similitud de coseno entre consulta y prototipos de dominio,
- distancia L2 para penalizar ruido,
- actualizacion bayesiana simplificada por evidencia observada,
- score de prioridad operativo derivado.
"""

from __future__ import annotations

import math
import unicodedata
from typing import Any


class ClinicalMathInferenceService:
    """Inferencia matematica local sin dependencias de pago."""

    _DOMAIN_FEATURES: dict[str, tuple[str, ...]] = {
        "critical_ops": ("shock", "hipotension", "tas", "ecg", "sepsis", "red flag"),
        "nephrology": ("oliguria", "anuria", "k", "k+", "creatinina", "dialisis", "renal"),
        "gynecology_obstetrics": (
            "gestante",
            "embarazo",
            "ta",
            "fosfenos",
            "cefalea",
            "sangrado",
            "beta-hcg",
        ),
        "oncology": ("oncologia", "neutropenia", "fiebre", "quimioterapia", "tumor"),
        "pediatrics_neonatology": ("pediatr", "neonat", "sarampion", "apgar", "tosferina"),
    }

    @staticmethod
    def _normalize(text: str) -> str:
        lowered = text.lower()
        normalized = unicodedata.normalize("NFD", lowered)
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return " ".join(normalized.split())

    @classmethod
    def _tokenize(cls, text: str) -> list[str]:
        normalized = cls._normalize(text)
        return [token.strip(".,;:()[]{}!?") for token in normalized.split() if token]

    @classmethod
    def _build_query_vector(cls, query: str, features: tuple[str, ...]) -> list[float]:
        normalized_query = cls._normalize(query)
        vector: list[float] = []
        for feature in features:
            normalized_feature = cls._normalize(feature)
            vector.append(1.0 if normalized_feature in normalized_query else 0.0)
        return vector

    @staticmethod
    def _cosine_similarity(x: list[float], y: list[float]) -> float:
        if not x or not y or len(x) != len(y):
            return 0.0
        dot = sum(a * b for a, b in zip(x, y))
        nx = math.sqrt(sum(a * a for a in x))
        ny = math.sqrt(sum(b * b for b in y))
        if nx == 0 or ny == 0:
            return 0.0
        return max(0.0, min(1.0, dot / (nx * ny)))

    @staticmethod
    def _l2_distance(x: list[float], y: list[float]) -> float:
        if not x or not y or len(x) != len(y):
            return 1.0
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(x, y)))

    @staticmethod
    def _normalize_distribution(values: dict[str, float]) -> dict[str, float]:
        total = sum(max(0.0, value) for value in values.values())
        if total <= 0:
            base = 1.0 / max(1, len(values))
            return {key: base for key in values}
        return {key: max(0.0, value) / total for key, value in values.items()}

    @classmethod
    def _bayes_update(
        cls,
        *,
        priors: dict[str, float],
        likelihoods: dict[str, float],
    ) -> dict[str, float]:
        posterior_unnormalized = {
            key: max(0.001, priors.get(key, 0.0)) * max(0.001, likelihoods.get(key, 0.0))
            for key in priors
        }
        return cls._normalize_distribution(posterior_unnormalized)

    @staticmethod
    def _priority_from_probability(top_probability: float) -> str:
        if top_probability >= 0.75:
            return "high"
        if top_probability >= 0.45:
            return "medium"
        return "low"

    @staticmethod
    def _normalized_entropy(probabilities: list[float]) -> float:
        if not probabilities:
            return 0.0
        safe = [max(0.0, min(1.0, value)) for value in probabilities]
        total = sum(safe)
        if total <= 0:
            return 0.0
        normalized = [value / total for value in safe]
        entropy = -sum(p * math.log(max(p, 1e-12)) for p in normalized)
        max_entropy = math.log(len(normalized)) if len(normalized) > 1 else 1.0
        return max(0.0, min(1.0, entropy / max_entropy))

    @staticmethod
    def _posterior_variance_top(top_probability: float) -> float:
        """
        Varianza Bernoulli sobre la hipotesis top (proxy local de incertidumbre).
        """
        p = max(0.0, min(1.0, top_probability))
        return p * (1.0 - p)

    @staticmethod
    def _uncertainty_level(
        *,
        top_probability: float,
        margin_top2: float,
        normalized_entropy: float,
    ) -> str:
        if top_probability < 0.42 or margin_top2 < 0.10 or normalized_entropy > 0.80:
            return "high"
        if top_probability < 0.56 or margin_top2 < 0.18 or normalized_entropy > 0.62:
            return "medium"
        return "low"

    @classmethod
    def analyze_query(
        cls,
        *,
        query: str,
        matched_domains: list[str],
        effective_specialty: str,
        extracted_facts: list[str],
        memory_facts_used: list[str],
    ) -> dict[str, Any]:
        domains = list(dict.fromkeys([*matched_domains, effective_specialty]))
        domains = [domain for domain in domains if domain in cls._DOMAIN_FEATURES]
        if not domains:
            domains = [effective_specialty] if effective_specialty in cls._DOMAIN_FEATURES else []
        if not domains:
            return {
                "enabled": False,
                "trace": {
                    "math_enabled": "0",
                    "math_top_domain": "none",
                    "math_top_probability": "0.0",
                    "math_margin_top2": "0.0",
                    "math_entropy": "1.0",
                    "math_posterior_variance": "0.25",
                    "math_uncertainty_level": "high",
                    "math_abstention_recommended": "1",
                    "math_priority_score": "low",
                    "math_ood_score": "1.0",
                    "math_ood_level": "high",
                    "math_domains_evaluated": "0",
                    "math_model": "cosine+l2+bayes",
                },
            }

        priors = cls._normalize_distribution({domain: 1.0 for domain in domains})
        normalized_blob = cls._normalize(" ".join([query, *extracted_facts, *memory_facts_used]))

        likelihoods: dict[str, float] = {}
        similarity_details: list[dict[str, Any]] = []
        coverage_by_domain: dict[str, float] = {}
        for domain in domains:
            features = cls._DOMAIN_FEATURES[domain]
            query_vector = cls._build_query_vector(normalized_blob, features)
            proto_vector = [1.0] * len(features)
            cosine = cls._cosine_similarity(query_vector, proto_vector)
            l2 = cls._l2_distance(query_vector, proto_vector)
            feature_coverage = (
                sum(1.0 for value in query_vector if value > 0) / max(1, len(query_vector))
            )
            # Score combinado: alta similitud + menor distancia.
            combined = max(0.01, min(0.99, 0.75 * cosine + 0.25 * (1.0 / (1.0 + l2))))
            likelihoods[domain] = combined
            coverage_by_domain[domain] = feature_coverage
            similarity_details.append(
                {
                    "domain": domain,
                    "cosine_similarity": round(cosine, 4),
                    "l2_distance": round(l2, 4),
                    "feature_coverage": round(feature_coverage, 4),
                    "combined_score": round(combined, 4),
                }
            )

        posterior = cls._bayes_update(priors=priors, likelihoods=likelihoods)
        ranked = sorted(posterior.items(), key=lambda item: item[1], reverse=True)
        top_domain, top_probability = ranked[0]
        second_probability = ranked[1][1] if len(ranked) > 1 else 0.0
        margin_top2 = max(0.0, top_probability - second_probability)
        normalized_entropy = cls._normalized_entropy([probability for _, probability in ranked])
        posterior_variance_top = cls._posterior_variance_top(top_probability)
        top_coverage = float(coverage_by_domain.get(top_domain, 0.0))
        # OOD ligero: combina baja cobertura y baja confianza posterior.
        ood_score = max(0.0, min(1.0, 1.0 - (0.6 * top_coverage + 0.4 * top_probability)))
        if ood_score >= 0.70:
            ood_level = "high"
        elif ood_score >= 0.45:
            ood_level = "medium"
        else:
            ood_level = "low"
        uncertainty_level = cls._uncertainty_level(
            top_probability=top_probability,
            margin_top2=margin_top2,
            normalized_entropy=normalized_entropy,
        )
        abstention_recommended = uncertainty_level == "high"
        priority_score = cls._priority_from_probability(top_probability)

        return {
            "enabled": True,
            "top_domain": top_domain,
            "top_probability": round(top_probability, 4),
            "margin_top2": round(margin_top2, 4),
            "normalized_entropy": round(normalized_entropy, 4),
            "posterior_variance_top": round(posterior_variance_top, 4),
            "top_feature_coverage": round(top_coverage, 4),
            "ood_score": round(ood_score, 4),
            "ood_level": ood_level,
            "uncertainty_level": uncertainty_level,
            "abstention_recommended": abstention_recommended,
            "priority_score": priority_score,
            "posterior_topk": [
                {"domain": domain, "probability": round(probability, 4)}
                for domain, probability in ranked[:5]
            ],
            "gmm_responsibilities_topk": [
                {"domain": domain, "responsibility": round(probability, 4)}
                for domain, probability in ranked[:5]
            ],
            "similarity_details": similarity_details[:5],
            "trace": {
                "math_enabled": "1",
                "math_top_domain": top_domain,
                "math_top_probability": f"{round(top_probability, 4)}",
                "math_margin_top2": f"{round(margin_top2, 4)}",
                "math_entropy": f"{round(normalized_entropy, 4)}",
                "math_posterior_variance": f"{round(posterior_variance_top, 4)}",
                "math_uncertainty_level": uncertainty_level,
                "math_abstention_recommended": "1" if abstention_recommended else "0",
                "math_priority_score": priority_score,
                "math_ood_score": f"{round(ood_score, 4)}",
                "math_ood_level": ood_level,
                "math_domains_evaluated": str(len(domains)),
                "math_model": "cosine+l2+bayes",
            },
        }
