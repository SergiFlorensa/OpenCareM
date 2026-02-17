"""
Motor operativo neurologico para urgencias.

No diagnostica; organiza rutas de alto riesgo para validacion clinica humana.
"""
from app.schemas.neurology_support_protocol import (
    NeurologySupportProtocolRecommendation,
    NeurologySupportProtocolRequest,
)


class NeurologySupportProtocolService:
    """Construye recomendaciones operativas para neurologia de urgencias."""

    @staticmethod
    def _vascular_pathway(
        payload: NeurologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        alerts: list[str] = []
        actions: list[str] = []
        stroke_pathway: list[str] = []
        trace: list[str] = []

        if payload.sudden_severe_headache:
            alerts.append("Cefalea brusca: descartar hemorragia subaracnoidea de forma inmediata.")
            actions.append("Priorizar TAC craneal urgente ante cefalea de inicio brusco.")
            trace.append("Disparador HSA activado por cefalea brusca.")

        if payload.cranial_ct_subarachnoid_hyperdensity:
            alerts.append("TAC con hiperdensidad subaracnoidea: alta sospecha de HSA.")
            actions.append("Activar circuito neurovascular/neuroquirurgico urgente.")
            trace.append("Imagen compatible con sangrado subaracnoideo.")

        if payload.perimesencephalic_bleeding_pattern:
            actions.append(
                "Patron perimesencefalico (~10% de HSA): considerar origen "
                "no aneurismatico de mejor pronostico."
            )
            trace.append("Fenotipo perimesencefalico detectado.")
            if payload.cerebral_angiography_result == "normal":
                actions.append(
                    "Angiografia normal con patron perimesencefalico: curso tipicamente benigno."
                )

        if payload.aneurysm_or_malformation_suspected:
            actions.append(
                "Si sospecha de aneurisma/malformacion, recordar angiografia cerebral "
                "como patron oro."
            )
            trace.append("Regla de gold standard vascular aplicada.")

        if payload.suspected_stroke:
            stroke_pathway.append("Sospecha de ictus: activar codigo ictus inmediato.")
            trace.append("Codigo ictus activado.")

            unknown_onset = (
                payload.wake_up_stroke
                or not payload.symptom_onset_known
                or payload.hours_since_symptom_onset is None
            )
            if unknown_onset:
                stroke_pathway.append(
                    "Inicio desconocido/wake-up stroke: priorizar TAC perfusion para penumbra."
                )
                if payload.ct_perfusion_performed and payload.salvageable_penumbra_present:
                    stroke_pathway.append(
                        "Penumbra salvable en inicio desconocido: valorar trombectomia hasta 24 h."
                    )
                elif (
                    payload.ct_perfusion_performed and payload.salvageable_penumbra_present is False
                ):
                    stroke_pathway.append(
                        "Perfusion sin penumbra salvable: reevaluar beneficio de "
                        "reperfusion invasiva."
                    )
                trace.append("Ruta de inicio desconocido activada.")
            else:
                if payload.hours_since_symptom_onset <= 4.5:
                    stroke_pathway.append(
                        "Ventana <=4.5 h: valorar fibrinolisis con alteplasa segun criterios."
                    )
                    trace.append("Ventana de fibrinolisis potencialmente abierta.")
                elif payload.hours_since_symptom_onset <= 24:
                    if payload.ct_perfusion_performed and payload.salvageable_penumbra_present:
                        stroke_pathway.append(
                            "Hasta 24 h con penumbra salvable: valorar trombectomia mecanica."
                        )
                        trace.append("Trombectomia tardia sustentada por perfusion con penumbra.")
                    else:
                        stroke_pathway.append(
                            "Fuera de fibrinolisis: completar imagen de perfusion para "
                            "seleccion de trombectomia."
                        )
                else:
                    stroke_pathway.append(
                        "Tiempo de evolucion >24 h: individualizar segun imagen y clinica."
                    )

            if payload.aspects_score is not None:
                if payload.aspects_score >= 8:
                    stroke_pathway.append(
                        "ASPECTS alto (8-10): poca isquemia establecida, favorecer "
                        "estrategia de reperfusion."
                    )
                    trace.append("ASPECTS alto favorece tratamiento activo.")
                elif payload.aspects_score <= 5:
                    stroke_pathway.append(
                        "ASPECTS bajo: alta carga isquemica, reevaluar balance riesgo-beneficio."
                    )

        return alerts, actions, stroke_pathway, trace

    @staticmethod
    def _differential_clues(
        payload: NeurologySupportProtocolRequest,
    ) -> tuple[list[str], list[str]]:
        clues: list[str] = []
        trace: list[str] = []

        if payload.parkinsonism_suspected:
            atypical_flags = [
                payload.levodopa_response == "pobre",
                payload.early_falls,
                payload.severe_early_dysautonomia,
                payload.ocular_movement_limitation,
            ]
            if (
                payload.levodopa_response == "excelente"
                and payload.mibg_cardiac_denervation is True
                and not any(atypical_flags)
            ):
                clues.append(
                    "Perfil compatible con Parkinson (respuesta a levodopa + MIBG desinervado)."
                )
                trace.append("Regla de apoyo a Parkinson clasico activada.")
            if any(atypical_flags):
                clues.append(
                    "Red flags de parkinsonismo atipico: respuesta pobre a levodopa, "
                    "caidas precoces, disautonomia grave o paresia ocular."
                )
                trace.append("Red flags de parkinsonismo atipico detectadas.")
            if payload.datscan_presynaptic_deficit is True:
                clues.append(
                    "DaTSCAN alterado confirma via nigroestriada, pero no diferencia "
                    "Parkinson vs parkinsonismos atipicos."
                )

        if payload.facial_weakness_pattern == "mitad_inferior":
            clues.append(
                "Paralisis facial de mitad inferior: orienta a origen central supranuclear."
            )
            trace.append("Mapa facial sugiere lesion central.")
        elif payload.facial_weakness_pattern == "hemicara_completa":
            clues.append("Paralisis facial de hemicara completa: orienta a origen periferico.")
            trace.append("Mapa facial sugiere lesion periferica.")

        if payload.bilateral_pressing_headache and not payload.headache_activity_limitation:
            clues.append(
                "Patron compatible con cefalea tensional (bilateral, opresiva, funcional)."
            )
        if (
            payload.pulsatile_unilateral_headache
            and payload.headache_activity_limitation
            and (payload.nausea_or_vomiting or payload.photophobia)
        ):
            clues.append(
                "Patron compatible con migrana (unilateral pulsatil y sintomas asociados)."
            )

        return clues, trace

    @staticmethod
    def _autoimmune_neuromuscular_pathway(
        payload: NeurologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        pathway: list[str] = []
        contraindications: list[str] = []
        trace: list[str] = []

        gbs_suspected = payload.rapidly_progressive_weakness and payload.areflexia_or_hyporeflexia
        if gbs_suspected:
            pathway.append(
                "SGB probable: debilidad progresiva + arreflexia/hiporreflexia, vigilar progresion."
            )
            trace.append("Criterio clinico de SGB activado.")
            if payload.csf_albuminocytologic_dissociation:
                pathway.append("LCR con disociacion albumino-citologica apoya SGB.")
            if payload.corticosteroids_planned:
                contraindications.append(
                    "SGB: corticoides contraindicados; reevaluar plan terapeutico."
                )
                trace.append("Alerta de seguridad por corticoides en SGB.")

        if payload.fluctuating_weakness and payload.ocular_ptosis_or_diplopia:
            pathway.append("Miastenia gravis probable: debilidad fluctuante con predominio ocular.")
            if payload.pupils_spared:
                pathway.append("Respeta pupila: dato semiologico compatible con miastenia.")
            if payload.myasthenia_seronegative:
                pathway.append(
                    "Miastenia seronegativa: puede tener respuesta terapeutica menos predecible."
                )
            trace.append("Perfil clinico de miastenia detectado.")

        anti_nmda_profile = all(
            [
                payload.young_woman,
                payload.acute_psychiatric_symptoms,
                payload.seizures_present,
                payload.orofacial_dyskinesias,
            ]
        )
        if anti_nmda_profile:
            pathway.append(
                "Perfil compatible con encefalitis anti-NMDA: combinar manejo "
                "neurologico y psiquiatrico."
            )
            if not payload.ovarian_teratoma_screening_done:
                pathway.append("Realizar busqueda obligatoria de teratoma ovarico asociado.")
            trace.append("Disparador anti-NMDA activado por fenotipo clinico completo.")

        return pathway, contraindications, trace

    @staticmethod
    def _biomarker_guidance(
        payload: NeurologySupportProtocolRequest,
    ) -> tuple[list[str], list[str]]:
        guidance: list[str] = []
        trace: list[str] = []

        if payload.csf_tau_elevated is True and payload.csf_beta_amyloid_42_decreased is True:
            guidance.append(
                "Perfil LCR (Tau alta + beta-amiloide42 baja) compatible con Alzheimer temprano."
            )
            trace.append("Regla de biomarcadores de Alzheimer activada.")
        if payload.apoe_e4_present is True:
            guidance.append("ApoE4 es factor de riesgo, pero no establece diagnostico por si solo.")

        if payload.aneurysm_or_malformation_suspected:
            guidance.append(
                "Angiografia/arteriografia cerebral mantiene rol de patron oro en aneurismas/MAV."
            )
        if payload.datscan_presynaptic_deficit is True:
            guidance.append(
                "DaTSCAN alterado indica via nigroestriada afectada sin diferenciar subtipo."
            )

        return guidance, trace

    @staticmethod
    def _advanced_decision_support(
        payload: NeurologySupportProtocolRequest,
    ) -> tuple[list[str], list[str]]:
        support: list[str] = []
        trace: list[str] = []

        if payload.dbs_candidate_considered:
            if (
                payload.parkinson_symptoms_levodopa_responsive
                and not payload.severe_cognitive_decline
            ):
                support.append(
                    "DBS (nucleo subtalamico) potencialmente util en sintomas "
                    "levodopa-responsivos."
                )
                trace.append(
                    "DBS favorecida por respuesta a levodopa sin deterioro cognitivo grave."
                )
            if payload.severe_cognitive_decline:
                support.append(
                    "DBS no indicada para deterioro cognitivo no respondedor a levodopa."
                )

        if payload.progressive_paraparesis and payload.upper_motor_neuron_signs:
            support.append(
                "Paraparesia progresiva con signos de 1a motoneurona: priorizar RM cervical."
            )
            if payload.sphincter_dysfunction:
                support.append(
                    "Compromiso esfinteriano refuerza sospecha de mielopatia compresiva."
                )
            if payload.worsens_with_cervical_flexion_extension:
                support.append(
                    "Empeoramiento con flexo-extension cervical sugiere compresion mecanica."
                )
            if payload.cervical_mri_compressive_pattern_t2 is True:
                support.append(
                    "RM cervical con patron compresivo: valorar descompresion segun neurocirugia."
                )
            trace.append("Ruta de mielopatia cervical compresiva activada.")

        return support, trace

    @staticmethod
    def _severity(
        *,
        vascular_alerts: list[str],
        stroke_pathway: list[str],
        contraindication_alerts: list[str],
        autoimmune_pathway: list[str],
    ) -> str:
        if vascular_alerts or contraindication_alerts:
            return "critical"
        if any("codigo ictus" in item.lower() for item in stroke_pathway):
            return "high"
        if autoimmune_pathway:
            return "high"
        return "medium"

    @staticmethod
    def build_recommendation(
        payload: NeurologySupportProtocolRequest,
    ) -> NeurologySupportProtocolRecommendation:
        """Genera recomendacion operativa neurologica para validacion humana."""
        (
            vascular_alerts,
            immediate_actions,
            stroke_pathway,
            vascular_trace,
        ) = NeurologySupportProtocolService._vascular_pathway(payload)
        (
            differential_clues,
            differential_trace,
        ) = NeurologySupportProtocolService._differential_clues(payload)
        (
            autoimmune_pathway,
            contraindications,
            autoimmune_trace,
        ) = NeurologySupportProtocolService._autoimmune_neuromuscular_pathway(payload)
        biomarker_guidance, biomarker_trace = NeurologySupportProtocolService._biomarker_guidance(
            payload
        )
        (
            advanced_support,
            advanced_trace,
        ) = NeurologySupportProtocolService._advanced_decision_support(payload)

        severity = NeurologySupportProtocolService._severity(
            vascular_alerts=vascular_alerts,
            stroke_pathway=stroke_pathway,
            contraindication_alerts=contraindications,
            autoimmune_pathway=autoimmune_pathway,
        )

        interpretability_trace = (
            vascular_trace
            + differential_trace
            + autoimmune_trace
            + biomarker_trace
            + advanced_trace
        )

        return NeurologySupportProtocolRecommendation(
            severity_level=severity,
            vascular_life_threat_alerts=vascular_alerts,
            immediate_actions=immediate_actions,
            stroke_reperfusion_pathway=stroke_pathway,
            differential_clues=differential_clues,
            autoimmune_neuromuscular_pathway=autoimmune_pathway,
            biomarker_guidance=biomarker_guidance,
            advanced_decision_support=advanced_support,
            contraindication_alerts=contraindications,
            interpretability_trace=interpretability_trace,
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. Requiere validacion neurologica/neuroquirurgica."
            ),
        )
