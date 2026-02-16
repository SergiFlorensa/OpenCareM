"""
Motor operativo para SCASEST en urgencias.

No diagnostica: orienta pruebas iniciales, tratamiento temprano y escalado.
"""
from app.schemas.scasest_protocol import (
    ScasestProtocolRecommendation,
    ScasestProtocolRequest,
)


class ScasestProtocolService:
    """Construye recomendaciones operativas para sospecha de SCASEST."""

    @staticmethod
    def _suspected(payload: ScasestProtocolRequest) -> bool:
        symptoms = payload.chest_pain_typical or payload.dyspnea or payload.syncope
        objective = (
            payload.ecg_st_depression
            or payload.ecg_t_inversion
            or payload.troponin_positive
        )
        return bool(symptoms and objective)

    @staticmethod
    def _high_risk(payload: ScasestProtocolRequest, suspected: bool) -> bool:
        if not suspected:
            return False
        if payload.hemodynamic_instability or payload.ventricular_arrhythmias:
            return True
        if payload.refractory_angina:
            return True
        if payload.grace_score is not None and payload.grace_score > 140:
            return True
        return False

    @staticmethod
    def _diagnostic_actions(payload: ScasestProtocolRequest, suspected: bool) -> list[str]:
        if not suspected:
            return ["Reevaluar diagnostico diferencial de dolor toracico."]

        actions = [
            "Realizar ECG seriado y monitorizacion continua.",
            "Solicitar troponinas seriadas y analitica basica.",
            "Solicitar radiografia de torax y valorar ecocardiograma temprano.",
        ]
        return actions

    @staticmethod
    def _initial_treatment_actions(payload: ScasestProtocolRequest, suspected: bool) -> list[str]:
        if not suspected:
            return ["No activar tratamiento SCASEST hasta confirmacion clinica."]

        actions: list[str] = []
        if not payload.contraindication_antiplatelet:
            actions.append("Valorar AAS carga inicial y segundo antiagregante segun protocolo.")
        if not payload.contraindication_anticoagulation:
            actions.append("Valorar anticoagulacion inicial (ej. fondaparinux) segun protocolo.")
        actions.append("Valorar nitratos y control de sintomas isquemicos.")

        if payload.heart_rate_bpm is not None and payload.heart_rate_bpm > 60:
            actions.append("Valorar betabloqueo si no hay contraindicaciones hemodinamicas.")
        return actions

    @staticmethod
    def _escalation_actions(payload: ScasestProtocolRequest, high_risk: bool) -> list[str]:
        actions: list[str] = []
        if high_risk:
            actions.append("Escalar a circuito coronario urgente y avisar cardiologia.")
            actions.append("Priorizar cama monitorizada/UCI coronaria segun estabilidad.")
        elif payload.grace_score is not None:
            actions.append("Estratificar destino segun GRACE y evolucion clinica.")
        return actions

    @staticmethod
    def _alerts(
        payload: ScasestProtocolRequest,
        suspected: bool,
        high_risk: bool,
    ) -> list[str]:
        alerts: list[str] = []
        if not suspected:
            alerts.append("SCASEST no claramente soportado por datos actuales.")
            return alerts

        if high_risk:
            alerts.append("SCASEST de alto riesgo: no demorar escalado invasivo.")
        if payload.hemodynamic_instability:
            alerts.append("Inestabilidad hemodinamica detectada.")
        if payload.ventricular_arrhythmias:
            alerts.append("Arritmias ventriculares: riesgo de deterioro inmediato.")
        if payload.oxygen_saturation_percent is not None and payload.oxygen_saturation_percent < 90:
            alerts.append("Hipoxemia significativa: corregir oxigenacion de inmediato.")
        return alerts

    @staticmethod
    def build_recommendation(
        payload: ScasestProtocolRequest,
    ) -> ScasestProtocolRecommendation:
        """Genera recomendacion operativa de SCASEST para validacion humana."""
        suspected = ScasestProtocolService._suspected(payload)
        high_risk = ScasestProtocolService._high_risk(payload, suspected)
        return ScasestProtocolRecommendation(
            scasest_suspected=suspected,
            high_risk_scasest=high_risk,
            diagnostic_actions=ScasestProtocolService._diagnostic_actions(payload, suspected),
            initial_treatment_actions=ScasestProtocolService._initial_treatment_actions(
                payload, suspected
            ),
            escalation_actions=ScasestProtocolService._escalation_actions(payload, high_risk),
            alerts=ScasestProtocolService._alerts(payload, suspected, high_risk),
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. Requiere validacion clinica humana."
            ),
        )
