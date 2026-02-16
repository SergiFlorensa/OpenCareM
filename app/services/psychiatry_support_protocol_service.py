"""
Motor operativo de psiquiatria para urgencias.

No diagnostica; organiza rutas de riesgo para validacion clinica humana.
"""
from app.schemas.psychiatry_support_protocol import (
    PsychiatrySupportProtocolRecommendation,
    PsychiatrySupportProtocolRequest,
)


class PsychiatrySupportProtocolService:
    """Construye recomendaciones operativas de psiquiatria en urgencias."""

    @staticmethod
    def _temporal_triage_pathway(
        payload: PsychiatrySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        triage_actions: list[str] = []
        diagnostic_support: list[str] = []
        trace: list[str] = []

        trauma_cluster = (
            payload.reexperiencing_symptoms
            or payload.avoidance_symptoms
            or payload.hyperarousal_symptoms
        )
        if payload.traumatic_event_exposure and trauma_cluster:
            if payload.days_since_traumatic_event is not None:
                if payload.days_since_traumatic_event < 30:
                    diagnostic_support.append(
                        "Sintomas en dias-semanas post evento grave: "
                        "compatible con reaccion de estres aguda."
                    )
                    trace.append("Clasificacion temporal de estres agudo aplicada.")
                else:
                    diagnostic_support.append(
                        "Persistencia >= 1 mes tras trauma: "
                        "priorizar evaluacion de TEPT."
                    )
                    triage_actions.append(
                        "Escalar seguimiento especializado por duracion prolongada."
                    )
                    trace.append("Umbral temporal de TEPT activado.")
            else:
                diagnostic_support.append(
                    "Completar cronologia del trauma para diferenciar "
                    "estres agudo vs TEPT."
                )

        if payload.psychosocial_stressor_present:
            if (
                payload.days_since_psychosocial_stressor is not None
                and payload.days_since_psychosocial_stressor <= 30
            ):
                diagnostic_support.append(
                    "Inicio en el mes posterior a estresor psicosocial comun: "
                    "considerar trastorno adaptativo."
                )
                trace.append("Ruta operativa de trastorno adaptativo activada.")
            else:
                diagnostic_support.append(
                    "Si no existe evento catastrofico, priorizar evaluacion "
                    "de adaptacion psicosocial."
                )

        return triage_actions, diagnostic_support, trace

    @staticmethod
    def _suicide_risk_pathway(
        payload: PsychiatrySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        triage_actions: list[str] = []
        diagnostic_support: list[str] = []
        trace: list[str] = []

        if payload.age_years < 18 and payload.self_harm_present:
            critical_alerts.append(
                "Autolesiones en menor de edad: elevar riesgo suicida a nivel maximo."
            )
            triage_actions.append(
                "Activar evaluacion psiquiatrica inmediata y observacion estrecha."
            )
            triage_actions.append("Registrar prioridad operativa maxima en triaje.")
            trace.append("Regla infanto-juvenil de riesgo suicida maximo activada.")

        additional_risk_factors = sum(
            [
                payload.prior_suicide_attempt,
                payload.family_history_suicide,
                payload.social_isolation,
                payload.male_sex,
            ]
        )
        if additional_risk_factors >= 2:
            critical_alerts.append(
                "Multiples factores de riesgo suicida acumulados; reforzar "
                "contencion y vigilancia."
            )
            diagnostic_support.append(
                "Documentar antecedentes de intento previo, red de apoyo y "
                "riesgo familiar."
            )

        return critical_alerts, triage_actions, diagnostic_support, trace

    @staticmethod
    def _psychosis_and_prognosis_pathway(
        payload: PsychiatrySupportProtocolRequest,
    ) -> tuple[list[str], list[str]]:
        prognosis_flags: list[str] = []
        diagnostic_support: list[str] = []

        if payload.psychosis_suspected:
            diagnostic_support.append(
                "Ante psicosis, priorizar evaluacion estructurada de sintomas "
                "positivos y negativos."
            )
            if payload.psychosis_onset_acute:
                prognosis_flags.append(
                    "Inicio agudo de psicosis: factor de mejor pronostico operativo."
                )
            if payload.psychosis_early_age_onset:
                prognosis_flags.append(
                    "Inicio temprano de psicosis: factor de mal pronostico."
                )
            if payload.negative_symptoms_predominant:
                prognosis_flags.append(
                    "Predominio de sintomas negativos: riesgo de peor respuesta y "
                    "retraso diagnostico."
                )

        return prognosis_flags, diagnostic_support

    @staticmethod
    def _pharmacologic_safety_pathway(
        payload: PsychiatrySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        pharmacologic_safety_alerts: list[str] = []
        maternal_fetal_actions: list[str] = []
        triage_actions: list[str] = []
        trace: list[str] = []

        planned = (payload.planned_mood_stabilizer or "").strip().lower()
        if payload.bipolar_disorder_known and payload.pregnancy_ongoing:
            maternal_fetal_actions.append(
                "En bipolaridad durante embarazo, priorizar lamotrigina "
                "como estabilizador de referencia."
            )
            if planned in {"litio", "lithium"}:
                critical_alerts.append(
                    "Embarazo + litio: contraindicado por riesgo de anomalia de Ebstein."
                )
            elif planned in {"acido valproico", "valproato", "valproic acid"}:
                critical_alerts.append(
                    "Embarazo + valproato: contraindicado por teratogenia grave."
                )
            elif planned == "carbamazepina":
                pharmacologic_safety_alerts.append(
                    "Embarazo + carbamazepina: alto riesgo de defectos del "
                    "tubo neural y malformaciones craneofaciales."
                )
            elif planned == "lamotrigina":
                maternal_fetal_actions.append(
                    "Lamotrigina seleccionada: mantener monitorizacion "
                    "obstetrica y psiquiatrica estrecha."
                )

        if payload.age_years >= 80 and payload.insomnia_present:
            triage_actions.append(
                "Activar flujo de deteccion de causas secundarias de dolor "
                "antes de sugerir hipnoticos."
            )
            trace.append("Regla de insomnio geriatrico con causa secundaria activada.")
            if payload.pain_secondary_cause_suspected:
                triage_actions.append(
                    "Si el insomnio es secundario a dolor, priorizar analgesia "
                    "inicial (p. ej., paracetamol) y reevaluar."
                )
            if payload.benzodiazepine_planned:
                pharmacologic_safety_alerts.append(
                    "Evitar benzodiacepinas en ancianos por riesgo de caidas, "
                    "delirium y deterioro cognitivo."
                )
            if payload.hypnotic_planned and not payload.pain_secondary_cause_suspected:
                pharmacologic_safety_alerts.append(
                    "No iniciar hipnoticos sin descartar causa secundaria "
                    "de insomnio en >80 anos."
                )

        return (
            critical_alerts,
            pharmacologic_safety_alerts,
            maternal_fetal_actions,
            triage_actions,
            trace,
        )

    @staticmethod
    def _internal_medicine_and_psychodynamics_pathway(
        payload: PsychiatrySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        internal_medicine_alerts: list[str] = []
        psychodynamic_flags: list[str] = []
        critical_alerts: list[str] = []
        diagnostic_support: list[str] = []

        if payload.eating_disorder_suspected:
            if payload.lanugo_present:
                internal_medicine_alerts.append(
                    "Lanugo presente: compatible con desnutricion de trastorno alimentario."
                )
            if payload.hypotension_present:
                internal_medicine_alerts.append(
                    "Hipotension en probable anorexia: vigilar compromiso hemodinamico."
                )
            if payload.sinus_bradycardia_present:
                internal_medicine_alerts.append(
                    "Bradicardia sinusal en probable anorexia: hallazgo fisiopatologico esperado."
                )
            if payload.tachycardia_present:
                critical_alerts.append(
                    "Taquicardia en anorexia no es patron tipico: descartar complicacion aguda."
                )
            if payload.purging_vomiting_present:
                diagnostic_support.append(
                    "Con purgas, solicitar iones y gasometria para detectar "
                    "hipopotasemia/alcalosis hipocloromica."
                )
                if payload.hypokalemia_present or payload.hypochloremic_alkalosis_present:
                    critical_alerts.append(
                        "Complicacion metabolica por purga (hipopotasemia/alcalosis): "
                        "riesgo arrtimico y necesidad de correccion urgente."
                    )

        if payload.delusional_disorder_suspected:
            if payload.defense_projection:
                psychodynamic_flags.append(
                    "Mecanismo de defensa probable: proyeccion."
                )
            if payload.defense_denial:
                psychodynamic_flags.append("Mecanismo de defensa probable: negacion.")
            if payload.defense_reaction_formation:
                psychodynamic_flags.append(
                    "Mecanismo de defensa probable: formacion reactiva."
                )
            if payload.defense_regression:
                psychodynamic_flags.append(
                    "Regresion reportada: menos caracteristica de psicosis delirante."
                )

        return (
            internal_medicine_alerts,
            psychodynamic_flags,
            critical_alerts,
            diagnostic_support,
        )

    @staticmethod
    def _severity(
        *,
        critical_alerts: list[str],
        pharmacologic_safety_alerts: list[str],
        prognosis_flags: list[str],
    ) -> str:
        if critical_alerts:
            return "critical"
        if pharmacologic_safety_alerts:
            return "high"
        if prognosis_flags:
            return "medium"
        return "low"

    @staticmethod
    def build_recommendation(
        payload: PsychiatrySupportProtocolRequest,
    ) -> PsychiatrySupportProtocolRecommendation:
        """Genera recomendacion operativa de psiquiatria para validacion humana."""
        triage_time, diagnostic_time, trace_time = (
            PsychiatrySupportProtocolService._temporal_triage_pathway(payload)
        )
        critical_suicide, triage_suicide, diagnostic_suicide, trace_suicide = (
            PsychiatrySupportProtocolService._suicide_risk_pathway(payload)
        )
        prognosis_flags, diagnostic_psychosis = (
            PsychiatrySupportProtocolService._psychosis_and_prognosis_pathway(payload)
        )
        (
            critical_pharm,
            safety_pharm,
            maternal_fetal_actions,
            triage_pharm,
            trace_pharm,
        ) = PsychiatrySupportProtocolService._pharmacologic_safety_pathway(payload)
        (
            internal_alerts,
            psychodynamic_flags,
            critical_internal,
            diagnostic_internal,
        ) = PsychiatrySupportProtocolService._internal_medicine_and_psychodynamics_pathway(
            payload
        )

        critical_alerts = critical_suicide + critical_pharm + critical_internal
        triage_actions = triage_time + triage_suicide + triage_pharm
        diagnostic_support = (
            diagnostic_time
            + diagnostic_suicide
            + diagnostic_psychosis
            + diagnostic_internal
        )
        interpretability_trace = trace_time + trace_suicide + trace_pharm
        severity = PsychiatrySupportProtocolService._severity(
            critical_alerts=critical_alerts,
            pharmacologic_safety_alerts=safety_pharm,
            prognosis_flags=prognosis_flags,
        )

        return PsychiatrySupportProtocolRecommendation(
            severity_level=severity,
            critical_alerts=critical_alerts,
            triage_actions=triage_actions,
            diagnostic_support=diagnostic_support,
            pharmacologic_safety_alerts=safety_pharm,
            prognosis_flags=prognosis_flags,
            maternal_fetal_actions=maternal_fetal_actions,
            internal_medicine_alerts=internal_alerts,
            psychodynamic_flags=psychodynamic_flags,
            interpretability_trace=interpretability_trace,
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. "
                "Requiere validacion por psiquiatria/equipo de urgencias."
            ),
        )
