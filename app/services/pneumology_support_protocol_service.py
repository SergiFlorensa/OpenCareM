"""
Motor operativo de neumologia para urgencias.

No diagnostica; organiza rutas de riesgo para validacion clinica humana.
"""
from app.schemas.pneumology_support_protocol import (
    PneumologySupportProtocolRecommendation,
    PneumologySupportProtocolRequest,
)


class PneumologySupportProtocolService:
    """Construye recomendaciones operativas neumologicas en urgencias."""

    @staticmethod
    def _imaging_pathway(
        payload: PneumologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        imaging_assessment: list[str] = []
        diagnostic_actions: list[str] = []
        trace: list[str] = []

        if payload.ct_peripheral_subpleural_consolidation and payload.air_bronchogram_present:
            imaging_assessment.append(
                "Patron de consolidacion periferica/subpleural con broncograma aereo: "
                "compatible con NOC."
            )
            trace.append("Regla de NOC por patron consolidativo periferico activada.")

        if payload.centrilobular_upper_lobe_nodules and payload.smoker_active_or_history:
            imaging_assessment.append(
                "Nodulos centrilobulillares en lobulos superiores en fumador: "
                "sugieren bronquiolitis respiratoria."
            )

        if payload.interstitial_pattern_predominant:
            imaging_assessment.append(
                "Patron intersticial predominante: considerar neumonia intersticial inespecifica."
            )

        if not payload.obstructive_lesion_signs and not payload.significant_volume_loss_signs:
            imaging_assessment.append(
                "Atelectasia menos probable por ausencia de signos de obstruccion "
                "o perdida de volumen relevante."
            )
            trace.append("Regla de descarte operativo de atelectasia aplicada.")
        elif payload.obstructive_lesion_signs or payload.significant_volume_loss_signs:
            diagnostic_actions.append(
                "Completar estudio de atelectasia (obstruccion endobronquial y perdida de volumen)."
            )

        return imaging_assessment, diagnostic_actions, trace

    @staticmethod
    def _ventilatory_pathway(
        payload: PneumologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        ventilatory_assessment: list[str] = []
        therapeutic_actions: list[str] = []
        trace: list[str] = []

        if payload.po2_low_detected:
            ventilatory_assessment.append(
                "Hipoxemia: predominio de activacion por quimiorreceptores perifericos "
                "(carotideos/aorticos)."
            )
        if payload.pco2_high_detected or payload.respiratory_acidosis_present:
            ventilatory_assessment.append(
                "Hipercapnia/acidosis respiratoria: predominio de respuesta en "
                "quimiorreceptores centrales."
            )

        if payload.pco2_high_detected and payload.respiratory_acidosis_present:
            therapeutic_actions.append(
                "Preferir BiPAP para soporte ventilatorio en insuficiencia "
                "hipercapnica/acidosis respiratoria."
            )
            trace.append("Regla BiPAP activada por hipercapnia con acidosis.")
        elif payload.po2_low_detected and not payload.pco2_high_detected:
            therapeutic_actions.append(
                "Priorizar estrategia de oxigenacion (CPAP/oxigenoterapia) "
                "en insuficiencia hipoxemica sin hipercapnia."
            )

        if payload.chronic_hypercapnia_days is not None and payload.chronic_hypercapnia_days >= 2:
            ventilatory_assessment.append(
                "Con hipercapnia sostenida por dias, la respuesta ventilatoria al CO2 "
                "se atenúa por compensacion progresiva."
            )
            if payload.renal_compensation_evidence:
                trace.append("Atenuacion de respuesta al CO2 reforzada por compensacion renal.")

        return ventilatory_assessment, therapeutic_actions, trace

    @staticmethod
    def _physical_exam_pathway(
        payload: PneumologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        diagnostic_actions: list[str] = []
        procedural_safety_alerts: list[str] = []
        trace: list[str] = []

        if payload.hemoptysis_present:
            if payload.known_bronchiectasis:
                diagnostic_actions.append(
                    "Hemoptisis con bronquiectasias conocidas: priorizarlas "
                    "como causa frecuente."
                )
            else:
                diagnostic_actions.append(
                    "Hemoptisis sin etiologia definida: descartar bronquiectasias y otras causas."
                )

        if (
            payload.bibasal_velcro_crackles_present
            or payload.digital_clubbing_present
            or payload.reduced_breath_sounds_present
        ):
            diagnostic_actions.append(
                "Perfil de EPID/fibrosis (crepitantes tipo Velcro, acropaquias, "
                "murmullo vesicular disminuido)."
            )

        if payload.wheeze_present and (
            payload.bibasal_velcro_crackles_present or payload.digital_clubbing_present
        ):
            procedural_safety_alerts.append(
                "Sibilancias en contexto fibrosante: hallazgo menos tipico, "
                "revisar diferencial bronquial (asma/EPOC)."
            )
            trace.append("Red flag de diferencial fibrosis vs arbol bronquial activada.")

        return diagnostic_actions, procedural_safety_alerts, trace

    @staticmethod
    def _copd_asthma_pathway(
        payload: PneumologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        therapeutic_actions: list[str] = []
        biologic_strategy: list[str] = []
        procedural_safety_alerts: list[str] = []
        trace: list[str] = []

        if (
            payload.copd_diagnosed
            and payload.on_laba_lama
            and (payload.persistent_frequent_exacerbator or payload.frequent_hospitalizations)
        ):
            if payload.eosinophils_per_ul is not None and payload.eosinophils_per_ul > 100:
                therapeutic_actions.append(
                    "EPOC agudizador con eosinofilos >100/uL pese a LABA+LAMA: "
                    "escalar a triple terapia (LAMA+LABA+corticoide inhalado)."
                )
                trace.append("Escalada GOLD a triple terapia activada.")
            else:
                therapeutic_actions.append(
                    "EPOC agudizador persistente con eosinofilos no favorables: "
                    "revalorar fenotipo y causas de exacerbacion."
                )

        if payload.copd_diagnosed and payload.on_laba_ics_without_lama:
            procedural_safety_alerts.append(
                "En EPOC no se recomienda LABA+corticoide inhalado como "
                "paso inicial/preferente sin LAMA."
            )

        if payload.severe_asthma and payload.eosinophilic_phenotype:
            if payload.chronic_rhinosinusitis_with_polyposis:
                biologic_strategy.append(
                    "Fenotipo eosinofilico con poliposis nasal: priorizar mepolizumab."
                )
            else:
                biologic_strategy.append(
                    "Fenotipo eosinofilico sin poliposis predominante: considerar benralizumab."
                )
        if payload.severe_asthma and payload.allergic_asthma_phenotype:
            biologic_strategy.append("Fenotipo alergico mediado por IgE: considerar omalizumab.")

        planned = (payload.biologic_planned or "").strip().lower()
        if planned and biologic_strategy:
            if "mepolizumab" in planned and not payload.chronic_rhinosinusitis_with_polyposis:
                procedural_safety_alerts.append(
                    "Biologico planificado no alineado con fenotipo dominante; "
                    "revisar seleccion en comite de asma grave."
                )
            if "omalizumab" in planned and not payload.allergic_asthma_phenotype:
                procedural_safety_alerts.append(
                    "Omalizumab planificado sin fenotipo alergico claro; revisar indicacion."
                )

        return therapeutic_actions, biologic_strategy, procedural_safety_alerts, trace

    @staticmethod
    def _lba_and_interventional_pathway(
        payload: PneumologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        diagnostic_actions: list[str] = []
        therapeutic_actions: list[str] = []
        procedural_safety_alerts: list[str] = []

        if (
            payload.bal_performed
            and payload.bal_pas_positive_lipoproteins
            and payload.bal_clears_with_serial_lavage
        ):
            diagnostic_actions.append(
                "LBA compatible con proteinosis alveolar (material lipoproteico PAS+ "
                "y aclaramiento con lavados sucesivos)."
            )

        if payload.sarcoidosis_suspected and payload.bal_cd4_cd8_high:
            diagnostic_actions.append(
                "LBA con CD4/CD8 alto: hallazgo de apoyo en sarcoidosis "
                "(requiere confirmacion adicional)."
            )
            procedural_safety_alerts.append(
                "En sarcoidosis, el LBA es de apoyo: confirmar con biopsia/criterios integrados."
            )

        if payload.hypersensitivity_pneumonitis_suspected and payload.bal_lymphocytosis_present:
            diagnostic_actions.append(
                "LBA con celularidad compatible con neumonitis por hipersensibilidad "
                "(hallazgo de apoyo)."
            )
            procedural_safety_alerts.append(
                "En neumonitis por hipersensibilidad, confirmar con radiologia/IgG especificas."
            )

        if payload.solitary_nodule_malignancy_suspected and payload.pet_positive:
            if payload.vo2max_ml_kg_min is not None and payload.vo2max_ml_kg_min < 10:
                critical_alerts.append(
                    "Funcion pulmonar deteriorada (VO2 max < 10 ml/kg/min): "
                    "cirugia no recomendable."
                )
                therapeutic_actions.append(
                    "En nodulo sospechoso con alto riesgo operatorio, priorizar radioterapia."
                )
                if payload.surgery_planned:
                    procedural_safety_alerts.append(
                        "Evitar lobectomia en VO2 max por debajo del umbral de seguridad."
                    )
            elif payload.surgery_planned:
                therapeutic_actions.append(
                    "Si riesgo funcional aceptable, la cirugia sigue siendo estandar "
                    "en nodulo con alta sospecha de malignidad."
                )
            else:
                diagnostic_actions.append(
                    "Completar estratificacion funcional para definir cirugia vs alternativa."
                )

            if payload.biopsy_high_risk:
                therapeutic_actions.append(
                    "Con alto riesgo de biopsia y perfil funcional limite, "
                    "valorar estrategia no invasiva consensuada."
                )

        return critical_alerts, diagnostic_actions, therapeutic_actions, procedural_safety_alerts

    @staticmethod
    def _severity(*, critical_alerts: list[str], procedural_safety_alerts: list[str]) -> str:
        if critical_alerts:
            return "critical"
        if procedural_safety_alerts:
            return "high"
        return "medium"

    @staticmethod
    def build_recommendation(
        payload: PneumologySupportProtocolRequest,
    ) -> PneumologySupportProtocolRecommendation:
        """Genera recomendacion operativa neumologica para validacion humana."""
        (
            imaging_assessment,
            diagnostic_imaging,
            trace_imaging,
        ) = PneumologySupportProtocolService._imaging_pathway(payload)
        (
            ventilatory_assessment,
            therapeutic_vent,
            trace_vent,
        ) = PneumologySupportProtocolService._ventilatory_pathway(payload)
        (
            diagnostic_exam,
            safety_exam,
            trace_exam,
        ) = PneumologySupportProtocolService._physical_exam_pathway(payload)
        (
            therapeutic_copd,
            biologic_strategy,
            safety_copd,
            trace_copd,
        ) = PneumologySupportProtocolService._copd_asthma_pathway(payload)
        (
            critical_lba,
            diagnostic_lba,
            therapeutic_lba,
            safety_lba,
        ) = PneumologySupportProtocolService._lba_and_interventional_pathway(payload)

        critical_alerts = critical_lba
        diagnostic_actions = diagnostic_imaging + diagnostic_exam + diagnostic_lba
        therapeutic_actions = therapeutic_vent + therapeutic_copd + therapeutic_lba
        procedural_safety_alerts = safety_exam + safety_copd + safety_lba
        interpretability_trace = trace_imaging + trace_vent + trace_exam + trace_copd
        severity = PneumologySupportProtocolService._severity(
            critical_alerts=critical_alerts,
            procedural_safety_alerts=procedural_safety_alerts,
        )

        return PneumologySupportProtocolRecommendation(
            severity_level=severity,
            critical_alerts=critical_alerts,
            imaging_assessment=imaging_assessment,
            ventilatory_control_assessment=ventilatory_assessment,
            diagnostic_actions=diagnostic_actions,
            therapeutic_actions=therapeutic_actions,
            biologic_strategy=biologic_strategy,
            procedural_safety_alerts=procedural_safety_alerts,
            interpretability_trace=interpretability_trace,
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. "
                "Requiere validacion por neumologia/equipo de urgencias."
            ),
        )
