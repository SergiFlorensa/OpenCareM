"""
Motor operativo de riesgo cardiovascular para urgencias.

No diagnostica: orienta estratificacion inicial y acciones para validacion humana.
"""
from app.schemas.cardio_risk_protocol import (
    CardioRiskProtocolRecommendation,
    CardioRiskProtocolRequest,
)


class CardioRiskSupportService:
    """Construye recomendaciones operativas de riesgo cardiovascular."""

    @staticmethod
    def _score(payload: CardioRiskProtocolRequest) -> int:
        score = 0
        if payload.age_years >= 75:
            score += 4
        elif payload.age_years >= 65:
            score += 3
        elif payload.age_years >= 55:
            score += 2
        elif payload.age_years >= 45:
            score += 1

        if payload.smoker:
            score += 2

        if payload.systolic_bp >= 160:
            score += 2
        elif payload.systolic_bp >= 140:
            score += 1

        if payload.non_hdl_mg_dl >= 220:
            score += 3
        elif payload.non_hdl_mg_dl >= 190:
            score += 2
        elif payload.non_hdl_mg_dl >= 160:
            score += 1

        if payload.apob_mg_dl is not None:
            if payload.apob_mg_dl >= 130:
                score += 2
            elif payload.apob_mg_dl >= 100:
                score += 1

        if payload.diabetes:
            score += 2
        if payload.chronic_kidney_disease:
            score += 2
        if payload.family_history_premature_cvd:
            score += 1
        if payload.chronic_inflammatory_state:
            score += 1
        return score

    @staticmethod
    def _risk_level(payload: CardioRiskProtocolRequest, score: int) -> str:
        if payload.established_atherosclerotic_cvd:
            return "very_high"
        if score >= 10:
            return "very_high"
        if score >= 7:
            return "high"
        if score >= 4:
            return "moderate"
        return "low"

    @staticmethod
    def _estimated_10y_risk_percent(risk_level: str) -> float:
        mapping = {
            "low": 4.0,
            "moderate": 9.0,
            "high": 18.0,
            "very_high": 30.0,
        }
        return mapping.get(risk_level, 9.0)

    @staticmethod
    def _targets(risk_level: str) -> tuple[int, int]:
        ldl_target_map = {
            "very_high": 55,
            "high": 70,
            "moderate": 100,
            "low": 116,
        }
        ldl_target = ldl_target_map.get(risk_level, 100)
        non_hdl_target = ldl_target + 30
        return ldl_target, non_hdl_target

    @staticmethod
    def _intensive_lifestyle_required(
        payload: CardioRiskProtocolRequest,
        risk_level: str,
        non_hdl_target_required: bool,
    ) -> bool:
        if risk_level in {"high", "very_high"}:
            return True
        if payload.smoker or payload.diabetes:
            return True
        return non_hdl_target_required

    @staticmethod
    def _pharmacologic_strategy_suggested(
        payload: CardioRiskProtocolRequest,
        risk_level: str,
        non_hdl_target_required: bool,
    ) -> bool:
        if risk_level in {"high", "very_high"}:
            return True
        if payload.established_atherosclerotic_cvd:
            return True
        if payload.diabetes and non_hdl_target_required:
            return True
        return payload.non_hdl_mg_dl >= 190

    @staticmethod
    def _priority_actions(
        payload: CardioRiskProtocolRequest,
        *,
        risk_level: str,
        non_hdl_target_required: bool,
        pharmacologic_strategy_suggested: bool,
        intensive_lifestyle_required: bool,
    ) -> list[str]:
        actions: list[str] = []
        if non_hdl_target_required:
            actions.append(
                "Priorizar reduccion de colesterol no-HDL y confirmar ApoB segun disponibilidad."
            )
        else:
            actions.append(
                "Mantener control de riesgo cardiovascular y seguimiento de no-HDL en reevaluacion."
            )

        if intensive_lifestyle_required:
            actions.append(
                "Activar intervencion intensiva en estilo de vida: nutricion, "
                "actividad fisica y cese tabaquico."
            )

        if pharmacologic_strategy_suggested:
            if payload.statin_intolerance:
                actions.append(
                    "Valorar estrategia hipolipemiante alternativa por intolerancia a estatinas."
                )
            else:
                actions.append(
                    "Valorar inicio o intensificacion de terapia hipolipemiante "
                    "segun estrato de riesgo."
                )
        elif payload.on_lipid_lowering_therapy:
            actions.append("Revisar adherencia y respuesta a terapia hipolipemiante actual.")

        if risk_level == "very_high":
            actions.append("Escalar priorizacion clinica por riesgo cardiovascular muy alto.")
        return actions

    @staticmethod
    def _additional_markers_recommended(
        payload: CardioRiskProtocolRequest,
        *,
        non_hdl_target_required: bool,
    ) -> list[str]:
        markers: list[str] = []
        if payload.apob_mg_dl is None:
            markers.append("Solicitar ApoB para conteo de particulas aterogenicas.")
        if payload.triglycerides_mg_dl is not None and payload.triglycerides_mg_dl >= 150:
            markers.append("Revisar colesterol remanente y contexto de resistencia a insulina.")
        if non_hdl_target_required:
            markers.append("Programar control analitico de no-HDL en ventana corta.")
        return markers

    @staticmethod
    def _alerts(
        payload: CardioRiskProtocolRequest,
        *,
        risk_level: str,
        non_hdl_target_required: bool,
    ) -> list[str]:
        alerts: list[str] = []
        if risk_level == "very_high":
            alerts.append("Riesgo cardiovascular muy alto: requiere validacion clinica inmediata.")
        elif risk_level == "high":
            alerts.append("Riesgo cardiovascular alto: evitar demoras en plan de control.")

        if non_hdl_target_required and payload.non_hdl_mg_dl >= 220:
            alerts.append("No-HDL marcadamente elevado.")
        if payload.apob_mg_dl is not None and payload.apob_mg_dl >= 130:
            alerts.append("ApoB alto: carga aterogenica elevada.")
        if payload.smoker:
            alerts.append("Tabaquismo activo incrementa riesgo residual.")
        return alerts

    @staticmethod
    def build_recommendation(
        payload: CardioRiskProtocolRequest,
    ) -> CardioRiskProtocolRecommendation:
        """Genera recomendacion operativa cardiovascular para validacion humana."""
        score = CardioRiskSupportService._score(payload)
        risk_level = CardioRiskSupportService._risk_level(payload, score)
        estimated_10y_risk_percent = CardioRiskSupportService._estimated_10y_risk_percent(
            risk_level
        )
        ldl_target_mg_dl, non_hdl_target_mg_dl = CardioRiskSupportService._targets(risk_level)
        non_hdl_target_required = payload.non_hdl_mg_dl > non_hdl_target_mg_dl
        intensive_lifestyle_required = CardioRiskSupportService._intensive_lifestyle_required(
            payload,
            risk_level,
            non_hdl_target_required,
        )
        pharmacologic_strategy_suggested = (
            CardioRiskSupportService._pharmacologic_strategy_suggested(
                payload,
                risk_level,
                non_hdl_target_required,
            )
        )
        return CardioRiskProtocolRecommendation(
            risk_level=risk_level,
            estimated_10y_risk_percent=estimated_10y_risk_percent,
            ldl_target_mg_dl=ldl_target_mg_dl,
            non_hdl_target_mg_dl=non_hdl_target_mg_dl,
            non_hdl_target_required=non_hdl_target_required,
            intensive_lifestyle_required=intensive_lifestyle_required,
            pharmacologic_strategy_suggested=pharmacologic_strategy_suggested,
            priority_actions=CardioRiskSupportService._priority_actions(
                payload,
                risk_level=risk_level,
                non_hdl_target_required=non_hdl_target_required,
                pharmacologic_strategy_suggested=pharmacologic_strategy_suggested,
                intensive_lifestyle_required=intensive_lifestyle_required,
            ),
            additional_markers_recommended=CardioRiskSupportService._additional_markers_recommended(
                payload,
                non_hdl_target_required=non_hdl_target_required,
            ),
            alerts=CardioRiskSupportService._alerts(
                payload,
                risk_level=risk_level,
                non_hdl_target_required=non_hdl_target_required,
            ),
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. Requiere validacion clinica humana."
            ),
        )
