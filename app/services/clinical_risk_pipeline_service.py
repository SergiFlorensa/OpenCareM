"""
Pipeline clinico ligero para riesgo operativo (fase actual).

Incluye:
- extraccion de features desde texto
- imputacion simple (medianas de referencia)
- escalado estandar
- clasificacion probabilistica (logistica)
- deteccion basica de anomalias (z-score agregado)
"""
from __future__ import annotations

import math
import re
import unicodedata
from typing import Any


class ClinicalRiskPipelineService:
    """Motor probabilistico local para priorizacion de riesgo clinico."""

    _FEATURE_ORDER = (
        "systolic_bp",
        "potassium",
        "creatinine",
        "oliguria_flag",
        "qrs_wide_flag",
        "fever_flag",
        "neutropenia_flag",
        "hypoxemia_flag",
    )
    _MEDIANS = {
        "systolic_bp": 118.0,
        "potassium": 4.1,
        "creatinine": 1.0,
        "oliguria_flag": 0.0,
        "qrs_wide_flag": 0.0,
        "fever_flag": 0.0,
        "neutropenia_flag": 0.0,
        "hypoxemia_flag": 0.0,
    }
    _MEANS = {
        "systolic_bp": 118.0,
        "potassium": 4.2,
        "creatinine": 1.1,
        "oliguria_flag": 0.1,
        "qrs_wide_flag": 0.05,
        "fever_flag": 0.2,
        "neutropenia_flag": 0.08,
        "hypoxemia_flag": 0.15,
    }
    _STDS = {
        "systolic_bp": 18.0,
        "potassium": 0.8,
        "creatinine": 0.7,
        "oliguria_flag": 0.3,
        "qrs_wide_flag": 0.2,
        "fever_flag": 0.4,
        "neutropenia_flag": 0.27,
        "hypoxemia_flag": 0.36,
    }
    _COEFS = {
        "systolic_bp": -0.65,
        "potassium": 0.95,
        "creatinine": 0.72,
        "oliguria_flag": 0.88,
        "qrs_wide_flag": 0.91,
        "fever_flag": 0.36,
        "neutropenia_flag": 0.64,
        "hypoxemia_flag": 0.77,
    }
    _BIAS = -0.2

    _RE_TA = re.compile(r"\b(?:ta|tas)\s*[:=]?\s*(\d{2,3})(?:\s*/\s*(\d{2,3}))?")
    _RE_POTASSIUM = re.compile(r"\b(?:k|potasio)\s*[:=]?\s*(\d+(?:[.,]\d+)?)")
    _RE_CREATININE = re.compile(r"\bcreatinina(?:\s*(?:actual|act))?\s*[:=]?\s*(\d+(?:[.,]\d+)?)")
    _RE_SATO2 = re.compile(r"\b(?:sat(?:o2)?|saturacion)\s*[:=]?\s*(\d{2,3})")

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        return normalized.lower().strip()

    @staticmethod
    def _parse_float(raw: str | None) -> float | None:
        if raw is None:
            return None
        value = raw.replace(",", ".").strip()
        try:
            return float(value)
        except ValueError:
            return None

    @classmethod
    def _extract_raw_features(
        cls,
        *,
        query: str,
        extracted_facts: list[str],
    ) -> tuple[dict[str, float | None], list[str]]:
        text = cls._normalize(query)
        facts_text = cls._normalize(" ".join(extracted_facts or []))
        missing: list[str] = []

        raw: dict[str, float | None] = {
            "systolic_bp": None,
            "potassium": None,
            "creatinine": None,
            "oliguria_flag": 1.0 if "oliguria" in text or "anuria" in text else 0.0,
            "qrs_wide_flag": 1.0 if "qrs ancho" in text else 0.0,
            "fever_flag": 1.0 if "fiebre" in text or "febril" in text else 0.0,
            "neutropenia_flag": 1.0 if "neutropenia" in text else 0.0,
            "hypoxemia_flag": 1.0 if "hipox" in text or "sat" in text else 0.0,
        }

        ta_match = cls._RE_TA.search(text)
        if ta_match:
            raw["systolic_bp"] = cls._parse_float(ta_match.group(1))

        potassium_match = cls._RE_POTASSIUM.search(text)
        if potassium_match:
            raw["potassium"] = cls._parse_float(potassium_match.group(1))

        creat_match = cls._RE_CREATININE.search(text)
        if creat_match:
            raw["creatinine"] = cls._parse_float(creat_match.group(1))

        sat_match = cls._RE_SATO2.search(text)
        sat_value = cls._parse_float(sat_match.group(1) if sat_match else None)
        if sat_value is not None and sat_value < 92:
            raw["hypoxemia_flag"] = 1.0

        if "logic_rule:nephro_hyperkalemia_critical" in facts_text:
            raw["potassium"] = raw["potassium"] if raw["potassium"] is not None else 6.0
            raw["qrs_wide_flag"] = 1.0

        for feature in cls._FEATURE_ORDER:
            if raw[feature] is None:
                missing.append(feature)

        return raw, missing

    @classmethod
    def _impute_and_scale(
        cls,
        raw: dict[str, float | None],
    ) -> tuple[dict[str, float], dict[str, float]]:
        imputed: dict[str, float] = {}
        scaled: dict[str, float] = {}
        for feature in cls._FEATURE_ORDER:
            value = raw.get(feature)
            if value is None:
                value = cls._MEDIANS[feature]
            imputed[feature] = float(value)
            scaled[feature] = (
                imputed[feature] - cls._MEANS[feature]
            ) / max(cls._STDS[feature], 1e-6)
        return imputed, scaled

    @classmethod
    def _logistic_probability(cls, scaled: dict[str, float]) -> tuple[float, float]:
        linear = cls._BIAS
        for feature in cls._FEATURE_ORDER:
            linear += cls._COEFS[feature] * scaled[feature]
        probability = 1.0 / (1.0 + math.exp(-linear))
        return linear, probability

    @staticmethod
    def _anom_score(scaled: dict[str, float]) -> float:
        if not scaled:
            return 0.0
        return sum(abs(value) for value in scaled.values()) / len(scaled)

    @classmethod
    def analyze_query(
        cls,
        *,
        query: str,
        matched_domains: list[str],
        effective_specialty: str,
        extracted_facts: list[str],
    ) -> dict[str, Any]:
        raw, missing = cls._extract_raw_features(query=query, extracted_facts=extracted_facts)
        imputed, scaled = cls._impute_and_scale(raw)
        linear, probability = cls._logistic_probability(scaled)
        anomaly_score = cls._anom_score(scaled)
        anomaly_flag = anomaly_score >= 1.75

        if probability >= 0.75:
            priority = "high"
        elif probability >= 0.45:
            priority = "medium"
        else:
            priority = "low"

        trace = {
            "risk_pipeline_enabled": "1",
            "risk_model_linear_score": f"{round(linear, 4)}",
            "risk_model_probability": f"{round(probability, 4)}",
            "risk_model_priority": priority,
            "risk_model_features_missing": ",".join(missing) if missing else "none",
            "risk_model_anomaly_score": f"{round(anomaly_score, 4)}",
            "risk_model_anomaly_flag": "1" if anomaly_flag else "0",
            "risk_model_domains_considered": (
                ",".join(matched_domains) if matched_domains else "none"
            ),
            "risk_model_effective_specialty": effective_specialty or "general",
        }

        return {
            "enabled": True,
            "linear_score": round(linear, 4),
            "probability": round(probability, 4),
            "priority": priority,
            "anomaly_score": round(anomaly_score, 4),
            "anomaly_flag": anomaly_flag,
            "missing_features": missing,
            "imputed_features": imputed,
            "trace": trace,
            "memory_facts": [
                f"risk_probability:{round(probability, 3)}",
                f"risk_priority:{priority}",
                f"risk_anomaly:{1 if anomaly_flag else 0}",
            ],
        }
