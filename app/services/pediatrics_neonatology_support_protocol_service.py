"""
Motor operativo de pediatria y neonatologia para urgencias.

No diagnostica; organiza rutas de riesgo para validacion clinica humana.
"""
from app.schemas.pediatrics_neonatology_support_protocol import (
    PediatricsNeonatologySupportProtocolRecommendation,
    PediatricsNeonatologySupportProtocolRequest,
)


class PediatricsNeonatologySupportProtocolService:
    """Construye recomendaciones operativas pediatrico-neonatales."""

    @staticmethod
    def _measles_pathway(
        payload: PediatricsNeonatologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        actions: list[str] = []
        safety_blocks: list[str] = []
        trace: list[str] = []

        prodrome_triad = (
            payload.high_fever_present and payload.photophobia_present and payload.cough_present
        )
        exanthem_pattern = (
            payload.confluent_maculopapular_rash_present
            and payload.cephalocaudal_rash_progression_present
        )
        measles_suspected = prodrome_triad and (payload.koplik_spots_present or exanthem_pattern)

        if measles_suspected:
            critical_alerts.append(
                "Sospecha alta de sarampion: activar aislamiento respiratorio inmediato."
            )
            actions.append(
                "Priorizar notificacion y circuito de aislamiento respiratorio "
                "por cuadro exantematico."
            )
            trace.append("Regla de sarampion activada por triada prodromica con tos.")
            if not payload.respiratory_isolation_started:
                safety_blocks.append("Sospecha de sarampion sin aislamiento respiratorio iniciado.")

        if payload.koplik_spots_present:
            actions.append(
                "Manchas de Koplik presentes: hallazgo altamente sugestivo de sarampion."
            )

        if payload.patient_age_months is not None:
            if payload.patient_age_months < 12:
                actions.append(
                    "Lactante <12 meses: puede estar correctamente vacunado para su edad "
                    "y seguir susceptible."
                )
            elif payload.mmr_doses_received is not None and payload.mmr_doses_received == 0:
                safety_blocks.append(
                    "Paciente con edad de primera dosis (>12 meses) sin triple virica "
                    "registrada."
                )
            elif payload.patient_age_months >= 36 and (
                payload.mmr_doses_received is not None and payload.mmr_doses_received < 2
            ):
                actions.append(
                    "Esquema triple virica incompleto para edad >=3 anios: revisar "
                    "cobertura vacunal."
                )

        if payload.red_eye_present:
            actions.append(
                "Ojo rojo en cuadro febril/exantematico: incluir diferencial con "
                "enfermedad de Kawasaki."
            )
            if payload.kawasaki_features_present:
                critical_alerts.append(
                    "Signos compatibles con Kawasaki en diferencial de sarampion: "
                    "priorizar valoracion pediatrica."
                )

        return critical_alerts, actions, safety_blocks, trace

    @staticmethod
    def _neonatal_resuscitation_pathway(
        payload: PediatricsNeonatologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        actions: list[str] = []
        safety_blocks: list[str] = []
        trace: list[str] = []

        if payload.apgar_only_minute_0_recorded:
            safety_blocks.append(
                "Registro Apgar en minuto 0 no valida la escala: registrar minuto 1 y 5."
            )
        if payload.apgar_minute_1 is None:
            safety_blocks.append("Falta Apgar del minuto 1.")
        if payload.apgar_minute_5 is None:
            safety_blocks.append("Falta Apgar del minuto 5.")

        positive_initial_eval = (
            payload.neonatal_heart_rate_bpm is not None
            and payload.neonatal_heart_rate_bpm > 100
            and payload.spontaneous_breathing_present
        )
        if positive_initial_eval:
            actions.append("Evaluacion inicial positiva (FC>100 y respiracion espontanea).")
            if payload.neonatal_respiratory_distress_present:
                actions.append(
                    "Distres respiratorio con FC>100: modalidad inicial recomendada CPAP."
                )
                trace.append("Regla de CPAP activada por FC>100 con distres respiratorio.")
                if not payload.cpap_started:
                    safety_blocks.append("Distres neonatal con FC>100 sin CPAP iniciada.")

        if (
            payload.gestational_age_weeks is not None
            and payload.gestational_age_weeks > 30
            and payload.fio2_percent is not None
            and payload.fio2_percent < 21
        ):
            safety_blocks.append("FiO2 por debajo de 21% en RN >30 semanas.")

        minute_targets = {3: (60.0, 80.0), 5: (75.0, 85.0), 10: (85.0, 90.0)}
        if (
            payload.minute_of_life in minute_targets
            and payload.oxygen_saturation_percent is not None
        ):
            low, high = minute_targets[payload.minute_of_life]
            sat = payload.oxygen_saturation_percent
            if sat < low:
                actions.append(
                    f"SatO2 por debajo del objetivo al minuto {payload.minute_of_life}: "
                    "ajustar soporte ventilatorio."
                )
            elif sat > high:
                actions.append(
                    f"SatO2 por encima del objetivo al minuto {payload.minute_of_life}: "
                    "evitar hiperoxia."
                )

            minute_3_block = (
                payload.minute_of_life == 3
                and payload.neonatal_heart_rate_bpm is not None
                and payload.neonatal_heart_rate_bpm > 100
                and payload.neonatal_cyanosis_present
                and low <= sat <= high
            )
            if minute_3_block:
                trace.append("Minuto 3 con FC>100 y SatO2 en rango 60-80: no escalar oxigeno.")
                if payload.oxygen_increase_requested:
                    safety_blocks.append(
                        "Bloqueo: no aumentar O2 si SatO2 minuto 3 esta en 60-80 "
                        "con FC>100; priorizar CPAP 21%."
                    )
                actions.append(
                    "Con cianosis y SatO2 objetivo al minuto 3: mantener CPAP con FiO2 21%."
                )

        if (
            payload.gestational_age_weeks is not None
            and payload.gestational_age_weeks > 30
            and payload.fio2_percent is not None
            and payload.fio2_percent > 21
            and payload.minute_of_life is not None
            and payload.minute_of_life <= 3
        ):
            actions.append(
                "RN >30 semanas: revisar necesidad de FiO2 >21% al inicio para evitar hiperoxia."
            )

        return critical_alerts, actions, safety_blocks, trace

    @staticmethod
    def _pertussis_contacts_pathway(
        payload: PediatricsNeonatologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        actions: list[str] = []
        trace: list[str] = []

        close_contact = (
            payload.household_contact
            or payload.face_to_face_secretions_contact
            or payload.newborn_of_infectious_mother_at_delivery
            or payload.healthcare_airway_exposure_without_mask
        )
        if payload.confirmed_pertussis_case and close_contact:
            actions.append(
                "Contacto estrecho de tosferina: indicar profilaxis con azitromicina "
                "5 dias o claritromicina 7 dias."
            )
            actions.append(
                "Aplicar profilaxis a convivientes independientemente de edad o " "estado vacunal."
            )
            trace.append("Regla de profilaxis universal en contactos estrechos activada.")
            if not payload.macrolide_prophylaxis_started:
                critical_alerts.append(
                    "Contacto estrecho de tosferina sin profilaxis macrolida iniciada."
                )

        if payload.healthcare_airway_exposure_without_mask:
            actions.append(
                "Personal sanitario con exposicion de via aerea sin mascarilla: "
                "indicar profilaxis."
            )

        if payload.days_since_effective_pertussis_treatment is not None:
            if payload.days_since_effective_pertussis_treatment < 5:
                actions.append(
                    "Paciente con tosferina sigue contagioso hasta completar 5 dias "
                    "de tratamiento eficaz."
                )
        elif payload.days_since_pertussis_symptom_onset is not None:
            if payload.days_since_pertussis_symptom_onset <= 21:
                actions.append(
                    "Sin tratamiento eficaz, considerar contagiosidad hasta 21 dias "
                    "desde inicio de sintomas."
                )

        return critical_alerts, actions, trace

    @staticmethod
    def _intussusception_pathway(
        payload: PediatricsNeonatologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        actions: list[str] = []
        trace: list[str] = []

        in_risk_age = (
            payload.patient_age_months is not None and 6 <= payload.patient_age_months <= 24
        )
        typical_colic_pattern = (
            payload.intermittent_colicky_abdominal_pain
            and payload.asymptomatic_intervals_between_pain
        )
        if in_risk_age and typical_colic_pattern:
            critical_alerts.append(
                "Sospecha de invaginacion intestinal (6-24 meses con colico intermitente)."
            )
            actions.append(
                "Priorizar evaluacion por obstruccion intestinal y confirmar "
                "localizacion iliocecal."
            )
            trace.append("Regla de invaginacion activada por patron clinico tipico.")

        if payload.peritonitis_signs_present:
            critical_alerts.append(
                "Signos de peritonitis en probable invaginacion: riesgo de gangrena/perforacion."
            )

        if payload.recent_respiratory_infection_adenovirus_suspected:
            actions.append(
                "Antecedente respiratorio reciente compatible con adenovirus: "
                "factor asociado a invaginacion."
            )

        if (
            payload.days_since_rotavirus_vaccine is not None
            and payload.days_since_rotavirus_vaccine <= 21
        ):
            actions.append(
                "Cuadro dentro de 3 semanas post-vacuna rotavirus: considerar aumento "
                "ligero de riesgo sin contraindicar vacunacion."
            )

        return critical_alerts, actions, trace

    @staticmethod
    def _congenital_syphilis_pathway(
        payload: PediatricsNeonatologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        actions: list[str] = []
        trace: list[str] = []

        hutchinson_features = [
            payload.hutchinson_teeth_present,
            payload.interstitial_keratitis_present,
            payload.sensorineural_deafness_present,
        ]
        hutchinson_count = sum(1 for present in hutchinson_features if present)
        if hutchinson_count >= 2:
            critical_alerts.append(
                "Estigmas tardios compatibles con sifilis congenita (triada de "
                "Hutchinson parcial/completa)."
            )
            trace.append("Regla de sifilis congenita tardia activada por triada de Hutchinson.")

        other_stigmata = [
            payload.saddle_nose_present,
            payload.mulberry_molars_present,
            payload.saber_shins_present,
            payload.frontal_bossing_present,
            payload.clutton_joints_present,
        ]
        if any(other_stigmata):
            actions.append(
                "Estigmas tardios adicionales presentes (nariz en silla de montar, "
                "molares de Morera, tibias en sable, frente prominente o "
                "articulaciones de Clutton)."
            )

        if payload.congenital_heart_disease_present:
            actions.append(
                "Cardiopatia congenita no es manifestacion tipica de sifilis "
                "congenita: ampliar diferencial."
            )

        return critical_alerts, actions, trace

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
        payload: PediatricsNeonatologySupportProtocolRequest,
    ) -> PediatricsNeonatologySupportProtocolRecommendation:
        """Genera recomendacion operativa pediatrico-neonatal para validacion humana."""
        (
            critical_measles,
            measles_actions,
            measles_safety,
            measles_trace,
        ) = PediatricsNeonatologySupportProtocolService._measles_pathway(payload)
        (
            critical_neonatal,
            neonatal_actions,
            neonatal_safety,
            neonatal_trace,
        ) = PediatricsNeonatologySupportProtocolService._neonatal_resuscitation_pathway(payload)
        (
            critical_pertussis,
            pertussis_actions,
            pertussis_trace,
        ) = PediatricsNeonatologySupportProtocolService._pertussis_contacts_pathway(payload)
        (
            critical_surgical,
            surgical_actions,
            surgical_trace,
        ) = PediatricsNeonatologySupportProtocolService._intussusception_pathway(payload)
        (
            critical_syphilis,
            syphilis_actions,
            syphilis_trace,
        ) = PediatricsNeonatologySupportProtocolService._congenital_syphilis_pathway(payload)

        critical_alerts = (
            critical_measles
            + critical_neonatal
            + critical_pertussis
            + critical_surgical
            + critical_syphilis
        )
        safety_blocks = measles_safety + neonatal_safety
        has_actions = any(
            [
                measles_actions,
                neonatal_actions,
                pertussis_actions,
                surgical_actions,
                syphilis_actions,
            ]
        )
        severity = PediatricsNeonatologySupportProtocolService._severity(
            critical_alerts=critical_alerts,
            safety_blocks=safety_blocks,
            has_actions=has_actions,
        )

        return PediatricsNeonatologySupportProtocolRecommendation(
            severity_level=severity,
            critical_alerts=critical_alerts,
            infectious_exanthem_actions=measles_actions,
            neonatal_resuscitation_actions=neonatal_actions,
            pertussis_contact_actions=pertussis_actions,
            surgical_pediatric_actions=surgical_actions,
            congenital_syphilis_actions=syphilis_actions,
            safety_blocks=safety_blocks,
            interpretability_trace=(
                measles_trace + neonatal_trace + pertussis_trace + surgical_trace + syphilis_trace
            ),
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. "
                "Requiere validacion por pediatria/neonatologia."
            ),
        )
