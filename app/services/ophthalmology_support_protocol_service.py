"""
Motor operativo de oftalmologia para urgencias.

No diagnostica; organiza rutas de riesgo para validacion clinica humana.
"""
from app.schemas.ophthalmology_support_protocol import (
    OphthalmologySupportProtocolRecommendation,
    OphthalmologySupportProtocolRequest,
)


class OphthalmologySupportProtocolService:
    """Construye recomendaciones operativas oftalmologicas en urgencias."""

    @staticmethod
    def _vascular_pathway(
        payload: OphthalmologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        actions: list[str] = []
        safety_blocks: list[str] = []
        trace: list[str] = []

        ovcr_pattern = (
            payload.fundus_flame_hemorrhages_present
            or payload.fundus_papilledema_present
            or payload.cotton_wool_exudates_present
        )
        oacr_pattern = payload.cherry_red_spot_present or payload.diffuse_retinal_whitening_present

        if payload.sudden_visual_loss and ovcr_pattern:
            critical_alerts.append(
                "Perdida visual brusca con hemorragias en llama/exudados: priorizar OVCR."
            )
            actions.append(
                "Solicitar fondo de ojo urgente completo y estratificar edema papilar/isquemia."
            )
            trace.append("Regla OVCR activada por perdida visual brusca + hemorragias en llama.")

        if payload.sudden_visual_loss and oacr_pattern:
            critical_alerts.append(
                "Perdida visual brusca con mancha rojo cereza/retina blanquecina: priorizar OACR."
            )
            actions.append(
                "Activar ruta de evento arterial retiniano con evaluacion sistemica urgente."
            )
            trace.append("Regla OACR activada por mancha rojo cereza.")

        if ovcr_pattern and oacr_pattern:
            safety_blocks.append(
                "Patron mixto OVCR/OACR en fondo de ojo: requerir reevaluacion "
                "oftalmologica inmediata."
            )

        if payload.intraocular_pressure_mmhg is not None and payload.intraocular_pressure_mmhg > 21:
            actions.append(
                "PIO elevada: considerar control hipotensor ocular "
                "(ej. latanoprost/timolol) segun contexto."
            )
            if payload.sudden_visual_loss and ovcr_pattern:
                critical_alerts.append(
                    "OVCR con PIO elevada: mayor riesgo de progresion isquemica."
                )

        if payload.embolic_arrhythmia_suspected and payload.sudden_visual_loss and oacr_pattern:
            actions.append(
                "Sospecha emboligena asociada: coordinar estudio cardiaco y manejo antiarritmico."
            )
            if not payload.antiarrhythmic_management_planned:
                safety_blocks.append(
                    "Sospecha emboligena en OACR sin plan antiarritmico/cardiologico documentado."
                )

        return critical_alerts, actions, safety_blocks, trace

    @staticmethod
    def _neuro_ophthalmology_pathway(
        payload: OphthalmologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        actions: list[str] = []
        safety_blocks: list[str] = []
        trace: list[str] = []

        if payload.relative_afferent_pupillary_defect_present:
            actions.append(
                "DPAR (Marcus Gunn) presente: priorizar lesion de nervio optico o retina extensa."
            )
            if not (
                payload.optic_nerve_disease_suspected or payload.extensive_retinal_disease_suspected
            ):
                safety_blocks.append(
                    "DPAR sin sospecha de lesion aferente documentada: revisar exploracion pupilar."
                )

        if payload.anisocoria_present:
            if payload.anisocoria_worse_in_darkness:
                actions.append(
                    "Anisocoria que aumenta en oscuridad: orientar a disfuncion simpatica (Horner)."
                )
            if payload.anisocoria_worse_in_bright_light:
                actions.append(
                    "Anisocoria que aumenta con luz: orientar a disfuncion parasimpatica."
                )
            if payload.anisocoria_worse_in_darkness and payload.anisocoria_worse_in_bright_light:
                safety_blocks.append(
                    "Anisocoria con patrones simpatico y parasimpatico simultaneos: repetir examen."
                )

        if (
            payload.posterior_communicating_aneurysm_suspected
            or payload.compressive_third_nerve_signs_present
        ):
            critical_alerts.append(
                "Sospecha de lesion compresiva del III par (aneurisma comunicante posterior)."
            )
            actions.append(
                "Priorizar neuroimagen urgente por riesgo de compromiso de fibras pupilares."
            )

        trace.append(
            "Reflejo fotomotor: via aferente retina/nervio optico y via eferente "
            "parasimpatica del III par."
        )
        return critical_alerts, actions, safety_blocks, trace

    @staticmethod
    def _surface_inflammation_pathway(
        payload: OphthalmologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        actions: list[str] = []
        trace: list[str] = []

        allergic_profile = (
            payload.abrupt_conjunctival_reaction_after_exposure
            and payload.palpebral_edema_or_erythema_present
            and payload.chemosis_present
            and payload.intense_itching_present
        )
        if allergic_profile:
            actions.append(
                "Perfil compatible con conjuntivitis alergica aguda: valorar antihistaminico "
                "topico o corticoide de baja potencia."
            )
            trace.append("Regla de superficie ocular alergica activada por quemosis + prurito.")

        if (
            payload.long_term_diabetes_present
            and payload.ocular_pain_present
            and payload.intraocular_pressure_mmhg is not None
            and payload.intraocular_pressure_mmhg > 21
        ):
            critical_alerts.append(
                "Dolor ocular + PIO alta en diabetes de larga evolucion: "
                "descartar glaucoma neovascular."
            )

        return critical_alerts, actions, trace

    @staticmethod
    def _cataract_ifis_pathway(
        payload: OphthalmologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        actions: list[str] = []
        safety_blocks: list[str] = []
        trace: list[str] = []

        if payload.cataract_surgery_planned and payload.tamsulosin_or_alpha_blocker_active:
            critical_alerts.append(
                "Riesgo de IFIS por tamsulosina/alfabloqueante en cirugia de catarata."
            )
            actions.append("Planificar fenilefrina intracamerular al inicio para estabilizar iris.")
            trace.append("Alerta IFIS activada por uso de tamsulosina preoperatoria.")
            if not payload.intracameral_phenylephrine_planned:
                safety_blocks.append(
                    "Cirugia de catarata con tamsulosina sin plan de fenilefrina intracamerular."
                )
            if payload.recommendation_to_stop_tamsulosin_preop:
                safety_blocks.append(
                    "No recomendar suspension aislada de tamsulosina: el riesgo IFIS "
                    "puede persistir."
                )

        if payload.index_myopia_shift_present:
            actions.append(
                "Miopia de indice preoperatoria: correlacionar mejoria cercana "
                "paradoxica con progresion de catarata."
            )

        if (
            payload.cataract_surgery_planned
            and payload.high_myopia_present
            and payload.young_patient_for_lens_surgery
        ):
            critical_alerts.append(
                "Riesgo aumentado de desprendimiento de retina postcirugia en paciente miope joven."
            )

        return critical_alerts, actions, safety_blocks, trace

    @staticmethod
    def _dmae_pathway(
        payload: OphthalmologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        actions: list[str] = []
        trace: list[str] = []

        dry_pattern = (
            payload.drusen_present
            and payload.retinal_pigment_epithelium_thinning_or_changes
            and payload.visual_loss_progressive_over_months
            and not payload.neovascular_membrane_or_exudation_present
        )
        wet_pattern = payload.neovascular_membrane_or_exudation_present or (
            payload.sudden_visual_loss and payload.drusen_present
        )

        if dry_pattern:
            actions.append(
                "Perfil compatible con DMAE seca: observacion estructurada y "
                "suplementos antioxidantes segun protocolo."
            )
            trace.append("Clasificacion operativa DMAE seca por drusas + evolucion lenta.")

        if wet_pattern:
            critical_alerts.append(
                "Perfil compatible con DMAE humeda/exudativa: priorizar anti-VEGF intravitreo."
            )
            actions.append(
                "Coordinar ruta de retina para confirmacion de membrana neovascular y tratamiento."
            )
            if not payload.anti_vegf_planned:
                critical_alerts.append("DMAE humeda sospechada sin plan anti-VEGF documentado.")
            trace.append("Clasificacion operativa DMAE humeda por exudacion/neovascularizacion.")

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
        payload: OphthalmologySupportProtocolRequest,
    ) -> OphthalmologySupportProtocolRecommendation:
        """Genera recomendacion operativa oftalmologica para validacion humana."""
        (
            critical_vascular,
            vascular_actions,
            safety_vascular,
            trace_vascular,
        ) = OphthalmologySupportProtocolService._vascular_pathway(payload)
        (
            critical_neuro,
            neuro_actions,
            safety_neuro,
            trace_neuro,
        ) = OphthalmologySupportProtocolService._neuro_ophthalmology_pathway(payload)
        (
            critical_surface,
            surface_actions,
            trace_surface,
        ) = OphthalmologySupportProtocolService._surface_inflammation_pathway(payload)
        (
            critical_ifis,
            cataract_actions,
            safety_ifis,
            trace_ifis,
        ) = OphthalmologySupportProtocolService._cataract_ifis_pathway(payload)
        critical_dmae, dmae_actions, trace_dmae = OphthalmologySupportProtocolService._dmae_pathway(
            payload
        )

        critical_alerts = (
            critical_vascular + critical_neuro + critical_surface + critical_ifis + critical_dmae
        )
        safety_blocks = safety_vascular + safety_neuro + safety_ifis
        has_actions = any(
            [vascular_actions, neuro_actions, surface_actions, cataract_actions, dmae_actions]
        )
        severity = OphthalmologySupportProtocolService._severity(
            critical_alerts=critical_alerts,
            safety_blocks=safety_blocks,
            has_actions=has_actions,
        )

        return OphthalmologySupportProtocolRecommendation(
            severity_level=severity,
            critical_alerts=critical_alerts,
            vascular_triage_actions=vascular_actions,
            neuro_ophthalmology_actions=neuro_actions,
            inflammation_actions=surface_actions,
            cataract_safety_actions=cataract_actions,
            dmae_actions=dmae_actions,
            safety_blocks=safety_blocks,
            interpretability_trace=(
                trace_vascular + trace_neuro + trace_surface + trace_ifis + trace_dmae
            ),
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. "
                "Requiere validacion por oftalmologia/equipo de urgencias."
            ),
        )
