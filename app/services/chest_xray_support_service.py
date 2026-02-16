"""
Motor de soporte operativo para interpretacion radiografica de torax.

Entrega orientacion por patrones y signos, sin sustituir informe radiologico
ni juicio medico.
"""
from app.schemas.chest_xray_support import (
    ChestXRaySupportRecommendation,
    ChestXRaySupportRequest,
)


class ChestXRaySupportService:
    """Genera recomendaciones operativas basadas en patrones radiograficos."""

    @staticmethod
    def _build_suspected_patterns(payload: ChestXRaySupportRequest) -> list[str]:
        suspected: list[str] = []
        signs = set(payload.signs)

        if payload.pattern in {"alveolar", "mixto"}:
            if "broncograma_aereo" in signs:
                suspected.append(
                    "Ocupacion alveolar compatible con consolidacion (ej. neumonia o edema)."
                )
            else:
                suspected.append(
                    "Patron alveolar probable; correlacionar con clinica y evolucion."
                )

        if payload.pattern in {"intersticial", "mixto"}:
            if "lineas_kerley_b" in signs:
                suspected.append(
                    "Patron intersticial con lineas B de Kerley (considerar congestion)."
                )
            else:
                suspected.append(
                    "Patron intersticial sugerido; completar evaluacion hemodinamica."
                )

        if payload.pattern == "atelectasia" or "desplazamiento_cisuras" in signs:
            suspected.append("Perdida de volumen compatible con atelectasia.")

        if payload.pattern == "neumotorax" or (
            "linea_pleural_visceral" in signs and "ausencia_trama_periferica" in signs
        ):
            suspected.append("Neumotorax probable por signos pleurales tipicos.")

        if payload.pattern == "derrame_pleural" or "signo_menisco" in signs:
            suspected.append("Derrame pleural probable por signo de menisco.")

        if payload.lesion_size_cm is not None:
            if payload.lesion_size_cm >= 3:
                suspected.append(
                    "Lesion >=3 cm: clasifica como masa y requiere estudio prioritario."
                )
            elif payload.lesion_size_cm > 0:
                suspected.append(
                    "Lesion focal <3 cm: clasifica como nodulo y requiere seguimiento."
                )

        if not suspected:
            suspected.append(
                "Sin patron dominante; mantener lectura sistematica y correlacion clinica."
            )
        return suspected

    @staticmethod
    def _build_urgent_red_flags(payload: ChestXRaySupportRequest) -> list[str]:
        red_flags: list[str] = []
        signs = set(payload.signs)

        if (
            payload.pattern == "neumotorax"
            and "desplazamiento_mediastinico" in signs
            and "linea_pleural_visceral" in signs
        ):
            red_flags.append(
                "Sospecha de neumotorax a tension: priorizar descompresion y escalado inmediato."
            )
        if "neumoperitoneo_subdiafragmatico" in signs:
            red_flags.append(
                "Aire subdiafragmatico sugerente de neumoperitoneo: "
                "valorar urgencia quirurgica."
            )
        return red_flags

    @staticmethod
    def _build_projection_caveats(payload: ChestXRaySupportRequest) -> list[str]:
        caveats: list[str] = []
        if payload.projection == "ap":
            caveats.append(
                "Proyeccion AP puede magnificar silueta cardiaca (falsa cardiomegalia)."
            )
        if payload.inspiratory_quality == "suboptima":
            caveats.append("Inspiracion suboptima puede simular aumento de densidad basal.")
        return caveats

    @staticmethod
    def _build_suggested_actions(
        payload: ChestXRaySupportRequest,
        red_flags: list[str],
    ) -> list[str]:
        actions: list[str] = []
        signs = set(payload.signs)

        if red_flags:
            actions.append("Escalar de inmediato a equipo senior/criticos segun protocolo local.")

        if payload.pattern == "neumotorax":
            actions.append("Confirmar extension y monitorizar compromiso hemodinamico.")

        if payload.pattern in {"alveolar", "intersticial", "mixto"}:
            actions.append("Correlacionar hallazgos con gasometria, saturacion y estado clinico.")

        if payload.projection == "ap" and "cardiomegalia_aparente_ap" in signs:
            actions.append(
                "Evitar sobrediagnosticar cardiomegalia en AP sin correlacion clinica."
            )

        if payload.pattern == "neumotorax" and payload.inspiratory_quality == "adecuada":
            actions.append(
                "Si persiste duda de pequeno neumotorax, considerar placa en espiracion."
            )

        if "signo_menisco" in signs:
            actions.append(
                "Valorar cuantia de derrame y causa de base "
                "(cardiaca, infecciosa, neoplasica)."
            )

        if not actions:
            actions.append(
                "Continuar lectura sistematica y reevaluar con contexto clinico del paciente."
            )
        return actions

    @staticmethod
    def build_recommendation(
        payload: ChestXRaySupportRequest,
    ) -> ChestXRaySupportRecommendation:
        """Construye recomendacion operativa trazable para RX de torax."""
        red_flags = ChestXRaySupportService._build_urgent_red_flags(payload)
        return ChestXRaySupportRecommendation(
            suspected_patterns=ChestXRaySupportService._build_suspected_patterns(payload),
            urgent_red_flags=red_flags,
            suggested_actions=ChestXRaySupportService._build_suggested_actions(
                payload, red_flags
            ),
            projection_caveats=ChestXRaySupportService._build_projection_caveats(payload),
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. Requiere validacion clinica humana."
            ),
        )
