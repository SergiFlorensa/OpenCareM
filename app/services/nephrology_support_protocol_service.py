"""
Motor operativo de nefrologia para urgencias.

No diagnostica; organiza rutas de riesgo para validacion clinica humana.
"""
from app.schemas.nephrology_support_protocol import (
    NephrologySupportProtocolRecommendation,
    NephrologySupportProtocolRequest,
)


class NephrologySupportProtocolService:
    """Construye recomendaciones operativas nefrologicas en urgencias."""

    @staticmethod
    def _aki_classification_pathway(
        payload: NephrologySupportProtocolRequest,
    ) -> tuple[str, list[str], list[str], list[str]]:
        diagnostic_actions: list[str] = []
        glomerular_flags: list[str] = []
        trace: list[str] = []

        if payload.abrupt_anuria_present or payload.hydronephrosis_ultrasound_present:
            trace.append("Clasificacion FRA obstructivo por anuria/hidronefrosis.")
            diagnostic_actions.append(
                "Priorizar descarte de obstruccion urinaria y descompresion urgente si procede."
            )
            return "obstructive", diagnostic_actions, glomerular_flags, trace

        if payload.urine_sodium_mmol_l is not None:
            if payload.urine_sodium_mmol_l < 20:
                trace.append("Clasificacion FRA prerrenal por sodio urinario bajo.")
                return "prerenal", diagnostic_actions, glomerular_flags, trace
            if payload.urine_sodium_mmol_l > 40:
                trace.append(
                    "Clasificacion FRA parenquimatoso (NTA probable) por sodio urinario elevado."
                )
                return "parenchymal", diagnostic_actions, glomerular_flags, trace

        if payload.diabetic_retinopathy_present and payload.acute_kidney_injury_present:
            glomerular_flags.append(
                "Retinopatia diabetica asociada: refuerza contexto de dano "
                "renal vascular diabetico."
            )

        trace.append("Clasificacion FRA indeterminada; completar datos de sedimento/imagen.")
        diagnostic_actions.append(
            "Completar perfil urinario y ecografia para clasificacion sindromica del FRA."
        )
        return "indeterminate", diagnostic_actions, glomerular_flags, trace

    @staticmethod
    def _renopulmonary_and_glomerular_pathway(
        payload: NephrologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        diagnostic_actions: list[str] = []
        therapeutic_actions: list[str] = []
        glomerular_flags: list[str] = []
        trace: list[str] = []

        renopulmonary = (
            payload.proteinuria_present
            and payload.microhematuria_present
            and payload.bilateral_ground_glass_ct_present
            and payload.acute_anemization_present
        )
        if renopulmonary:
            critical_alerts.append(
                "Sindrome renopulmonar critico: probable GNRP con hemorragia alveolar."
            )
            therapeutic_actions.append(
                "Escalar inicio urgente de inmunosupresion y plasmaferesis segun protocolo local."
            )
            trace.append("Regla sindromica renopulmonar activada.")
            if payload.platelet_count_typo_suspected:
                trace.append(
                    "Se prioriza diagnostico sindromico renopulmonar sobre "
                    "recuento plaquetario dudoso."
                )
                diagnostic_actions.append(
                    "Repetir hemograma por posible error tipografico sin frenar la ruta critica."
                )

        if payload.anti_gbm_positive:
            critical_alerts.append(
                "Anti-MBG positivo: plasmaferesis obligatoria en estrategia inicial."
            )
        if payload.rapidly_progressive_gn_requires_dialysis:
            critical_alerts.append(
                "GNRP con necesidad de dialisis: plasmaferesis obligatoria."
            )
        if payload.pulmonary_hemorrhage_present:
            critical_alerts.append(
                "Hemorragia pulmonar asociada: plasmaferesis obligatoria."
            )

        if payload.dysmorphic_rbc_present:
            glomerular_flags.append(
                "Hematies dismorficos en sedimento: origen glomerular del sangrado."
            )

        if (
            payload.microhematuria_present
            and payload.dysmorphic_rbc_present
            and payload.iga_mesangial_deposits_biopsy
            and payload.c3_mesangial_deposits_biopsy
        ):
            glomerular_flags.append(
                "Patron compatible con nefropatia IgA (Berger) en contexto de biopsia."
            )
            therapeutic_actions.append(
                "Control estricto de TA y proteinuria con IECA o ARA-II."
            )
            if (
                payload.proteinuria_g_24h is not None
                and payload.proteinuria_g_24h > 1
                and payload.months_conservative_therapy is not None
                and payload.months_conservative_therapy >= 6
            ):
                therapeutic_actions.append(
                    "Tras 6 meses de manejo conservador y proteinuria >1 g/24h, "
                    "valorar corticoides."
                )

        if (
            payload.anca_positive
            and payload.crescents_percent_glomeruli is not None
            and payload.crescents_percent_glomeruli >= 50
            and payload.pauci_immune_if_negative
        ):
            glomerular_flags.append(
                "Vasculitis ANCA pauci-inmune probable (semilunas >50% + IF negativa)."
            )
            diagnostic_actions.append(
                "Correlacionar con ANCA y anatomia patologica para estrategia inmunosupresora."
            )

        if (
            payload.acute_kidney_injury_present
            and payload.recent_drug_trigger_present
            and payload.fever_present
            and payload.rash_present
            and payload.eosinophilia_present
        ):
            glomerular_flags.append(
                "Perfil compatible con nefritis intersticial aguda farmacologica."
            )
            therapeutic_actions.append(
                "Suspender inmediatamente el farmaco sospechoso."
            )
            if payload.suspected_drug_name:
                diagnostic_actions.append(
                    f"Registrar trigger farmacologico reportado: {payload.suspected_drug_name}."
                )
            if payload.no_improvement_after_48_72h:
                therapeutic_actions.append(
                    "Sin mejoria en 48-72h: considerar corticoides segun protocolo."
                )

        return (
            critical_alerts,
            diagnostic_actions,
            therapeutic_actions,
            glomerular_flags,
            trace,
        )

    @staticmethod
    def _acid_base_pathway(
        payload: NephrologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        acid_base_assessment: list[str] = []
        trace: list[str] = []

        if (
            payload.ph is None
            or payload.hco3_mmol_l is None
            or payload.pco2_mm_hg is None
        ):
            return critical_alerts, acid_base_assessment, trace

        if payload.ph < 7.35 and payload.hco3_mmol_l < 24:
            acid_base_assessment.append(
                "Acidosis metabolica: pH < 7.35 con bicarbonato < 24."
            )
            expected_pco2 = 40 - (24 - payload.hco3_mmol_l)
            acid_base_assessment.append(
                "Compensacion esperada aproximada: "
                f"PCO2 ~ {round(expected_pco2, 1)} mmHg."
            )
            trace.append("Regla de compensacion respiratoria lineal aplicada.")

            if payload.pco2_mm_hg < 40 and payload.pco2_mm_hg <= expected_pco2 + 2:
                acid_base_assessment.append(
                    "Acidosis metabolica parcialmente compensada (pH aun acidemico)."
                )
            elif payload.pco2_mm_hg > expected_pco2 + 2:
                critical_alerts.append(
                    "Trastorno mixto probable: acidosis metabolica + acidosis respiratoria."
                )

        return critical_alerts, acid_base_assessment, trace

    @staticmethod
    def _aeiou_dialysis_pathway(
        payload: NephrologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        dialysis_alerts: list[str] = []
        therapeutic_actions: list[str] = []

        triggers: list[str] = []
        if payload.refractory_metabolic_acidosis:
            triggers.append("A: acidosis metabolica refractaria")
        if payload.refractory_hyperkalemia_with_ecg_changes:
            triggers.append("E: hiperpotasemia toxica refractaria")
        if payload.severe_tumor_hypercalcemia_neurologic:
            triggers.append("E: hipercalcemia tumoral grave con afectacion neurologica")
        if payload.dialyzable_intoxication_lithium:
            triggers.append("I: intoxicacion por litio")
        if payload.dialyzable_intoxication_salicylates:
            triggers.append("I: intoxicacion por salicilatos")
        if payload.refractory_volume_overload_pulmonary_edema:
            triggers.append("O: sobrecarga de volumen con edema pulmonar refractario")
        if payload.uremic_encephalopathy:
            triggers.append("U: encefalopatia uremica")
        if payload.uremic_pericarditis:
            triggers.append("U: pericarditis uremica")

        if triggers:
            dialysis_alerts.extend(triggers)
            critical_alerts.append(
                "Criterios AEIOU presentes: activar interconsulta nefrologica "
                "para dialisis urgente."
            )
            therapeutic_actions.append(
                "Coordinar ventana de hemodialisis urgente segun estabilidad hemodinamica."
            )

        return critical_alerts, dialysis_alerts, therapeutic_actions

    @staticmethod
    def _nephroprotection_pathway(
        payload: NephrologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        nephro_actions: list[str] = []
        safety_alerts: list[str] = []
        trace: list[str] = []

        if payload.diabetic_nephropathy_suspected or payload.proteinuric_ckd_present:
            nephro_actions.append(
                "Valorar iSGLT2 para reducir hiperfiltracion y proteinuria "
                "en contexto proteinurico."
            )
            nephro_actions.append(
                "Estrategia combinada valida: iSGLT2 + IECA/ARA-II (sin doble bloqueo)."
            )
            trace.append("Ruta de nefroproteccion con iSGLT2 activada.")
            if not payload.sglt2_planned:
                nephro_actions.append(
                    "Documentar motivo si iSGLT2 no se inicia en candidato elegible."
                )

        if payload.acei_active and payload.arb_active:
            safety_alerts.append(
                "Doble bloqueo IECA + ARA-II contraindicado por riesgo de "
                "hiperpotasemia y dano hemodinamico."
            )

        return nephro_actions, safety_alerts, trace

    @staticmethod
    def _severity(
        *,
        critical_alerts: list[str],
        dialysis_alerts: list[str],
        safety_alerts: list[str],
        glomerular_flags: list[str],
    ) -> str:
        if critical_alerts or dialysis_alerts:
            return "critical"
        if safety_alerts or glomerular_flags:
            return "high"
        return "medium"

    @staticmethod
    def build_recommendation(
        payload: NephrologySupportProtocolRequest,
    ) -> NephrologySupportProtocolRecommendation:
        """Genera recomendacion operativa de nefrologia para validacion humana."""
        aki_classification, diag_aki, flags_aki, trace_aki = (
            NephrologySupportProtocolService._aki_classification_pathway(payload)
        )
        (
            critical_glom,
            diag_glom,
            tx_glom,
            flags_glom,
            trace_glom,
        ) = NephrologySupportProtocolService._renopulmonary_and_glomerular_pathway(payload)
        critical_ab, acid_base_assessment, trace_ab = (
            NephrologySupportProtocolService._acid_base_pathway(payload)
        )
        critical_dial, dialysis_alerts, tx_dial = (
            NephrologySupportProtocolService._aeiou_dialysis_pathway(payload)
        )
        nephro_actions, safety_alerts, trace_nephro = (
            NephrologySupportProtocolService._nephroprotection_pathway(payload)
        )

        critical_alerts = critical_glom + critical_ab + critical_dial
        diagnostic_actions = diag_aki + diag_glom
        therapeutic_actions = tx_glom + tx_dial
        glomerular_flags = flags_aki + flags_glom
        interpretability_trace = trace_aki + trace_glom + trace_ab + trace_nephro
        severity = NephrologySupportProtocolService._severity(
            critical_alerts=critical_alerts,
            dialysis_alerts=dialysis_alerts,
            safety_alerts=safety_alerts,
            glomerular_flags=glomerular_flags,
        )

        return NephrologySupportProtocolRecommendation(
            severity_level=severity,
            critical_alerts=critical_alerts,
            aki_classification=aki_classification,
            acid_base_assessment=acid_base_assessment,
            diagnostic_actions=diagnostic_actions,
            therapeutic_actions=therapeutic_actions,
            dialysis_alerts=dialysis_alerts,
            nephroprotection_actions=nephro_actions,
            pharmacologic_safety_alerts=safety_alerts,
            glomerular_interstitial_flags=glomerular_flags,
            interpretability_trace=interpretability_trace,
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. "
                "Requiere validacion por nefrologia/equipo de urgencias."
            ),
        )
