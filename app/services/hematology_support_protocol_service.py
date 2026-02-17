"""
Motor operativo de hematologia para urgencias.

No diagnostica; organiza rutas de riesgo para validacion clinica humana.
"""
from app.schemas.hematology_support_protocol import (
    HematologySupportProtocolRecommendation,
    HematologySupportProtocolRequest,
)


class HematologySupportProtocolService:
    """Construye recomendaciones operativas de hematologia en urgencias."""

    @staticmethod
    def _microangiopathy_and_hemolysis_pathway(
        payload: HematologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        diagnostic_actions: list[str] = []
        therapeutic_actions: list[str] = []
        trace: list[str] = []

        if (
            payload.mah_anemia_present
            and payload.thrombocytopenia_present
            and payload.organ_damage_present
        ):
            critical_alerts.append(
                "Triada de microangiopatia trombotica (MAT) detectada: "
                "anemia hemolitica + trombocitopenia + dano de organo."
            )
            diagnostic_actions.append(
                "Activar estudio urgente de MAT con frotis, hemolisis y funcion organica."
            )
            trace.append("Regla de triada MAT activada.")

        if (
            payload.cold_exposure_trigger
            and payload.intravascular_hemolysis_sudden
            and payload.hemoglobinuria_present
            and payload.free_plasma_hemoglobin_high
        ):
            critical_alerts.append(
                "Sospecha de hemoglobinuria paroxistica a frigore (Donath-Landsteiner)."
            )
            diagnostic_actions.append(
                "Correlacionar con mecanismo anti-P mediado por complemento y "
                "priorizar estudio de hemolisis intravascular."
            )
            if payload.hypotension_present or payload.acral_cyanosis_present:
                critical_alerts.append(
                    "Hemolisis intravascular con compromiso hemodinamico/acral: riesgo vital."
                )
            if payload.hemophagocytosis_in_smear:
                diagnostic_actions.append(
                    "Hemofagocitosis en frotis como hallazgo de apoyo (no patognomonico)."
                )

        shu_suspected = (
            payload.bloody_diarrhea_prodrome
            and payload.direct_coombs_negative
            and payload.thrombocytopenia_present
            and payload.creatinine_elevated
        )
        if payload.schistocytes_percent is not None:
            shu_suspected = shu_suspected and payload.schistocytes_percent > 10

        if shu_suspected:
            critical_alerts.append("Patron compatible con SHU tipico posdiarreico (Shiga-toxina).")
            diagnostic_actions.append(
                "Confirmar etiologia enterica y monitorizar dano renal/neurologico seriado."
            )
            therapeutic_actions.append(
                "En SHU tipico, priorizar soporte + antibiotico segun protocolo local."
            )
            therapeutic_actions.append(
                "No priorizar plasmaferesis en SHU tipico por baja utilidad."
            )
            if payload.neurological_involvement:
                critical_alerts.append(
                    "SHU con afectacion neurologica: escalar monitorizacion en area critica."
                )

        return critical_alerts, diagnostic_actions, therapeutic_actions, trace

    @staticmethod
    def _hit_and_hemostasis_pathway(
        payload: HematologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        therapeutic_actions: list[str] = []
        safety_alerts: list[str] = []
        trace: list[str] = []

        if payload.heparin_exposure_active:
            in_window = (
                payload.days_since_heparin_start is not None
                and 5 <= payload.days_since_heparin_start <= 10
            )
            drop_50 = (
                payload.platelet_drop_percent is not None and payload.platelet_drop_percent > 50
            )
            if in_window and drop_50:
                critical_alerts.append(
                    "Sospecha alta de TIH (ventana 5-10 dias + caida plaquetaria >50%)."
                )
                therapeutic_actions.append("Suspender heparina de forma inmediata.")
                if payload.renal_failure_present:
                    therapeutic_actions.append("En insuficiencia renal, priorizar Argatroban.")
                elif payload.hepatic_failure_present:
                    therapeutic_actions.append(
                        "En fallo hepatico, valorar Danaparoide o Fondaparinux."
                    )
                else:
                    therapeutic_actions.append(
                        "Iniciar anticoagulacion alternativa no heparinica segun riesgo."
                    )
                trace.append("Ruta de seguridad TIH activada.")
                if payload.major_orthopedic_postop_context:
                    critical_alerts.append(
                        "Contexto postquirurgico ortopedico mayor incrementa riesgo trombotico."
                    )

        if (
            payload.hemophilia_a_severe
            and payload.high_titer_factor_viii_inhibitors
            and payload.acute_hemarthrosis
        ):
            critical_alerts.append("Hemofilia A grave con inhibidores en sangrado articular agudo.")
            therapeutic_actions.append(
                "Usar agentes bypass: rFVIIa o complejo protrombinico (segun contexto)."
            )
            if payload.on_emicizumab_prophylaxis:
                safety_alerts.append(
                    "Emicizumab es profilaxis; no sustituye control del sangrado agudo."
                )
                if payload.prothrombin_complex_planned:
                    critical_alerts.append(
                        "Evitar complejo protrombinico junto a Emicizumab por riesgo de MAT."
                    )

        return critical_alerts, therapeutic_actions, safety_alerts, trace

    @staticmethod
    def _oncology_and_genetic_pathway(
        payload: HematologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
        diagnostic_actions: list[str] = []
        oncology_notes: list[str] = []
        fanconi_flags: list[str] = []
        transplant_flags: list[str] = []
        trace: list[str] = []

        if payload.fine_needle_aspirate_only and not payload.biopsy_histology_available:
            diagnostic_actions.append(
                "PAAF aislada insuficiente para clasificacion: requerir biopsia histologica."
            )
        elif payload.biopsy_histology_available:
            diagnostic_actions.append(
                "Biopsia histologica disponible: base valida para clasificacion de linfoma."
            )

        if payload.cd20_positive and not payload.cd3_positive:
            oncology_notes.append("Inmunofenotipo compatible con LBDCG (CD20+, CD3-).")
        if payload.cd15_positive and payload.cd30_positive:
            oncology_notes.append(
                "Patron compatible con linfoma de Hodgkin clasico (CD15+, CD30+)."
            )
        if payload.cd19_positive and payload.cd5_positive and payload.cd23_positive:
            if payload.cd20_weak:
                oncology_notes.append("Patron compatible con LLC (CD19+, CD5+, CD23+, CD20 debil).")
            else:
                oncology_notes.append(
                    "Perfil sugiere LLC; confirmar intensidad de CD20 y correlacion clinica."
                )
        if payload.cd5_positive and not payload.cd23_positive:
            if payload.cyclin_d1_positive or payload.sox11_positive:
                oncology_notes.append(
                    "CD5+ con CD23- y CiclinaD1/SOX11: sugiere linfoma del manto."
                )

        if payload.hhv8_positive:
            oncology_notes.append("HHV-8 asociado a linfoma primario de cavidades.")
        if payload.ebv_positive:
            oncology_notes.append("EBV asociado a Burkitt, Hodgkin y NK/T nasal.")
        if payload.htlv1_positive:
            oncology_notes.append("HTLV-1 asociado a leucemia/linfoma T del adulto.")

        fanconi_phenotype_points = sum(
            [
                payload.short_stature,
                payload.cafe_au_lait_spots,
                payload.thumb_or_radius_hypoplasia,
                payload.renal_anomaly_present,
                payload.micrognathia_present,
            ]
        )
        if payload.pediatric_patient and fanconi_phenotype_points >= 3:
            fanconi_flags.append(
                "Fenotipo compatible con anemia de Fanconi: activar ruta de insuficiencia medular."
            )
            if payload.macrocytosis_present or payload.thrombocytopenia_present:
                fanconi_flags.append("Evolucion hematologica sugestiva (macrocitosis/trombopenia).")
            if payload.pancytopenia_present:
                fanconi_flags.append(
                    "Pancitopenia en contexto Fanconi: alto riesgo de progresion medular."
                )
            fanconi_flags.append(
                "Activar cribado onco-hematologico por riesgo de LMA y tumores solidos."
            )
            trace.append("Ruta de sospecha de Fanconi pediatrica activada.")

        if (
            payload.hsct_recipient
            and payload.recipient_male
            and payload.donor_karyotype_47xxy_detected
        ):
            transplant_flags.append(
                "Quimerismo post-trasplante sugiere posible sindrome de Klinefelter en donante."
            )

        return diagnostic_actions, oncology_notes, fanconi_flags, transplant_flags, trace

    @staticmethod
    def _postsplenectomy_safety_pathway(
        payload: HematologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        checklist: list[str] = []
        trace: list[str] = []

        if payload.planned_splenectomy:
            if payload.encapsulated_vaccines_completed_preop:
                if (
                    payload.days_vaccines_before_splenectomy is not None
                    and payload.days_vaccines_before_splenectomy >= 14
                ):
                    checklist.append(
                        "Vacunacion preoperatoria frente a encapsulados "
                        "completada en ventana segura."
                    )
                else:
                    critical_alerts.append(
                        "Vacunacion preoperatoria insuficiente (<2 semanas) antes de esplenectomia."
                    )
            else:
                critical_alerts.append(
                    "Falta vacunacion preoperatoria frente a encapsulados antes de esplenectomia."
                )
            trace.append("Checklist de seguridad preesplenectomia evaluado.")

        if payload.postsplenectomy_status:
            if payload.active_bleeding:
                checklist.append(
                    "Posesplenectomia con sangrado activo: diferir tromboprofilaxis hasta control."
                )
            elif payload.thromboprophylaxis_started:
                checklist.append("Tromboprofilaxis posesplenectomia iniciada correctamente.")
            else:
                critical_alerts.append(
                    "Posesplenectomia sin tromboprofilaxis: riesgo tromboembolico elevado."
                )

        return critical_alerts, checklist, trace

    @staticmethod
    def _severity(
        *,
        critical_alerts: list[str],
        safety_alerts: list[str],
        fanconi_flags: list[str],
    ) -> str:
        if critical_alerts:
            return "critical"
        if safety_alerts or fanconi_flags:
            return "high"
        return "medium"

    @staticmethod
    def build_recommendation(
        payload: HematologySupportProtocolRequest,
    ) -> HematologySupportProtocolRecommendation:
        """Genera recomendacion operativa de hematologia para validacion humana."""
        (
            critical_mat,
            diagnostic_mat,
            therapeutic_mat,
            trace_mat,
        ) = HematologySupportProtocolService._microangiopathy_and_hemolysis_pathway(payload)
        (
            critical_hit,
            therapeutic_hit,
            safety_hit,
            trace_hit,
        ) = HematologySupportProtocolService._hit_and_hemostasis_pathway(payload)
        (
            diagnostic_onco,
            oncology_notes,
            fanconi_flags,
            transplant_flags,
            trace_onco,
        ) = HematologySupportProtocolService._oncology_and_genetic_pathway(payload)
        (
            critical_spl,
            spl_checklist,
            trace_spl,
        ) = HematologySupportProtocolService._postsplenectomy_safety_pathway(payload)

        critical_alerts = critical_mat + critical_hit + critical_spl
        diagnostic_actions = diagnostic_mat + diagnostic_onco
        therapeutic_actions = therapeutic_mat + therapeutic_hit
        safety_alerts = safety_hit
        interpretability_trace = trace_mat + trace_hit + trace_onco + trace_spl

        severity = HematologySupportProtocolService._severity(
            critical_alerts=critical_alerts,
            safety_alerts=safety_alerts,
            fanconi_flags=fanconi_flags,
        )

        return HematologySupportProtocolRecommendation(
            severity_level=severity,
            critical_alerts=critical_alerts,
            diagnostic_actions=diagnostic_actions,
            therapeutic_actions=therapeutic_actions,
            pharmacologic_safety_alerts=safety_alerts,
            oncology_immunophenotype_notes=oncology_notes,
            inherited_bone_marrow_failure_flags=fanconi_flags,
            postsplenectomy_checklist=spl_checklist,
            transplant_flags=transplant_flags,
            interpretability_trace=interpretability_trace,
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. "
                "Requiere validacion por hematologia/equipo de urgencias."
            ),
        )
