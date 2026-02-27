"""
Servicio de triaje clinico tipo SVM (lineal) para soporte de decision.

No reemplaza el juicio clinico ni el motor principal. Aporta:
- score lineal
- margen geometrico aproximado
- hinge loss (robustez)
- clasificacion operativa (critical/stable)
"""
from __future__ import annotations

import math
import re
import unicodedata
from typing import Any


class ClinicalSVMTriageService:
    """Capa ligera de clasificacion lineal con trazabilidad estilo SVM."""

    _TOKEN_PATTERN = re.compile(r"[a-z0-9]{3,}", flags=re.IGNORECASE)
    _NUMBER_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)?\b")

    _WEIGHTS: dict[str, float] = {
        "hemodynamic_instability": 1.8,
        "electrolyte_critical": 1.7,
        "respiratory_failure": 1.5,
        "obstetric_red_flag": 1.6,
        "neuro_red_flag": 1.6,
        "infection_severe": 1.2,
        "oncology_critical": 1.3,
        "renal_critical": 1.4,
        "pediatric_signal": 0.7,
        "stability_signal": -0.8,
    }
    _BIAS = -0.35

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        return normalized.lower().strip()

    @classmethod
    def _tokenize(cls, text: str) -> set[str]:
        return {token for token in cls._TOKEN_PATTERN.findall(cls._normalize(text))}

    @classmethod
    def _extract_features(
        cls,
        *,
        query: str,
        extracted_facts: list[str],
    ) -> dict[str, float]:
        normalized_query = cls._normalize(query)
        tokens = cls._tokenize(query)
        facts_text = " ".join(extracted_facts or [])
        normalized_facts = cls._normalize(facts_text)

        def has_any(*needles: str) -> bool:
            return any(
                needle in normalized_query or needle in normalized_facts
                for needle in needles
            )

        numbers = [
            float(item.replace(",", "."))
            for item in cls._NUMBER_PATTERN.findall(normalized_query)
        ]
        max_number = max(numbers) if numbers else 0.0

        features: dict[str, float] = {
            "hemodynamic_instability": 0.0,
            "electrolyte_critical": 0.0,
            "respiratory_failure": 0.0,
            "obstetric_red_flag": 0.0,
            "neuro_red_flag": 0.0,
            "infection_severe": 0.0,
            "oncology_critical": 0.0,
            "renal_critical": 0.0,
            "pediatric_signal": 0.0,
            "stability_signal": 0.0,
        }

        if has_any("tas ", "ta ", "hipotension", "shock", "map", "inestable"):
            features["hemodynamic_instability"] = 1.0
        if has_any("k 6", "hiperkal", "qrs ancho", "potasio", "arritmia"):
            features["electrolyte_critical"] = 1.0
        if has_any("sat", "hipox", "disnea", "cpap", "bipap", "insuficiencia respiratoria"):
            features["respiratory_failure"] = 1.0
        if has_any("gestante", "preecl", "eclamps", "fosfen", "34 semanas"):
            features["obstetric_red_flag"] = 1.0
        if has_any("ictus", "focal", "anisocoria", "convulsion", "glasgow"):
            features["neuro_red_flag"] = 1.0
        if has_any("sepsis", "lactato", "fiebre", "febril", "qsofa"):
            features["infection_severe"] = 1.0
        if has_any("neutropenia", "oncolog", "quimioterapia", "irae"):
            features["oncology_critical"] = 1.0
        if has_any("oliguria", "anuria", "creatinina", "dialisis", "nefro", "renal"):
            features["renal_critical"] = 1.0
        if has_any("pediatr", "neonat", "lactante", "nino", "nina"):
            features["pediatric_signal"] = 1.0

        # Señal de estabilidad: ausencia de red flags con mensaje de control.
        red_flag_sum = sum(
            features[name]
            for name in (
                "hemodynamic_instability",
                "electrolyte_critical",
                "respiratory_failure",
                "obstetric_red_flag",
                "neuro_red_flag",
                "infection_severe",
                "oncology_critical",
                "renal_critical",
            )
        )
        if red_flag_sum == 0 and has_any("estable", "control", "seguimiento", "monitorizacion"):
            features["stability_signal"] = 1.0

        # Ajuste numerico conservador (ej. TAS muy baja o K alta)
        if max_number >= 6.0 and "k" in tokens:
            features["electrolyte_critical"] = max(features["electrolyte_critical"], 1.0)
        if "tas" in tokens and any(value <= 90 for value in numbers):
            features["hemodynamic_instability"] = max(features["hemodynamic_instability"], 1.0)

        return features

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
        features = cls._extract_features(query=query, extracted_facts=extracted_facts)
        score = cls._BIAS
        for name, value in features.items():
            score += cls._WEIGHTS.get(name, 0.0) * float(value)

        norm_w = math.sqrt(sum(weight * weight for weight in cls._WEIGHTS.values())) or 1.0
        margin = abs(score) / norm_w
        predicted_label = 1 if score >= 0 else -1
        predicted_class = "critical" if predicted_label == 1 else "stable"
        hinge_loss = max(0.0, 1.0 - (predicted_label * score))

        if score >= 1.8:
            priority_score = "high"
        elif score >= 0.7:
            priority_score = "medium"
        else:
            priority_score = "low"

        support_signals = [key for key, value in features.items() if value > 0]
        trace = {
            "svm_enabled": "1",
            "svm_score": f"{round(score, 4)}",
            "svm_margin": f"{round(margin, 4)}",
            "svm_hinge_loss": f"{round(hinge_loss, 4)}",
            "svm_class": predicted_class,
            "svm_priority_score": priority_score,
            "svm_support_signals": ",".join(support_signals) if support_signals else "none",
            "svm_domains_considered": ",".join(matched_domains) if matched_domains else "none",
            "svm_effective_specialty": effective_specialty or "general",
        }

        return {
            "enabled": True,
            "score": round(score, 4),
            "margin": round(margin, 4),
            "hinge_loss": round(hinge_loss, 4),
            "predicted_class": predicted_class,
            "priority_score": priority_score,
            "support_signals": support_signals,
            "trace": trace,
            "memory_facts": [
                f"svm_class:{predicted_class}",
                f"svm_priority:{priority_score}",
            ],
        }
