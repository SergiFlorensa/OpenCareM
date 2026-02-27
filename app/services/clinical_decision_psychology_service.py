"""
Servicio de apoyo psicologico para decision clinica.

Incluye dos capas ligeras y locales:
- Escala psicofisica tipo Fechner para intensidad/salto percibido de sintomas.
- Framing de riesgo inspirado en Prospect Theory para comunicacion operativa.

No realiza diagnostico ni reemplaza juicio clinico.
"""

from __future__ import annotations

import math
import re
import unicodedata
from typing import Any


class ClinicalDecisionPsychologyService:
    """Calcula señales psicofisicas y de comunicacion de riesgo."""

    _PAIN_RANGE_PATTERN = re.compile(
        r"(?:dolor|escala)\s*(?:de\s*)?(\d{1,2})\s*(?:a|-)\s*(\d{1,2})(?:\s*/\s*10)?",
        flags=re.IGNORECASE,
    )
    _PAIN_LEVEL_PATTERN = re.compile(
        r"(?:dolor(?:\s*(?:nivel|intensidad))?\s*)(\d{1,2})(?:\s*/\s*10)?",
        flags=re.IGNORECASE,
    )
    _TA_PATTERN = re.compile(
        r"(?:\bta\b|tension arterial)\s*[:=]?\s*(\d{2,3})\s*/\s*(\d{2,3})",
        flags=re.IGNORECASE,
    )
    _SAT_PATTERN = re.compile(
        r"(?:\bsat(?:o2)?\b|\bspo2\b)\s*[:=]?\s*(\d{2,3})%?",
        flags=re.IGNORECASE,
    )
    _POTASSIUM_PATTERN = re.compile(
        r"\bk(?:\s*\+)?\s*[:=]?\s*(\d+(?:[.,]\d+)?)",
        flags=re.IGNORECASE,
    )

    _RED_FLAG_TERMS = (
        "shock",
        "inestable",
        "inestabilidad",
        "anuria",
        "oliguria",
        "disnea intensa",
        "convulsion",
        "hemorragia",
        "hemorragico",
        "cefalea intensa",
        "fosfenos",
    )

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        return normalized.lower().strip()

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))

    @classmethod
    def _fechner_intensity(cls, level_0_10: float) -> float:
        capped = cls._clamp(level_0_10, 0.0, 10.0)
        return math.log1p(capped) / math.log1p(10.0)

    @classmethod
    def _parse_pain_metrics(cls, query: str) -> tuple[float | None, float | None]:
        range_match = cls._PAIN_RANGE_PATTERN.search(query)
        if range_match:
            start = float(range_match.group(1))
            end = float(range_match.group(2))
            start_score = cls._fechner_intensity(start)
            end_score = cls._fechner_intensity(end)
            return end_score, abs(end_score - start_score)

        level_match = cls._PAIN_LEVEL_PATTERN.search(query)
        if level_match:
            level = float(level_match.group(1))
            return cls._fechner_intensity(level), None
        return None, None

    @classmethod
    def analyze_query(
        cls,
        *,
        query: str,
        matched_domains: list[str],
        effective_specialty: str,
    ) -> dict[str, Any]:
        normalized_query = cls._normalize(query)
        primary_domain = matched_domains[0] if matched_domains else effective_specialty

        fechner_intensity, fechner_change = cls._parse_pain_metrics(query)
        risk_score = 0.0
        signals: list[str] = []

        ta_match = cls._TA_PATTERN.search(query)
        if ta_match:
            systolic = int(ta_match.group(1))
            diastolic = int(ta_match.group(2))
            if systolic <= 90:
                risk_score += 0.45
                signals.append("hypotension_critical")
            if systolic >= 160 or diastolic >= 110:
                risk_score += 0.35
                signals.append("hypertension_severe")

        sat_match = cls._SAT_PATTERN.search(query)
        if sat_match:
            saturation = int(sat_match.group(1))
            if saturation <= 91:
                risk_score += 0.4
                signals.append("oxygenation_critical")
            elif saturation <= 94:
                risk_score += 0.2
                signals.append("oxygenation_warning")

        potassium_match = cls._POTASSIUM_PATTERN.search(query)
        if potassium_match:
            potassium = float(potassium_match.group(1).replace(",", "."))
            if potassium >= 6.0:
                risk_score += 0.45
                signals.append("hyperkalemia_critical")
            elif potassium >= 5.5:
                risk_score += 0.25
                signals.append("hyperkalemia_warning")

        if fechner_intensity is not None and fechner_intensity >= 0.82:
            risk_score += 0.15
            signals.append("pain_high_perceived_intensity")
        if fechner_change is not None and fechner_change >= 0.18:
            risk_score += 0.15
            signals.append("pain_perceived_worsening")

        for term in cls._RED_FLAG_TERMS:
            if term in normalized_query:
                risk_score += 0.08
                signals.append(f"red_flag:{term.replace(' ', '_')}")

        if primary_domain == "gynecology_obstetrics" and "hypertension_severe" in signals:
            risk_score += 0.1
            signals.append("obstetric_hypertensive_priority")

        risk_score = cls._clamp(risk_score, 0.0, 1.0)
        if risk_score >= 0.60:
            risk_level = "high"
            frame = "loss_avoidance_critical"
            hint = (
                "Prioriza decisiones que minimicen perdida critica (deterioro evitable) "
                "antes que beneficios diferidos."
            )
        elif risk_score >= 0.35:
            risk_level = "medium"
            frame = "loss_avoidance_moderate"
            hint = (
                "Explica el coste de demorar medidas clave y mantiene monitorizacion "
                "con revaluacion temprana."
            )
        else:
            risk_level = "low"
            frame = "gain_focus_monitoring"
            hint = "Mantener vigilancia estructurada y reforzar criterios de reconsulta."

        memory_facts = [f"prospect_frame:{frame}", f"prospect_risk:{risk_level}"]
        if fechner_intensity is not None:
            memory_facts.append(f"fechner_intensity:{fechner_intensity:.3f}")
        if fechner_change is not None:
            memory_facts.append(f"fechner_change:{fechner_change:.3f}")

        return {
            "domain": primary_domain,
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "prospect_frame": frame,
            "communication_hint": hint,
            "fechner_intensity": (
                round(fechner_intensity, 3) if fechner_intensity is not None else None
            ),
            "fechner_change": round(fechner_change, 3) if fechner_change is not None else None,
            "signals": signals[:8],
            "memory_facts": memory_facts,
        }
