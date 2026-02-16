"""
Motor operativo de sepsis para urgencias.

No diagnostica: prioriza bundle de primera hora y escalado por riesgo.
"""
from app.schemas.sepsis_protocol import (
    SepsisProtocolRecommendation,
    SepsisProtocolRequest,
)


class SepsisProtocolService:
    """Construye recomendaciones operativas tempranas para sepsis."""

    @staticmethod
    def _qsofa_score(payload: SepsisProtocolRequest) -> int:
        score = 0
        if payload.respiratory_rate_rpm is not None and payload.respiratory_rate_rpm >= 22:
            score += 1
        if payload.systolic_bp is not None and payload.systolic_bp <= 100:
            score += 1
        if payload.altered_mental_status:
            score += 1
        return score

    @staticmethod
    def _high_sepsis_risk(payload: SepsisProtocolRequest, qsofa_score: int) -> bool:
        return bool(payload.suspected_infection and qsofa_score >= 2)

    @staticmethod
    def _septic_shock_suspected(payload: SepsisProtocolRequest) -> bool:
        lactate_flag = payload.lactate_mmol_l is not None and payload.lactate_mmol_l >= 4
        map_flag = payload.map_mmhg is not None and payload.map_mmhg < 65
        vasopressor_flag = payload.vasopressor_started
        return bool(lactate_flag or (map_flag and vasopressor_flag))

    @staticmethod
    def _bundle_actions(payload: SepsisProtocolRequest, high_risk: bool) -> list[str]:
        actions: list[str] = []
        if high_risk:
            if not payload.blood_cultures_collected:
                actions.append("Extraer hemocultivos antes de antibiotico si no retrasa inicio.")
            if not payload.antibiotics_started:
                actions.append("Iniciar antibioterapia de amplio espectro en <1 hora.")
            if (payload.fluid_bolus_ml_per_kg or 0) < 30:
                actions.append("Completar fluidoterapia inicial hasta 30 ml/kg (cristaloides).")
            if payload.lactate_mmol_l is None:
                actions.append("Solicitar lactato inicial y planificar control seriado.")
        else:
            actions.append("Mantener reevaluacion clinica y vigilancia de disfuncion organica.")
        return actions

    @staticmethod
    def _escalation_actions(payload: SepsisProtocolRequest, shock_suspected: bool) -> list[str]:
        actions: list[str] = []
        if shock_suspected:
            actions.append("Escalar a circuito de shock septico y avisar equipo senior/UCI.")
            actions.append("Objetivo PAM >=65 mmHg con noradrenalina si refractario a fluidos.")
            actions.append("Monitorizar lactato y perfusion de forma estrecha.")
        if (
            payload.time_since_detection_minutes is not None
            and payload.time_since_detection_minutes > 60
        ):
            actions.append("Revisar demora del bundle de sepsis y corregir cuellos de botella.")
        return actions

    @staticmethod
    def _alerts(
        payload: SepsisProtocolRequest,
        high_risk: bool,
        shock_suspected: bool,
    ) -> list[str]:
        alerts: list[str] = []
        if not payload.suspected_infection:
            alerts.append("Sin infeccion sospechada: validar pertinencia del protocolo.")
            return alerts

        if high_risk:
            alerts.append("qSOFA >=2 con infeccion sospechada: alto riesgo de sepsis.")
        if shock_suspected:
            alerts.append("Criterios operativos compatibles con shock septico.")
        if payload.lactate_mmol_l is not None and payload.lactate_mmol_l > 2:
            alerts.append("Lactato elevado: requiere reevaluacion y control de tendencia.")
        if (
            payload.time_since_detection_minutes is not None
            and payload.time_since_detection_minutes > 60
        ):
            alerts.append("Ventana >60 min desde deteccion: riesgo de retraso terapeutico.")
        return alerts

    @staticmethod
    def build_recommendation(
        payload: SepsisProtocolRequest,
    ) -> SepsisProtocolRecommendation:
        """Genera recomendacion operativa de sepsis para validacion humana."""
        qsofa_score = SepsisProtocolService._qsofa_score(payload)
        high_risk = SepsisProtocolService._high_sepsis_risk(payload, qsofa_score)
        shock_suspected = SepsisProtocolService._septic_shock_suspected(payload)
        return SepsisProtocolRecommendation(
            qsofa_score=qsofa_score,
            high_sepsis_risk=high_risk,
            septic_shock_suspected=shock_suspected,
            one_hour_bundle_actions=SepsisProtocolService._bundle_actions(payload, high_risk),
            escalation_actions=SepsisProtocolService._escalation_actions(payload, shock_suspected),
            alerts=SepsisProtocolService._alerts(payload, high_risk, shock_suspected),
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. Requiere validacion clinica humana."
            ),
        )
