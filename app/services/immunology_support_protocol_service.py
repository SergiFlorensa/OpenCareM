"""
Motor operativo de inmunologia para urgencias.

No diagnostica; organiza rutas de riesgo para validacion clinica humana.
"""
from app.schemas.immunology_support_protocol import (
    ImmunologySupportProtocolRecommendation,
    ImmunologySupportProtocolRequest,
)


class ImmunologySupportProtocolService:
    """Construye recomendaciones operativas inmunologicas en urgencias."""

    @staticmethod
    def _primary_immunodeficiency_pathway(
        payload: ImmunologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        actions: list[str] = []
        safety_blocks: list[str] = []
        trace: list[str] = []

        bruton_pattern = (
            payload.peripheral_cd19_cd20_b_cells_absent
            and payload.igg_low_or_absent
            and payload.iga_low_or_absent
            and payload.igm_low_or_absent
        )

        if bruton_pattern:
            critical_alerts.append(
                "Perfil compatible con agammaglobulinemia ligada al X (Bruton/BTK)."
            )
            actions.append(
                "Priorizar valoracion de inmunologia clinica y ruta de reposicion "
                "de inmunoglobulinas segun protocolo."
            )
            trace.append(
                "Regla Bruton activada por ausencia CD19/CD20 + panhipogammaglobulinemia."
            )

        if payload.btk_mutation_confirmed:
            actions.append(
                "Mutacion BTK confirmada: consolidar fenotipo, infecciones previas "
                "y plan de seguimiento inmunologico."
            )
            if not payload.patient_male:
                safety_blocks.append(
                    "Mutacion BTK en paciente no varon: validar fenotipo y contexto "
                    "genetico por posible presentacion atipica."
                )

        if payload.x_linked_family_pattern_suspected:
            actions.append(
                "Sospecha de herencia ligada al X: ampliar trazabilidad familiar "
                "y consejo genetico."
            )

        if payload.b_cell_maturation_block_suspected:
            actions.append(
                "Bloqueo madurativo de linfocito B sospechado: coordinar confirmacion "
                "inmunofenotipica y genetica."
            )

        age_after_maternal_window = payload.age_months is not None and payload.age_months > 6
        if age_after_maternal_window and (
            payload.recurrent_sinopulmonary_bacterial_infections
            or payload.severe_infection_after_6_months
        ):
            critical_alerts.append(
                "Infecciones bacterianas recurrentes tras ventana de IgG materna: "
                "escalado inmunologico urgente."
            )

        if payload.age_months is not None and payload.age_months <= 6:
            trace.append(
                "Interpretacion pediatrica: la IgG materna puede enmascarar "
                "deficit humoral durante primeros meses."
            )

        if payload.monocyte_function_abnormal_reported and bruton_pattern:
            safety_blocks.append(
                "En Bruton clasico, la funcion monocitaria suele preservarse: "
                "revisar causas alternativas del defecto funcional reportado."
            )

        if payload.peripheral_cd19_cd20_b_cells_absent and not bruton_pattern:
            safety_blocks.append(
                "Ausencia de CD19/CD20 sin patron completo de agammaglobulinemia: "
                "revisar perfil inmunoglobulinico y diagnostico diferencial."
            )

        return critical_alerts, actions, safety_blocks, trace

    @staticmethod
    def _innate_pulmonary_pathway(
        payload: ImmunologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        actions: list[str] = []
        trace: list[str] = []

        if payload.lower_respiratory_infection_active:
            actions.append(
                "Infeccion respiratoria activa: priorizar evaluacion de defensa "
                "innata pulmonar (macrofago alveolar como primera linea)."
            )

        if payload.alveolar_macrophage_dysfunction_suspected:
            actions.append(
                "Sospecha de disfuncion de macrofago alveolar: reforzar vigilancia "
                "de carga infecciosa distal y respuesta inflamatoria local."
            )
            trace.append(
                "Regla pulmonar activada por compromiso de primera linea fagocitica."
            )
            if payload.lower_respiratory_infection_active:
                critical_alerts.append(
                    "Infeccion respiratoria con posible fallo de macrofago alveolar: "
                    "priorizar escalado clinico temprano."
                )

        if payload.neutrophil_recruitment_failure_suspected:
            actions.append(
                "Fallo de reclutamiento inflamatorio sospechado: valorar integridad de "
                "ejes de quimiocinas y respuesta neutrofilica."
            )

        if payload.mucociliary_clearance_failure_suspected:
            actions.append(
                "Disfuncion mucociliar sospechada: reforzar control de aclaramiento "
                "mecanico y riesgo de colonizacion."
            )

        if payload.complement_support_failure_suspected:
            actions.append(
                "Defecto de soporte por complemento sospechado: coordinar estudio "
                "inmunologico complementario."
            )

        if payload.antimicrobial_peptide_barrier_failure_suspected:
            actions.append(
                "Compromiso de barrera antimicrobiana sospechado: aumentar vigilancia "
                "de infecciones respiratorias recurrentes."
            )

        return critical_alerts, actions, trace

    @staticmethod
    def _humoral_differential_pathway(
        payload: ImmunologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        actions: list[str] = []
        safety_blocks: list[str] = []
        trace: list[str] = []

        selective_iga_profile = (
            payload.iga_low_or_absent
            and not payload.igg_low_or_absent
            and not payload.igm_low_or_absent
            and not payload.igm_elevated
        )
        hyper_igm_profile = (
            payload.igm_elevated
            and payload.igg_low_or_absent
            and payload.iga_low_or_absent
        )
        cvid_profile = (
            payload.igg_low_or_absent
            and (payload.iga_low_or_absent or payload.igm_low_or_absent)
            and not payload.peripheral_cd19_cd20_b_cells_absent
        )

        if selective_iga_profile:
            actions.append(
                "Perfil compatible con deficit selectivo de IgA "
                "(IgA baja con IgG/IgM conservadas)."
            )
            trace.append("Diferencial humoral: patron selectivo de IgA.")

        if hyper_igm_profile:
            critical_alerts.append(
                "Perfil compatible con sindrome de hiper-IgM "
                "(IgM alta con IgG/IgA bajas)."
            )
            actions.append(
                "Priorizar validacion inmunologica de cambio de clase y riesgo "
                "infeccioso asociado."
            )
            trace.append("Diferencial humoral: patron hiper-IgM.")

        if cvid_profile:
            actions.append(
                "Perfil compatible con inmunodeficiencia comun variable "
                "(descenso de IgG +/- IgA/IgM)."
            )
            trace.append("Diferencial humoral: patron compatible con CVID.")

        if payload.igm_low_or_absent and payload.igm_elevated:
            safety_blocks.append(
                "IgM marcada simultaneamente como baja y elevada: revisar consistencia "
                "del dato de laboratorio."
            )

        if payload.peripheral_cd19_cd20_b_cells_absent and payload.igm_elevated:
            safety_blocks.append(
                "Ausencia de linfocitos B perifericos con IgM elevada: perfil no "
                "congruente para Bruton clasico, revisar diferencial."
            )

        if sum([selective_iga_profile, hyper_igm_profile, cvid_profile]) > 1:
            safety_blocks.append(
                "Multiples perfiles humorales activados en paralelo: requerir "
                "revalidacion analitica e inmunofenotipica."
            )

        humoral_abnormality_present = any(
            [
                payload.igg_low_or_absent,
                payload.iga_low_or_absent,
                payload.igm_low_or_absent,
                payload.igm_elevated,
                payload.peripheral_cd19_cd20_b_cells_absent,
            ]
        )
        if humoral_abnormality_present and not any(
            [selective_iga_profile, hyper_igm_profile, cvid_profile]
        ):
            safety_blocks.append(
                "Alteraciones humorales presentes sin encaje claro en perfil Bruton/IgA/"
                "Hiper-IgM/CVID: completar estudio inmunologico."
            )

        return critical_alerts, actions, safety_blocks, trace

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
        payload: ImmunologySupportProtocolRequest,
    ) -> ImmunologySupportProtocolRecommendation:
        """Genera recomendacion operativa inmunologica para validacion humana."""
        critical_pid, pid_actions, safety_pid, trace_pid = (
            ImmunologySupportProtocolService._primary_immunodeficiency_pathway(payload)
        )
        critical_pulmonary, pulmonary_actions, trace_pulmonary = (
            ImmunologySupportProtocolService._innate_pulmonary_pathway(payload)
        )
        critical_diff, differential_actions, safety_diff, trace_diff = (
            ImmunologySupportProtocolService._humoral_differential_pathway(payload)
        )

        critical_alerts = critical_pid + critical_pulmonary + critical_diff
        safety_blocks = safety_pid + safety_diff
        has_actions = any([pid_actions, pulmonary_actions, differential_actions])
        severity = ImmunologySupportProtocolService._severity(
            critical_alerts=critical_alerts,
            safety_blocks=safety_blocks,
            has_actions=has_actions,
        )

        return ImmunologySupportProtocolRecommendation(
            severity_level=severity,
            critical_alerts=critical_alerts,
            primary_immunodeficiency_actions=pid_actions,
            innate_pulmonary_actions=pulmonary_actions,
            humoral_differential_actions=differential_actions,
            safety_blocks=safety_blocks,
            interpretability_trace=trace_pid + trace_pulmonary + trace_diff,
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. "
                "Requiere validacion por inmunologia/equipo de urgencias."
            ),
        )
