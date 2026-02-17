"""
Motor operativo de oncologia para urgencias.

No diagnostica; organiza rutas de riesgo para validacion clinica humana.
"""
from app.schemas.oncology_support_protocol import (
    OncologySupportProtocolRecommendation,
    OncologySupportProtocolRequest,
)


class OncologySupportProtocolService:
    """Construye recomendaciones operativas oncologicas en urgencias."""

    @staticmethod
    def _immunotherapy_and_biomarkers(
        payload: OncologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        mechanism_notes: list[str] = []
        biomarker_strategy: list[str] = []
        trace: list[str] = []

        checkpoint_class = (payload.checkpoint_inhibitor_class or "").strip().lower()
        checkpoint_agent = (payload.checkpoint_agent_name or "").strip().lower()

        if checkpoint_class in {"pd-1", "pd1"} or checkpoint_agent in {
            "nivolumab",
            "pembrolizumab",
        }:
            mechanism_notes.append(
                "Inhibidor PD-1: bloquea receptor PD-1 del linfocito T y "
                "restaura activacion inmune antitumoral."
            )
        if checkpoint_class in {"pd-l1", "pdl1", "pd-l2", "pdl2"} or checkpoint_agent in {
            "atezolizumab",
            "avelumab",
            "durvalumab",
        }:
            mechanism_notes.append(
                "Inhibidor PD-L1/L2: bloquea ligandos tumorales e impide "
                "senal inhibitoria sobre linfocitos T."
            )
        if checkpoint_class in {"ctla-4", "ctla4"} or checkpoint_agent in {
            "ipilimumab",
        }:
            mechanism_notes.append(
                "Inhibidor CTLA-4: refuerza activacion de linfocitos T "
                "a nivel de priming inmune."
            )

        if (
            payload.metastatic_crc_unresectable
            and payload.first_line_setting
            and (payload.dmmr_present or payload.msi_high_present)
        ):
            biomarker_strategy.append(
                "CCR metastasico irresecable con dMMR/MSI-high: priorizar inmunoterapia "
                "(pembrolizumab o nivolumab+ipilimumab) sobre quimioterapia inicial."
            )
            trace.append("Regla biomarcador dMMR/MSI-high de primera linea activada.")
        elif payload.metastatic_crc_unresectable and payload.first_line_setting:
            biomarker_strategy.append(
                "Sin biomarcador dMMR/MSI-high documentado: no escalar a inmunoterapia "
                "de primera linea sin reevaluacion molecular."
            )

        return mechanism_notes, biomarker_strategy, trace

    @staticmethod
    def _immune_toxicity_pathway(
        payload: OncologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        management_actions: list[str] = []
        trace: list[str] = []

        grade3_hepatotoxicity = False
        if payload.hepatic_toxicity_grade is not None and payload.hepatic_toxicity_grade >= 3:
            grade3_hepatotoxicity = True
        if (
            payload.transaminases_multiple_uln is not None
            and payload.transaminases_multiple_uln > 5
        ):
            grade3_hepatotoxicity = True
        if (
            payload.total_bilirubin_mg_dl is not None
            and payload.total_bilirubin_mg_dl > 2.3
            and payload.transaminases_multiple_uln is not None
            and payload.transaminases_multiple_uln > 3
        ):
            grade3_hepatotoxicity = True

        if payload.immune_hepatotoxicity_suspected:
            management_actions.append(
                "Toxicidad inmunomediada sospechada: gradar segun NCI y "
                "monitorizar analitica seriada."
            )

        if grade3_hepatotoxicity:
            critical_alerts.append(
                "Hepatotoxicidad inmunomediada grado >=3: suspender "
                "inmunoterapia de forma temporal."
            )
            management_actions.append(
                "Iniciar prednisona/equivalente 1-2 mg/kg/dia como primera linea."
            )
            if not payload.immunotherapy_suspended:
                critical_alerts.append(
                    "Toxicidad hepatica grave sin suspension documentada del farmaco."
                )
            if payload.prednisone_mg_kg_day is not None and payload.prednisone_mg_kg_day < 1:
                critical_alerts.append(
                    "Dosis corticoide por debajo de rango recomendado en toxicidad grave."
                )
            trace.append("Regla de hepatotoxicidad grado 3 por transaminasas/bilirrubina activada.")

        if payload.refractory_to_steroids:
            management_actions.append(
                "Toxicidad refractaria a corticoides: escalar inmunosupresion de segunda linea."
            )
            if payload.infliximab_considered:
                management_actions.append(
                    "Infliximab considerado como segunda linea en refractarios."
                )
            else:
                critical_alerts.append(
                    "Refractariedad a esteroides sin estrategia de segunda linea documentada."
                )

        if payload.rechallenge_considered_after_resolution:
            management_actions.append(
                "Tras resolucion clinica/analitica puede valorarse reintroduccion controlada."
            )

        return critical_alerts, management_actions, trace

    @staticmethod
    def _cardio_oncology_pathway(
        payload: OncologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        cardio_actions: list[str] = []
        trace: list[str] = []

        cardio_risk_therapy = payload.trastuzumab_planned or payload.anthracycline_planned
        if cardio_risk_therapy:
            cardio_actions.append(
                "Terapia con riesgo cardiotoxico detectada: FEVI basal obligatoria "
                "por eco o medicina nuclear antes de iniciar."
            )
            if not payload.baseline_lvef_assessed and payload.baseline_lvef_percent is None:
                critical_alerts.append(
                    "Bloquear inicio de trastuzumab/antraciclina sin FEVI basal."
                )
            if payload.baseline_lvef_percent is not None:
                trace.append("FEVI basal documentada para ruta cardio-oncologica.")
                if payload.baseline_lvef_percent < 50:
                    critical_alerts.append(
                        "FEVI basal reducida: activar valoracion cardio-oncologica prioritaria."
                    )

        return critical_alerts, cardio_actions, trace

    @staticmethod
    def _febrile_neutropenia_pathway(
        payload: OncologySupportProtocolRequest,
    ) -> tuple[list[str], list[str], list[str]]:
        critical_alerts: list[str] = []
        fn_actions: list[str] = []
        trace: list[str] = []

        fever_criterion = (
            (payload.temperature_c_single is not None and payload.temperature_c_single > 38.3)
            or payload.fever_over_38_more_than_1h
            or payload.fever_three_measurements_24h
        )

        neutropenia_criterion = False
        if payload.absolute_neutrophil_count_mm3 is not None:
            if payload.absolute_neutrophil_count_mm3 < 500:
                neutropenia_criterion = True
            elif (
                500 <= payload.absolute_neutrophil_count_mm3 < 1000
                and payload.anc_expected_to_drop_below_500
            ):
                neutropenia_criterion = True

        if fever_criterion and neutropenia_criterion:
            critical_alerts.append(
                "Neutropenia febril: activar aislamiento y antibioterapia empirica inmediata."
            )
            fn_actions.append(
                "Tomar cultivos y no retrasar inicio de antibiotico de amplio espectro."
            )
            trace.append("Regla diagnostica de neutropenia febril activada.")
            if payload.perioperative_or_adjuvant_context:
                fn_actions.append(
                    "Contexto perioperatorio/adyuvante: considerar mayor intensidad de riesgo."
                )
            if payload.palliative_later_line_context:
                fn_actions.append(
                    "Contexto paliativo de lineas avanzadas: ajustar intensidad "
                    "segun estado global."
                )

        return critical_alerts, fn_actions, trace

    @staticmethod
    def _sarcoma_response_pathway(
        payload: OncologySupportProtocolRequest,
    ) -> tuple[list[str], list[str]]:
        actions: list[str] = []
        trace: list[str] = []

        if payload.bone_sarcoma_post_neoadjuvant_specimen_available:
            if payload.necrosis_rate_percent is not None:
                actions.append(
                    "Registrar tasa de necrosis en pieza quirurgica como marcador "
                    "pronostico principal."
                )
                if payload.necrosis_rate_percent >= 90:
                    actions.append(
                        "Alta necrosis post-neoadyuvancia: sugiere mejor respuesta patologica."
                    )
                else:
                    actions.append(
                        "Necrosis suboptima: considerar riesgo pronostico mayor "
                        "y reevaluacion terapeutica."
                    )
                trace.append("Regla pronostica por necrosis en sarcoma oseo activada.")

        if payload.ewing_sarcoma_suspected:
            if payload.ewsr1_rearrangement_documented:
                actions.append("Reordenamiento EWSR1 documentado en soporte diagnostico de Ewing.")
            else:
                actions.append(
                    "Sarcoma de Ewing sospechado: completar/confirmar estado de "
                    "reordenamiento EWSR1."
                )

        return actions, trace

    @staticmethod
    def _severity(
        *,
        critical_alerts: list[str],
        management_actions: list[str],
    ) -> str:
        if critical_alerts:
            return "critical"
        if management_actions:
            return "high"
        return "medium"

    @staticmethod
    def build_recommendation(
        payload: OncologySupportProtocolRequest,
    ) -> OncologySupportProtocolRecommendation:
        """Genera recomendacion operativa oncológica para validacion humana."""
        (
            mechanism_notes,
            biomarker_strategy,
            trace_immuno,
        ) = OncologySupportProtocolService._immunotherapy_and_biomarkers(payload)
        (
            critical_tox,
            toxicity_actions,
            trace_tox,
        ) = OncologySupportProtocolService._immune_toxicity_pathway(payload)
        (
            critical_cardio,
            cardio_actions,
            trace_cardio,
        ) = OncologySupportProtocolService._cardio_oncology_pathway(payload)
        (
            critical_fn,
            fn_actions,
            trace_fn,
        ) = OncologySupportProtocolService._febrile_neutropenia_pathway(payload)
        sarcoma_actions, trace_sarcoma = OncologySupportProtocolService._sarcoma_response_pathway(
            payload
        )

        critical_alerts = critical_tox + critical_cardio + critical_fn
        interpretability_trace = trace_immuno + trace_tox + trace_cardio + trace_fn + trace_sarcoma
        severity = OncologySupportProtocolService._severity(
            critical_alerts=critical_alerts,
            management_actions=toxicity_actions + cardio_actions + fn_actions + sarcoma_actions,
        )

        return OncologySupportProtocolRecommendation(
            severity_level=severity,
            critical_alerts=critical_alerts,
            immunotherapy_mechanism_notes=mechanism_notes,
            biomarker_strategy=biomarker_strategy,
            toxicity_management_actions=toxicity_actions,
            cardio_oncology_actions=cardio_actions,
            febrile_neutropenia_actions=fn_actions,
            sarcoma_response_actions=sarcoma_actions,
            interpretability_trace=interpretability_trace,
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. "
                "Requiere validacion por oncologia/equipo de urgencias."
            ),
        )
