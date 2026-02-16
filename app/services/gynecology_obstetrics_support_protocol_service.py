"""
Motor operativo de ginecologia y obstetricia para urgencias.

No diagnostica; organiza rutas de riesgo para validacion clinica humana.
"""
from app.schemas.gynecology_obstetrics_support_protocol import (
    GynecologyObstetricsSupportProtocolRecommendation,
    GynecologyObstetricsSupportProtocolRequest,
)


class GynecologyObstetricsSupportProtocolService:
    """Construye recomendaciones operativas gineco-obstetricas."""

    @staticmethod
    def _hereditary_oncology_pathway(
        payload: GynecologyObstetricsSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        actions: list[str] = []
        trace: list[str] = []

        amsterdam_ii_suspected = (
            payload.family_lynch_related_cancers_count >= 3
            and payload.family_generations_affected_count >= 2
            and payload.family_lynch_related_cancers_under_50_count >= 1
        )
        if amsterdam_ii_suspected:
            critical_alerts.append(
                "Criterios de Amsterdam II compatibles con sindrome de Lynch: "
                "activar ruta onco-genetica prioritaria."
            )
            actions.append(
                "Revisar antecedentes paternos y maternos de colon, endometrio, ovario, "
                "estomago y pancreas."
            )
            trace.append("Regla Amsterdam II activada por patron familiar.")

        if payload.endometrial_cancer_diagnosed and (
            payload.age_at_endometrial_cancer_diagnosis is not None
            and payload.age_at_endometrial_cancer_diagnosis <= 45
        ):
            actions.append(
                "Cancer de endometrio en paciente joven: priorizar descarte de "
                "sindrome hereditario (Lynch/MMR)."
            )

        if payload.known_mismatch_repair_mutation:
            actions.append(
                "Mutacion MMR conocida: reforzar estrategia de consejeria genetica "
                "y vigilancia familiar."
            )

        if payload.endometrial_tumor_molecular_profile == "pole_ultramutated":
            actions.append(
                "Perfil molecular POLE ultramutado: pronostico favorable relativo."
            )
        elif payload.endometrial_tumor_molecular_profile == "p53_mutated_serous_like":
            critical_alerts.append(
                "Perfil molecular P53 mutado (serous-like): alto riesgo oncologico."
            )
        elif payload.endometrial_tumor_molecular_profile == "mismatch_repair_deficient":
            actions.append(
                "Perfil dMMR: evaluar implicaciones pronosticas y geneticas asociadas."
            )

        if payload.breast_cancer_subtype == "triple_negative":
            critical_alerts.append(
                "Subtipo mama triple negativo: fenotipo de mayor agresividad clinica."
            )
        elif payload.breast_cancer_subtype == "luminal_a":
            actions.append(
                "Subtipo luminal A: fenotipo frecuente con mejor pronostico relativo."
            )

        return critical_alerts, actions, trace

    @staticmethod
    def _urgent_gynecology_pathway(
        payload: GynecologyObstetricsSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        actions: list[str] = []
        trace: list[str] = []

        if payload.reproductive_age_with_abdominal_pain_or_bleeding:
            actions.append(
                "Mujer en edad reproductiva con dolor/sangrado: descartar primero "
                "patologia gestacional."
            )

        ectopic_triage = (
            payload.pregnancy_test_positive
            and payload.severe_abdominal_pain
            and payload.vaginal_spotting_present
        )
        if ectopic_triage:
            critical_alerts.append(
                "Triada de alerta de gestacion ectopica: test positivo + dolor intenso + "
                "manchado vaginal."
            )
            trace.append("Regla de ectopico activada.")

        rupture_signs = (
            payload.pregnancy_test_positive
            and payload.free_intraperitoneal_fluid_on_ultrasound
            and payload.dilated_or_violaceous_tube_on_ultrasound
        )
        if rupture_signs:
            critical_alerts.append(
                "Signos ecograficos de probable rotura ectopica: priorizar ruta "
                "quirurgica urgente."
            )

        if payload.cyclic_pelvic_pain_with_menses:
            actions.append(
                "Dolor ciclico asociado a menstruacion: priorizar endometriosis como "
                "hipotesis operativa inicial."
            )
        if payload.deep_endometriosis_digestive_implants_suspected:
            actions.append(
                "Sospecha de endometriosis profunda con compromiso digestivo: valorar "
                "plan conjunto ginecologia-cirugia."
            )

        return critical_alerts, actions, trace

    @staticmethod
    def _obstetric_pathway(
        payload: GynecologyObstetricsSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        actions: list[str] = []
        trace: list[str] = []

        if (
            payload.first_trimester_crl_available
            and payload.lmp_vs_first_trimester_ultrasound_difference_days is not None
            and abs(payload.lmp_vs_first_trimester_ultrasound_difference_days) >= 5
        ):
            actions.append(
                "Datacion: ajustar fecha probable de parto segun CRL de primer trimestre "
                "por diferencia >=5 dias."
            )
            trace.append("Regla de ajuste de datacion por CRL activada.")

        if (
            payload.gestational_age_weeks is not None
            and payload.gestational_age_weeks < 28
            and payload.fetal_percentile is not None
            and payload.fetal_percentile < 3
        ):
            critical_alerts.append(
                "CIR severo precoz (<P3 antes de semana 28): priorizar estudio invasivo "
                "segun protocolo."
            )
            actions.append(
                "Considerar amniocentesis para estudio microbiologico y genetico (arrays)."
            )

        if payload.monochorionic_pregnancy:
            recipient_threshold = 10.0
            if payload.gestational_age_weeks is not None and payload.gestational_age_weeks < 20:
                recipient_threshold = 8.0

            recipient_poly = (
                payload.recipient_amniotic_vertical_pocket_cm is not None
                and payload.recipient_amniotic_vertical_pocket_cm > recipient_threshold
            )
            donor_oligo = (
                payload.donor_amniotic_vertical_pocket_cm is not None
                and payload.donor_amniotic_vertical_pocket_cm < 2.0
            )
            donor_bladder_not_visible = payload.donor_bladder_visible is False

            if recipient_poly and donor_oligo:
                actions.append(
                    "Secuencia oligoamnios-polidramnios compatible con STFF: "
                    "escalar evaluacion fetal especializada."
                )
                if payload.recipient_bladder_distended and donor_bladder_not_visible:
                    critical_alerts.append(
                        "STFF compatible con estadio 2 de Quintero: receptor con vejiga "
                        "distendida y donante sin vejiga visible."
                    )

        return critical_alerts, actions, trace

    @staticmethod
    def _infectious_varicella_pathway(
        payload: GynecologyObstetricsSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        actions: list[str] = []
        safety_blocks: list[str] = []

        if payload.varicella_exposure_in_pregnancy and payload.varicella_igg_positive is False:
            if payload.hours_since_varicella_exposure is not None:
                if payload.hours_since_varicella_exposure <= 72:
                    actions.append(
                        "Gestante sin inmunidad tras exposicion: administrar gammaglobulina "
                        "hiperinmune idealmente dentro de 72h."
                    )
                elif payload.hours_since_varicella_exposure <= 240:
                    actions.append(
                        "Profilaxis post-exposicion aun util hasta 10 dias tras contacto."
                    )
                else:
                    actions.append(
                        "Exposicion fuera de ventana habitual de profilaxis: revalorar "
                        "estrategia con infectologia/obstetricia."
                    )

        if payload.live_attenuated_vaccine_requested_during_pregnancy:
            safety_blocks.append(
                "Vacunas vivas atenuadas (varicela/triple virica) contraindicadas en "
                "embarazo."
            )

        if payload.maternal_varicella_confirmed:
            if payload.gestational_age_weeks is not None and payload.gestational_age_weeks < 20:
                actions.append(
                    "Infeccion materna antes de semana 20: vigilar riesgo de teratogenia fetal."
                )
            if (
                payload.days_from_maternal_varicella_to_delivery is not None
                and -5 <= payload.days_from_maternal_varicella_to_delivery <= 2
            ):
                critical_alerts.append(
                    "Varicela periparto en ventana de alto riesgo neonatal respiratorio "
                    "(-5 a +2 dias del parto)."
                )

        return critical_alerts, actions, safety_blocks

    @staticmethod
    def _preeclampsia_pathway(
        payload: GynecologyObstetricsSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        actions: list[str] = []
        safety_blocks: list[str] = []
        trace: list[str] = []

        if (
            payload.postpartum_preeclampsia_suspected
            and payload.target_organ_damage_present
            and payload.proteinuria_present is False
        ):
            actions.append(
                "Preeclampsia posparto: la afectacion de organo diana permite diagnostico "
                "sin proteinuria."
            )

        severe_systolic = (
            payload.systolic_bp_mm_hg is not None and payload.systolic_bp_mm_hg >= 160
        )
        if severe_systolic:
            critical_alerts.append(
                "Preeclampsia con sistolica >=160 mmHg: priorizar antihipertensivo IV inmediato."
            )
            actions.append(
                "Activar flujo de tratamiento intravenoso y monitorizacion estrecha."
            )
            trace.append("Regla de tension grave en preeclampsia activada.")

        if payload.severe_features_present:
            actions.append(
                "Preeclampsia con criterios de gravedad: sulfato de magnesio como "
                "prevencion de convulsiones."
            )

        if severe_systolic and not payload.iv_antihypertensive_started:
            safety_blocks.append(
                "Sistolica >=160 sin antihipertensivo IV registrado: corregir de forma inmediata."
            )
        if payload.severe_features_present and not payload.magnesium_sulfate_started:
            safety_blocks.append(
                "Criterios de gravedad sin sulfato de magnesio iniciado: validar omision."
            )
        if payload.preeclampsia_labeled_as_moderate:
            safety_blocks.append(
                "Terminologia invalida: preeclampsia se clasifica como leve o grave, "
                "no moderada."
            )

        return critical_alerts, actions, safety_blocks, trace

    @staticmethod
    def _pharmacology_prevention_pathway(
        payload: GynecologyObstetricsSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        actions: list[str] = []
        safety_blocks: list[str] = []
        trace: list[str] = []

        if payload.oral_contraception_planned:
            if not payload.baseline_history_completed:
                safety_blocks.append(
                    "Anticoncepcion oral sin historia clinica basal registrada."
                )
            if not payload.baseline_bp_recorded:
                safety_blocks.append(
                    "Anticoncepcion oral sin toma basal de tension arterial."
                )
            if not payload.baseline_bmi_recorded:
                safety_blocks.append(
                    "Anticoncepcion oral sin calculo basal de IMC."
                )
            if payload.routine_cytology_required_before_ocp:
                safety_blocks.append(
                    "No exigir citologia rutinaria como requisito previo universal para ACO."
                )
            if payload.routine_thrombophilia_panel_required_before_ocp:
                safety_blocks.append(
                    "No exigir trombofilia rutinaria antes de ACO sin indicacion clinica."
                )

            if payload.progestin_generation == "second_levonorgestrel":
                actions.append(
                    "Progestageno de segunda generacion (levonorgestrel): menor riesgo "
                    "relativo de tromboembolismo."
                )
            elif payload.progestin_generation in {"third", "fourth"}:
                actions.append(
                    "Progestageno de tercera/cuarta generacion: vigilar riesgo tromboembolico "
                    "relativo superior."
                )

        if payload.gestational_diabetes_one_step_75g_performed:
            if (
                payload.fasting_glucose_mg_dl is not None
                or payload.glucose_1h_mg_dl is not None
                or payload.glucose_2h_mg_dl is not None
            ):
                gdm_positive = (
                    (
                        payload.fasting_glucose_mg_dl is not None
                        and payload.fasting_glucose_mg_dl >= 92
                    )
                    or (
                        payload.glucose_1h_mg_dl is not None
                        and payload.glucose_1h_mg_dl >= 180
                    )
                    or (
                        payload.glucose_2h_mg_dl is not None
                        and payload.glucose_2h_mg_dl >= 153
                    )
                )
                if gdm_positive:
                    actions.append(
                        "Sobrecarga oral 75g positiva (92/180/153): activar ruta de "
                        "diabetes gestacional."
                    )
                else:
                    trace.append(
                        "Sobrecarga oral 75g sin umbrales diagnosticos de diabetes gestacional."
                    )

        if payload.fetal_neuroprotection_magnesium_requested:
            if (
                payload.gestational_age_weeks is not None
                and payload.gestational_age_weeks < 32
                and payload.risk_of_imminent_preterm_birth
            ):
                actions.append(
                    "Neuroproteccion fetal con magnesio indicada (<32 semanas y parto inminente)."
                )
            elif (
                payload.ruptured_membranes_present
                and payload.cervix_long_without_contractions
            ):
                safety_blocks.append(
                    "Neuroproteccion fetal con magnesio no indicada en RPM con cuello largo "
                    "sin dinamica uterina."
                )
            elif (
                payload.gestational_age_weeks is not None
                and payload.gestational_age_weeks >= 32
            ):
                safety_blocks.append(
                    "Neuroproteccion fetal con magnesio fuera de umbral (<32 semanas)."
                )

        if (
            payload.chronic_lymphedema_post_oncologic_surgery
            and payload.diuretic_prescription_requested
        ):
            safety_blocks.append(
                "Bloqueo de diureticos en linfedema cronico post-oncologico."
            )
            actions.append(
                "Sugerir fisioterapia descongestiva y ejercicio fisico como manejo preferente."
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
        payload: GynecologyObstetricsSupportProtocolRequest,
    ) -> GynecologyObstetricsSupportProtocolRecommendation:
        """Genera recomendacion operativa gineco-obstetrica para validacion humana."""
        (
            critical_oncology,
            oncology_actions,
            oncology_trace,
        ) = GynecologyObstetricsSupportProtocolService._hereditary_oncology_pathway(payload)
        (
            critical_urgent,
            urgent_actions,
            urgent_trace,
        ) = GynecologyObstetricsSupportProtocolService._urgent_gynecology_pathway(payload)
        (
            critical_obstetric,
            obstetric_actions,
            obstetric_trace,
        ) = GynecologyObstetricsSupportProtocolService._obstetric_pathway(payload)
        (
            critical_varicella,
            infectious_actions,
            infectious_safety,
        ) = GynecologyObstetricsSupportProtocolService._infectious_varicella_pathway(payload)
        (
            critical_preeclampsia,
            preeclampsia_actions,
            preeclampsia_safety,
            preeclampsia_trace,
        ) = GynecologyObstetricsSupportProtocolService._preeclampsia_pathway(payload)
        (
            pharm_actions,
            pharm_safety,
            pharm_trace,
        ) = GynecologyObstetricsSupportProtocolService._pharmacology_prevention_pathway(payload)

        critical_alerts = (
            critical_oncology
            + critical_urgent
            + critical_obstetric
            + critical_varicella
            + critical_preeclampsia
        )
        safety_blocks = infectious_safety + preeclampsia_safety + pharm_safety
        has_actions = any(
            [
                oncology_actions,
                urgent_actions,
                obstetric_actions,
                infectious_actions,
                preeclampsia_actions,
                pharm_actions,
            ]
        )
        severity = GynecologyObstetricsSupportProtocolService._severity(
            critical_alerts=critical_alerts,
            safety_blocks=safety_blocks,
            has_actions=has_actions,
        )

        return GynecologyObstetricsSupportProtocolRecommendation(
            severity_level=severity,
            critical_alerts=critical_alerts,
            hereditary_oncology_actions=oncology_actions,
            urgent_gynecology_actions=urgent_actions,
            obstetric_monitoring_actions=obstetric_actions,
            infectious_risk_actions=infectious_actions,
            preeclampsia_actions=preeclampsia_actions,
            pharmacology_prevention_actions=pharm_actions,
            safety_blocks=safety_blocks,
            interpretability_trace=(
                oncology_trace
                + urgent_trace
                + obstetric_trace
                + preeclampsia_trace
                + pharm_trace
            ),
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. "
                "Requiere validacion por ginecologia/obstetricia."
            ),
        )
