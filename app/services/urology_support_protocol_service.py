"""
Motor operativo de urologia para urgencias.

No diagnostica; organiza rutas de riesgo para validacion clinica humana.
"""
from app.schemas.urology_support_protocol import (
    UrologySupportProtocolRecommendation,
    UrologySupportProtocolRequest,
)


class UrologySupportProtocolService:
    """Construye recomendaciones operativas urologicas en urgencias."""

    @staticmethod
    def _emphysematous_pyelonephritis_pathway(
        payload: UrologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        infection_actions: list[str] = []
        trace: list[str] = []

        metabolic_risk = payload.diabetes_mellitus_poor_control or payload.hypertension_present
        if payload.urinary_tract_gas_on_imaging:
            infection_actions.append(
                "Gas en via urinaria: iniciar antibioterapia de amplio espectro de forma inmediata."
            )
            if payload.urinary_obstruction_lithiasis_suspected:
                infection_actions.append(
                    "Componente obstructivo probable: activar derivacion urinaria urgente."
                )
            if payload.suspected_pathogen_e_coli:
                infection_actions.append(
                    "Escherichia coli es etiologia frecuente; ajustar cultivo y cobertura."
                )

            if metabolic_risk:
                critical_alerts.append(
                    "Sospecha de pielonefritis enfisematosa en paciente de alto riesgo metabolico."
                )
                trace.append(
                    "Regla de PFE por gas en via urinaria + " "riesgo metabolico activada."
                )
            else:
                critical_alerts.append(
                    "Gas en via urinaria con potencial infeccion necrotizante: "
                    "manejar como urgencia."
                )

            if not payload.urgent_urinary_diversion_planned:
                critical_alerts.append(
                    "Gas urinario con obstruccion potencial sin derivacion urgente planificada."
                )

            if payload.xanthogranulomatous_chronic_pattern_suspected:
                infection_actions.append(
                    "Diferenciar de pielonefritis xantogranulomatosa (curso cronico) "
                    "antes del plan definitivo."
                )

        return critical_alerts, infection_actions, trace

    @staticmethod
    def _obstructive_aki_pathway(
        payload: UrologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        obstruction_actions: list[str] = []
        safety_blocks: list[str] = []

        renal_severity = (
            payload.creatinine_mg_dl is not None and payload.creatinine_mg_dl > 7
        ) or (payload.egfr_ml_min is not None and payload.egfr_ml_min < 15)
        colic_context = payload.colicky_flank_pain_present or payload.vomiting_present
        triad_obstructive_aki = (
            colic_context
            and payload.anuria_present
            and renal_severity
            and payload.bilateral_pyelocaliceal_dilation_on_ultrasound
        )

        if triad_obstructive_aki:
            critical_alerts.append(
                "FRA obstructivo grave (colico/anuria/deterioro renal con dilatacion bilateral)."
            )
            obstruction_actions.append(
                "Prioridad absoluta: derivacion urinaria urgente antes de TAC avanzado."
            )
            if not payload.urgent_urinary_diversion_planned:
                critical_alerts.append("FRA obstructivo sin derivacion urgente documentada.")
            if payload.urgent_ct_planned_before_diversion:
                safety_blocks.append(
                    "Bloquear secuencia TAC previo: primero derivacion urinaria en FRA obstructivo."
                )
        elif payload.bilateral_pyelocaliceal_dilation_on_ultrasound and renal_severity:
            obstruction_actions.append(
                "Dilatacion de via urinaria + deterioro renal: coordinar desobstruccion temprana."
            )
            if payload.urgent_ct_planned_before_diversion:
                safety_blocks.append(
                    "Evitar retraso por imagen avanzada antes de resolver obstruccion."
                )

        return critical_alerts, obstruction_actions, safety_blocks

    @staticmethod
    def _penile_trauma_pathway(
        payload: UrologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        trauma_actions: list[str] = []
        safety_blocks: list[str] = []
        trace: list[str] = []

        fracture_suspicion = (
            payload.genital_trauma_during_erection
            and payload.penile_edema_or_expansive_hematoma_present
        )
        if payload.flaccid_penis_after_trauma:
            fracture_suspicion = fracture_suspicion or (
                payload.penile_edema_or_expansive_hematoma_present
            )

        if fracture_suspicion:
            critical_alerts.append(
                "Sospecha de fractura de pene: activar revision quirurgica urgente."
            )
            trauma_actions.append(
                "Indicar exploracion quirurgica aun con ecografia no concluyente por hematoma."
            )
            if not payload.urgent_surgical_review_planned:
                critical_alerts.append(
                    "Sospecha de fractura sin revision quirurgica urgente planificada."
                )
            if payload.bladder_catheterization_planned and (
                payload.penile_edema_or_expansive_hematoma_present
                or payload.urethral_injury_suspected
            ):
                safety_blocks.append(
                    "Bloquear orden de sondaje vesical en traumatismo genital con hematoma."
                )
            if payload.cavernosal_blood_gas_planned:
                safety_blocks.append(
                    "Gasometria de cuerpos cavernosos no indicada en fractura de pene "
                    "(util en diferencial de priapismo)."
                )
            trace.append("Regla de trauma genital con hematoma y flujo quirurgico activada.")

        return critical_alerts, trauma_actions, safety_blocks, trace

    @staticmethod
    def _oncology_pathway(
        payload: UrologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        oncologic_actions: list[str] = []
        safety_blocks: list[str] = []

        nephron_sparing_context = (
            payload.localized_renal_tumor_suspected
            and payload.renal_mass_cm is not None
            and payload.renal_mass_cm <= 7
            and (payload.solitary_functional_kidney or payload.contralateral_kidney_atrophy_present)
        )
        if nephron_sparing_context:
            oncologic_actions.append(
                "Tumor renal localizado en rinon unico/contralateral atrofico: "
                "priorizar nefrectomia parcial conservadora de nefronas."
            )
            if payload.planned_radical_nephrectomy:
                safety_blocks.append(
                    "Reevaluar nefrectomia radical en contexto de preservacion renal obligada."
                )
            if not payload.planned_partial_nephrectomy:
                oncologic_actions.append(
                    "Valorar plan quirurgico conservador como estrategia de eleccion."
                )

        if payload.prostate_mri_anterior_lesion_present:
            oncologic_actions.append(
                "Lesion prostatica anterior en RM: recomendar biopsia transperineal "
                "sistematica y dirigida por fusion RM-ecografia."
            )
            if (
                payload.transrectal_biopsy_planned
                and not payload.transperineal_fusion_biopsy_planned
            ):
                safety_blocks.append(
                    "Acceso trasrectal aislado insuficiente para lesion anterior; "
                    "priorizar via transperineal."
                )

        high_volume_inferred = payload.prostate_metastatic_high_volume or (
            payload.gleason_score is not None
            and payload.gleason_score >= 9
            and payload.bone_metastases_present
            and payload.liver_metastases_present
        )
        if high_volume_inferred:
            oncologic_actions.append(
                "Prostata metastasica de alto volumen: estrategia sistemica de triple terapia "
                "(LHRH + docetaxel + antiandrogeno de nueva generacion)."
            )
            if not payload.lhrh_analog_planned:
                critical_alerts.append(
                    "Triple terapia incompleta: falta analogo LHRH en alto volumen metastasico."
                )
            if not payload.docetaxel_planned:
                critical_alerts.append(
                    "Triple terapia incompleta: falta docetaxel en alto volumen metastasico."
                )
            antiandrogen = (payload.novel_antiandrogen_name or "").strip().lower()
            if antiandrogen not in {"darolutamida", "abiraterona"}:
                critical_alerts.append(
                    "Triple terapia incompleta o no alineada: falta antiandrogeno "
                    "de nueva generacion recomendado."
                )
            if antiandrogen == "enzalutamida" and payload.docetaxel_planned:
                safety_blocks.append(
                    "Combinacion docetaxel-enzalutamida con evidencia conjunta limitada; "
                    "priorizar esquemas estandar validados."
                )
            if payload.local_curative_treatment_planned:
                safety_blocks.append(
                    "Bloquear tratamiento local curativo en enfermedad metastasica de alto volumen."
                )
            if payload.radiotherapy_planned and not payload.low_volume_metastatic_profile:
                safety_blocks.append(
                    "Radioterapia local suele reservarse para enfermedad "
                    "metastasica de bajo volumen."
                )

        return critical_alerts, oncologic_actions, safety_blocks

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
        payload: UrologySupportProtocolRequest,
    ) -> UrologySupportProtocolRecommendation:
        """Genera recomendacion operativa urologica para validacion humana."""
        (
            critical_inf,
            infection_actions,
            trace_inf,
        ) = UrologySupportProtocolService._emphysematous_pyelonephritis_pathway(payload)
        (
            critical_obs,
            obstruction_actions,
            safety_obs,
        ) = UrologySupportProtocolService._obstructive_aki_pathway(payload)
        (
            critical_trauma,
            trauma_actions,
            safety_trauma,
            trace_trauma,
        ) = UrologySupportProtocolService._penile_trauma_pathway(payload)
        (
            critical_onco,
            oncologic_actions,
            safety_onco,
        ) = UrologySupportProtocolService._oncology_pathway(payload)

        critical_alerts = critical_inf + critical_obs + critical_trauma + critical_onco
        safety_blocks = safety_obs + safety_trauma + safety_onco
        has_actions = any(
            [infection_actions, obstruction_actions, trauma_actions, oncologic_actions]
        )
        severity = UrologySupportProtocolService._severity(
            critical_alerts=critical_alerts,
            safety_blocks=safety_blocks,
            has_actions=has_actions,
        )

        return UrologySupportProtocolRecommendation(
            severity_level=severity,
            critical_alerts=critical_alerts,
            infection_actions=infection_actions,
            obstruction_actions=obstruction_actions,
            trauma_actions=trauma_actions,
            oncologic_actions=oncologic_actions,
            safety_blocks=safety_blocks,
            interpretability_trace=trace_inf + trace_trauma,
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. "
                "Requiere validacion por urologia/equipo de urgencias."
            ),
        )
