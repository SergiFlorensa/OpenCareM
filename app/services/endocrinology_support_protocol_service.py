"""
Motor operativo de endocrinologia y metabolismo para urgencias.

No diagnostica; organiza rutas de riesgo para validacion clinica humana.
"""
from app.schemas.endocrinology_support_protocol import (
    EndocrinologySupportProtocolRecommendation,
    EndocrinologySupportProtocolRequest,
)


class EndocrinologySupportProtocolService:
    """Construye recomendaciones operativas endocrino-metabolicas en urgencias."""

    @staticmethod
    def _metabolic_emergency_pathway(
        payload: EndocrinologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        diagnostic_actions: list[str] = []
        therapeutic_actions: list[str] = []
        trace: list[str] = []

        if payload.suspected_hypoglycemia and not payload.ketosis_present:
            critical_alerts.append(
                "Hipoglucemia sin cetosis: activar flujo de defectos de beta-oxidacion."
            )
            diagnostic_actions.append(
                "Solicitar perfil metabolico urgente con lactato, amonio y dicarboxilicos."
            )
            trace.append("Regla de hipoglucemia hipocetosica aplicada para errores innatos.")
            if payload.fasting_context:
                diagnostic_actions.append(
                    "Contexto de ayuno presente: aumenta sospecha de deficit "
                    "de acil-CoA deshidrogenasa."
                )

        if (
            payload.suspected_hypoglycemia
            and not payload.ketosis_present
            and payload.lactic_acidosis_present
            and payload.hyperammonemia_present
        ):
            critical_alerts.append(
                "Triada bioquimica critica (hipoglucemia hipocetosica + acidosis "
                "lactica + hiperamonemia)."
            )
            therapeutic_actions.append(
                "Escalar a area critica y soporte metabolico urgente segun protocolo local."
            )

        if payload.dicarboxylic_acids_elevated:
            diagnostic_actions.append(
                "Dicarboxilicos elevados: hallazgo de apoyo para bloqueo en beta-oxidacion."
            )

        return critical_alerts, diagnostic_actions, therapeutic_actions, trace

    @staticmethod
    def _thyroid_pathway(
        payload: EndocrinologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        diagnostic_actions: list[str] = []
        therapeutic_actions: list[str] = []
        safety_alerts: list[str] = []
        trace: list[str] = []

        if payload.pediatric_patient and payload.pediatric_growth_deceleration:
            diagnostic_actions.append(
                "Desaceleracion del crecimiento pediatrico: priorizar cribado tiroideo (TSH/T4L)."
            )
            if payload.tsh_elevated:
                diagnostic_actions.append(
                    "TSH elevada: hallazgo principal para hipotiroidismo en contexto compatible."
                )
            if payload.anti_tpo_positive or payload.anti_thyroglobulin_positive:
                diagnostic_actions.append(
                    "Autoinmunidad tiroidea positiva: compatible con tiroiditis de Hashimoto."
                )
            if payload.diffuse_firm_painless_goiter:
                diagnostic_actions.append(
                    "Bocio difuso firme e indoloro: hallazgo fisico de apoyo para Hashimoto."
                )
            trace.append("Ruta de hipotiroidismo pediatrico aplicada.")

        if payload.medullary_thyroid_carcinoma_suspected:
            therapeutic_actions.append(
                "Plan quirurgico de referencia: tiroidectomia total con linfadenectomia central."
            )
            if payload.central_or_lateral_nodes_suspected:
                therapeutic_actions.append(
                    "Si hay afectacion ganglionar lateral, ampliar linfadenectomia lateral."
                )
            if not payload.preop_urinary_metanephrines_completed:
                critical_alerts.append(
                    "Sospecha de CMT sin metanefrinas urinarias preoperatorias: "
                    "descartar feocromocitoma antes de cirugia."
                )
            if payload.thyroglobulin_followup_planned:
                safety_alerts.append(
                    "En CMT, tiroglobulina no es marcador de seguimiento util; "
                    "usar calcitonina y CEA."
                )
            if not payload.calcitonin_available or not payload.cea_available:
                diagnostic_actions.append(
                    "Asegurar marcadores de seguimiento para CMT: calcitonina y CEA."
                )
            if not payload.ret_genetic_study_completed:
                diagnostic_actions.append("Completar estudio genetico del protooncogen RET.")
            trace.append("Ruta operativa de carcinoma medular tiroideo aplicada.")

        return critical_alerts, diagnostic_actions, therapeutic_actions, safety_alerts, trace

    @staticmethod
    def _pituitary_water_adrenal_pathway(
        payload: EndocrinologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        diagnostic_actions: list[str] = []
        therapeutic_actions: list[str] = []
        safety_alerts: list[str] = []
        checklist: list[str] = []

        if (
            payload.hyponatremia_present
            and payload.plasma_hypoosmolarity_present
            and payload.inappropriately_concentrated_urine
        ):
            diagnostic_actions.append(
                "Perfil compatible con SIADH: hiponatremia hipoosmolar con "
                "orina inapropiadamente concentrada."
            )
            if (
                payload.serum_sodium_mmol_l is not None and payload.serum_sodium_mmol_l < 120
            ) or payload.neurologic_symptoms_present:
                critical_alerts.append(
                    "SIADH grave/sintomatica: iniciar suero salino hipertónico a ritmo lento."
                )
            else:
                therapeutic_actions.append(
                    "SIADH cronica/leve: restriccion hidrica y dieta rica en sal."
                )
                if payload.siadh_course_chronic:
                    checklist.append(
                        "Reevaluar sodio seriado en SIADH cronica para evitar correccion brusca."
                    )

            if payload.tolvaptan_planned:
                therapeutic_actions.append(
                    "Tolvaptan: antagonista selectivo V2 indicado segun contexto."
                )
                if payload.water_restriction_planned:
                    safety_alerts.append(
                        "Con tolvaptan, evitar restriccion hidrica estricta y "
                        "mantener acceso libre al agua."
                    )

        if payload.hyperprolactinemia_present:
            diagnostic_actions.append(
                "Antes de RM hipofisaria, descartar embarazo, farmacos "
                "antidopaminergicos e hipotiroidismo primario."
            )
            if not payload.pregnancy_ruled_out:
                diagnostic_actions.append(
                    "Completar descarte de embarazo como causa fisiologica de hiperprolactinemia."
                )
            if payload.prolactin_ng_ml is not None and payload.prolactin_ng_ml >= 100:
                if not payload.pituitary_mri_planned:
                    critical_alerts.append(
                        "Prolactina >=100 ng/mL sin causa explicada: priorizar RM hipofisaria."
                    )
            elif (
                payload.prolactin_ng_ml is not None
                and payload.prolactin_ng_ml > 0
                and not payload.dopamine_antagonist_exposure
                and not payload.primary_hypothyroidism_present
                and not payload.pituitary_mri_planned
            ):
                diagnostic_actions.append(
                    "Hiperprolactinemia inexplicada: considerar RM hipofisaria."
                )

        if (
            payload.refractory_hypotension_present
            and payload.abdominal_pain_or_vomiting_present
            and payload.skin_mucosal_hyperpigmentation_present
            and payload.hyponatremia_present
        ):
            critical_alerts.append(
                "Patron compatible con crisis suprarrenal (Addison) en urgencias."
            )
            therapeutic_actions.append(
                "Escalar manejo de insuficiencia suprarrenal aguda segun protocolo institucional."
            )

        return critical_alerts, diagnostic_actions, therapeutic_actions, safety_alerts, checklist

    @staticmethod
    def _incidentaloma_diabetes_and_confounders_pathway(
        payload: EndocrinologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        therapeutic_actions: list[str] = []
        safety_alerts: list[str] = []
        staging_support: list[str] = []
        context_flags: list[str] = []

        if payload.adrenal_incidentaloma_present:
            if payload.isolated_serum_cortisol_screening_planned:
                critical_alerts.append(
                    "Incidentaloma suprarrenal: rechazar cortisol serico aislado "
                    "como cribado valido."
                )
            if payload.hypertension_present and not payload.aldosterone_renin_ratio_completed:
                critical_alerts.append(
                    "Incidentaloma en hipertenso sin ratio aldosterona/renina: cribado incompleto."
                )
            if not payload.overnight_dexamethasone_1mg_test_completed:
                critical_alerts.append(
                    "Incidentaloma sin test de supresion con 1 mg de dexametasona nocturna."
                )
            if not payload.urinary_metanephrines_24h_completed:
                critical_alerts.append("Incidentaloma sin metanefrinas fraccionadas en orina 24h.")

        if payload.t1d_autoimmunity_positive:
            if (
                payload.glucose_normal
                and not payload.prediabetes_range
                and not payload.diabetes_criteria_present
            ):
                staging_support.append("DM1 estadio 1: autoinmunidad positiva con glucosa normal.")
            elif payload.prediabetes_range and not payload.diabetes_criteria_present:
                staging_support.append(
                    "DM1 estadio 2: autoinmunidad positiva con disglucemia/prediabetes."
                )
            elif payload.diabetes_criteria_present:
                staging_support.append(
                    "DM1 estadio 3: autoinmunidad positiva con criterios clinicos de diabetes."
                )

        if payload.obesity_present and payload.high_cardiovascular_risk:
            therapeutic_actions.append(
                "Priorizar agonista GLP-1 por beneficio en peso y riesgo cardiovascular."
            )
            if not payload.glp1_ra_planned:
                safety_alerts.append(
                    "Valorar inclusion de GLP-1 RA como estrategia de alto valor clinico."
                )
        if payload.weight_loss_priority and payload.pioglitazone_planned:
            safety_alerts.append(
                "Evitar pioglitazona si el objetivo es perder peso "
                "(retencion hidrica/ganancia ponderal)."
            )
        if payload.weight_loss_priority and payload.sulfonylurea_planned:
            safety_alerts.append(
                "Evitar sulfonilureas cuando se prioriza menor hipoglucemia y no ganancia de peso."
            )
        if payload.weight_loss_priority and payload.insulin_planned:
            safety_alerts.append(
                "Reevaluar necesidad de insulinizacion si objetivo principal "
                "es evitar ganancia de peso."
            )

        if payload.hypercalcemia_present and payload.thiazide_exposure:
            context_flags.append(
                "Tiazidas pueden explicar hipercalcemia; descartar causa "
                "farmacologica antes de hiperparatiroidismo primario."
            )
        if (
            payload.chronic_alcohol_use
            and payload.hypertriglyceridemia_present
            and payload.hdl_low_present
        ):
            context_flags.append(
                "Perfil compatible con sindrome metabolico asociado a alcohol "
                "(hipertrigliceridemia y descenso de HDL)."
            )

        if payload.insulin_resistance_suspected and payload.hexokinase2_downregulation_reported:
            context_flags.append(
                "Resistencia insulinica con menor expresion de exoquinasa 2 reportada."
            )
        if payload.insulin_resistance_suspected and payload.hepatic_foxo1_activation_reported:
            context_flags.append(
                "Activacion hepatica de genes gluconeogenicos mediada por FoxO1 no fosforilado."
            )

        return critical_alerts, therapeutic_actions, safety_alerts, staging_support, context_flags

    @staticmethod
    def _severity(
        *,
        critical_alerts: list[str],
        safety_alerts: list[str],
        staging_support: list[str],
        context_flags: list[str],
    ) -> str:
        if critical_alerts:
            return "critical"
        if safety_alerts:
            return "high"
        if staging_support or context_flags:
            return "medium"
        return "low"

    @staticmethod
    def build_recommendation(
        payload: EndocrinologySupportProtocolRequest,
    ) -> EndocrinologySupportProtocolRecommendation:
        """Genera recomendacion operativa endocrino-metabolica para validacion humana."""
        (
            critical_met,
            diagnostic_met,
            therapeutic_met,
            trace_met,
        ) = EndocrinologySupportProtocolService._metabolic_emergency_pathway(payload)
        (
            critical_thy,
            diagnostic_thy,
            therapeutic_thy,
            safety_thy,
            trace_thy,
        ) = EndocrinologySupportProtocolService._thyroid_pathway(payload)
        (
            critical_pit,
            diagnostic_pit,
            therapeutic_pit,
            safety_pit,
            checklist_pit,
        ) = EndocrinologySupportProtocolService._pituitary_water_adrenal_pathway(payload)
        (
            critical_misc,
            therapeutic_misc,
            safety_misc,
            staging_support,
            context_flags,
        ) = EndocrinologySupportProtocolService._incidentaloma_diabetes_and_confounders_pathway(
            payload
        )

        critical_alerts = critical_met + critical_thy + critical_pit + critical_misc
        diagnostic_actions = diagnostic_met + diagnostic_thy + diagnostic_pit
        therapeutic_actions = therapeutic_met + therapeutic_thy + therapeutic_pit + therapeutic_misc
        safety_alerts = safety_thy + safety_pit + safety_misc
        interpretability_trace = trace_met + trace_thy
        severity = EndocrinologySupportProtocolService._severity(
            critical_alerts=critical_alerts,
            safety_alerts=safety_alerts,
            staging_support=staging_support,
            context_flags=context_flags,
        )

        return EndocrinologySupportProtocolRecommendation(
            severity_level=severity,
            critical_alerts=critical_alerts,
            diagnostic_actions=diagnostic_actions,
            therapeutic_actions=therapeutic_actions,
            pharmacologic_safety_alerts=safety_alerts,
            screening_checklist=checklist_pit,
            diabetes_staging_support=staging_support,
            metabolic_context_flags=context_flags,
            interpretability_trace=interpretability_trace,
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. "
                "Requiere validacion por endocrinologia/equipo de urgencias."
            ),
        )
