"""
Motor operativo de trauma para urgencias.

No diagnostica; prioriza acciones para validacion clinica humana.
"""
from app.schemas.trauma_support_protocol import (
    TraumaConditionCard,
    TraumaSupportRecommendation,
    TraumaSupportRequest,
)


class TraumaSupportProtocolService:
    """Construye recomendacion operativa para trauma con reglas interpretables."""

    SOURCE = "CCM 2025 - Especialidad Urgencias"

    @staticmethod
    def _mortality_phase(payload: TraumaSupportRequest) -> str:
        if payload.suspected_major_brain_injury or payload.suspected_major_vascular_injury:
            return "immediate"
        if (
            payload.epidural_hematoma_suspected
            or payload.massive_hemothorax_suspected
            or payload.splenic_rupture_suspected
            or payload.minutes_since_trauma <= 360
        ):
            return "early"
        if payload.sepsis_signs_post_stabilization or payload.persistent_organ_dysfunction:
            return "late"
        return "mixed"

    @staticmethod
    def _tecla_ticla_priority(payload: TraumaSupportRequest, phase: str) -> str:
        if phase == "immediate":
            return "nivel_i"
        if phase == "early" and payload.minutes_since_trauma <= 360:
            return "nivel_i"
        if phase in {"early", "late"}:
            return "nivel_ii"
        return "monitorizacion_estrecha"

    @staticmethod
    def _laryngeal_triad(payload: TraumaSupportRequest) -> bool:
        return bool(
            payload.laryngeal_fracture_palpable
            and payload.hoarseness_present
            and payload.subcutaneous_emphysema_present
        )

    @staticmethod
    def _airway_red_flags(payload: TraumaSupportRequest, triad_present: bool) -> list[str]:
        flags: list[str] = []
        if triad_present:
            flags.append(
                "Triada de trauma laringeo completa: activar via aerea "
                "dificil/quirurgica inmediata."
            )
        if payload.agitation_present:
            flags.append("Agitacion compatible con hipoxemia en progreso.")
        if payload.stupor_present:
            flags.append("Estupor compatible con hipercapnia severa.")
        if payload.intercostal_retractions_present or payload.accessory_muscle_use_present:
            flags.append("Tiraje o uso de musculos accesorios: riesgo de fatiga respiratoria.")
        return flags

    @staticmethod
    def _airway_priority(payload: TraumaSupportRequest, triad_present: bool) -> str:
        if triad_present:
            return "nivel_i"
        if (
            payload.stupor_present
            or payload.intercostal_retractions_present
            or payload.accessory_muscle_use_present
        ):
            return "alto"
        return "moderado"

    @staticmethod
    def _oxygen_curve_shift_right(payload: TraumaSupportRequest) -> bool:
        return bool(
            payload.hyperthermia_present or payload.hypercapnia_present or payload.acidosis_present
        )

    @staticmethod
    def _spinal_syndrome(payload: TraumaSupportRequest) -> str:
        if payload.ipsilateral_motor_vibration_loss and payload.contralateral_pain_temperature_loss:
            return "brown_sequard"
        if (
            payload.motor_loss_global
            and payload.sensory_loss_global
            and payload.preserved_vibration_proprioception
        ):
            return "anterior_cord"
        if payload.motor_loss_arms_more_than_legs:
            return "central_cord"
        return "indeterminado"

    @staticmethod
    def _hypothermia_stage(payload: TraumaSupportRequest) -> str:
        temp = payload.core_temperature_celsius
        if temp is None:
            return "none"
        if temp < 28:
            return "severe"
        if temp < 32:
            return "moderate"
        if temp < 35:
            return "mild"
        return "none"

    @staticmethod
    def _hypothermia_alerts(payload: TraumaSupportRequest, stage: str) -> list[str]:
        alerts: list[str] = []
        temp = payload.core_temperature_celsius
        if stage in {"mild", "moderate", "severe"}:
            alerts.append("Hipotermia detectada: iniciar recalentamiento segun gravedad.")
        if payload.osborn_j_wave_present or (temp is not None and temp < 31):
            alerts.append(
                "Ondas J de Osborne probables/presentes: vigilar inestabilidad electrica."
            )
        if temp is not None and temp <= 28:
            alerts.append("Riesgo alto de fibrilacion ventricular por temperatura <=28C.")
        if temp is not None and temp <= 24:
            alerts.append("Riesgo de asistolia por temperatura <=24C.")
        return alerts

    @staticmethod
    def _gustilo_grade(payload: TraumaSupportRequest) -> str:
        if payload.open_fracture_wound_cm is None and not payload.high_energy_open_fracture:
            return "no_aplica"
        if payload.high_energy_open_fracture:
            return "grado_iii"
        wound = payload.open_fracture_wound_cm or 0
        if wound < 1:
            return "grado_i"
        if wound <= 10:
            return "grado_ii"
        return "grado_iii"

    @staticmethod
    def _antibiotic_coverage(grade: str) -> str:
        if grade == "grado_i":
            return "Cobertura inicial para Gram positivos."
        if grade == "grado_ii":
            return "Cobertura para Gram positivos y ampliacion segun contaminacion/localizacion."
        if grade == "grado_iii":
            return (
                "Cobertura amplia Gram positivos + Gram negativos (cefalosporina + aminoglucosido)."
            )
        return "No aplica en este episodio (sin fractura expuesta declarada)."

    @staticmethod
    def _special_population_actions(payload: TraumaSupportRequest) -> list[str]:
        actions: list[str] = []
        if payload.patient_profile == "geriatrico":
            actions.append(
                "En geriatria, la caida es causa frecuente: considerar neuroimagen con umbral bajo."
            )
            actions.append("Evitar sobrecarga de fluidos por fragilidad renal.")
        if payload.patient_profile == "pediatrico":
            actions.append(
                "Usar cinta de Broselow para dosis/dispositivos."
                if payload.broselow_tape_used
                else "Activar cinta de Broselow para estimacion de dosis/dispositivos."
            )
            actions.append(
                "Mantener posicion de olfateo para via aerea pediatrica."
                if payload.sniffing_position_applied
                else "Aplicar posicion de olfateo para alinear ejes de via aerea pediatrica."
            )
        if payload.patient_profile == "embarazada":
            actions.append(
                "Decubito lateral izquierdo 15-30 grados activo."
                if payload.left_lateral_decubitus_applied
                else "Aplicar decubito lateral izquierdo 15-30 grados de forma inmediata."
            )
            actions.append(
                "Considerar anemia fisiologica gestacional e hiperventilacion "
                "basal en la interpretacion."
            )
        return actions

    @staticmethod
    def _primary_actions(
        payload: TraumaSupportRequest, phase: str, triad_present: bool, stage: str
    ) -> list[str]:
        actions: list[str] = [
            "Iniciar revision primaria X-ABCDE en 2-5 minutos.",
            "Oxigeno suplementario y control de hemorragia (Stop the bleeding).",
            "Inmovilizacion cervical con collarin rigido hasta descartar lesion.",
        ]
        if phase in {"immediate", "early"}:
            actions.append(
                "Optimizar TECLA/TICLA en periodo de oro para reducir mortalidad temprana."
            )
        if triad_present:
            actions.append(
                "Activar equipo de via aerea dificil y preparar acceso quirurgico de rescate."
            )
        if payload.crush_injury_suspected:
            actions.append("Iniciar protocolo de aplastamiento y solicitar ECG seriados.")
        if stage in {"moderate", "severe"}:
            actions.append(
                "Combinar recalentamiento externo e interno con soluciones a 40C segun recursos."
            )
        return actions

    @staticmethod
    def _hemorrhagic_shock_grade(payload: TraumaSupportRequest) -> int:
        blood = payload.estimated_blood_loss_ml or 0
        if blood > 2000:
            return 4
        if blood > 1500:
            return 3
        if blood > 750:
            return 2
        return 1

    @staticmethod
    def _has_tension_pneumothorax(payload: TraumaSupportRequest) -> bool:
        return bool(
            payload.dyspnea_present
            and payload.percussion_hyperresonance_present
            and payload.tracheal_deviation_present
        )

    @staticmethod
    def _has_cardiac_tamponade(payload: TraumaSupportRequest) -> bool:
        return bool(
            payload.beck_hypotension_present
            and payload.beck_muffled_heart_sounds_present
            and payload.beck_jvd_present
        )

    @staticmethod
    def _condition_cards(payload: TraumaSupportRequest) -> list[TraumaConditionCard]:
        cards: list[TraumaConditionCard] = []

        cards.append(
            TraumaConditionCard(
                condition="Paciente Politraumatizado",
                classification_category="Revision Primaria (ABCDE)",
                key_signs_symptoms=[
                    "Lesiones con riesgo de vida, extremidad u organo",
                    "Hemorragia activa",
                ],
                diagnostic_method=[
                    "Evaluacion clinica 2-5 min",
                    "Protocolo X-ABCDE",
                    "Gasometria (pH, lactato, deficit de base)",
                    "Rx pelvis AP y torax AP",
                ],
                initial_immediate_treatment=[
                    "Oxigeno suplementario",
                    "Control de hemorragia",
                    "Inmovilizacion cervical con collarin rigido",
                ],
                definitive_surgical_treatment=[
                    "Manejo segun revision secundaria y cirugia si hay compromiso inminente"
                ],
                technical_observations=[
                    "Toda victima de trauma se considera con fractura cervical hasta descartarla",
                    "La uresis es indicador clave de reanimacion",
                ],
                source=TraumaSupportProtocolService.SOURCE,
            )
        )

        shock_grade = TraumaSupportProtocolService._hemorrhagic_shock_grade(payload)
        cards.append(
            TraumaConditionCard(
                condition="Choque Hipovolemico (Hemorragico)",
                classification_category=f"Estado de Choque (Grado {shock_grade})",
                key_signs_symptoms=[
                    "Perdida hematica",
                    "Taquicardia",
                    "Hipotension (habitual desde grado 3)",
                    "Alteracion del estado de conciencia",
                ],
                diagnostic_method=[
                    "Estimacion de perdida hematica",
                    "Frecuencia cardiaca y tension arterial",
                    "Frecuencia respiratoria y uresis",
                ],
                initial_immediate_treatment=[
                    "Reanimacion con cristaloides",
                    "Control de fuente de sangrado",
                ],
                definitive_surgical_treatment=[
                    "Transfusion de hemoderivados",
                    "Cirugia de control de danos segun necesidad",
                ],
                technical_observations=["Es el tipo de choque mas frecuente en trauma."],
                source=TraumaSupportProtocolService.SOURCE,
            )
        )

        if TraumaSupportProtocolService._has_tension_pneumothorax(payload):
            cards.append(
                TraumaConditionCard(
                    condition="Neumotorax a Tension",
                    classification_category="Trauma de Torax / Choque Obstructivo",
                    key_signs_symptoms=[
                        "Dolor toracico",
                        "Disnea",
                        "Taquicardia/hipotension",
                        "Hiperresonancia",
                        "Desviacion traqueal",
                    ],
                    diagnostic_method=[
                        "Diagnostico clinico prioritario",
                        "Rx torax (si no retrasa descompresion)",
                    ],
                    initial_immediate_treatment=[
                        "Descompresion con aguja en 5to espacio intercostal linea axilar",
                    ],
                    definitive_surgical_treatment=["Tubo de pleurostomia con sello pleural"],
                    technical_observations=["Produce choque obstructivo por menor retorno venoso."],
                    source=TraumaSupportProtocolService.SOURCE,
                )
            )

        if TraumaSupportProtocolService._has_cardiac_tamponade(payload):
            cards.append(
                TraumaConditionCard(
                    condition="Taponamiento Cardiaco",
                    classification_category="Trauma de Torax / Choque Obstructivo",
                    key_signs_symptoms=[
                        "Triada de Beck: hipotension, ruidos cardiacos velados, "
                        "ingurgitacion yugular",
                    ],
                    diagnostic_method=[
                        "Clinico",
                        "FAST ventana pericardica",
                        "ECG con alternancia electrica",
                    ],
                    initial_immediate_treatment=["Pericardiocentesis"],
                    definitive_surgical_treatment=["Toracotomia quirurgica"],
                    technical_observations=[
                        "La sangre pericardica impide sistole/diastole efectivas.",
                    ],
                    source=TraumaSupportProtocolService.SOURCE,
                )
            )

        if payload.glasgow_coma_scale is not None:
            cards.append(
                TraumaConditionCard(
                    condition="Traumatismo Craneoencefalico (TCE)",
                    classification_category="Trauma Neurologico",
                    key_signs_symptoms=[
                        "Alteracion del estado de alerta",
                        "Vomitos/amnesia",
                        "Focalizacion neurologica",
                    ],
                    diagnostic_method=["Escala de Glasgow", "TAC craneo como estudio de eleccion"],
                    initial_immediate_treatment=[
                        "Asegurar via aerea si Glasgow <=8",
                        "Mantener normocarnia, normoxemia y normoglucemia",
                    ],
                    definitive_surgical_treatment=[
                        "Neurocirugia para evacuacion de hematoma segun clasificacion",
                    ],
                    technical_observations=[
                        "Epidural: biconvexo (arterial). Subdural: media luna (venoso)."
                    ],
                    source=TraumaSupportProtocolService.SOURCE,
                )
            )

        if (
            payload.compartment_pressure_mm_hg is not None
            or payload.compartment_pain_out_of_proportion
        ):
            cards.append(
                TraumaConditionCard(
                    condition="Sindrome Compartimental",
                    classification_category="Trauma Musculoesqueletico",
                    key_signs_symptoms=[
                        "6P: parestesias, dolor, presion, palidez, ausencia de pulso, paralisis",
                    ],
                    diagnostic_method=[
                        "Clinico",
                        "Presion compartimental (>35 mmHg)",
                    ],
                    initial_immediate_treatment=["Retirar yesos o vendajes compresivos"],
                    definitive_surgical_treatment=["Fasciotomia urgente"],
                    technical_observations=[
                        "Ventana critica aproximada de 8 horas para evitar dano irreversible.",
                    ],
                    source=TraumaSupportProtocolService.SOURCE,
                )
            )

        if payload.burn_tbsa_percent is not None:
            cards.append(
                TraumaConditionCard(
                    condition="Quemaduras",
                    classification_category="Emergencia Termica",
                    key_signs_symptoms=[
                        "Eritema/ampollas/tejido carbonaceo segun profundidad",
                    ],
                    diagnostic_method=[
                        "Regla de los nueves en adultos",
                        "Lund-Browder en pediatria",
                    ],
                    initial_immediate_treatment=[
                        "Asegurar via aerea",
                        "Reanimacion hidrica con formula de Parkland (2-4 ml/kg/%SCQ)",
                    ],
                    definitive_surgical_treatment=[
                        "Antibioticos topicos",
                        "Escarectomia e injertos segun profundidad",
                    ],
                    technical_observations=[
                        "No usar antibioticos sistemicos profilacticos.",
                        "Administrar profilaxis antitetanica.",
                    ],
                    source=TraumaSupportProtocolService.SOURCE,
                )
            )

        return cards

    @staticmethod
    def _alerts(
        phase: str,
        triad_present: bool,
        airway_flags: list[str],
        spinal_syndrome: str,
        crush_alert: bool,
        renal_risk_high: bool,
        serial_ecg_required: bool,
        stage: str,
        gustilo_grade: str,
        has_tension_pneumothorax: bool,
        has_tamponade: bool,
        gcs: int | None,
    ) -> list[str]:
        alerts: list[str] = []
        if phase == "immediate":
            alerts.append(
                "Ventana de mortalidad inmediata: maxima prioridad prehospitalaria y de sala."
            )
        elif phase == "early":
            alerts.append("Ventana de mortalidad temprana activa: optimizar TECLA/TICLA.")
        elif phase == "late":
            alerts.append("Riesgo de mortalidad tardia: vigilar sepsis y falla multiorganica.")

        if triad_present:
            alerts.append("Triada laringea positiva: elevar prioridad a Nivel I.")
        alerts.extend(airway_flags)

        if has_tension_pneumothorax:
            alerts.append("Sospecha de neumotorax a tension: descompresion inmediata.")
        if has_tamponade:
            alerts.append("Triada de Beck positiva: tratar como taponamiento cardiaco.")
        if gcs is not None and gcs <= 8:
            alerts.append("Glasgow <=8: asegurar via aerea y ventilacion protegida.")

        if spinal_syndrome == "anterior_cord":
            alerts.append("Patron de cordon anterior: peor pronostico funcional esperado.")
        if spinal_syndrome == "brown_sequard":
            alerts.append("Patron cruzado compatible con Brown-Sequard.")

        if crush_alert:
            alerts.append("Sindrome de aplastamiento: riesgo de rabdomiolisis, FRA y CID.")
        if renal_risk_high:
            alerts.append("Riesgo renal alto por mioglobinuria e hipovolemia de tercer espacio.")
        if serial_ecg_required:
            alerts.append("ECG seriados requeridos por riesgo arritmico metabolico.")

        if stage == "severe":
            alerts.append("Hipotermia severa: protocolo avanzado de recalentamiento.")
        if gustilo_grade == "grado_iii":
            alerts.append("Fractura expuesta grado III: prioridad quirurgica y antibiotico amplio.")

        return alerts

    @staticmethod
    def build_recommendation(payload: TraumaSupportRequest) -> TraumaSupportRecommendation:
        """Genera recomendacion operativa de trauma para validacion humana."""
        phase = TraumaSupportProtocolService._mortality_phase(payload)
        triad_present = TraumaSupportProtocolService._laryngeal_triad(payload)
        airway_flags = TraumaSupportProtocolService._airway_red_flags(payload, triad_present)
        spinal_syndrome = TraumaSupportProtocolService._spinal_syndrome(payload)

        crush_alert = payload.crush_injury_suspected
        renal_risk_high = bool(
            crush_alert and (payload.hyperkalemia_risk or payload.hyperphosphatemia_present)
        )
        serial_ecg_required = bool(crush_alert and not payload.ecg_series_started)

        stage = TraumaSupportProtocolService._hypothermia_stage(payload)
        gustilo_grade = TraumaSupportProtocolService._gustilo_grade(payload)

        has_tension_pneumothorax = TraumaSupportProtocolService._has_tension_pneumothorax(payload)
        has_tamponade = TraumaSupportProtocolService._has_cardiac_tamponade(payload)

        return TraumaSupportRecommendation(
            mortality_phase_risk=phase,
            tecla_ticla_priority=TraumaSupportProtocolService._tecla_ticla_priority(payload, phase),
            laryngeal_trauma_triad_present=triad_present,
            airway_priority_level=TraumaSupportProtocolService._airway_priority(
                payload, triad_present
            ),
            airway_red_flags=airway_flags,
            oxygen_curve_shift_right_risk=TraumaSupportProtocolService._oxygen_curve_shift_right(
                payload
            ),
            suspected_spinal_syndrome=spinal_syndrome,
            crush_syndrome_alert=crush_alert,
            renal_failure_risk_high=renal_risk_high,
            serial_ecg_required=serial_ecg_required,
            crush_complications=[
                "rabdomiolisis",
                "fracaso_renal_agudo",
                "cid",
                "arritmias_por_hipercalemia",
            ]
            if crush_alert
            else [],
            hypothermia_stage=stage,
            hypothermia_alerts=TraumaSupportProtocolService._hypothermia_alerts(payload, stage),
            open_fracture_gustilo_grade=gustilo_grade,
            antibiotic_coverage_recommendation=TraumaSupportProtocolService._antibiotic_coverage(
                gustilo_grade
            ),
            condition_matrix=TraumaSupportProtocolService._condition_cards(payload),
            special_population_actions=TraumaSupportProtocolService._special_population_actions(
                payload
            ),
            primary_actions=TraumaSupportProtocolService._primary_actions(
                payload, phase, triad_present, stage
            ),
            alerts=TraumaSupportProtocolService._alerts(
                phase=phase,
                triad_present=triad_present,
                airway_flags=airway_flags,
                spinal_syndrome=spinal_syndrome,
                crush_alert=crush_alert,
                renal_risk_high=renal_risk_high,
                serial_ecg_required=serial_ecg_required,
                stage=stage,
                gustilo_grade=gustilo_grade,
                has_tension_pneumothorax=has_tension_pneumothorax,
                has_tamponade=has_tamponade,
                gcs=payload.glasgow_coma_scale,
            ),
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. Requiere validacion clinica "
                "humana."
            ),
        )
