"""
Motor de recomendaciones de humanizacion pediatrica en alta complejidad.

La salida es operativa y exige validacion humana antes de ejecutar decisiones.
"""
from app.schemas.humanization_protocol import (
    HumanizationProtocolRecommendation,
    HumanizationProtocolRequest,
)


class HumanizationProtocolService:
    """Construye planes de apoyo familiar, comunicacion y coordinacion clinica."""

    @staticmethod
    def _build_communication_plan(payload: HumanizationProtocolRequest) -> list[str]:
        plan: list[str] = [
            "Explicar situacion en lenguaje claro, sin tecnicismos innecesarios.",
            "Confirmar comprension con tecnica de repeticion por parte de la familia.",
        ]
        if payload.family_understanding_level <= 4:
            plan.append("Programar segundo bloque informativo en menos de 2 horas.")
        if payload.emotional_distress_level >= 7:
            plan.append("Realizar comunicacion en entorno tranquilo con pausas guiadas.")
        return plan

    @staticmethod
    def _build_family_integration_plan(payload: HumanizationProtocolRequest) -> list[str]:
        plan: list[str] = []
        if payload.family_present:
            plan.append("Incluir a tutores en el plan diario como co-terapeutas informados.")
        else:
            plan.append("Activar contacto remoto estructurado con tutores en cada hito clinico.")
        if payload.sibling_support_needed:
            plan.append("Coordinar soporte para hermanos con trabajo social/psicologia.")
        if payload.informed_consent_status in {"pendiente", "rechazado"}:
            plan.append("Revisar consentimiento con enfoque gradual y dudas abiertas.")
        return plan

    @staticmethod
    def _build_support_plan(payload: HumanizationProtocolRequest) -> list[str]:
        plan: list[str] = []
        if payload.social_risk_flags:
            plan.append("Escalar a trabajo social por factores de riesgo psicosocial.")
        if payload.needs_spiritual_support:
            plan.append("Ofrecer atencion espiritual voluntaria segun preferencia familiar.")
        if payload.emotional_distress_level >= 8:
            plan.append("Solicitar intervencion de psicologia clinica pediatrica.")
        if not plan:
            plan.append("Mantener seguimiento psicosocial estandar en unidad.")
        return plan

    @staticmethod
    def _build_innovation_coordination_plan(payload: HumanizationProtocolRequest) -> list[str]:
        plan: list[str] = []
        if payload.primary_context == "neuro_oncologia":
            plan.append("Coordinar sesion breve neuro-oncologia + familia para plan actualizado.")
        if payload.has_clinical_trial_option:
            plan.append("Valorar pre-elegibilidad a ensayo clinico con revision multidisciplinar.")
            plan.append("Sincronizar ventana operativa con anestesia y equipo de investigacion.")
        if not plan:
            plan.append("Mantener coordinacion clinica convencional segun protocolo de servicio.")
        return plan

    @staticmethod
    def _build_team_care_plan(payload: HumanizationProtocolRequest) -> list[str]:
        plan: list[str] = []
        if payload.professional_burnout_risk == "high":
            plan.append("Activar pausa operativa de equipo y reparto de carga asistencial.")
        if payload.professional_burnout_risk in {"medium", "high"}:
            plan.append("Planificar micro-huddle de 10 minutos al cierre de turno.")
        if "anestesia" not in [item.lower() for item in payload.multidisciplinary_team]:
            plan.append("Revisar necesidad de incluir anestesia en procedimientos complejos.")
        return plan

    @staticmethod
    def _build_alerts(payload: HumanizationProtocolRequest) -> list[str]:
        alerts: list[str] = []
        if payload.emotional_distress_level >= 8:
            alerts.append("Distres emocional alto: priorizar contencion familiar inmediata.")
        if payload.family_understanding_level <= 3:
            alerts.append("Riesgo de baja comprension: reforzar comunicacion estructurada.")
        if payload.informed_consent_status == "rechazado":
            alerts.append("Consentimiento rechazado: requiere reevaluacion clinico-legal humana.")
        if payload.primary_context == "ensayo_clinico" and not payload.has_clinical_trial_option:
            alerts.append("Contexto de ensayo sin opcion activa: validar coherencia del caso.")
        return alerts

    @staticmethod
    def build_recommendation(
        payload: HumanizationProtocolRequest,
    ) -> HumanizationProtocolRecommendation:
        """Genera recomendacion operativa con enfoque de humanizacion pediatrica."""
        return HumanizationProtocolRecommendation(
            communication_plan=HumanizationProtocolService._build_communication_plan(payload),
            family_integration_plan=HumanizationProtocolService._build_family_integration_plan(
                payload
            ),
            support_plan=HumanizationProtocolService._build_support_plan(payload),
            innovation_coordination_plan=(
                HumanizationProtocolService._build_innovation_coordination_plan(payload)
            ),
            team_care_plan=HumanizationProtocolService._build_team_care_plan(payload),
            alerts=HumanizationProtocolService._build_alerts(payload),
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. Requiere validacion clinica humana."
            ),
        )
