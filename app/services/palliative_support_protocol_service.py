"""
Motor operativo de cuidados paliativos para urgencias.

No diagnostica; organiza rutas de riesgo para validacion clinica humana.
"""
from app.schemas.palliative_support_protocol import (
    PalliativeSupportProtocolRecommendation,
    PalliativeSupportProtocolRequest,
)


class PalliativeSupportProtocolService:
    """Construye recomendaciones operativas paliativas en urgencias."""

    @staticmethod
    def _ethical_legal_pathway(
        payload: PalliativeSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        actions: list[str] = []
        safety_blocks: list[str] = []
        trace: list[str] = []

        if payload.patient_rejects_life_prolonging_treatment:
            actions.append(
                "Rechazo a tratamiento: respetar decision del paciente tras informacion "
                "completa y documentada."
            )
            if not payload.informed_consequences_documented:
                safety_blocks.append(
                    "Rechazo informado no documentado: registrar consecuencias y "
                    "capacidad de decision antes de cerrar la decision."
                )
            trace.append("Ruta de rechazo informado del paciente activada.")

        if payload.effort_adequation_planned:
            actions.append(
                "Adecuacion del esfuerzo terapeutico: evitar medidas futiles y "
                "priorizar proporcion clinica."
            )
            if not payload.professional_futility_assessment_documented:
                safety_blocks.append(
                    "Adecuacion sin fundamento de futilidad documentado por el equipo."
                )
            else:
                trace.append("Ruta de adecuacion terapeutica por futilidad activada.")

        if payload.patient_rejects_life_prolonging_treatment and payload.effort_adequation_planned:
            actions.append(
                "Distinguir rechazo del paciente (autonomia) de adecuacion clinica "
                "profesional para seguridad etico-legal."
            )

        if payload.aid_in_dying_request_expressed:
            actions.append(
                "Solicitud de prestacion de ayuda para morir: activar circuito "
                "legal especifico de la LO 3/2021."
            )
            if not payload.aid_in_dying_request_reiterated:
                safety_blocks.append(
                    "Solicitud expresada sin reiteracion documentada: no ejecutar "
                    "procedimientos fuera del circuito legal."
                )
            if not payload.aid_in_dying_process_formalized_per_lo_3_2021:
                safety_blocks.append(
                    "Solicitud sin formalizacion legal completa: bloquear actuacion "
                    "hasta completar requisitos normativos."
                )
            if (
                payload.aid_in_dying_request_reiterated
                and payload.aid_in_dying_process_formalized_per_lo_3_2021
            ):
                actions.append(
                    "Con circuito formalizado, diferenciar modalidad: administracion "
                    "directa (eutanasia) vs autoadministracion (suicidio asistido)."
                )
                trace.append("Ruta legal de ayuda para morir formalizada activada.")

        return actions, safety_blocks, trace

    @staticmethod
    def _opioid_pathway(
        payload: PalliativeSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        actions: list[str] = []
        critical_alerts: list[str] = []
        trace: list[str] = []

        opioid_name = (payload.current_opioid_name or "").strip().lower()
        renal_risk = payload.renal_failure_present or (
            payload.renal_clearance_ml_min is not None and payload.renal_clearance_ml_min < 30
        )
        morphine_in_use = payload.morphine_active or opioid_name == "morfina"

        if renal_risk:
            actions.append(
                "Insuficiencia renal: priorizar opioides con mejor perfil (fentanilo, "
                "metadona o buprenorfina) y evitar acumulacion neurotoxica."
            )
            if morphine_in_use:
                critical_alerts.append(
                    "Morfina activa con insuficiencia renal: riesgo elevado de "
                    "acumulacion de metabolitos neurotoxicos."
                )
                actions.append(
                    "Realizar rotacion opioide preferente a fentanilo o metadona "
                    "(alternativa: buprenorfina segun contexto)."
                )
                trace.append("Regla de seguridad renal con morfina activada.")

        if payload.chronic_pain_baseline_present and not payload.long_acting_opioid_active:
            actions.append(
                "Dolor cronico basal: considerar opioide de vida media larga/liberacion "
                "prolongada para control de base."
            )

        if payload.breakthrough_pain_present:
            if payload.rapid_onset_rescue_opioid_planned:
                actions.append(
                    "Dolor irruptivo: mantener rescate de inicio rapido sobre tratamiento basal."
                )
                if payload.transmucosal_fentanyl_planned:
                    actions.append(
                        "Fentanilo oral transmucoso alineado con recomendacion de rescate rapido."
                    )
            else:
                actions.append(
                    "Dolor irruptivo sin rescate rapido: ajustar pauta para evitar "
                    "infra-tratamiento en picos agudos."
                )

        return actions, critical_alerts, trace

    @staticmethod
    def _advanced_dementia_pathway(
        payload: PalliativeSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        actions: list[str] = []
        critical_alerts: list[str] = []
        trace: list[str] = []

        if payload.advanced_dementia_present and payload.dysphagia_or_oral_intake_refusal:
            actions.append(
                "Demencia avanzada con disfagia/rechazo de ingesta: priorizar alimentacion "
                "de confort."
            )
            if payload.enteral_tube_sng_or_peg_planned:
                critical_alerts.append(
                    "SNG/PEG no indicada de rutina en demencia avanzada por baja "
                    "utilidad y posible aumento de broncoaspiracion."
                )
            if not payload.comfort_feeding_planned:
                actions.append(
                    "Definir explicitamente plan de alimentacion de confort con familia/cuidador."
                )
            trace.append("Ruta de demencia avanzada y nutricion de confort activada.")

        if payload.aspiration_infection_terminal_context:
            actions.append(
                "Broncoaspiracion en fase terminal: valorar medidas de confort y "
                "evitar intervenciones desproporcionadas."
            )
            if (
                payload.hospital_admission_planned
                and not payload.shared_advance_care_plan_available
            ):
                critical_alerts.append(
                    "Decision de ingreso sin plan compartido previo en escenario terminal: "
                    "revaluar proporcionalidad de objetivos."
                )
            if not payload.shared_advance_care_plan_available:
                actions.append(
                    "Iniciar planificacion compartida de objetivos terapeuticos "
                    "con familia/equipo de referencia."
                )

        return actions, critical_alerts, trace

    @staticmethod
    def _delirium_and_neurotoxicity_pathway(
        payload: PalliativeSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        actions: list[str] = []
        critical_alerts: list[str] = []
        safety_blocks: list[str] = []
        trace: list[str] = []

        opioid_neurotoxicity_pattern = (
            payload.renal_function_deterioration_present
            and payload.intense_somnolence_present
            and payload.tactile_hallucinations_present
        )
        if opioid_neurotoxicity_pattern:
            critical_alerts.append(
                "Patron compatible con neurotoxicidad por opioides (fallo renal + "
                "somnolencia intensa + alucinaciones tactiles)."
            )
            actions.append(
                "Reducir dosis opioide al 50% o realizar rotacion a fentanilo/metadona "
                "segun estabilidad clinica."
            )
            trace.append("Regla de triada de neurotoxicidad opioide activada.")

        if payload.delirium_present:
            actions.append("Delirium: buscar y corregir causa subyacente de forma prioritaria.")
            if not payload.reversible_cause_addressed:
                safety_blocks.append(
                    "Delirium sin abordaje etiologico documentado: no limitarse a sedacion "
                    "sintomatica."
                )

            if payload.neuroleptic_planned:
                if payload.persistent_delirium_after_cause_treatment:
                    actions.append(
                        "Uso sintomatico de neuroleptico razonable tras tratar causa reversible."
                    )
                else:
                    safety_blocks.append(
                        "Neuroleptico planificado antes de confirmar persistencia "
                        "post-correccion etiologica."
                    )

            if payload.steroid_psychosis_hyperactive_profile:
                actions.append(
                    "Diferenciar delirium toxico hipoactivo de posible psicosis por "
                    "corticoides (perfil hiperactivo/ansioso)."
                )

        return actions, critical_alerts, safety_blocks, trace

    @staticmethod
    def _severity(
        *,
        critical_alerts: list[str],
        safety_blocks: list[str],
        actions: list[str],
    ) -> str:
        if critical_alerts:
            return "critical"
        if safety_blocks:
            return "high"
        if actions:
            return "medium"
        return "low"

    @staticmethod
    def build_recommendation(
        payload: PalliativeSupportProtocolRequest,
    ) -> PalliativeSupportProtocolRecommendation:
        """Genera recomendacion operativa paliativa para validacion humana."""
        (
            ethical_actions,
            ethical_safety,
            trace_ethical,
        ) = PalliativeSupportProtocolService._ethical_legal_pathway(payload)
        (
            opioid_actions,
            opioid_critical,
            trace_opioid,
        ) = PalliativeSupportProtocolService._opioid_pathway(payload)
        (
            dementia_actions,
            dementia_critical,
            trace_dementia,
        ) = PalliativeSupportProtocolService._advanced_dementia_pathway(payload)
        (
            delirium_actions,
            delirium_critical,
            delirium_safety,
            trace_delirium,
        ) = PalliativeSupportProtocolService._delirium_and_neurotoxicity_pathway(payload)

        critical_alerts = opioid_critical + dementia_critical + delirium_critical
        safety_blocks = ethical_safety + delirium_safety
        all_actions = ethical_actions + opioid_actions + dementia_actions + delirium_actions
        severity = PalliativeSupportProtocolService._severity(
            critical_alerts=critical_alerts,
            safety_blocks=safety_blocks,
            actions=all_actions,
        )

        return PalliativeSupportProtocolRecommendation(
            severity_level=severity,
            critical_alerts=critical_alerts,
            ethical_legal_actions=ethical_actions,
            opioid_safety_actions=opioid_actions,
            dementia_comfort_actions=dementia_actions,
            delirium_management_actions=delirium_actions,
            safety_blocks=safety_blocks,
            interpretability_trace=trace_ethical + trace_opioid + trace_dementia + trace_delirium,
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. "
                "Requiere validacion por paliativos/equipo de urgencias."
            ),
        )
