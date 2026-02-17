"""
Motor operativo reuma-inmuno para urgencias.

No diagnostica; organiza rutas de riesgo para validacion clinica humana.
"""
from app.schemas.rheum_immuno_support_protocol import (
    RheumImmunoSupportProtocolRecommendation,
    RheumImmunoSupportProtocolRequest,
)


class RheumImmunoSupportProtocolService:
    """Construye recomendaciones operativas reuma-inmunologicas."""

    @staticmethod
    def _vital_risk_pathway(
        payload: RheumImmunoSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        diagnostic_actions: list[str] = []
        therapeutic_actions: list[str] = []
        trace: list[str] = []

        if payload.lupus_known and payload.new_unexplained_dyspnea:
            critical_alerts.append(
                "LES + disnea inexplicable: priorizar descarte de tromboembolismo pulmonar (TEP)."
            )
            diagnostic_actions.append(
                "Solicitar Dimero D inmediato como primer paso de estratificacion."
            )
            trace.append("Disparador de TEP en LES activado.")
            if payload.prior_aptt_prolonged:
                critical_alerts.append(
                    "TTPa prolongado previo compatible con anticoagulante lupico: "
                    "mayor riesgo trombotico."
                )

        if (
            payload.systemic_sclerosis_known
            and payload.raynaud_phenomenon_active
            and payload.active_digital_ischemic_ulcers
        ):
            critical_alerts.append(
                "Isquemia digital critica en esclerosis sistemica: riesgo de perdida tisular."
            )
            therapeutic_actions.append(
                "Priorizar prostaglandinas intravenosas en ulceras isquemicas activas."
            )
            therapeutic_actions.append(
                "Calcioantagonistas o inhibidores PDE5 para control/prevision de Raynaud."
            )
            trace.append("Ruta de isquemia digital critica activada.")

        if payload.giant_cell_arteritis_suspected and payload.esr_mm_h is not None:
            if payload.esr_mm_h <= 20:
                diagnostic_actions.append(
                    "VSG normal en urgencias: arteritis temporal menos probable."
                )
                trace.append("Criterio de exclusion operativa para arteritis temporal aplicado.")
            else:
                critical_alerts.append(
                    "VSG elevada con sospecha de arteritis temporal: "
                    "mantener via rapida diagnostica."
                )

        return critical_alerts, diagnostic_actions, therapeutic_actions, trace

    @staticmethod
    def _diagnostic_workflows(
        payload: RheumImmunoSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str], list[str]]:
        diagnostic_actions: list[str] = []
        therapeutic_actions: list[str] = []
        safety_alerts: list[str] = []
        trace: list[str] = []

        if payload.proximal_symmetric_weakness:
            diagnostic_actions.append(
                "Debilidad proximal simetrica: orientar estudio a miopatia inflamatoria."
            )
            trace.append("Patron clinico de miopatia inflamatoria detectado.")
        if payload.myalgia_prominent and not payload.proximal_symmetric_weakness:
            diagnostic_actions.append(
                "Mialgia aislada sin perdida de fuerza: reevaluar diferencial no miopatico."
            )
        if payload.anti_mda5_positive:
            safety_alerts.append("Anti-MDA5 positivo: activar vigilancia estrecha de EPI agresiva.")
            if payload.interstitial_lung_disease_signs:
                critical = (
                    "Anti-MDA5 + signos de afectacion intersticial: "
                    "escalada respiratoria precoz."
                )
                safety_alerts.append(critical)

        behcet_triade = (
            payload.recurrent_oral_aphthae
            and payload.ocular_inflammation_or_uveitis
            and payload.erythema_nodosum_present
        )
        if behcet_triade:
            diagnostic_actions.append("Triada de Behcet en urgencias: alta sospecha clinica.")
            therapeutic_actions.append(
                "Primera linea sugerida: pulsos de corticoides + azatioprina."
            )
            trace.append("Ruta diagnostico-terapeutica de Behcet activada.")
        if payload.cerebral_parenchymal_involvement and payload.cyclosporine_planned:
            safety_alerts.append(
                "Behcet neurologico: evitar ciclosporina por riesgo de empeoramiento cerebral."
            )

        return diagnostic_actions, therapeutic_actions, safety_alerts, trace

    @staticmethod
    def _imaging_and_screening_pathway(
        payload: RheumImmunoSupportProtocolRequest,
    ) -> tuple[list[str], list[str]]:
        imaging_actions: list[str] = []
        therapeutic_actions: list[str] = []

        if payload.elderly_male_with_acute_monoarthritis and payload.intercurrent_trigger_present:
            if not payload.wrist_xray_chondrocalcinosis:
                imaging_actions.append(
                    "Pseudo-gota probable con carpo negativo: solicitar RX de rodillas."
                )
                imaging_actions.append(
                    "Completar cribado de condrocalcinosis con RX de sinfisis del pubis."
                )
            else:
                imaging_actions.append(
                    "Condrocalcinosis carpiana detectada: compatible con artritis por pirofosfato."
                )

        if payload.young_male_with_inflammatory_back_pain:
            if payload.sacroiliitis_on_imaging:
                imaging_actions.append(
                    "Sacroileitis en imagen: respalda espondiloartropatia axial."
                )
                therapeutic_actions.append(
                    "Primera linea: AINEs + fisioterapia en espondiloartropatia."
                )
                therapeutic_actions.append(
                    "Si refractaria: valorar anti-TNF/anti-IL17/inhibidores JAK."
                )
                if payload.peripheral_joint_involvement:
                    therapeutic_actions.append(
                        "Metotrexato util cuando hay afectacion articular periferica."
                    )
                else:
                    therapeutic_actions.append(
                        "Metotrexato con utilidad limitada en fenotipo axial puro."
                    )

        return imaging_actions, therapeutic_actions

    @staticmethod
    def _maternal_fetal_and_data_domains(
        payload: RheumImmunoSupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        maternal_fetal_actions: list[str] = []
        data_model_flags: list[str] = []

        if payload.pregnancy_ongoing and (payload.anti_ro_positive or payload.anti_la_positive):
            maternal_fetal_actions.append(
                "Gestacion con anti-Ro/anti-La: vigilancia ecocardiografica fetal estrecha."
            )
            if payload.fetal_conduction_or_myocardial_risk:
                if not payload.fluorinated_corticosteroids_started:
                    critical_alerts.append(
                        "Riesgo fetal cardiaco en lupus neonatal: iniciar corticoides fluorados."
                    )
                else:
                    maternal_fetal_actions.append(
                        "Corticoides fluorados iniciados para riesgo de bloqueo cardiaco fetal."
                    )

        if payload.pregnancy_ongoing and payload.anti_desmoglein3_positive:
            maternal_fetal_actions.append(
                "Antidesmogleina 3 positiva: monitorizar posible afectacion neonatal."
            )
        if payload.pregnancy_ongoing and payload.anti_acetylcholine_receptor_positive:
            maternal_fetal_actions.append(
                "Antirreceptor ACh positiva: vigilar miastenia neonatal transitoria."
            )

        if payload.igg4_related_disease_suspected:
            required_igg4 = [
                payload.igg4_lymphoplasmacytic_infiltrate,
                payload.igg4_obliterative_phlebitis,
                payload.igg4_storiform_fibrosis,
            ]
            if all(required_igg4):
                data_model_flags.append(
                    "IgG4: triada histologica completa (infiltrado, flebitis, "
                    "fibrosis estoriforme)."
                )
            else:
                data_model_flags.append(
                    "IgG4: completar campos histologicos obligatorios para clasificacion."
                )

        if payload.aps_clinical_event_present and payload.aps_laboratory_criterion_present:
            data_model_flags.append("SAF: criterio de entrada clinico + analitico presente.")
            if payload.thrombocytopenia_present:
                data_model_flags.append(
                    "SAF: trombopenia registrada como dominio relevante en clasificacion actual."
                )

        return critical_alerts, maternal_fetal_actions, data_model_flags

    @staticmethod
    def _severity(
        *,
        critical_alerts: list[str],
        safety_alerts: list[str],
    ) -> str:
        if critical_alerts:
            return "critical"
        if safety_alerts:
            return "high"
        return "medium"

    @staticmethod
    def build_recommendation(
        payload: RheumImmunoSupportProtocolRequest,
    ) -> RheumImmunoSupportProtocolRecommendation:
        """Genera recomendacion operativa reuma-inmuno para validacion humana."""
        (
            critical_vital,
            diagnostic_vital,
            therapeutic_vital,
            trace_vital,
        ) = RheumImmunoSupportProtocolService._vital_risk_pathway(payload)
        (
            diagnostic_core,
            therapeutic_core,
            safety_alerts,
            trace_core,
        ) = RheumImmunoSupportProtocolService._diagnostic_workflows(payload)
        (
            imaging_actions,
            therapeutic_imaging,
        ) = RheumImmunoSupportProtocolService._imaging_and_screening_pathway(payload)
        (
            critical_mf,
            maternal_fetal_actions,
            data_model_flags,
        ) = RheumImmunoSupportProtocolService._maternal_fetal_and_data_domains(payload)

        critical_alerts = critical_vital + critical_mf
        diagnostic_actions = diagnostic_vital + diagnostic_core
        therapeutic_actions = therapeutic_vital + therapeutic_core + therapeutic_imaging
        interpretability_trace = trace_vital + trace_core
        severity = RheumImmunoSupportProtocolService._severity(
            critical_alerts=critical_alerts,
            safety_alerts=safety_alerts,
        )

        return RheumImmunoSupportProtocolRecommendation(
            severity_level=severity,
            critical_alerts=critical_alerts,
            diagnostic_actions=diagnostic_actions,
            therapeutic_actions=therapeutic_actions,
            safety_alerts=safety_alerts,
            imaging_screening_actions=imaging_actions,
            maternal_fetal_actions=maternal_fetal_actions,
            data_model_flags=data_model_flags,
            interpretability_trace=interpretability_trace,
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. "
                "Requiere validacion de Reumatologia/Medicina Interna."
            ),
        )
