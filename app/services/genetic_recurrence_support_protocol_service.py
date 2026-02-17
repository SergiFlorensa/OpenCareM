"""
Motor operativo para recurrencia genetica en osteogenesis imperfecta.

No diagnostica; organiza alertas de recurrencia para validacion genetica humana.
"""
from app.schemas.genetic_recurrence_support_protocol import (
    GeneticRecurrenceSupportProtocolRecommendation,
    GeneticRecurrenceSupportProtocolRequest,
)


class GeneticRecurrenceSupportProtocolService:
    """Construye recomendaciones operativas de recurrencia genetica."""

    @staticmethod
    def _core_recurrence_pathway(
        payload: GeneticRecurrenceSupportProtocolRequest,
    ) -> tuple[bool, str, float | None, list[str], list[str], list[str],]:
        critical_alerts: list[str] = []
        recurrence_actions: list[str] = []
        trace: list[str] = []

        recurrence_count = payload.recurrent_affected_pregnancies_count
        recurrence_detected = (
            payload.previous_pregnancy_with_same_condition or recurrence_count >= 2
        )
        dominant_parent_unaffected_pattern = (
            payload.autosomal_dominant_condition_suspected
            and recurrence_detected
            and payload.parents_phenotypically_unaffected
        )
        oi_dominant_signature = payload.oi_type_ii_suspected and payload.col1a1_or_col1a2_involved

        mosaicism_alert_active = False
        prioritized_mechanism = "indeterminado"
        recurrence_risk_percent = payload.estimated_mutated_gamete_fraction_percent

        if dominant_parent_unaffected_pattern:
            mosaicism_alert_active = True
            prioritized_mechanism = "mosaicismo_germinal_probable"
            critical_alerts.append(
                "Alerta de mosaicismo: recurrencia de enfermedad dominante en progenitores "
                "fenotipicamente sanos."
            )
            recurrence_actions.append(
                "Priorizar hipotesis de mosaicismo germinal frente a de novo aislado."
            )
            trace.append("Regla principal activada: patron dominante + recurrencia + padres sanos.")

        if oi_dominant_signature:
            recurrence_actions.append(
                "OI tipo II con COL1A1/COL1A2: reforzar ruta de consejo genetico y "
                "estimacion de riesgo de recurrencia."
            )
            trace.append("Firma molecular/clinica OI dominante detectada.")

        if payload.germline_mosaicism_confirmed:
            mosaicism_alert_active = True
            prioritized_mechanism = "mosaicismo_germinal_confirmado"
            recurrence_actions.append(
                "Mosaicismo germinal confirmado: usar este mecanismo como base principal "
                "de asesoramiento reproductivo."
            )
            if recurrence_risk_percent is None:
                recurrence_actions.append(
                    "Estimar fraccion de gametos mutados para cuantificar riesgo de "
                    "recurrencia en futuras gestaciones."
                )
            else:
                trace.append("Riesgo proporcional a fraccion germinal mutada reportada.")

        if recurrence_risk_percent is not None and not payload.germline_mosaicism_confirmed:
            trace.append(
                "Fraccion germinal mutada reportada sin confirmacion formal: validar "
                "origen del dato antes de usarlo en consejeria."
            )

        if (
            not payload.autosomal_dominant_condition_suspected
            and not payload.oi_type_ii_suspected
            and not payload.col1a1_or_col1a2_involved
        ):
            recurrence_actions.append(
                "Sin firma dominante especifica: mantener evaluacion etiologica abierta "
                "hasta confirmar mecanismo."
            )

        return (
            mosaicism_alert_active,
            prioritized_mechanism,
            recurrence_risk_percent,
            critical_alerts,
            recurrence_actions,
            trace,
        )

    @staticmethod
    def _differential_pathway(
        payload: GeneticRecurrenceSupportProtocolRequest,
        *,
        recurrence_detected: bool,
        dominant_parent_unaffected_pattern: bool,
    ) -> tuple[list[str], list[str], list[str]]:
        differential_mechanisms: list[str] = []
        safety_blocks: list[str] = []
        trace: list[str] = []

        if payload.autosomal_recessive_hypothesis_active:
            differential_mechanisms.append(
                "Herencia autosomica recesiva: confirmar portadores parentales y "
                "segregacion antes de priorizar."
            )
            if dominant_parent_unaffected_pattern:
                trace.append(
                    "Hipotesis recesiva marcada como diferencial secundario por "
                    "patron dominante recurrente."
                )

        if payload.de_novo_hypothesis_active:
            differential_mechanisms.append(
                "Mutacion de novo aislada: plausible en evento unico, menos probable "
                "si existe recurrencia repetida."
            )
            if recurrence_detected:
                safety_blocks.append(
                    "Recurrencia detectada: no clasificar como de novo aislado sin "
                    "descartar mosaicismo germinal."
                )

        if payload.incomplete_penetrance_hypothesis_active:
            differential_mechanisms.append(
                "Penetrancia incompleta: considerar solo tras correlacion genotipo-fenotipo "
                "parental y evidencia familiar robusta."
            )
            if dominant_parent_unaffected_pattern:
                safety_blocks.append(
                    "Penetrancia incompleta no debe desplazar la prioridad de "
                    "mosaicismo en patron dominante recurrente con padres sanos."
                )

        if payload.somatic_mosaicism_only_confirmed:
            differential_mechanisms.append(
                "Mosaicismo somatico: puede explicar fenotipos en tejidos, pero no "
                "justifica por si solo transmision vertical."
            )
            if recurrence_detected:
                safety_blocks.append(
                    "Mosaicismo somatico aislado no explica recurrencia vertical; "
                    "investigar componente germinal."
                )

        return differential_mechanisms, safety_blocks, trace

    @staticmethod
    def _counseling_and_consistency_pathway(
        payload: GeneticRecurrenceSupportProtocolRequest,
        *,
        recurrence_detected: bool,
        prioritized_mechanism: str,
    ) -> tuple[list[str], list[str], list[str]]:
        counseling_actions: list[str] = []
        safety_blocks: list[str] = []
        trace: list[str] = []

        if recurrence_detected:
            counseling_actions.append(
                "Activar consejo genetico reproductivo con explicacion de riesgo de "
                "recurrencia no trivial."
            )
            counseling_actions.append(
                "Planificar ruta de diagnostico prenatal/preimplantacional segun protocolo "
                "institucional y preferencias familiares."
            )

        if not payload.molecular_confirmation_available:
            safety_blocks.append(
                "Sin confirmacion molecular: no cerrar mecanismo de recurrencia "
                "hasta validar variante y segregacion."
            )

        if not payload.parental_germline_testing_available and prioritized_mechanism.startswith(
            "mosaicismo_germinal"
        ):
            counseling_actions.append(
                "Considerar estudio genetico parental dirigido para soportar hipotesis "
                "de mosaicismo germinal."
            )

        if payload.parents_phenotypically_unaffected and (
            payload.mother_phenotypically_affected or payload.father_phenotypically_affected
        ):
            safety_blocks.append(
                "Inconsistencia fenotipica parental: revisar campos de entrada "
                "(padres sanos vs progenitor afectado)."
            )

        if payload.germline_mosaicism_confirmed and payload.somatic_mosaicism_only_confirmed:
            safety_blocks.append(
                "Mosaicismo germinal confirmado y somatico exclusivo marcados en paralelo: "
                "normalizar clasificacion del mecanismo."
            )

        if payload.gestational_age_weeks is not None and payload.gestational_age_weeks >= 24:
            trace.append(
                "Gestacion avanzada: priorizar decision operativa coordinada con "
                "obstetricia/genetica."
            )

        return counseling_actions, safety_blocks, trace

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
        payload: GeneticRecurrenceSupportProtocolRequest,
    ) -> GeneticRecurrenceSupportProtocolRecommendation:
        """Genera recomendacion operativa de recurrencia genetica."""
        recurrence_detected = (
            payload.previous_pregnancy_with_same_condition
            or payload.recurrent_affected_pregnancies_count >= 2
        )
        dominant_parent_unaffected_pattern = (
            payload.autosomal_dominant_condition_suspected
            and recurrence_detected
            and payload.parents_phenotypically_unaffected
        )

        (
            mosaicism_alert_active,
            prioritized_mechanism,
            recurrence_risk_percent,
            critical_core,
            recurrence_actions,
            core_trace,
        ) = GeneticRecurrenceSupportProtocolService._core_recurrence_pathway(payload)
        (
            differential_mechanisms,
            differential_safety,
            differential_trace,
        ) = GeneticRecurrenceSupportProtocolService._differential_pathway(
            payload,
            recurrence_detected=recurrence_detected,
            dominant_parent_unaffected_pattern=dominant_parent_unaffected_pattern,
        )
        (
            counseling_actions,
            counseling_safety,
            counseling_trace,
        ) = GeneticRecurrenceSupportProtocolService._counseling_and_consistency_pathway(
            payload,
            recurrence_detected=recurrence_detected,
            prioritized_mechanism=prioritized_mechanism,
        )

        safety_blocks = differential_safety + counseling_safety
        has_actions = any([recurrence_actions, counseling_actions, differential_mechanisms])
        severity = GeneticRecurrenceSupportProtocolService._severity(
            critical_alerts=critical_core,
            safety_blocks=safety_blocks,
            has_actions=has_actions,
        )

        return GeneticRecurrenceSupportProtocolRecommendation(
            severity_level=severity,
            mosaicism_alert_active=mosaicism_alert_active,
            prioritized_recurrence_mechanism=prioritized_mechanism,
            estimated_recurrence_risk_percent=recurrence_risk_percent,
            critical_alerts=critical_core,
            recurrence_interpretation_actions=recurrence_actions,
            genetic_counseling_actions=counseling_actions,
            differential_mechanisms=differential_mechanisms,
            safety_blocks=safety_blocks,
            interpretability_trace=core_trace + differential_trace + counseling_trace,
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. "
                "Requiere validacion por genetica clinica/obstetricia."
            ),
        )
