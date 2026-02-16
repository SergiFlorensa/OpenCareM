"""
Motor operativo de anestesiologia y reanimacion para urgencias.

No diagnostica; organiza rutas de riesgo para validacion clinica humana.
"""
from app.schemas.anesthesiology_support_protocol import (
    AnesthesiologySupportProtocolRecommendation,
    AnesthesiologySupportProtocolRequest,
)


class AnesthesiologySupportProtocolService:
    """Construye recomendaciones operativas anestesiologicas en urgencias."""

    @staticmethod
    def _rsi_pathway(
        payload: AnesthesiologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        rsi_actions: list[str] = []
        safety_blocks: list[str] = []
        trace: list[str] = []

        rsi_trigger = (
            payload.no_preop_fasting
            or payload.intestinal_obstruction_present
            or payload.acute_hematemesis_present
            or payload.full_stomach_risk_other
        )
        if payload.intestinal_obstruction_present or payload.acute_hematemesis_present:
            rsi_actions.append(
                "Priorizar kit de induccion de secuencia rapida (ISR) en modulo de via aerea."
            )
            trace.append(
                "Regla de priorizacion automatica ISR por obstruccion/hematemesis activada."
            )

        if not (payload.emergency_airway_needed and rsi_trigger):
            return critical_alerts, rsi_actions, safety_blocks, trace

        rsi_actions.append("Preoxigenar con FiO2 alta durante 3-5 minutos antes de la induccion.")

        if payload.preoxygenation_minutes_planned is not None:
            if payload.preoxygenation_minutes_planned < 3:
                safety_blocks.append("Preoxigenacion por debajo del minimo operativo de 3 minutos.")
            if payload.preoxygenation_minutes_planned > 5:
                safety_blocks.append("Preoxigenacion fuera de ventana ISR (3-5 minutos).")

        if payload.bag_mask_manual_ventilation_planned:
            critical_alerts.append(
                "Evitar ventilacion manual con bolsa-mascarilla durante ISR por riesgo de "
                "distension gastrica/regurgitacion."
            )

        if payload.expected_intubation_seconds_after_iv is not None and not (
            45 <= payload.expected_intubation_seconds_after_iv <= 60
        ):
            safety_blocks.append(
                "Objetivo tecnico de intubacion ISR fuera de ventana 45-60 segundos."
            )

        if not payload.iv_route_confirmed:
            critical_alerts.append(
                "ISR requiere administracion IV exclusiva; acceso no confirmado."
            )

        if payload.inhaled_halogenated_induction_planned:
            safety_blocks.append(
                "Bloquear induccion inhalatoria con halogenados en ISR por lentitud."
            )

        hypnotic = (payload.hypnotic_agent or "").strip().lower()
        blocker = (payload.neuromuscular_blocker_agent or "").strip().lower()
        if hypnotic and hypnotic != "propofol":
            rsi_actions.append(
                "Hipnotico distinto de propofol: confirmar protocolo local y estabilidad."
            )
        if not hypnotic:
            safety_blocks.append("No se documento hipnotico para ISR.")
        if blocker and blocker != "rocuronio":
            rsi_actions.append(
                "Bloqueante distinto de rocuronio: validar equivalencia y tiempos de inicio."
            )
        if not blocker:
            safety_blocks.append("No se documento bloqueante neuromuscular para ISR.")

        if not payload.sellick_maneuver_planned:
            safety_blocks.append(
                "Considerar maniobra de Sellick para reducir riesgo de regurgitacion."
            )
        else:
            rsi_actions.append(
                "Mantener Sellick hasta verificar tubo e inflado de neumotaponamiento."
            )
            if payload.tube_position_verified and payload.cuff_inflated:
                rsi_actions.append(
                    "Tras verificar posicion y cuff inflado, puede finalizarse la "
                    "maniobra de Sellick."
                )
            else:
                safety_blocks.append(
                    "Sellick no debe retirarse hasta confirmar posicion del tubo y cuff inflado."
                )

        trace.append("Ruta ISR de estomago lleno y seguridad de via aerea activada.")
        return critical_alerts, rsi_actions, safety_blocks, trace

    @staticmethod
    def _pain_block_pathway(
        payload: AnesthesiologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        block_recommendations: list[str] = []
        differential_recommendations: list[str] = []
        trace: list[str] = []

        refractory_or_intolerant_opioids = (
            payload.opioid_response_insufficient or payload.opioid_escalation_not_tolerated
        )
        if (
            payload.presacral_mass_present
            and payload.severe_perineal_or_pelvic_internal_pain
            and refractory_or_intolerant_opioids
        ):
            block_recommendations.append(
                "Masa presacra + dolor perineal/pelvico + opioides insuficientes/no tolerados: "
                "sugerir bloqueo del ganglio impar como eleccion."
            )
            trace.append("Regla de eleccion de ganglio impar por masa presacra activada.")
        elif payload.severe_perineal_or_pelvic_internal_pain:
            block_recommendations.append(
                "Dolor perineal/pelvico interno: considerar bloqueo del ganglio impar."
            )

        if (
            payload.neuropathic_pain_component
            or payload.visceral_pain_component
            or payload.vascular_pain_component
        ):
            block_recommendations.append(
                "Ganglio impar cubre dolor neuropatico/visceral/vascular de pelvis "
                "interna y perine."
            )

        if payload.upper_abdominal_visceral_pain:
            differential_recommendations.append(
                "Dolor abdominal alto visceral: priorizar bloqueo de plexo celiaco."
            )
        if payload.pelvic_genital_autonomic_pain:
            differential_recommendations.append(
                "Dolor/disfuncion autonomica pelvica-genital: valorar bloqueo de "
                "nervios esplacnicos."
            )
        if payload.perineal_external_genital_pain:
            differential_recommendations.append(
                "Dolor de perine/genitales externos: valorar bloqueo de nervios pudendos."
            )
        if payload.perineal_pelvic_internal_pain:
            differential_recommendations.append(
                "Dolor perineal/pelvico interno visceral: priorizar bloqueo de ganglio impar."
            )

        return block_recommendations, differential_recommendations, trace

    @staticmethod
    def _severity(
        *,
        critical_alerts: list[str],
        safety_blocks: list[str],
        rsi_actions: list[str],
        block_recommendations: list[str],
    ) -> str:
        if critical_alerts:
            return "critical"
        if safety_blocks:
            return "high"
        if rsi_actions or block_recommendations:
            return "medium"
        return "low"

    @staticmethod
    def build_recommendation(
        payload: AnesthesiologySupportProtocolRequest,
    ) -> AnesthesiologySupportProtocolRecommendation:
        """Genera recomendacion operativa anestesiologica para validacion humana."""
        critical_alerts, rsi_actions, safety_blocks, trace_rsi = (
            AnesthesiologySupportProtocolService._rsi_pathway(payload)
        )
        block_recommendations, differential_recommendations, trace_blocks = (
            AnesthesiologySupportProtocolService._pain_block_pathway(payload)
        )

        severity = AnesthesiologySupportProtocolService._severity(
            critical_alerts=critical_alerts,
            safety_blocks=safety_blocks,
            rsi_actions=rsi_actions,
            block_recommendations=block_recommendations,
        )

        return AnesthesiologySupportProtocolRecommendation(
            severity_level=severity,
            critical_alerts=critical_alerts,
            rapid_sequence_induction_actions=rsi_actions,
            airway_safety_blocks=safety_blocks,
            sympathetic_block_recommendations=block_recommendations,
            differential_block_recommendations=differential_recommendations,
            interpretability_trace=trace_rsi + trace_blocks,
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. "
                "Requiere validacion por anestesia/reanimacion y urgencias."
            ),
        )
