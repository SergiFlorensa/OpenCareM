"""
Motor operativo de geriatria y fragilidad para urgencias.

No diagnostica; organiza rutas de riesgo para validacion clinica humana.
"""
from app.schemas.geriatrics_support_protocol import (
    GeriatricsSupportProtocolRecommendation,
    GeriatricsSupportProtocolRequest,
)


class GeriatricsSupportProtocolService:
    """Construye recomendaciones operativas geriatricas en urgencias."""

    @staticmethod
    def _aging_morphology_pathway(
        payload: GeriatricsSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        interpretation: list[str] = []
        diagnostic_actions: list[str] = []
        trace: list[str] = []

        renal_aging_pattern = (
            payload.mesangial_matrix_expansion_present
            or payload.glomerular_basement_membrane_thickening_present
            or payload.glomerulosclerosis_present
        )
        if renal_aging_pattern:
            interpretation.append(
                "Cambios nefrourologicos compatibles con envejecimiento "
                "(mesangio/membrana basal/glomeruloesclerosis)."
            )
            if not payload.nephrology_red_flags_present:
                interpretation.append(
                    "La expansion mesangial aislada se interpreta como hallazgo de edad "
                    "y no como dano necesariamente patologico."
                )
                trace.append(
                    "Regla geriatrica renal aplicada: aumento de matriz mesangial "
                    "sin red flags no se etiqueta como patologia por si sola."
                )
            else:
                diagnostic_actions.append(
                    "Correlacionar hallazgos renales de envejecimiento con "
                    "red flags nefrologicas."
                )

        if (
            payload.cerebral_volume_loss_age_expected
            and payload.widened_sulci_or_ventricles_present
        ):
            interpretation.append(
                "Patron cerebral de envejecimiento esperado: menor masa cerebral "
                "con aumento de surcos/ventriculos."
            )
        if payload.sinus_node_pacemaker_cell_loss_suspected:
            interpretation.append(
                "Reduccion de celulas marcapasos del nodo sinusal compatible con edad avanzada."
            )
        if payload.tracheal_costal_cartilage_calcification_present:
            interpretation.append(
                "Calcificacion de cartilagos traqueales/costales compatible con envejecimiento."
            )

        return interpretation, diagnostic_actions, trace

    @staticmethod
    def _immobility_pathway(
        payload: GeriatricsSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        therapeutic_actions: list[str] = []
        safety_blocks: list[str] = []
        trace: list[str] = []

        if payload.prolonged_immobility_present:
            therapeutic_actions.append(
                "Inmovilidad prolongada: activar plan de movilizacion precoz y prevencion "
                "de desacondicionamiento."
            )
            if payload.nitrogen_balance_negative:
                critical_alerts.append(
                    "Balance nitrogenado negativo en inmovilidad: priorizar soporte proteico."
                )
                trace.append("Regla de fragilidad metabolica por inmovilidad activada.")
                if not payload.high_protein_support_plan_active:
                    safety_blocks.append(
                        "Falta plan proteico pese a balance nitrogenado negativo."
                    )
                else:
                    therapeutic_actions.append(
                        "Mantener/reforzar aporte proteico para frenar catabolismo."
                    )

            if payload.insulin_resistance_signs_present:
                therapeutic_actions.append(
                    "Monitorizar intolerancia hidrocarbonada asociada a inmovilidad."
                )
            if payload.resting_tachycardia_present:
                therapeutic_actions.append(
                    "Vigilar taquicardia de reposo por predominio simpatico en inmovilidad."
                )
            if payload.psychomotor_slowing_present:
                diagnostic_actions = (
                    "Enlentecimiento psicomotor en inmovilidad: "
                    "reevaluar estado cognitivo funcional "
                    "tras intervencion de movilidad."
                )
                therapeutic_actions.append(diagnostic_actions)

        return critical_alerts, therapeutic_actions, safety_blocks, trace

    @staticmethod
    def _delirium_pathway(
        payload: GeriatricsSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        diagnostic_actions: list[str] = []
        therapeutic_actions: list[str] = []
        safety_blocks: list[str] = []
        trace: list[str] = []

        if payload.delirium_suspected:
            therapeutic_actions.append(
                "Delirium: priorizar tratamiento de la causa subyacente antes de sedacion cronica."
            )
            if payload.infectious_trigger_suspected:
                diagnostic_actions.append(
                    "Buscar y tratar desencadenante infeccioso (p. ej., foco urinario)."
                )

            if payload.severe_behavioral_disturbance_present:
                therapeutic_actions.append(
                    "Trastorno conductual grave: considerar risperidona a dosis minima y "
                    "duracion corta."
                )
                if not payload.risperidone_active:
                    trace.append("Risperidona propuesta solo por gravedad conductual.")

            if (
                payload.risperidone_active
                and payload.behavioral_stabilization_after_causal_treatment
            ):
                therapeutic_actions.append(
                    "Iniciar desescalada progresiva de risperidona cuando conducta se estabiliza."
                )
                trace.append(
                    "Regla de retirada precoz de antipsicotico aplicada tras mejoria causal."
                )

            if payload.insomnia_present and payload.benzodiazepine_planned:
                critical_alerts.append(
                    "Bloqueo de benzodiacepinas en insomnio con delirium sospechado."
                )
                safety_blocks.append(
                    "Evitar benzodiacepinas: aumentan somnolencia diurna y deterioro funcional."
                )

            if payload.dementia_progression_assessment_planned_during_acute_event:
                safety_blocks.append(
                    "No valorar progresion de demencia durante delirium agudo reversible."
                )

        return critical_alerts, diagnostic_actions, therapeutic_actions, safety_blocks, trace

    @staticmethod
    def _start_v3_pathway(
        payload: GeriatricsSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        optimization_actions: list[str] = []
        safety_blocks: list[str] = []
        diagnostic_actions: list[str] = []

        if (
            payload.symptomatic_atrophic_vaginitis
            and not payload.topical_vaginal_estrogen_active
        ):
            optimization_actions.append(
                "START v3: valorar estrogenos topicos vaginales en vaginitis atrofica sintomatica."
            )

        if payload.lidocaine_patch_planned_for_general_joint_pain:
            if not payload.localized_neuropathic_pain_present:
                safety_blocks.append(
                    "Parches de lidocaina no indicados para dolor articular generalizado."
                )
            else:
                optimization_actions.append(
                    "Lidocaina topica compatible con dolor neuropatico localizado."
                )

        if payload.inhaled_corticosteroid_planned and payload.copd_gold_stage in {1, 2}:
            safety_blocks.append(
                "Evitar corticoide inhalado en EPOC GOLD 1-2 salvo indicacion justificada."
            )

        if payload.open_wound_present and payload.tetanus_booster_planned:
            if payload.tetanus_doses_completed is None:
                diagnostic_actions.append(
                    "Verificar esquema antitetanico previo antes de indicar recuerdo automatico."
                )
            elif (
                payload.tetanus_doses_completed
                and payload.years_since_last_tetanus_dose is not None
                and payload.years_since_last_tetanus_dose < 10
            ):
                safety_blocks.append(
                    "Refuerzo antitetanico no automatico: esquema completo y ultima dosis <10 anos."
                )

        return optimization_actions, safety_blocks, diagnostic_actions

    @staticmethod
    def _severity(
        *,
        critical_alerts: list[str],
        safety_blocks: list[str],
        therapeutic_actions: list[str],
    ) -> str:
        if critical_alerts:
            return "critical"
        if safety_blocks:
            return "high"
        if therapeutic_actions:
            return "medium"
        return "low"

    @staticmethod
    def build_recommendation(
        payload: GeriatricsSupportProtocolRequest,
    ) -> GeriatricsSupportProtocolRecommendation:
        """Genera recomendacion operativa geriatrica para validacion humana."""
        aging_interpretation, diagnostic_aging, trace_aging = (
            GeriatricsSupportProtocolService._aging_morphology_pathway(payload)
        )
        critical_immob, therapeutic_immob, safety_immob, trace_immob = (
            GeriatricsSupportProtocolService._immobility_pathway(payload)
        )
        (
            critical_delirium,
            diagnostic_delirium,
            therapeutic_delirium,
            safety_delirium,
            trace_delirium,
        ) = GeriatricsSupportProtocolService._delirium_pathway(payload)
        optimization_start, safety_start, diagnostic_start = (
            GeriatricsSupportProtocolService._start_v3_pathway(payload)
        )

        critical_alerts = critical_immob + critical_delirium
        diagnostic_actions = diagnostic_aging + diagnostic_delirium + diagnostic_start
        therapeutic_actions = therapeutic_immob + therapeutic_delirium
        safety_blocks = safety_immob + safety_delirium + safety_start
        interpretability_trace = trace_aging + trace_immob + trace_delirium
        severity = GeriatricsSupportProtocolService._severity(
            critical_alerts=critical_alerts,
            safety_blocks=safety_blocks,
            therapeutic_actions=therapeutic_actions,
        )

        return GeriatricsSupportProtocolRecommendation(
            severity_level=severity,
            critical_alerts=critical_alerts,
            aging_context_interpretation=aging_interpretation,
            diagnostic_actions=diagnostic_actions,
            therapeutic_actions=therapeutic_actions,
            pharmacologic_optimization_actions=optimization_start,
            safety_blocks=safety_blocks,
            interpretability_trace=interpretability_trace,
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. "
                "Requiere validacion por geriatria/equipo de urgencias."
            ),
        )
