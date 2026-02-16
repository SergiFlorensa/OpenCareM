"""
Motor de soporte medico-legal para operacion en urgencias.

Su objetivo es ordenar alertas, checklist documental y acciones
de mitigacion de riesgo legal para validacion humana.
"""
from app.schemas.medicolegal_ops import (
    MedicolegalOpsRecommendation,
    MedicolegalOpsRequest,
)


class MedicolegalOpsService:
    """Construye recomendacion operativa medico-legal interpretable."""

    @staticmethod
    def _is_pediatric_life_saving_conflict(payload: MedicolegalOpsRequest) -> bool:
        return (
            payload.patient_age_years < 18
            and payload.life_threatening_condition
            and payload.blood_transfusion_indicated
            and payload.parental_religious_refusal_life_saving_treatment
        )

    @staticmethod
    def _build_critical_alerts(payload: MedicolegalOpsRequest) -> list[str]:
        alerts: list[str] = []
        if payload.triage_wait_minutes is not None and payload.triage_wait_minutes > 5:
            alerts.append("Triaje fuera de ventana objetivo (<5 min) en urgencias.")
        if (
            payload.first_medical_contact_minutes is not None
            and payload.first_medical_contact_minutes > 30
        ):
            alerts.append("Valoracion medica inicial fuera de objetivo operativo (<30 min).")
        if (
            payload.invasive_procedure_planned
            and not payload.informed_consent_documented
            and payload.patient_has_decision_capacity
        ):
            alerts.append("Procedimiento invasivo sin consentimiento documentado.")
        if payload.intoxication_forensic_context and not payload.chain_of_custody_started:
            alerts.append("Contexto forense sin cadena de custodia iniciada.")
        if payload.non_natural_death_suspected:
            alerts.append("Sospecha de muerte no natural: no emitir certificado de defuncion.")
        if MedicolegalOpsService._is_pediatric_life_saving_conflict(payload):
            alerts.append(
                "Conflicto bioetico critico: menor en riesgo vital con rechazo "
                "representado de tratamiento potencialmente salvador."
            )
            alerts.append(
                "Priorizar interes superior del menor y preservacion de la vida "
                "como bien juridico prevalente."
            )
            if (
                payload.legal_representatives_deceased
                or not payload.legal_representative_present
            ):
                alerts.append(
                    "Desamparo legal inmediato: equipo clinico asume deber "
                    "de proteccion del menor."
                )
        return alerts

    @staticmethod
    def _build_required_documents(payload: MedicolegalOpsRequest) -> list[str]:
        docs: list[str] = ["Registro clinico estructurado con hallazgos positivos y negativos."]
        if payload.invasive_procedure_planned:
            docs.append("Consentimiento informado (escrito si procedimiento invasivo/riesgo).")
        if payload.suspected_crime_injuries:
            docs.append("Parte judicial de lesiones con terminologia medico-legal.")
        if payload.intoxication_forensic_context:
            docs.append("Formulario de cadena de custodia con fechas/firmas.")
        if payload.refuses_care:
            docs.append("Documento de alta voluntaria con riesgos explicados.")
        if payload.involuntary_psychiatric_admission:
            docs.append("Comunicacion de ingreso involuntario a Psiquiatria/Juzgado.")
        if payload.patient_escape_risk:
            docs.append("Registro de protocolo de fuga y notificacion a CFSE/Juzgado.")
        if MedicolegalOpsService._is_pediatric_life_saving_conflict(payload):
            docs.append(
                "Registro de ponderacion bioetica: interes superior del menor, "
                "riesgo vital e intervencion proporcional."
            )
            docs.append(
                "Nota clinico-legal de estado de necesidad terapeutica y "
                "fundamento de decision urgente."
            )
            docs.append(
                "Registro de comunicacion post-estabilizacion con asesoria "
                "juridica, trabajo social y autoridad judicial."
            )
        return docs

    @staticmethod
    def _build_operational_actions(payload: MedicolegalOpsRequest) -> list[str]:
        actions: list[str] = []
        if payload.triage_wait_minutes is not None and payload.triage_wait_minutes > 5:
            actions.append("Escalar saturacion operativa y priorizar triaje seguro.")
        if payload.refuses_care and payload.patient_has_decision_capacity:
            actions.append("Confirmar decision informada y registrar riesgos especificos.")
        if payload.refuses_care and not payload.patient_has_decision_capacity:
            actions.append(
                "No formalizar alta voluntaria; activar proteccion clinica por incapacidad."
            )
        if payload.public_health_risk:
            actions.append("Aplicar excepcion por salud publica segun normativa vigente.")
        if payload.intoxication_forensic_context and payload.chain_of_custody_started:
            actions.append("Mantener trazabilidad de muestras hasta laboratorio receptor.")
        if payload.non_natural_death_suspected:
            actions.append("Judicializar caso y coordinar con forense/autoridad competente.")
        if MedicolegalOpsService._is_pediatric_life_saving_conflict(payload):
            actions.append(
                "Activar supervision clinica senior inmediata "
                "(urgencias/pediatria/criticos)."
            )
            actions.append(
                "No demorar medida de soporte vital indicada por tramitacion "
                "judicial cuando riesgo vital es inminente."
            )
            if (
                payload.legal_representatives_deceased
                or not payload.legal_representative_present
            ):
                actions.append(
                    "Proceder bajo deber de proteccion del menor y estado de "
                    "necesidad, con trazabilidad completa de tiempos y motivos."
                )
            if not payload.immediate_judicial_authorization_available:
                actions.append(
                    "Escalar comunicacion judicial tan pronto como la "
                    "estabilizacion lo permita."
                )
        if not actions:
            actions.append("Mantener vigilancia medico-legal estandar y documentacion completa.")
        return actions

    @staticmethod
    def _build_compliance_checklist(payload: MedicolegalOpsRequest) -> list[str]:
        checklist = [
            "Verificar identificacion del paciente y profesional responsable.",
            "Registrar cronologia asistencial (triaje, valoracion, decisiones).",
            "Documentar razon clinica de pruebas e intervenciones.",
        ]
        if payload.invasive_procedure_planned:
            checklist.append("Confirmar consentimiento documentado antes de tecnica invasiva.")
        if payload.intoxication_forensic_context:
            checklist.append("Completar cadena de custodia sin rupturas.")
        if payload.suspected_crime_injuries:
            checklist.append("Emitir parte judicial de lesiones con descripcion forense.")
        if payload.patient_age_years < 16:
            checklist.append("Validar decision con representante legal por minoria de edad.")
        if MedicolegalOpsService._is_pediatric_life_saving_conflict(payload):
            checklist.append(
                "Documentar riesgo vital inminente y proporcionalidad de la medida."
            )
            checklist.append(
                "Registrar causa de imposibilidad de autorizacion judicial inmediata."
            )
            checklist.append(
                "Registrar hora exacta de decision e intervencion en linea temporal."
            )
        return checklist

    @staticmethod
    def _estimate_legal_risk_level(
        critical_alerts: list[str], payload: MedicolegalOpsRequest
    ) -> str:
        if MedicolegalOpsService._is_pediatric_life_saving_conflict(payload):
            return "high"
        if len(critical_alerts) >= 3:
            return "high"
        if len(critical_alerts) >= 1:
            return "medium"
        return "low"

    @staticmethod
    def build_recommendation(
        payload: MedicolegalOpsRequest,
    ) -> MedicolegalOpsRecommendation:
        """Genera recomendacion operativa medico-legal para validacion humana."""
        alerts = MedicolegalOpsService._build_critical_alerts(payload)
        life_preserving_override_recommended = (
            MedicolegalOpsService._is_pediatric_life_saving_conflict(payload)
            and (
                payload.legal_representatives_deceased
                or not payload.legal_representative_present
                or not payload.immediate_judicial_authorization_available
            )
        )
        ethical_legal_basis: list[str] = []
        if MedicolegalOpsService._is_pediatric_life_saving_conflict(payload):
            ethical_legal_basis.extend(
                [
                    "Interes superior del menor como criterio prevalente en riesgo vital.",
                    "Deber de beneficencia y no maleficencia ante dano irreversible evitable.",
                    "Estado de necesidad terapeutica en urgencia extrema.",
                    "Proteccion de autonomia futura del menor preservando su vida.",
                ]
            )
            if (
                payload.legal_representatives_deceased
                or not payload.legal_representative_present
            ):
                ethical_legal_basis.append(
                    "Desamparo de representacion: el equipo clinico asume funcion de garante."
                )
        if life_preserving_override_recommended:
            urgency_summary = (
                "Riesgo vital inminente: se recomienda priorizar medida de soporte vital "
                "indicada sin demoras administrativas, con trazabilidad reforzada."
            )
        elif MedicolegalOpsService._is_pediatric_life_saving_conflict(payload):
            urgency_summary = (
                "Conflicto pediatrico critico activo: mantener escalado clinico-juridico "
                "inmediato y decision centrada en preservacion de vida."
            )
        else:
            urgency_summary = "Sin conflicto pediatrico vital activo en esta evaluacion."
        return MedicolegalOpsRecommendation(
            legal_risk_level=MedicolegalOpsService._estimate_legal_risk_level(alerts, payload),
            life_preserving_override_recommended=life_preserving_override_recommended,
            ethical_legal_basis=ethical_legal_basis,
            urgency_summary=urgency_summary,
            critical_legal_alerts=alerts,
            required_documents=MedicolegalOpsService._build_required_documents(payload),
            operational_actions=MedicolegalOpsService._build_operational_actions(payload),
            compliance_checklist=MedicolegalOpsService._build_compliance_checklist(payload),
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico ni consejo legal formal. "
                "Requiere validacion clinica y juridica humana."
            ),
        )
