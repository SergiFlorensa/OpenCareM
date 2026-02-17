"""
Motor de soporte operativo para diferencial acne/rosacea.

Integra reglas clinicas interpretables y alertas de seguridad farmacologica.
"""
from app.schemas.acne_rosacea_protocol import (
    AcneRosaceaDifferentialRecommendation,
    AcneRosaceaDifferentialRequest,
)


class AcneRosaceaProtocolService:
    """Construye recomendacion operativa no diagnostica para acne/rosacea."""

    @staticmethod
    def _score_acne(payload: AcneRosaceaDifferentialRequest) -> tuple[int, list[str]]:
        score = 0
        findings: list[str] = []
        distribution = set(payload.lesion_distribution)

        if payload.comedones_present:
            score += 4
            findings.append("Comedones presentes, hallazgo clave a favor de acne.")
        if payload.lesion_pattern in {"polimorfo", "nodulo_quistico"}:
            score += 2
            findings.append("Patron lesional polimorfo/nodulo-quistico compatible con acne.")
        if distribution.intersection({"torax", "espalda"}):
            score += 2
            findings.append("Afectacion troncal frecuente en acne.")
        if payload.suspected_hyperandrogenism and payload.sex == "femenino":
            score += 1
            findings.append("Contexto de posible hiperandrogenismo asociado.")
        if payload.flushing_present or payload.telangiectasias_present:
            score -= 1
        return score, findings

    @staticmethod
    def _score_rosacea(payload: AcneRosaceaDifferentialRequest) -> tuple[int, list[str]]:
        score = 0
        findings: list[str] = []
        distribution = set(payload.lesion_distribution)

        if not payload.comedones_present:
            score += 2
            findings.append("Ausencia de comedones, orienta a rosacea.")
        if payload.flushing_present:
            score += 2
            findings.append("Flushing facial presente.")
        if payload.telangiectasias_present:
            score += 2
            findings.append("Telangiectasias presentes.")
        if payload.vasodilatory_triggers_present or payload.photosensitivity_triggered:
            score += 1
            findings.append("Detonantes vasodilatadores/fotoexposicion reportados.")
        if distribution.intersection({"mejillas", "nariz", "frente", "menton"}):
            score += 1
            findings.append("Distribucion centrofacial compatible.")
        if payload.ocular_symptoms_present:
            score += 1
            findings.append("Sintomas oculares compatibles con subtipo ocular.")
        if payload.phymatous_changes_present:
            score += 2
            findings.append("Cambios fimatosos presentes.")
        return score, findings

    @staticmethod
    def _build_red_flags(payload: AcneRosaceaDifferentialRequest) -> list[str]:
        alerts: list[str] = []
        if (
            payload.severe_nodules_abscesses_present
            and payload.systemic_symptoms_present
            and payload.elevated_vsg_or_leukocytosis
        ):
            alerts.append("Sospecha de acne fulminans: priorizar valoracion dermatologica urgente.")
        if payload.phymatous_changes_present:
            alerts.append(
                "Rosacea fimatosa: valorar derivacion para manejo quirurgico/laser especializado."
            )
        if payload.ocular_symptoms_present:
            alerts.append("Rosacea ocular probable: coordinar valoracion oftalmologica precoz.")
        return alerts

    @staticmethod
    def _choose_condition(acne_score: int, rosacea_score: int) -> str:
        if acne_score < 2 and rosacea_score < 2:
            return "indeterminado"
        if abs(acne_score - rosacea_score) <= 1:
            return "indeterminado"
        return "acne" if acne_score > rosacea_score else "rosacea"

    @staticmethod
    def _infer_subtype(
        payload: AcneRosaceaDifferentialRequest,
        condition: str,
    ) -> str:
        if condition == "acne":
            if payload.severe_nodules_abscesses_present:
                return "acne_grave_nodulo_quistico"
            if payload.lesion_pattern == "polimorfo":
                return "acne_vulgar_polimorfo"
            return "acne_papulo_pustuloso"
        if condition == "rosacea":
            if payload.phymatous_changes_present:
                return "rosacea_fimatosa"
            if payload.ocular_symptoms_present:
                return "rosacea_ocular"
            if payload.flushing_present or payload.telangiectasias_present:
                return "rosacea_eritematotelangiectasica"
            return "rosacea_papulopustulosa"
        return "diferencial_abierto"

    @staticmethod
    def _infer_severity(
        payload: AcneRosaceaDifferentialRequest,
        red_flags: list[str],
    ) -> str:
        if red_flags or payload.severe_nodules_abscesses_present:
            return "high"
        if payload.lesion_pattern in {"papulo_pustuloso", "polimorfo"}:
            return "medium"
        return "low"

    @staticmethod
    def _build_initial_management(
        condition: str,
        subtype: str,
    ) -> list[str]:
        if condition == "acne":
            actions = [
                "Base topica inicial: peroxido de benzoilo + retinoide topico segun tolerancia.",
            ]
            if subtype == "acne_grave_nodulo_quistico":
                actions.append("Escalar a terapia sistemica y derivacion dermatologica preferente.")
            else:
                actions.append(
                    "Valorar antibiotico oral en acne moderado " "si no hay respuesta topica."
                )
            return actions
        if condition == "rosacea":
            actions = [
                "Evitar detonantes vasodilatadores y reforzar fotoproteccion diaria.",
            ]
            if subtype == "rosacea_eritematotelangiectasica":
                actions.append("Considerar brimonidina topica para control de eritema persistente.")
            elif subtype == "rosacea_papulopustulosa":
                actions.append("Primera linea topica: metronidazol/azelaico/ivermectina.")
            else:
                actions.append("Derivacion especializada por subtipo no leve.")
            return actions
        return ["No iniciar estrategia dirigida hasta confirmar diferencial en consulta."]

    @staticmethod
    def _build_pharmacologic_considerations(
        payload: AcneRosaceaDifferentialRequest,
        condition: str,
    ) -> list[str]:
        notes: list[str] = []
        if condition == "acne":
            if payload.pediatric_patient:
                notes.append(
                    "Evitar tetraciclinas en paciente pediatrico; "
                    "considerar alternativa segun edad."
                )
            if payload.suspected_hyperandrogenism and payload.sex == "femenino":
                notes.append("Valorar estrategia antiandrogenica en coordinacion con ginecologia.")
        if payload.pregnant_or_pregnancy_possible:
            notes.append("Contraindicar retinoides sistemicos si existe embarazo posible.")
        if payload.current_systemic_tetracycline and payload.current_retinoid_oral:
            notes.append(
                "Revisar seguridad por combinacion sistemica y ajustar "
                "pauta segun criterio experto."
            )
        if not notes:
            notes.append("Sin alertas farmacologicas mayores en datos reportados.")
        return notes

    @staticmethod
    def _build_isotretinoin_checklist(
        payload: AcneRosaceaDifferentialRequest,
    ) -> list[str]:
        if not payload.isotretinoin_candidate:
            return ["No aplica en este episodio (candidato a isotretinoina no activado)."]
        return [
            "Confirmar consentimiento informado especifico de isotretinoina.",
            "Solicitar perfil lipidico basal y seguimiento seriado.",
            "Solicitar funcion hepatica (GOT/GPT) basal y seguimiento.",
            "Monitorizar CPK, especialmente si realiza ejercicio intenso.",
            "Asegurar estrategia anticonceptiva y test de embarazo segun protocolo.",
            "Plan de hidratacion/fotoproteccion por xerosis y fotosensibilidad esperables.",
        ]

    @staticmethod
    def build_recommendation(
        payload: AcneRosaceaDifferentialRequest,
    ) -> AcneRosaceaDifferentialRecommendation:
        """Construye recomendacion diferencial operativa acne/rosacea."""
        acne_score, acne_findings = AcneRosaceaProtocolService._score_acne(payload)
        rosacea_score, rosacea_findings = AcneRosaceaProtocolService._score_rosacea(payload)
        red_flags = AcneRosaceaProtocolService._build_red_flags(payload)
        condition = AcneRosaceaProtocolService._choose_condition(acne_score, rosacea_score)
        subtype = AcneRosaceaProtocolService._infer_subtype(payload, condition)
        severity = AcneRosaceaProtocolService._infer_severity(payload, red_flags)

        differential = ["acne", "rosacea", "urticaria_vasculitis"]
        findings = acne_findings if condition == "acne" else rosacea_findings
        if condition == "indeterminado":
            findings = (acne_findings[:1] + rosacea_findings[:1]) or [
                "Datos clinicos no concluyentes para clasificacion unica."
            ]

        return AcneRosaceaDifferentialRecommendation(
            most_likely_condition=condition,
            suspected_subtype=subtype,
            severity_level=severity,
            differential_diagnoses=differential,
            supporting_findings=findings,
            initial_management=AcneRosaceaProtocolService._build_initial_management(
                condition,
                subtype,
            ),
            pharmacologic_considerations=(
                AcneRosaceaProtocolService._build_pharmacologic_considerations(
                    payload,
                    condition,
                )
            ),
            isotretinoin_monitoring_checklist=(
                AcneRosaceaProtocolService._build_isotretinoin_checklist(payload)
            ),
            urgent_red_flags=red_flags,
            follow_up_recommendations=[
                "Reevaluar respuesta en 2-4 semanas o antes si empeora.",
                "Escalar a dermatologia si no hay mejoria clinica inicial.",
            ],
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. Requiere validacion clinica humana."
            ),
        )
