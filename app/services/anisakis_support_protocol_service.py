"""
Motor operativo de sospecha de reaccion por Anisakis en urgencias.

No diagnostica; organiza rutas de riesgo para validacion clinica humana.
"""
from app.schemas.anisakis_support_protocol import (
    AnisakisSupportProtocolRecommendation,
    AnisakisSupportProtocolRequest,
)


class AnisakisSupportProtocolService:
    """Construye recomendaciones operativas para escenarios de anisakis."""

    @staticmethod
    def _exposure_pathway(
        payload: AnisakisSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        diagnostic_actions: list[str] = []
        trace: list[str] = []

        recent_ingestion = (
            payload.fish_ingestion_last_hours is not None and payload.fish_ingestion_last_hours <= 6
        )
        risk_exposure = (
            payload.raw_or_undercooked_fish_exposure
            or payload.preparation_risk_present
            or payload.insufficient_cooking_suspected
        )

        if recent_ingestion and (
            payload.urticaria_present
            or payload.angioedema_present
            or payload.anaphylaxis_present
            or payload.respiratory_compromise_present
            or payload.hypotension_present
        ):
            critical_alerts.append(
                "Sospecha de alergia a Anisakis por reaccion inmediata tras ingesta de pescado."
            )
            trace.append("Regla de latencia <=6h con fenotipo alergico activada.")

        if risk_exposure and (
            payload.digestive_symptoms_present
            or payload.urticaria_present
            or payload.angioedema_present
            or payload.anaphylaxis_present
        ):
            diagnostic_actions.append(
                "Diferenciar infestacion digestiva de reaccion alergica IgE mediada."
            )

        return critical_alerts, diagnostic_actions, trace

    @staticmethod
    def _allergy_severity_pathway(
        payload: AnisakisSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        acute_actions: list[str] = []
        safety_blocks: list[str] = []

        severe_allergy = (
            payload.anaphylaxis_present
            or payload.respiratory_compromise_present
            or payload.hypotension_present
        )
        if severe_allergy:
            critical_alerts.append(
                "Fenotipo de anafilaxia grave: activar protocolo inmediato de anafilaxia."
            )
            acute_actions.append(
                "Priorizar estabilizacion ABC y adrenalina intramuscular segun protocolo local."
            )

        if payload.urticaria_present or payload.angioedema_present:
            acute_actions.append(
                "Vigilar progresion de sintomas cutaneo-mucosos y posible compromiso sistemico."
            )

        suspicion_allergy = (
            payload.urticaria_present or payload.angioedema_present or severe_allergy
        )
        if suspicion_allergy and not payload.specific_ige_requested:
            safety_blocks.append(
                "Solicitar IgE especifica frente a Anisakis ante sospecha alergica."
            )

        return critical_alerts, acute_actions, safety_blocks

    @staticmethod
    def _diagnostic_pathway(
        payload: AnisakisSupportProtocolRequest,
    ) -> tuple[list[str], list[str]]:
        diagnostic_actions: list[str] = []
        trace: list[str] = []

        suspicion_allergy = (
            payload.urticaria_present
            or payload.angioedema_present
            or payload.anaphylaxis_present
            or payload.respiratory_compromise_present
            or payload.hypotension_present
        )
        if suspicion_allergy:
            diagnostic_actions.append("Solicitar IgE especifica frente a Anisakis simplex.")
            diagnostic_actions.append(
                "Considerar prueba cutanea (prick test) en evaluacion alergologica diferida."
            )

        if payload.anisakis_specific_ige_positive or payload.prick_test_positive:
            trace.append("Biomarcadores de hipersensibilidad inmediata compatibles con anisakis.")

        if payload.digestive_symptoms_present and not suspicion_allergy:
            diagnostic_actions.append(
                "Cuadro digestivo sin fenotipo alergico: valorar carga parasitaria e infestacion."
            )

        return diagnostic_actions, trace

    @staticmethod
    def _discharge_prevention_pathway(
        payload: AnisakisSupportProtocolRequest,
    ) -> tuple[list[str], list[str]]:
        prevention_actions: list[str] = []
        safety_blocks: list[str] = []

        prevention_actions.append("Al alta: congelar pescado a -20 C durante al menos 72 horas.")
        prevention_actions.append(
            "Al alta: cocinar por encima de 60 C, evitar vuelta y vuelta y "
            "microondas insuficiente."
        )
        prevention_actions.append(
            "Priorizar pescado ultracongelado/eviscerado en altamar cuando " "sea posible."
        )
        prevention_actions.append(
            "Reducir riesgo de exposicion priorizando piezas de cola frente a "
            "zonas proximas a la cabeza."
        )

        if (
            payload.freezing_temperature_c is not None and payload.freezing_temperature_c > -20
        ) or (payload.freezing_duration_hours is not None and payload.freezing_duration_hours < 72):
            safety_blocks.append(
                "Congelacion previa insuficiente: reforzar estandar -20 C por 72h."
            )

        if (
            payload.cooking_temperature_c is not None and payload.cooking_temperature_c <= 60
        ) or payload.insufficient_cooking_suspected:
            safety_blocks.append(
                "Coccion insuficiente sospechada: reforzar cocinado completo >60 C."
            )

        if not payload.deep_sea_eviscerated_or_ultrafrozen_fish_consumed:
            prevention_actions.append(
                "Informar riesgo de migracion larvaria cuando no hay evisceracion temprana."
            )

        return prevention_actions, safety_blocks

    @staticmethod
    def _severity(
        *,
        critical_alerts: list[str],
        safety_blocks: list[str],
        has_actions: bool,
    ) -> str:
        if critical_alerts:
            return "critical"
        if safety_blocks:
            return "high"
        if has_actions:
            return "medium"
        return "low"

    @staticmethod
    def build_recommendation(
        payload: AnisakisSupportProtocolRequest,
    ) -> AnisakisSupportProtocolRecommendation:
        """Genera recomendacion operativa anisakis para validacion humana."""
        (
            critical_exposure,
            diagnostic_exposure,
            trace_exposure,
        ) = AnisakisSupportProtocolService._exposure_pathway(payload)
        (
            critical_allergy,
            acute_actions,
            safety_allergy,
        ) = AnisakisSupportProtocolService._allergy_severity_pathway(payload)
        diagnostic_actions, trace_diagnostic = AnisakisSupportProtocolService._diagnostic_pathway(
            payload
        )
        (
            prevention_actions,
            safety_prevention,
        ) = AnisakisSupportProtocolService._discharge_prevention_pathway(payload)

        critical_alerts = critical_exposure + critical_allergy
        safety_blocks = safety_allergy + safety_prevention
        diagnostic_actions_full = diagnostic_exposure + diagnostic_actions
        has_actions = any(
            [
                diagnostic_actions_full,
                acute_actions,
                prevention_actions,
            ]
        )
        severity = AnisakisSupportProtocolService._severity(
            critical_alerts=critical_alerts,
            safety_blocks=safety_blocks,
            has_actions=has_actions,
        )

        return AnisakisSupportProtocolRecommendation(
            severity_level=severity,
            critical_alerts=critical_alerts,
            diagnostic_actions=diagnostic_actions_full,
            acute_management_actions=acute_actions,
            discharge_prevention_actions=prevention_actions,
            safety_blocks=safety_blocks,
            interpretability_trace=trace_exposure + trace_diagnostic,
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. "
                "Requiere validacion por urgencias/alergologia."
            ),
        )
