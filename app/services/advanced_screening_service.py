"""
Motor de screening operativo avanzado para urgencias.

Incluye reglas interpretables de riesgo geriatrico, cribado precedente,
alertas con control de fatiga y criterios operativos de COVID persistente.
"""
from collections.abc import Iterable
from typing import Literal

from app.schemas.advanced_screening import (
    AdvancedScreeningRecommendation,
    AdvancedScreeningRequest,
)


class AdvancedScreeningService:
    """Construye recomendacion de screening interpretable y accionable."""

    _HIV_INDICATOR_KEYWORDS = {
        "its",
        "neumonia",
        "sindrome mononucleosico",
        "perdida de peso",
        "plaquetopenia",
        "fiebre sin foco",
    }

    @staticmethod
    def _contains_keywords(values: Iterable[str], keywords: set[str]) -> bool:
        normalized = " ".join(values).lower()
        return any(keyword in normalized for keyword in keywords)

    @staticmethod
    def _geriatric_risk_level(
        payload: AdvancedScreeningRequest,
    ) -> Literal["low", "medium", "high"]:
        if payload.age_years < 65:
            return "low"

        risk_score = 0
        if payload.systolic_bp is not None and payload.systolic_bp < 115:
            risk_score += 2
        if payload.can_walk_independently is False:
            risk_score += 1
        if (
            payload.oxygen_saturation_percent is not None
            and payload.oxygen_saturation_percent < 92
        ):
            risk_score += 1
        if payload.heart_rate_bpm is not None and payload.heart_rate_bpm > 110:
            risk_score += 1
        if payload.sodium_mmol_l is not None and (
            payload.sodium_mmol_l < 130 or payload.sodium_mmol_l > 150
        ):
            risk_score += 1
        if payload.glucose_mg_dl is not None and (
            payload.glucose_mg_dl < 70 or payload.glucose_mg_dl > 250
        ):
            risk_score += 1

        if risk_score >= 4:
            return "high"
        if risk_score >= 2:
            return "medium"
        return "low"

    @staticmethod
    def _build_screening_actions(payload: AdvancedScreeningRequest) -> list[str]:
        actions: list[str] = []
        complaints_or_conditions = payload.chief_complaints + payload.known_conditions
        if AdvancedScreeningService._contains_keywords(
            complaints_or_conditions, AdvancedScreeningService._HIV_INDICATOR_KEYWORDS
        ):
            actions.append("Sugerir cribado VIH por indicadores clinicos en urgencias.")
            actions.append("Registrar consentimiento informado para serologia de cribado.")

        if "sepsis" in " ".join(complaints_or_conditions).lower() or (
            payload.heart_rate_bpm and payload.heart_rate_bpm > 120
        ):
            actions.append("Activar ruta de sepsis temprana y monitorizacion estrecha.")

        if not actions:
            actions.append("Mantener vigilancia estandar y reevaluacion clinica programada.")
        return actions

    @staticmethod
    def _evaluate_long_acting_candidate(
        payload: AdvancedScreeningRequest,
    ) -> tuple[bool, str | None]:
        eligible_context = payload.infection_context in {
            "endocarditis",
            "osteomielitis",
            "infeccion_piel_tejidos_blandos",
        }
        if payload.stable_after_acute_phase and eligible_context:
            return (
                True,
                "Paciente estable tras fase aguda en contexto elegible: "
                "valorar estrategia long-acting para liberar cama.",
            )
        return False, None

    @staticmethod
    def _evaluate_persistent_covid(
        payload: AdvancedScreeningRequest,
    ) -> tuple[bool, list[str]]:
        suspected = bool(
            payload.immunosuppressed
            and payload.persistent_positive_days is not None
            and payload.persistent_positive_days >= 14
            and payload.persistent_symptoms
            and payload.imaging_compatible_with_persistent_infection
        )
        if not suspected:
            return False, []
        return True, [
            "Escalar caso a infecciosas por posible COVID persistente en inmunodeprimido.",
            "Valorar estrategia antiviral combinada segun protocolo institucional "
            "y validacion especialista.",
        ]

    @staticmethod
    def _build_alert_pool(
        payload: AdvancedScreeningRequest,
        geriatric_risk_level: str,
        persistent_covid_suspected: bool,
    ) -> list[tuple[str, str, str]]:
        alerts: list[tuple[str, str, str]] = []
        if (
            payload.age_years >= 65
            and payload.systolic_bp is not None
            and payload.systolic_bp < 115
        ):
            alerts.append(
                ("geri_pas_low", "high", "PAS <115 en mayor de 65: riesgo oculto elevado.")
            )
        if geriatric_risk_level == "high":
            alerts.append(
                (
                    "geri_high_risk",
                    "high",
                    "Riesgo geriatrico alto: priorizar reevaluacion temprana.",
                )
            )
        if payload.can_walk_independently is False:
            alerts.append(
                (
                    "mobility_risk",
                    "medium",
                    "No deambula independientemente: elevar vigilancia funcional.",
                )
            )
        if (
            payload.oxygen_saturation_percent is not None
            and payload.oxygen_saturation_percent < 92
        ):
            alerts.append(
                (
                    "spo2_low",
                    "high",
                    "Saturacion baja: priorizar valoracion respiratoria inmediata.",
                )
            )
        if AdvancedScreeningService._contains_keywords(
            payload.chief_complaints + payload.known_conditions,
            AdvancedScreeningService._HIV_INDICATOR_KEYWORDS,
        ):
            alerts.append(
                ("hiv_indicator", "medium", "Indicadores de cribado VIH presentes en triaje.")
            )
        if persistent_covid_suspected:
            alerts.append(
                (
                    "persistent_covid",
                    "high",
                    "Criterios operativos de COVID persistente detectados.",
                )
            )
        return alerts

    @staticmethod
    def _apply_alert_fatigue_control(
        alert_pool: list[tuple[str, str, str]],
    ) -> tuple[list[str], int, int]:
        # Deduplicamos por clave para no repetir la misma senal varias veces.
        unique_by_key: dict[str, tuple[str, str]] = {}
        for key, severity, message in alert_pool:
            current = unique_by_key.get(key)
            if current is None or (current[0] == "medium" and severity == "high"):
                unique_by_key[key] = (severity, message)

        # Priorizamos severidad y limitamos panel a 5 alertas de alto valor.
        ordered = sorted(
            unique_by_key.values(),
            key=lambda item: 0 if item[0] == "high" else 1,
        )
        max_visible = 5
        visible = [item[1] for item in ordered[:max_visible]]
        generated = len(alert_pool)
        suppressed = max(0, generated - len(visible))
        return visible, generated, suppressed

    @staticmethod
    def build_recommendation(
        payload: AdvancedScreeningRequest,
    ) -> AdvancedScreeningRecommendation:
        """Genera recomendacion operativa con reglas de screening interpretables."""
        geriatric_risk = AdvancedScreeningService._geriatric_risk_level(payload)
        screening_actions = AdvancedScreeningService._build_screening_actions(payload)
        long_acting_candidate, long_acting_rationale = (
            AdvancedScreeningService._evaluate_long_acting_candidate(payload)
        )
        persistent_covid_suspected, persistent_covid_actions = (
            AdvancedScreeningService._evaluate_persistent_covid(payload)
        )
        alert_pool = AdvancedScreeningService._build_alert_pool(
            payload=payload,
            geriatric_risk_level=geriatric_risk,
            persistent_covid_suspected=persistent_covid_suspected,
        )
        alerts, generated, suppressed = AdvancedScreeningService._apply_alert_fatigue_control(
            alert_pool
        )

        return AdvancedScreeningRecommendation(
            geriatric_risk_level=geriatric_risk,
            screening_actions=screening_actions,
            alerts=alerts,
            alerts_generated_total=generated,
            alerts_suppressed_total=suppressed,
            long_acting_candidate=long_acting_candidate,
            long_acting_rationale=long_acting_rationale,
            persistent_covid_suspected=persistent_covid_suspected,
            persistent_covid_actions=persistent_covid_actions,
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. Requiere validacion clinica humana."
            ),
        )
