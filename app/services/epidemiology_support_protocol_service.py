"""
Motor operativo de epidemiologia clinica para urgencias.

No diagnostica: organiza interpretacion de metricas poblacionales y analitica
de impacto para validacion humana.
"""
from app.schemas.epidemiology_support_protocol import (
    EpidemiologySupportProtocolRecommendation,
    EpidemiologySupportProtocolRequest,
)


class EpidemiologySupportProtocolService:
    """Construye recomendaciones operativas de epidemiologia aplicada."""

    @staticmethod
    def _safe_division(numerator: float, denominator: float) -> float | None:
        if denominator <= 0:
            return None
        return numerator / denominator

    @staticmethod
    def _frequency_metrics(
        payload: EpidemiologySupportProtocolRequest,
    ) -> tuple[float | None, float | None, float | None, list[str], list[str], list[str]]:
        actions: list[str] = []
        safety_blocks: list[str] = []
        trace: list[str] = []

        incidence_accumulated: float | None = None
        incidence_density: float | None = None
        prevalence: float | None = None

        if payload.new_cases_count is not None and payload.population_at_risk_count is not None:
            incidence_accumulated = EpidemiologySupportProtocolService._safe_division(
                float(payload.new_cases_count),
                float(payload.population_at_risk_count),
            )
            if incidence_accumulated is not None:
                trace.append(
                    "Incidencia acumulada calculada como casos nuevos / poblacion en riesgo."
                )

        if payload.new_cases_count is not None and payload.person_time_at_risk is not None:
            incidence_density = EpidemiologySupportProtocolService._safe_division(
                float(payload.new_cases_count),
                payload.person_time_at_risk,
            )
            if incidence_density is not None:
                trace.append(
                    "Densidad de incidencia calculada como casos nuevos / persona-tiempo."
                )
            else:
                safety_blocks.append(
                    "No se puede calcular densidad de incidencia sin persona-tiempo > 0."
                )

        if payload.existing_cases_count is not None and payload.population_total_count is not None:
            prevalence = EpidemiologySupportProtocolService._safe_division(
                float(payload.existing_cases_count),
                float(payload.population_total_count),
            )
            if prevalence is not None:
                trace.append("Prevalencia calculada como casos existentes / poblacion total.")

        if payload.requested_individual_risk_estimation:
            if incidence_accumulated is not None:
                actions.append(
                    "Usar incidencia acumulada para estimar probabilidad individual de "
                    "enfermar en el periodo."
                )
            else:
                safety_blocks.append(
                    "Falta numerador/denominador valido para incidencia acumulada "
                    "en estimacion individual."
                )

        if payload.requested_population_status_snapshot:
            if prevalence is not None:
                actions.append(
                    "Usar prevalencia para describir situacion actual de enfermedad "
                    "en la poblacion."
                )
            else:
                safety_blocks.append(
                    "Falta numerador/denominador valido para prevalencia en foto poblacional."
                )

        if incidence_density is not None:
            actions.append(
                "Interpretar densidad de incidencia como velocidad colectiva de "
                "transicion sano->enfermo por unidad de tiempo."
            )

        return (
            incidence_accumulated,
            incidence_density,
            prevalence,
            actions,
            safety_blocks,
            trace,
        )

    @staticmethod
    def _nnt_metrics(
        payload: EpidemiologySupportProtocolRequest,
    ) -> tuple[float | None, float | None, list[str], list[str], list[str]]:
        actions: list[str] = []
        safety_blocks: list[str] = []
        trace: list[str] = []

        absolute_risk_reduction: float | None = None
        number_needed_to_treat: float | None = None

        if (
            payload.control_event_risk is not None
            and payload.intervention_event_risk is not None
        ):
            absolute_risk_reduction = abs(
                payload.control_event_risk - payload.intervention_event_risk
            )
            trace.append(
                "RAR calculada como diferencia absoluta de riesgo entre control e intervencion."
            )
            if absolute_risk_reduction > 0:
                number_needed_to_treat = 1 / absolute_risk_reduction
                actions.append(
                    "Calcular NNT como inverso de la RAR usando riesgos en tanto por uno."
                )
                trace.append("NNT calculado como 1 / RAR.")
            else:
                safety_blocks.append(
                    "RAR igual a 0: NNT no interpretable (sin diferencia absoluta de riesgo)."
                )
        else:
            actions.append(
                "Para NNT se requieren riesgo de control y riesgo de intervencion en formato 0..1."
            )

        return absolute_risk_reduction, number_needed_to_treat, actions, safety_blocks, trace

    @staticmethod
    def _causal_inference_metrics(
        payload: EpidemiologySupportProtocolRequest,
    ) -> tuple[float | None, list[str], list[str], list[str], list[str]]:
        actions: list[str] = []
        safety_blocks: list[str] = []
        critical_alerts: list[str] = []
        trace: list[str] = []

        risk_relative: float | None = None
        if payload.exposed_risk is not None and payload.unexposed_risk is not None:
            if payload.unexposed_risk == 0:
                safety_blocks.append(
                    "RR no calculable: riesgo en no expuestos igual a 0."
                )
                if payload.exposed_risk > 0:
                    critical_alerts.append(
                        "RR potencialmente infinito: revisar calidad de datos y estratificacion."
                    )
            else:
                risk_relative = payload.exposed_risk / payload.unexposed_risk
                trace.append("RR calculado como riesgo expuestos / riesgo no expuestos.")
                actions.append(
                    "Interpretar RR como medida de asociacion antes de afirmar causalidad."
                )
                if risk_relative < 1:
                    relative_reduction_percent = round((1 - risk_relative) * 100, 2)
                    actions.append(
                        "En inferencia causal contrafactual, la incidencia en no expuestos "
                        f"se reduciria un {relative_reduction_percent}% si toda la poblacion "
                        "utilizara la intervencion."
                    )
                elif risk_relative > 1:
                    relative_increase_percent = round((risk_relative - 1) * 100, 2)
                    actions.append(
                        "En inferencia causal contrafactual, la incidencia en no expuestos "
                        f"aumentaria un {relative_increase_percent}% si toda la poblacion "
                        "estuviera expuesta."
                    )
                else:
                    actions.append(
                        "RR cercano a 1: no se observa diferencia de riesgo atribuible clara."
                    )

        hill_criteria = {
            "fuerza_asociacion": payload.hill_strength_of_association,
            "consistencia": payload.hill_consistency,
            "especificidad": payload.hill_specificity,
            "temporalidad": payload.hill_temporality,
            "gradiente_biologico": payload.hill_biological_gradient,
            "plausibilidad": payload.hill_plausibility,
            "coherencia": payload.hill_coherence,
            "experimento": payload.hill_experiment,
            "analogia": payload.hill_analogy,
        }
        positive_criteria = [name for name, enabled in hill_criteria.items() if enabled]
        if positive_criteria:
            actions.append(
                "Aplicar Bradford Hill para soporte causal: "
                + ", ".join(positive_criteria)
                + "."
            )
        if payload.hill_biological_gradient:
            actions.append(
                "El gradiente biologico (dosis-respuesta) respalda consistencia causal."
            )
        if not payload.hill_temporality:
            safety_blocks.append(
                "Sin temporalidad documentada no se puede sostener inferencia causal robusta."
            )

        trace.append(
            f"Criterios Bradford Hill positivos: {len(positive_criteria)} de 9."
        )
        return risk_relative, actions, safety_blocks, critical_alerts, trace

    @staticmethod
    def _economic_evaluation_metrics(
        payload: EpidemiologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        actions: list[str] = []
        safety_blocks: list[str] = []
        trace: list[str] = []

        study_type_raw = payload.economic_study_type or ""
        study_type = study_type_raw.strip().lower()
        is_cost_utility = any(
            token in study_type
            for token in ("coste-utilidad", "coste utilidad", "cost-utility")
        )

        if is_cost_utility:
            actions.append(
                "Clasificar como analisis coste-utilidad cuando el resultado se exprese "
                "en AVAC/QALY o utilidades."
            )
            if not payload.qaly_or_utility_outcomes_used:
                safety_blocks.append(
                    "Inconsistencia economica: coste-utilidad sin AVAC/QALY/utilidades declaradas."
                )
            trace.append("Estudio economico identificado como coste-utilidad.")
        elif study_type:
            actions.append(
                f"Clasificar estudio como '{study_type_raw}' y no interpretar "
                "resultados como utilidades."
            )
            if payload.qaly_or_utility_outcomes_used:
                safety_blocks.append(
                    "AVAC/QALY informados en estudio no clasificado como coste-utilidad."
                )
            trace.append("Estudio economico no clasificado como coste-utilidad.")
        else:
            actions.append(
                "Definir tipo de evaluacion economica "
                "(coste-utilidad/coste-efectividad/coste-beneficio)."
            )

        return actions, safety_blocks, trace

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
        payload: EpidemiologySupportProtocolRequest,
    ) -> EpidemiologySupportProtocolRecommendation:
        """Genera recomendacion operativa epidemiologica para validacion humana."""
        (
            incidence_accumulated,
            incidence_density,
            prevalence,
            frequency_actions,
            frequency_safety_blocks,
            frequency_trace,
        ) = EpidemiologySupportProtocolService._frequency_metrics(payload)
        (
            absolute_risk_reduction,
            number_needed_to_treat,
            nnt_actions,
            nnt_safety_blocks,
            nnt_trace,
        ) = EpidemiologySupportProtocolService._nnt_metrics(payload)
        (
            risk_relative,
            causal_actions,
            causal_safety_blocks,
            causal_critical_alerts,
            causal_trace,
        ) = EpidemiologySupportProtocolService._causal_inference_metrics(payload)
        (
            economic_actions,
            economic_safety_blocks,
            economic_trace,
        ) = EpidemiologySupportProtocolService._economic_evaluation_metrics(payload)

        safety_blocks = (
            frequency_safety_blocks
            + nnt_safety_blocks
            + causal_safety_blocks
            + economic_safety_blocks
        )
        critical_alerts = causal_critical_alerts
        has_actions = any(
            [
                frequency_actions,
                nnt_actions,
                causal_actions,
                economic_actions,
            ]
        )
        severity = EpidemiologySupportProtocolService._severity(
            critical_alerts=critical_alerts,
            safety_blocks=safety_blocks,
            has_actions=has_actions,
        )

        return EpidemiologySupportProtocolRecommendation(
            severity_level=severity,
            critical_alerts=critical_alerts,
            frequency_actions=frequency_actions,
            nnt_actions=nnt_actions,
            causal_inference_actions=causal_actions,
            economic_evaluation_actions=economic_actions,
            safety_blocks=safety_blocks,
            interpretability_trace=(
                frequency_trace + nnt_trace + causal_trace + economic_trace
            ),
            incidence_accumulated=incidence_accumulated,
            incidence_density=incidence_density,
            prevalence=prevalence,
            risk_relative=risk_relative,
            absolute_risk_reduction=absolute_risk_reduction,
            number_needed_to_treat=number_needed_to_treat,
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. "
                "Requiere validacion por epidemiologia clinica/equipo asistencial."
            ),
        )
