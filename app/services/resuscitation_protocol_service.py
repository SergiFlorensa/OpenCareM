"""
Motor operativo de reanimacion y soporte vital en urgencias.

No diagnostica ni sustituye protocolos ACLS/BLS institucionales.
"""
from app.schemas.resuscitation_protocol import (
    ResuscitationProtocolRecommendation,
    ResuscitationProtocolRequest,
)

_SHOCKABLE_RHYTHMS = {"vf", "pulseless_vt"}
_NON_SHOCKABLE_RHYTHMS = {"asystole", "pea"}


class ResuscitationProtocolService:
    """Construye recomendaciones operativas para escenarios de reanimacion."""

    @staticmethod
    def _narrow_pulse_pressure(payload: ResuscitationProtocolRequest) -> bool:
        if payload.systolic_bp_mm_hg is None or payload.diastolic_bp_mm_hg is None:
            return False
        return (payload.systolic_bp_mm_hg - payload.diastolic_bp_mm_hg) < 30

    @staticmethod
    def _is_unstable_with_pulse(payload: ResuscitationProtocolRequest) -> bool:
        return any(
            [
                payload.hypotension,
                payload.altered_mental_status,
                payload.shock_signs,
                payload.ischemic_chest_pain,
                payload.acute_heart_failure,
                ResuscitationProtocolService._narrow_pulse_pressure(payload),
            ]
        )

    @staticmethod
    def _severity(payload: ResuscitationProtocolRequest) -> str:
        if payload.context_type == "cardiac_arrest":
            return "critical"
        if payload.context_type == "post_rosc" and (
            payload.comatose_post_rosc or payload.map_mm_hg is not None
        ):
            if payload.comatose_post_rosc or (
                payload.map_mm_hg is not None and payload.map_mm_hg < 65
            ):
                return "critical"
            return "high"
        if payload.context_type in {"tachyarrhythmia_with_pulse", "bradyarrhythmia_with_pulse"}:
            return (
                "high"
                if ResuscitationProtocolService._is_unstable_with_pulse(payload)
                else "medium"
            )
        return "medium"

    @staticmethod
    def _rhythm_classification(payload: ResuscitationProtocolRequest) -> str:
        if payload.rhythm in _SHOCKABLE_RHYTHMS:
            return "shockable_arrest"
        if payload.rhythm in _NON_SHOCKABLE_RHYTHMS:
            return "non_shockable_arrest"
        if payload.rhythm in {"svt_flutter", "af", "vt_monomorphic"}:
            return "tachyarrhythmia_with_pulse"
        if payload.rhythm == "vt_polymorphic":
            return "polymorphic_ventricular_tachycardia"
        return "advanced_bradyarrhythmia"

    @staticmethod
    def _shock_recommended(
        payload: ResuscitationProtocolRequest, rhythm_classification: str
    ) -> bool:
        if rhythm_classification == "shockable_arrest":
            return True
        if payload.rhythm == "vt_polymorphic":
            return True
        if rhythm_classification == "tachyarrhythmia_with_pulse":
            return ResuscitationProtocolService._is_unstable_with_pulse(payload)
        return False

    @staticmethod
    def _cpr_quality_ok(payload: ResuscitationProtocolRequest) -> bool | None:
        if payload.context_type != "cardiac_arrest":
            return None
        if (
            payload.compression_depth_cm is None
            or payload.compression_rate_per_min is None
            or payload.interruption_seconds is None
            or payload.etco2_mm_hg is None
        ):
            return None
        return (
            payload.compression_depth_cm >= 5
            and 100 <= payload.compression_rate_per_min <= 120
            and payload.interruption_seconds <= 10
            and payload.etco2_mm_hg >= 10
        )

    @staticmethod
    def _primary_actions(
        payload: ResuscitationProtocolRequest, shock_recommended: bool
    ) -> list[str]:
        actions: list[str] = []
        if payload.context_type == "cardiac_arrest":
            actions.append("Iniciar RCP de alta calidad con interrupciones minimas.")
            if shock_recommended:
                actions.append(
                    "Aplicar desfibrilacion inmediata segun ritmo y energia recomendada."
                )
            else:
                actions.append("Confirmar ritmo no desfibrilable y mantener ciclos de RCP.")
        if payload.context_type == "tachyarrhythmia_with_pulse":
            if ResuscitationProtocolService._is_unstable_with_pulse(payload):
                actions.append(
                    "Priorizar cardioversion sincronizada por inestabilidad hemodinamica."
                )
            else:
                actions.append("Valorar control de frecuencia/ritmo y monitorizacion estrecha.")
        if payload.context_type == "bradyarrhythmia_with_pulse":
            actions.append("Evaluar bradicardia inestable y preparar marcapasos transcutaneo.")
        if payload.context_type == "post_rosc":
            actions.append("Optimizar hemodinamica y ventilacion para prevenir dano secundario.")
        return actions

    @staticmethod
    def _medication_actions(
        payload: ResuscitationProtocolRequest, shock_recommended: bool
    ) -> list[str]:
        actions: list[str] = []
        if payload.context_type == "cardiac_arrest":
            if shock_recommended:
                actions.append("Administrar adrenalina 1 mg cada 3-5 min tras segunda descarga.")
                actions.append(
                    "Valorar amiodarona 300 mg (o lidocaina alternativa) tras tercera descarga."
                )
            else:
                actions.append("Administrar adrenalina 1 mg cada 3-5 min de forma inmediata.")
        if payload.context_type == "bradyarrhythmia_with_pulse":
            actions.append("Atropina 1 mg inicial (maximo 3 mg) si no hay contraindicaciones.")
            actions.append(
                "Si refractaria, valorar infusion de dopamina "
                "(5-20 mcg/kg/min) o adrenalina (2-10 mcg/min)."
            )
        if payload.opioid_suspected:
            actions.append("Administrar naloxona precoz si se sospecha intoxicacion por opiaceos.")
        if (
            payload.context_type == "post_rosc"
            and payload.map_mm_hg is not None
            and payload.map_mm_hg < 65
        ):
            actions.append("Valorar norepinefrina para objetivo de PAM >= 65 mmHg.")
        return actions

    @staticmethod
    def _electrical_therapy_plan(
        payload: ResuscitationProtocolRequest,
        *,
        rhythm_classification: str,
        shock_recommended: bool,
    ) -> list[str]:
        plan: list[str] = []
        if rhythm_classification == "shockable_arrest":
            plan.append(
                "Desfibrilacion no sincronizada inmediata: 200 J bifasico "
                "o energia maxima disponible."
            )
            plan.append("No retrasar descarga por sedoanalgesia en paro sin pulso.")
            return plan
        if payload.rhythm == "vt_polymorphic":
            plan.append(
                "TV polimorfica: realizar desfibrilacion no sincronizada "
                "(200 J bifasico o 360 J monofasico)."
            )
            return plan
        if rhythm_classification == "tachyarrhythmia_with_pulse" and shock_recommended:
            plan.append(
                "Activar modo sincronizado y confirmar marcas sobre cada onda R "
                "antes de descargar."
            )
            if payload.rhythm == "svt_flutter":
                plan.append("Cardioversion sincronizada: 50-100 J inicial.")
            elif payload.rhythm == "af":
                plan.append(
                    "Cardioversion sincronizada: 120-200 J bifasico "
                    "(escalar a maxima energia si falla)."
                )
            elif payload.rhythm == "vt_monomorphic":
                plan.append("Cardioversion sincronizada: 100 J inicial.")
            plan.append(
                "Evitar fenomeno R sobre T: no descargar sin sincronizacion "
                "en ritmos organizados con pulso."
            )
            return plan
        if rhythm_classification == "tachyarrhythmia_with_pulse":
            plan.append(
                "Sin inestabilidad mayor: priorizar tratamiento medico y "
                "reevaluacion hemodinamica continua."
            )
            return plan
        if payload.context_type == "bradyarrhythmia_with_pulse":
            plan.append(
                "Bradiarritmia avanzada: considerar marcapasos transcutaneo "
                "si deterioro hemodinamico."
            )
        return plan

    @staticmethod
    def _sedoanalgesia_plan(
        payload: ResuscitationProtocolRequest,
        *,
        rhythm_classification: str,
        shock_recommended: bool,
    ) -> list[str]:
        plan: list[str] = []
        if rhythm_classification in {"shockable_arrest", "non_shockable_arrest"}:
            plan.append("En paro sin pulso no retrasar desfibrilacion/RCP por sedacion.")
            return plan
        if payload.rhythm == "vt_polymorphic":
            plan.append("Si pierde pulso, priorizar desfibrilacion inmediata sin demoras.")
            return plan
        if rhythm_classification == "tachyarrhythmia_with_pulse" and shock_recommended:
            if payload.hypotension or payload.shock_signs:
                plan.append(
                    "Fentanilo 0.5-1 mcg/kg (escenario muy inestable) "
                    "aprox. 3.5 min antes de descarga."
                )
            else:
                plan.append("Fentanilo 1-3 mcg/kg aprox. 3.5 min antes de descarga.")
            plan.append(
                "Etomidato 0.1-0.15 mg/kg 15-40 s antes "
                "(hipnotico de eleccion por estabilidad hemodinamica)."
            )
            plan.append(
                "Alternativa: propofol 1-1.5 mg/kg con precaucion por hipotension; "
                "considerar lidocaina IV previa para dolor en vena."
            )
            return plan
        return plan

    @staticmethod
    def _pre_shock_safety_checklist(
        payload: ResuscitationProtocolRequest,
        *,
        rhythm_classification: str,
    ) -> list[str]:
        checklist = [
            "Aplicar gel/pasta conductora suficiente para reducir impedancia.",
            "Aviso de seguridad: fuera equipo, fuera paciente, fuera oxigeno.",
            "Retirar fuente de oxigeno de alto flujo del campo inmediato.",
        ]
        if rhythm_classification == "tachyarrhythmia_with_pulse":
            checklist.append("Verificar modo sincronizado activo y marcas de onda R visibles.")
        else:
            checklist.append("Confirmar descarga no sincronizada para ritmo caotico o sin pulso.")
        if payload.pregnant:
            checklist.append(
                "Mantener desplazamiento uterino lateral manual durante todo el proceso."
            )
        return checklist

    @staticmethod
    def _ventilation_actions(payload: ResuscitationProtocolRequest) -> list[str]:
        actions: list[str] = []
        if payload.context_type == "cardiac_arrest":
            actions.append(
                "Si ventilador en RCP: FiO2 100%, PEEP 0, trigger off, "
                "FR 10/min y VT 8 ml/kg peso ideal."
            )
            actions.append(
                "Usar capnografia continua para confirmar via aerea y calidad de compresiones."
            )
        if payload.context_type == "post_rosc":
            actions.append("Objetivo post-ROSC: SpO2 92-98% y PaCO2 35-45 mmHg.")
            if payload.comatose_post_rosc:
                actions.append("Valorar manejo de temperatura objetivo (32-36°C) durante 24h.")
        if payload.opioid_suspected:
            actions.append("Priorizar ventilacion de rescate efectiva en sospecha de opiaceos.")
        return actions

    @staticmethod
    def _reversible_causes_checklist(payload: ResuscitationProtocolRequest) -> list[str]:
        checklist = [
            "Hipovolemia",
            "Hipoxia",
            "Acidosis (H+)",
            "Hipo/Hiperpotasemia",
            "Hipotermia",
            "Neumotorax a tension",
            "Taponamiento cardiaco",
            "Toxinas",
            "Trombosis pulmonar o coronaria",
        ]
        if payload.pregnant:
            checklist.extend(
                [
                    "Anestesia: complicaciones de via aerea o bloqueo neuroaxial",
                    "Bleeding: hemorragia obstetrica masiva",
                    "Cardiovascular: IAM/miocardiopatia periparto",
                    "Drugs: toxicidad por magnesio o anestesicos locales",
                    "Embolismo: TEP o embolia de liquido amniotico",
                    "Fiebre: desestabilizacion termica",
                    "Hipertension: preeclampsia/eclampsia",
                ]
            )
        return checklist

    @staticmethod
    def _special_situation_actions(payload: ResuscitationProtocolRequest) -> list[str]:
        actions: list[str] = []
        if payload.pregnant:
            actions.append(
                "Activar codigo obstetrico con equipo multidisciplinar: "
                "obstetricia, anestesiologia, neonatologia y enfermeria critica."
            )
            actions.append(
                "Mantener desplazamiento uterino lateral manual 15-30 grados "
                "priorizando compresiones en superficie firme."
            )
            actions.append(
                "Usar acceso vascular por encima del diafragma para farmacos de reanimacion."
            )
            if payload.fetal_monitor_connected:
                actions.append("Desconectar monitor fetal durante RCP para evitar interferencias.")
            if payload.context_type == "cardiac_arrest" and (
                payload.uterine_fundus_at_or_above_umbilicus
                or (payload.gestational_weeks is not None and payload.gestational_weeks >= 20)
            ):
                actions.append(
                    "Sospechar compresion aortocava relevante y mantener alivio mecanico continuo."
                )
            if (
                payload.context_type == "cardiac_arrest"
                and payload.minutes_since_arrest is not None
            ):
                if payload.minutes_since_arrest >= 4 and not payload.has_pulse:
                    actions.append(
                        "Aplicar regla 4-5 min: iniciar histerotomia resucitativa al minuto 4 "
                        "si no hay ROSC."
                    )
                if payload.minutes_since_arrest >= 5 and not payload.has_pulse:
                    actions.append(
                        "Objetivo operativo: extraccion fetal al minuto 5 "
                        "para mejorar ROSC materno."
                    )
            if payload.magnesium_infusion_active and payload.magnesium_toxicity_suspected:
                actions.append(
                    "Sospecha de toxicidad por magnesio: suspender infusion y administrar "
                    "gluconato/cloruro de calcio 1 g IV."
                )
            if payload.context_type == "cardiac_arrest":
                actions.append(
                    "Preparar neonatologia para recepcion " "y reanimacion neonatal avanzada."
                )
        return actions

    @staticmethod
    def _sla_alerts(payload: ResuscitationProtocolRequest) -> list[str]:
        alerts: list[str] = []
        if payload.door_ecg_minutes is not None and payload.door_ecg_minutes > 10:
            alerts.append("SLA puerta-electro incumplido (>10 min).")
        if payload.symptom_onset_minutes is not None and payload.symptom_onset_minutes > 360:
            alerts.append("Demora prolongada desde inicio de sintomas.")
        return alerts

    @staticmethod
    def _alerts(
        payload: ResuscitationProtocolRequest,
        *,
        severity_level: str,
        cpr_quality_ok: bool | None,
    ) -> list[str]:
        alerts: list[str] = []
        if severity_level == "critical":
            alerts.append("Escenario critico: validar decisiones de forma inmediata.")
        if cpr_quality_ok is False:
            alerts.append("Calidad de RCP por debajo de objetivo operativo.")
        if (
            payload.context_type == "post_rosc"
            and payload.map_mm_hg is not None
            and payload.map_mm_hg < 65
        ):
            alerts.append("PAM por debajo de objetivo post-ROSC.")
        if payload.oxygen_saturation_percent is not None and payload.oxygen_saturation_percent < 90:
            alerts.append("Hipoxemia significativa detectada.")
        if payload.pregnant and payload.access_above_diaphragm_secured is False:
            alerts.append(
                "Acceso vascular por encima del diafragma " "pendiente en paciente gestante."
            )
        if (
            payload.pregnant
            and payload.context_type == "cardiac_arrest"
            and payload.minutes_since_arrest is not None
            and payload.minutes_since_arrest >= 4
            and not payload.has_pulse
        ):
            alerts.append("Ventana critica 4-5 min activa para histerotomia resucitativa.")
        if payload.magnesium_infusion_active and payload.magnesium_toxicity_suspected:
            alerts.append("Riesgo de toxicidad por magnesio en contexto obstetrico critico.")
        if (
            payload.context_type == "tachyarrhythmia_with_pulse"
            and ResuscitationProtocolService._narrow_pulse_pressure(payload)
        ):
            alerts.append("Presion de pulso estrecha: posible bajo gasto hemodinamico.")
        return alerts

    @staticmethod
    def build_recommendation(
        payload: ResuscitationProtocolRequest,
    ) -> ResuscitationProtocolRecommendation:
        """Genera recomendacion operativa de reanimacion para validacion humana."""
        severity_level = ResuscitationProtocolService._severity(payload)
        rhythm_classification = ResuscitationProtocolService._rhythm_classification(payload)
        shock_recommended = ResuscitationProtocolService._shock_recommended(
            payload, rhythm_classification
        )
        cpr_quality_ok = ResuscitationProtocolService._cpr_quality_ok(payload)
        return ResuscitationProtocolRecommendation(
            severity_level=severity_level,
            rhythm_classification=rhythm_classification,
            shock_recommended=shock_recommended,
            cpr_quality_ok=cpr_quality_ok,
            primary_actions=ResuscitationProtocolService._primary_actions(
                payload, shock_recommended
            ),
            medication_actions=ResuscitationProtocolService._medication_actions(
                payload, shock_recommended
            ),
            electrical_therapy_plan=ResuscitationProtocolService._electrical_therapy_plan(
                payload,
                rhythm_classification=rhythm_classification,
                shock_recommended=shock_recommended,
            ),
            sedoanalgesia_plan=ResuscitationProtocolService._sedoanalgesia_plan(
                payload,
                rhythm_classification=rhythm_classification,
                shock_recommended=shock_recommended,
            ),
            pre_shock_safety_checklist=ResuscitationProtocolService._pre_shock_safety_checklist(
                payload,
                rhythm_classification=rhythm_classification,
            ),
            ventilation_actions=ResuscitationProtocolService._ventilation_actions(payload),
            reversible_causes_checklist=ResuscitationProtocolService._reversible_causes_checklist(
                payload
            ),
            special_situation_actions=ResuscitationProtocolService._special_situation_actions(
                payload
            ),
            sla_alerts=ResuscitationProtocolService._sla_alerts(payload),
            alerts=ResuscitationProtocolService._alerts(
                payload,
                severity_level=severity_level,
                cpr_quality_ok=cpr_quality_ok,
            ),
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. Requiere validacion clinica humana."
            ),
        )
