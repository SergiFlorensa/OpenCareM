"""
Motor operativo critico transversal para urgencias.

No diagnostica; organiza decisiones operativas para validacion clinica humana.
"""
from app.schemas.critical_ops_protocol import (
    CriticalOpsProtocolRecommendation,
    CriticalOpsProtocolRequest,
)


class CriticalOpsProtocolService:
    """Construye recomendaciones operativas para escenarios criticos transversales."""

    @staticmethod
    def _sla(payload: CriticalOpsProtocolRequest) -> tuple[list[str], list[str], list[str]]:
        alerts: list[str] = []
        breaches: list[str] = []
        trace: list[str] = []

        if payload.non_traumatic_chest_pain:
            alerts.append("Dolor toracico no traumatico: ECG obligatorio en <=10 minutos.")
            trace.append("Regla 10 minutos activada por dolor toracico no traumatico.")
            if payload.door_to_ecg_minutes is None:
                breaches.append("Sin registro de ECG inicial en dolor toracico.")
            elif payload.door_to_ecg_minutes > 10:
                breaches.append("SLA ECG incumplido (>10 min) en dolor toracico.")

        if payload.suspected_septic_shock:
            alerts.append(
                "Sospecha de shock septico: iniciar antibiotico empirico en <=60 minutos."
            )
            trace.append("Hora de oro de sepsis activada por sospecha de shock septico.")
            if payload.sepsis_antibiotic_minutes is None:
                breaches.append("Sin registro de inicio de antibiotico en sepsis.")
            elif payload.sepsis_antibiotic_minutes > 60:
                breaches.append("SLA sepsis incumplido (>60 min para antibiotico).")

        if payload.triage_level == "rojo":
            alerts.append("Triaje rojo: valoracion clinica obligatoria en <=5 minutos.")
            trace.append("SLA de triaje rojo activado (riesgo vital inminente).")
            if payload.triage_to_first_assessment_minutes is None:
                breaches.append("Sin registro de primera valoracion en triaje rojo.")
            elif payload.triage_to_first_assessment_minutes > 5:
                breaches.append("SLA de triaje rojo incumplido (>5 min).")

        return alerts, breaches, trace

    @staticmethod
    def _respiratory_support(
        payload: CriticalOpsProtocolRequest,
    ) -> tuple[str, str, list[str], list[str]]:
        trace: list[str] = []
        plan: list[str] = []
        target = "96-98%"

        if payload.hypercapnia_risk:
            target = "88-92%"
            trace.append("Objetivo de saturacion ajustado por riesgo de hipercapnia.")
        else:
            trace.append("Objetivo de saturacion estandar para paciente critico general.")

        device = "monitorizacion"
        severity = payload.respiratory_failure_severity

        if payload.respiratory_acidosis_present:
            device = "bipap"
            plan.append(
                "Insuficiencia respiratoria hipercapnica/acidosis respiratoria: priorizar BiPAP."
            )
            trace.append("BiPAP elegido por acidosis respiratoria/hipercapnia.")
        elif payload.pulmonary_edema_suspected and not payload.shock_or_severe_arrhythmia_present:
            device = "cpap"
            plan.append("Edema agudo de pulmon: considerar CPAP para mejorar oxigenacion.")
            trace.append("CPAP elegido por edema agudo de pulmon sin contraindicaciones mayores.")
        elif payload.pulmonary_edema_suspected and payload.shock_or_severe_arrhythmia_present:
            device = "mascarilla_reservorio"
            plan.append(
                "EAP con shock/arritmia grave: evitar CPAP inicialmente y usar "
                "mascarilla reservorio."
            )
            trace.append("CPAP descartado por contraindicacion hemodinamica.")
        elif severity == "grave":
            device = "mascarilla_reservorio"
            plan.append("Hipoxemia grave con mecanica preservada: usar mascarilla reservorio.")
            trace.append("Reservorio elegido por hipoxemia grave.")
        elif severity == "moderada" and payload.good_respiratory_mechanics:
            device = "mascarilla_venturi"
            plan.append("Hipoxemia moderada sin hipercapnia: usar mascarilla Venturi.")
            trace.append("Venturi elegido por hipoxemia moderada sin acidosis respiratoria.")
        elif severity == "leve":
            device = "gafas_nasales"
            plan.append("Paciente estable con hipoxemia leve: iniciar gafas nasales.")
            trace.append("Gafas nasales elegidas por hipoxemia leve.")
        else:
            plan.append(
                "Sin insuficiencia respiratoria relevante: mantener monitorizacion y reevaluar."
            )

        if payload.oxygen_saturation_percent is not None:
            plan.append(
                f"Saturacion actual registrada: {payload.oxygen_saturation_percent}%. "
                f"Objetivo operativo: {target}."
            )
        return device, target, plan, trace

    @staticmethod
    def _chest_pain_pe_pathway(payload: CriticalOpsProtocolRequest) -> tuple[list[str], list[str]]:
        pathway: list[str] = []
        trace: list[str] = []

        if not payload.suspected_pe:
            if payload.non_traumatic_chest_pain:
                pathway.append(
                    "Dolor toracico: integrar ECG precoz y correlacion clinico-analitica."
                )
            return pathway, trace

        if payload.wells_score is None:
            pathway.append("Calcular Wells para estimar probabilidad pretest de TEP.")
            trace.append("Ruta TEP pausada: Wells no informado.")
            return pathway, trace

        if payload.wells_score > 6:
            pathway.append("Wells >6: omitir Dimero D y solicitar Angio-TAC directamente.")
            trace.append("Wells alto (>6): ruta directa a Angio-TAC.")
            return pathway, trace

        pathway.append("Wells baja/intermedia: solicitar Dimero D.")
        trace.append("Wells <=6: activar ruta Dimero D previa a imagen.")
        if payload.d_dimer_ng_ml is None:
            pathway.append("Pendiente resultado de Dimero D para decidir imagen.")
        elif payload.d_dimer_ng_ml > 500:
            pathway.append("Dimero D >500: escalar a Angio-TAC.")
            trace.append("Dimero D positivo: recomendacion de Angio-TAC.")
        else:
            pathway.append("Dimero D <=500: TEP menos probable, reevaluar segun clinica.")
            trace.append("Dimero D negativo en Wells no alto.")
        return pathway, trace

    @staticmethod
    def _anaphylaxis_pathway(payload: CriticalOpsProtocolRequest) -> tuple[list[str], list[str]]:
        pathway: list[str] = []
        trace: list[str] = []
        probable_anaphylaxis = payload.rapid_cutaneous_mucosal_symptoms and (
            payload.respiratory_compromise or payload.cardiovascular_compromise
        )
        if not probable_anaphylaxis:
            return pathway, trace

        pathway.append("Anafilaxia probable: administrar adrenalina intramuscular inmediata.")
        pathway.append("Monitorizar via aerea, hemodinamica y necesidad de repeticion de dosis IM.")
        trace.append(
            "Anafilaxia activada por sintomas cutaneomucosos rapidos + compromiso organico."
        )
        if payload.on_beta_blocker and payload.anaphylaxis_refractory_to_im_adrenaline:
            pathway.append("Paciente en betabloqueantes refractario: considerar glucagon.")
            trace.append("Glucagon sugerido por refractariedad en paciente con betabloqueo.")
        return pathway, trace

    @staticmethod
    def _hemodynamic_profile(
        payload: CriticalOpsProtocolRequest,
    ) -> tuple[str, list[str], list[str]]:
        actions: list[str] = []
        trace: list[str] = []
        profile = "indeterminado"

        low_svr = payload.svr_dyn_s_cm5 is not None and payload.svr_dyn_s_cm5 < 900
        high_svr = payload.svr_dyn_s_cm5 is not None and payload.svr_dyn_s_cm5 > 1200
        low_or_normal_cvp = payload.cvp_mm_hg is not None and payload.cvp_mm_hg <= 10
        high_cvp = payload.cvp_mm_hg is not None and payload.cvp_mm_hg > 12
        low_co = payload.cardiac_output_l_min is not None and payload.cardiac_output_l_min < 4
        high_pcwp = (
            payload.pulmonary_capillary_wedge_pressure_mm_hg is not None
            and payload.pulmonary_capillary_wedge_pressure_mm_hg > 18
        )
        normal_pcwp = (
            payload.pulmonary_capillary_wedge_pressure_mm_hg is not None
            and payload.pulmonary_capillary_wedge_pressure_mm_hg <= 18
        )

        if low_svr and low_or_normal_cvp:
            profile = "shock_distributivo_probable"
            trace.append("Perfil distributivo: SVR bajo + PVC normal/baja.")
        elif high_cvp and high_svr and low_co and high_pcwp:
            profile = "shock_cardiogenico_probable"
            trace.append("Perfil cardiogenico: PVC alta + SVR alta + GC bajo + PCP alta.")
        elif high_cvp and high_svr and low_co and normal_pcwp:
            profile = "shock_obstructivo_probable"
            trace.append("Perfil obstructivo: PVC alta + SVR alta + GC bajo + PCP normal.")

        actions.append("Monitorizar lactato de forma seriada cada 2 horas.")
        if payload.lactate_interval_minutes is None or payload.lactate_interval_minutes > 120:
            actions.append("Ajustar intervalo de lactato a <=120 minutos.")
        if payload.lactate_mmol_l is not None and payload.lactate_mmol_l > 2:
            actions.append("Lactato elevado: reforzar evaluacion de hipoperfusion tisular.")
        if (
            payload.lactate_mmol_l is not None
            and payload.previous_lactate_mmol_l is not None
            and payload.lactate_mmol_l >= payload.previous_lactate_mmol_l
        ):
            actions.append("Lactato no desciende: considerar perfusion inadecuada persistente.")
            trace.append("Tendencia de lactato desfavorable (no clearance).")
        return profile, actions, trace

    @staticmethod
    def _nac_threshold_at_hour(hours: float) -> float:
        # Aproximacion lineal de la linea de tratamiento de Rumack-Matthew.
        # 150 mcg/mL a las 4 h y 25 mcg/mL a las 24 h.
        if hours <= 4:
            return 150.0
        if hours >= 24:
            return 25.0
        return 150.0 - ((hours - 4.0) * 6.25)

    @staticmethod
    def _toxicology(payload: CriticalOpsProtocolRequest) -> tuple[list[str], list[str], list[str]]:
        actions: list[str] = []
        alerts: list[str] = []
        trace: list[str] = []

        if payload.unknown_origin_coma:
            if (
                payload.capillary_glucose_mg_dl is not None
                and payload.capillary_glucose_mg_dl >= 70
            ):
                actions.append(
                    "Coma de origen no filiado con glucemia normal: considerar "
                    "naloxona y flumacenilo segun sospecha."
                )
                trace.append(
                    "Protocolo de coma desconocido activado tras descartar hipoglucemia capilar."
                )
            else:
                actions.append("Corregir hipoglucemia antes de protocolo de antidotos.")
            if payload.malnutrition_or_chronic_alcohol_use:
                actions.append("Administrar tiamina en paciente desnutrido/alcoholismo cronico.")

        if payload.opioid_intoxication_suspected:
            actions.append("Sospecha de opiaceos: priorizar ventilacion y naloxona temprana.")
        if payload.benzodiazepine_intoxication_suspected:
            actions.append("Sospecha de benzodiacepinas: valorar flumacenilo en contexto adecuado.")

        if payload.smoke_inhalation_suspected:
            actions.append("Intoxicacion por humo: administrar oxigeno al 100% de inmediato.")
            alerts.append("Intoxicacion por humo: descartar coexposicion a CO y cianuro.")
            trace.append("Ruta de humo activada con O2 al 100%.")
            if payload.cyanide_suspected:
                actions.append("Sospecha de cianuro: administrar hidroxocobalamina 5 g IV.")
                alerts.append("Posible intoxicacion por cianuro en incendio.")
                trace.append("Antidoto de cianuro sugerido por sospecha clinica.")

        if payload.paracetamol_overdose_suspected:
            if payload.hours_since_paracetamol_ingestion is None:
                actions.append(
                    "Paracetamol: documentar tiempo de ingesta y aplicar nomograma Rumack-Matthew."
                )
            elif payload.hours_since_paracetamol_ingestion < 4:
                actions.append(
                    "Paracetamol <4 h: obtener nivel a las 4 horas para decision de NAC."
                )
            elif payload.paracetamol_level_mcg_ml is None:
                actions.append("Paracetamol >=4 h: solicitar nivel plasmatico para nomograma.")
            else:
                threshold = CriticalOpsProtocolService._nac_threshold_at_hour(
                    payload.hours_since_paracetamol_ingestion
                )
                if payload.paracetamol_level_mcg_ml >= threshold:
                    actions.append("Nomograma sugiere toxicidad: iniciar N-acetilcisteina (NAC).")
                    trace.append("NAC recomendada por cruce de linea de tratamiento en nomograma.")
                else:
                    actions.append("Nivel por debajo de linea de tratamiento: vigilar y reevaluar.")

        if payload.core_temperature_celsius is not None and payload.core_temperature_celsius < 32:
            alerts.append("Hipotermia moderada/severa: recalentamiento activo obligatorio.")
            if payload.persistent_asystole:
                actions.append("No certificar muerte hasta recalentamiento (objetivo >28-32 C).")
                trace.append("Regla 'caliente y muerto' activada por hipotermia con asistolia.")
            if payload.core_temperature_celsius < 28:
                alerts.append("Temperatura <28 C: riesgo electrico extremo y alta prioridad.")

        return actions, alerts, trace

    @staticmethod
    def _red_flags(payload: CriticalOpsProtocolRequest) -> tuple[list[str], list[str]]:
        flags: list[str] = []
        trace: list[str] = []

        if payload.systemic_sclerosis_or_raynaud and payload.digital_necrosis_present:
            flags.append(
                "Isquemia digital en esclerosis/Raynaud: valorar prostaglandinas IV urgentes."
            )
            trace.append("Bandera roja de necrosis digital en contexto autoinmune.")

        if payload.abrupt_anuria_present:
            flags.append(
                "Anuria brusca: sospechar obstruccion bilateral y desobstruccion "
                "urgente (nefrostomia/doble J)."
            )
            trace.append("Bandera roja de anuria brusca con probable causa obstructiva.")

        if (
            payload.woman_childbearing_age
            and payload.lower_abdominal_pain
            and payload.vaginal_bleeding
            and payload.free_fluid_ultrasound
        ):
            flags.append(
                "Sospecha de embarazo ectopico roto: activar circuito ginecologico urgente."
            )
            trace.append("Triada de ectopico (dolor + sangrado + liquido libre) detectada.")

        if (
            payload.chest_tube_output_immediate_ml is not None
            and payload.chest_tube_output_immediate_ml > 1500
        ):
            flags.append(
                "Hemotorax masivo (>1500 ml inmediatos): indicacion de toracotomia urgente."
            )
            trace.append("Umbral quirurgico de hemotorax masivo superado.")

        return flags, trace

    @staticmethod
    def _radiology_actions(payload: CriticalOpsProtocolRequest) -> tuple[list[str], list[str]]:
        actions: list[str] = []
        trace: list[str] = []

        if payload.non_traumatic_chest_pain and not payload.chest_xray_performed:
            actions.append(
                "Solicitar radiografia de torax para descartar causas benignas "
                "y urgentes de dolor toracico."
            )
            trace.append("Integracion de RX torax en dolor toracico no traumatico.")
        if payload.hiatal_hernia_on_xray:
            actions.append(
                "Hallazgo de hernia de hiato en RX: correlacionar con clinica "
                "para evitar sobre-escalado."
            )
            trace.append("RX sugiere hernia de hiato como posible mimico de dolor toracico.")
        return actions, trace

    @staticmethod
    def _severity(
        *,
        sla_breaches: list[str],
        anaphylaxis_pathway: list[str],
        hemodynamic_profile: str,
        toxicology_alerts: list[str],
        red_flags: list[str],
    ) -> str:
        if sla_breaches or red_flags:
            return "critical"
        if anaphylaxis_pathway:
            return "critical"
        if hemodynamic_profile in {"shock_cardiogenico_probable", "shock_obstructivo_probable"}:
            return "high"
        if toxicology_alerts:
            return "high"
        return "medium"

    @staticmethod
    def build_recommendation(
        payload: CriticalOpsProtocolRequest,
    ) -> CriticalOpsProtocolRecommendation:
        """Genera recomendacion operativa critica para validacion humana."""
        sla_alerts, sla_breaches, sla_trace = CriticalOpsProtocolService._sla(payload)
        (
            respiratory_device,
            sat_target,
            respiratory_plan,
            respiratory_trace,
        ) = CriticalOpsProtocolService._respiratory_support(payload)
        chest_pathway, chest_trace = CriticalOpsProtocolService._chest_pain_pe_pathway(payload)
        anaphylaxis_pathway, anaphylaxis_trace = CriticalOpsProtocolService._anaphylaxis_pathway(
            payload
        )
        (
            hemodynamic_profile,
            hemodynamic_actions,
            hemodynamic_trace,
        ) = CriticalOpsProtocolService._hemodynamic_profile(payload)
        tox_actions, tox_alerts, tox_trace = CriticalOpsProtocolService._toxicology(payload)
        red_flags, red_trace = CriticalOpsProtocolService._red_flags(payload)
        radiology_actions, radiology_trace = CriticalOpsProtocolService._radiology_actions(payload)

        critical_alerts = []
        critical_alerts.extend(sla_breaches)
        critical_alerts.extend(red_flags)
        critical_alerts.extend(
            alert
            for alert in tox_alerts
            if "cianuro" in alert.lower() or "hipotermia" in alert.lower()
        )

        severity = CriticalOpsProtocolService._severity(
            sla_breaches=sla_breaches,
            anaphylaxis_pathway=anaphylaxis_pathway,
            hemodynamic_profile=hemodynamic_profile,
            toxicology_alerts=tox_alerts,
            red_flags=red_flags,
        )

        interpretability_trace = (
            sla_trace
            + respiratory_trace
            + chest_trace
            + anaphylaxis_trace
            + hemodynamic_trace
            + tox_trace
            + red_trace
            + radiology_trace
        )

        return CriticalOpsProtocolRecommendation(
            severity_level=severity,
            sla_alerts=sla_alerts,
            sla_breaches=sla_breaches,
            respiratory_device_recommended=respiratory_device,
            respiratory_target_saturation=sat_target,
            respiratory_support_plan=respiratory_plan,
            chest_pain_pe_pathway=chest_pathway,
            anaphylaxis_pathway=anaphylaxis_pathway,
            hemodynamic_profile=hemodynamic_profile,
            hemodynamic_actions=hemodynamic_actions,
            toxicology_reversal_actions=tox_actions,
            toxicology_alerts=tox_alerts,
            operational_red_flags=red_flags,
            radiology_actions=radiology_actions,
            critical_alerts=critical_alerts,
            interpretability_trace=interpretability_trace,
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. Requiere validacion clinica humana inmediata."
            ),
        )
