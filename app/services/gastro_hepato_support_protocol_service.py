"""
Motor operativo gastro-hepato para urgencias.

No diagnostica; organiza rutas de riesgo para validacion clinica humana.
"""
from app.schemas.gastro_hepato_support_protocol import (
    GastroHepatoSupportProtocolRecommendation,
    GastroHepatoSupportProtocolRequest,
)


class GastroHepatoSupportProtocolService:
    """Construye recomendaciones operativas digestivas/hepatobiliares."""

    @staticmethod
    def _vascular_hemodynamic_pathway(
        payload: GastroHepatoSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        actions: list[str] = []
        trace: list[str] = []

        portal_thrombosis_pattern = payload.portal_thrombosis_confirmed or (
            payload.abdominal_pain
            and payload.jaundice
            and payload.ascites
            and payload.portal_doppler_no_flow_silence
        )
        if portal_thrombosis_pattern:
            critical_alerts.append(
                "Sospecha de trombosis portal aguda: priorizar anticoagulacion inmediata."
            )
            actions.append(
                "Iniciar anticoagulacion oral como primera linea si no hay contraindicaciones."
            )
            trace.append("Patron clinico-Doppler de trombosis portal identificado.")
            if payload.failed_initial_anticoagulation:
                actions.append(
                    "Fracaso terapeutico: valorar TIPS/angioplastia en centro experimentado."
                )
            elif payload.endovascular_therapy_considered:
                actions.append(
                    "Terapia endovascular reservada para fracaso del manejo anticoagulante."
                )

        if payload.cirrhosis_known and payload.upper_gi_bleeding_suspected:
            actions.append("HDA en cirrotico: estabilizacion hemodinamica con fluidoterapia.")
            if not payload.vasoactive_somatostatin_started:
                critical_alerts.append(
                    "HDA en cirrotico sin somatostatina inmediata: riesgo de peor control inicial."
                )
            else:
                actions.append(
                    "Mantener farmaco vasoactivo precoz (somatostatina) previo a endoscopia."
                )

            if payload.endoscopy_performed:
                if payload.hours_to_endoscopy is not None and payload.hours_to_endoscopy > 12:
                    critical_alerts.append(
                        "Endoscopia >12 h en HDA cirrotico: incumplimiento de ventana objetivo."
                    )
                if payload.variceal_band_ligation_done:
                    actions.append("Endoscopia terapeutica con ligadura de varices realizada.")
            else:
                critical_alerts.append(
                    "HDA en cirrotico sin endoscopia temprana: priorizar procedimiento <12 h."
                )

            if payload.early_rebleeding or payload.bleeding_controlled_with_bands is False:
                actions.append(
                    "Hemorragia no controlada/resangrado precoz: valorar TIPS de rescate."
                )
                trace.append("Escalada a terapia de rescate por fracaso de bandas.")
            elif payload.tips_considered and payload.variceal_band_ligation_done is False:
                actions.append(
                    "Evitar TIPS precoz sin intento endoscopico, salvo inestabilidad extrema."
                )

        return critical_alerts, actions, trace

    @staticmethod
    def _imaging_and_differential_pathway(
        payload: GastroHepatoSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        imaging_red_flags: list[str] = []
        differential_clues: list[str] = []

        if (
            payload.abdominal_pain
            and payload.hypotension_present
            and payload.portal_venous_gas_on_ct
            and payload.gastric_pneumatosis_on_ct
        ):
            critical_alerts.append(
                "Triada critica (dolor + hipotension + gas portal/neumatosis): "
                "sugiere isquemia/necrosis gastrointestinal de mal pronostico."
            )
            imaging_red_flags.append(
                "Gas portal periferico asociado a neumatosis gastrica: red flag mayor."
            )
        elif payload.portal_venous_gas_on_ct and payload.gastric_pneumatosis_on_ct:
            imaging_red_flags.append(
                "Gas portal + neumatosis gastrica: vigilar isquemia intestinal "
                "y evolucion hemodinamica."
            )

        if payload.aerobilia_central_pattern:
            if payload.prior_biliary_instrumentation:
                differential_clues.append(
                    "Aerobilia central con manipulacion biliar previa: hallazgo esperado "
                    "post-procedimiento."
                )
            else:
                differential_clues.append(
                    "Aerobilia central sin antecedente instrumental: ampliar estudio etiologico."
                )

        courvoisier_pattern = (
            payload.painless_gallbladder_distension
            and payload.cholestatic_jaundice
            and payload.biliary_tree_dilation_intra_extrahepatic
        )
        if courvoisier_pattern:
            imaging_red_flags.append(
                "Signo de Courvoisier: priorizar estudio de obstruccion maligna distal."
            )
            differential_clues.append(
                "Patron sugiere tumor pancreatico/colangiocarcinoma distal mas que hepatitis "
                "medicamentosa."
            )
        elif (
            payload.recent_amoxicillin_clavulanate
            and not payload.biliary_tree_dilation_intra_extrahepatic
        ):
            differential_clues.append(
                "Colestasis por amoxicilina-clavulanato posible sin dilatacion biliar mecanica."
            )

        diverticulitis_pattern = all(
            [
                payload.left_lower_quadrant_pain,
                payload.fever_present,
                payload.leukocytosis_present,
                payload.crp_elevated,
                payload.ct_pericolonic_inflammation_sigmoid_descending,
            ]
        )
        if diverticulitis_pattern and not payload.bowel_loop_dilation_present:
            differential_clues.append(
                "Perfil compatible con diverticulitis aguda no oclusiva "
                "(sigma/colon descendente)."
            )
        elif diverticulitis_pattern and payload.bowel_loop_dilation_present:
            critical_alerts.append(
                "Dolor FII con dilatacion de asas: descartar proceso oclusivo/complicado."
            )

        if payload.hernia_below_inguinal_ligament:
            differential_clues.append(
                "Hernia crural/femoral: alto riesgo de incarceracion y obstruccion."
            )
            if payload.intestinal_obstruction_signs or payload.incarceration_or_strangulation_signs:
                critical_alerts.append(
                    "Hernia crural complicada con datos obstructivos: "
                    "valoracion quirurgica urgente."
                )

        return critical_alerts, imaging_red_flags, differential_clues

    @staticmethod
    def _surgical_pharmacology_genetic_pathway(
        payload: GastroHepatoSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        surgical_support: list[str] = []
        pharmacology_alerts: list[str] = []
        genetic_guidance: list[str] = []
        trace: list[str] = []

        if payload.porcelain_gallbladder:
            surgical_support.append(
                "Vesicula en porcelana: indicacion de colecistectomia programada "
                "por alto riesgo oncologico."
            )
            trace.append("Indicacion quirurgica fuerte por vesicula en porcelana.")

        if payload.gallstone_size_cm is not None and payload.gallstone_size_cm >= 2.5:
            surgical_support.append(
                "Calculos >=2.5-3 cm: considerar cirugia segun riesgo individual "
                "(evidencia limitada)."
            )
        if payload.symptomatic_microlithiasis:
            surgical_support.append(
                "Microlitiasis sintomatica: valorar colecistectomia por sintomas."
            )

        if payload.inguinal_hernia_repair_planned:
            if payload.wants_non_mesh_technique or payload.planned_hernia_technique == "shouldice":
                surgical_support.append(
                    "Shouldice: unica tecnica clasica sin malla para hernia inguinal."
                )
            if payload.planned_hernia_technique in {"tep", "tapp", "lichtenstein"}:
                surgical_support.append(
                    "Tecnica planificada con malla (TEP/TAPP/Lichtenstein) segun abordaje."
                )

        if (
            payload.duodenal_adenocarcinoma_non_metastatic
            and not payload.duodenal_adenocarcinoma_nodal_or_metastatic
        ):
            surgical_support.append(
                "Adenocarcinoma duodenal resecable: considerar duodenopancreatectomia "
                "cefalica (Whipple)."
            )

        if payload.ibd_patient and payload.azathioprine_active:
            pharmacology_alerts.append(
                "Azatioprina en EII: aumentar vigilancia de cancer cutaneo no melanocitico."
            )
        if payload.ibd_patient and payload.infliximab_or_biologic_active:
            pharmacology_alerts.append("Infliximab/biologico en EII: reforzar cribado de melanoma.")

        if payload.zenker_diverticulum_suspected:
            surgical_support.append(
                "Diverticulo de Zenker: diverticulo de pulsion por debilidad cricofaringea."
            )
            if payload.open_zenker_surgery_selected:
                surgical_support.append("Abordaje abierto de Zenker: via cervical izquierda.")

        if payload.gerd_preop_evaluation and not payload.esophageal_manometry_done:
            genetic_guidance.append(
                "ERGE prequirurgico: completar manometria esofagica " "(gold standard funcional)."
            )
        elif payload.gerd_preop_evaluation and payload.esophageal_manometry_done:
            genetic_guidance.append("Manometria esofagica realizada para planificacion de ERGE.")

        if payload.fap_suspected:
            genetic_guidance.append("PAF: priorizar estudio de mutacion APC.")
            if payload.mandibular_osteomas or payload.retinal_pigment_epithelium_hypertrophy:
                genetic_guidance.append(
                    "Manifestaciones extracolonicas (osteomas mandibulares/epitelio "
                    "pigmentario retiniano) apoyan PAF."
                )
            if payload.apc_mutation_present is True:
                genetic_guidance.append(
                    "Mutacion APC confirmada: seguimiento de alto riesgo oncologico."
                )

        return surgical_support, pharmacology_alerts, genetic_guidance, trace

    @staticmethod
    def _severity(
        *,
        critical_alerts: list[str],
        hemodynamic_actions: list[str],
        imaging_red_flags: list[str],
    ) -> str:
        if critical_alerts:
            return "critical"
        if hemodynamic_actions or imaging_red_flags:
            return "high"
        return "medium"

    @staticmethod
    def build_recommendation(
        payload: GastroHepatoSupportProtocolRequest,
    ) -> GastroHepatoSupportProtocolRecommendation:
        """Genera recomendacion operativa gastro-hepato para validacion humana."""
        (
            critical_vascular,
            hemodynamic_actions,
            vascular_trace,
        ) = GastroHepatoSupportProtocolService._vascular_hemodynamic_pathway(payload)
        (
            critical_imaging,
            imaging_red_flags,
            differential_clues,
        ) = GastroHepatoSupportProtocolService._imaging_and_differential_pathway(payload)
        (
            surgical_support,
            pharmacology_alerts,
            genetic_guidance,
            surgery_trace,
        ) = GastroHepatoSupportProtocolService._surgical_pharmacology_genetic_pathway(payload)

        critical_alerts = critical_vascular + critical_imaging
        severity = GastroHepatoSupportProtocolService._severity(
            critical_alerts=critical_alerts,
            hemodynamic_actions=hemodynamic_actions,
            imaging_red_flags=imaging_red_flags,
        )
        interpretability_trace = vascular_trace + surgery_trace

        return GastroHepatoSupportProtocolRecommendation(
            severity_level=severity,
            critical_alerts=critical_alerts,
            hemodynamic_actions=hemodynamic_actions,
            imaging_red_flags=imaging_red_flags,
            differential_clues=differential_clues,
            surgical_decision_support=surgical_support,
            pharmacology_safety_alerts=pharmacology_alerts,
            functional_genetic_guidance=genetic_guidance,
            interpretability_trace=interpretability_trace,
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. Requiere validacion de digestivo/cirugia."
            ),
        )
