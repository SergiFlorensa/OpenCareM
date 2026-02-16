"""
Motor de soporte operativo para diagnostico diferencial de pitiriasis.

Orienta entre pitiriasis versicolor, rosada y alba, incluyendo red flags
que requieren escalado por posible diagnostico alternativo de mayor riesgo.
"""
from app.schemas.pityriasis_protocol import (
    PityriasisDifferentialRecommendation,
    PityriasisDifferentialRequest,
)


class PityriasisProtocolService:
    """Genera una recomendacion diferencial interpretable y trazable."""

    @staticmethod
    def _score_versicolor(payload: PityriasisDifferentialRequest) -> tuple[int, list[str]]:
        score = 0
        findings: list[str] = []
        distribution = set(payload.lesion_distribution)

        if 15 <= payload.age_years <= 45:
            score += 1
            findings.append("Edad compatible con mayor prevalencia de pitiriasis versicolor.")
        if distribution.intersection({"torax", "espalda", "areas_seborreicas", "tronco"}):
            score += 2
            findings.append("Distribucion en tronco/areas seborreicas compatible con Malassezia.")
        if payload.fine_scaling_present:
            score += 1
            findings.append("Descamacion fina furfuracea presente.")
        if payload.signo_unyada_positive:
            score += 3
            findings.append("Signo de la unyada positivo.")
        if payload.wood_lamp_result == "amarillo_naranja":
            score += 2
            findings.append("Fluorescencia amarillo-naranja en luz de Wood.")
        if payload.koh_result == "positivo_spaghetti_albondigas":
            score += 4
            findings.append("KOH con patron de hifas cortas y esporas (spaghetti/albondigas).")
        if payload.recurrent_course:
            score += 1
            findings.append("Curso recidivante compatible con pitiriasis versicolor.")
        if payload.lesion_pigmentation in {"hipocromica", "hipercromica", "mixta"}:
            score += 1
            findings.append("Cambio pigmentario compatible con versicolor.")
        return score, findings

    @staticmethod
    def _score_rosada(payload: PityriasisDifferentialRequest) -> tuple[int, list[str]]:
        score = 0
        findings: list[str] = []
        distribution = set(payload.lesion_distribution)

        if payload.herald_patch_present:
            score += 3
            findings.append("Placa heraldica inicial reportada.")
        if payload.christmas_tree_pattern_present:
            score += 3
            findings.append("Patron en ramas de pino caidas presente.")
        if payload.viral_prodrome_present:
            score += 1
            findings.append("Prodromos virales previos al exantema.")
        if distribution.intersection({"tronco", "torax", "espalda"}):
            score += 1
            findings.append("Distribucion troncular compatible con pitiriasis rosada.")
        if payload.pruritus_intensity >= 4:
            score += 1
            findings.append("Prurito moderado/intenso.")
        if 10 <= payload.age_years <= 35:
            score += 1
            findings.append("Rango etario frecuente para pitiriasis rosada.")
        if payload.koh_result == "positivo_spaghetti_albondigas":
            score -= 2
        return score, findings

    @staticmethod
    def _score_alba(payload: PityriasisDifferentialRequest) -> tuple[int, list[str]]:
        score = 0
        findings: list[str] = []
        distribution = set(payload.lesion_distribution)

        if payload.age_years < 16:
            score += 3
            findings.append("Edad pediatrica compatible con pitiriasis alba.")
        if distribution.intersection({"cara", "extremidades_superiores"}):
            score += 2
            findings.append("Localizacion en cara/extremidades superiores.")
        if payload.lesion_pigmentation == "hipocromica":
            score += 2
            findings.append("Maculas hipocromicas predominantes.")
        if payload.fine_scaling_present:
            score += 1
            findings.append("Escama fina adherente compatible con fase intermedia.")
        if payload.atopic_background:
            score += 1
            findings.append("Antecedente atopico asociado.")
        if payload.recurrent_course:
            score += 1
            findings.append("Curso cronico/recidivante compatible con pitiriasis alba.")
        return score, findings

    @staticmethod
    def _build_urgent_red_flags(payload: PityriasisDifferentialRequest) -> list[str]:
        red_flags: list[str] = []
        if payload.sensory_loss_in_lesion:
            red_flags.append(
                "Perdida de sensibilidad en lesion: descartar lepra tuberculoide con prioridad."
            )
        if payload.deep_erythema_warmth_pain:
            red_flags.append(
                "Eritema doloroso/caliente profundo: descartar celulitis o erisipela."
            )
        if payload.systemic_signs and payload.deep_erythema_warmth_pain:
            red_flags.append(
                "Signos sistemicos con foco cutaneo doloroso: "
                "valorar antibioticoterapia sistemica urgente."
            )
        return red_flags

    @staticmethod
    def _choose_most_likely(scores: dict[str, int]) -> str:
        ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        top_name, top_score = ordered[0]
        if top_score < 3:
            return "indeterminado"
        if len(ordered) > 1 and (top_score - ordered[1][1]) <= 1:
            return "indeterminado"
        return top_name

    @staticmethod
    def _build_recommended_tests(
        payload: PityriasisDifferentialRequest,
        most_likely_condition: str,
        red_flags: list[str],
    ) -> list[str]:
        tests: list[str] = []
        if most_likely_condition == "pitiriasis_versicolor":
            if payload.koh_result == "no_realizado":
                tests.append(
                    "Realizar examen directo con KOH para confirmar patron "
                    "'spaghetti y albondigas'."
                )
            if payload.wood_lamp_result == "no_realizada":
                tests.append("Completar evaluacion con luz de Wood en consulta.")
        elif most_likely_condition == "pitiriasis_rosada":
            if payload.koh_result == "no_realizado":
                tests.append(
                    "Si hay duda morfologica, realizar KOH para descartar tinea corporis."
                )
        elif most_likely_condition == "indeterminado":
            tests.extend(
                [
                    "Completar KOH y luz de Wood para acotar etiologia.",
                    "Valorar interconsulta con dermatologia para confirmacion diagnostica.",
                ]
            )
        if red_flags:
            tests.append(
                "Escalar estudio etiologico alternativo "
                "(incluyendo infeccion profunda o lepra) por red flags."
            )
        if not tests:
            tests.append("No se requieren pruebas adicionales inmediatas; seguimiento clinico.")
        return tests

    @staticmethod
    def _build_initial_management(
        most_likely_condition: str,
        red_flags: list[str],
    ) -> list[str]:
        management: list[str] = []
        if most_likely_condition == "pitiriasis_versicolor":
            management.extend(
                [
                    "Primera linea: azoles topicos o sulfuro de selenio.",
                    "Considerar terapia sistemica solo en cuadros extensos o muy recidivantes.",
                ]
            )
        elif most_likely_condition == "pitiriasis_rosada":
            management.extend(
                [
                    "Manejo expectante: proceso habitualmente autolimitado.",
                    "Control sintomatico de prurito con antihistaminicos "
                    "y corticoide topico de baja potencia.",
                ]
            )
        elif most_likely_condition == "pitiriasis_alba":
            management.extend(
                [
                    "Hidratacion cutanea intensiva con emolientes.",
                    "Fotoproteccion diaria para reducir contraste de hipopigmentacion.",
                ]
            )
        else:
            management.append(
                "No iniciar tratamiento dirigido hasta clarificar etiologia "
                "con pruebas complementarias."
            )

        if red_flags:
            management.insert(
                0,
                "Priorizar valoracion presencial urgente para descartar "
                "diagnosticos de mayor riesgo.",
            )
        return management

    @staticmethod
    def _build_follow_up_recommendations(
        most_likely_condition: str,
        red_flags: list[str],
    ) -> list[str]:
        follow_up = [
            "Reevaluar evolucion clinica y respuesta terapéutica en 2-4 semanas.",
            "Escalar antes si aparecen dolor intenso, fiebre o extension rapida de lesiones.",
        ]
        if most_likely_condition == "pitiriasis_alba":
            follow_up.append(
                "Informar curso potencialmente prolongado en hipopigmentacion residual."
            )
        if most_likely_condition == "pitiriasis_versicolor":
            follow_up.append(
                "Explicar riesgo de recidiva y necesidad de adherencia a tratamiento topico."
            )
        if red_flags:
            follow_up.append(
                "No esperar control ambulatorio si persisten red flags; "
                "derivar a evaluacion urgente."
            )
        return follow_up

    @staticmethod
    def build_recommendation(
        payload: PityriasisDifferentialRequest,
    ) -> PityriasisDifferentialRecommendation:
        """Construye recomendacion diferencial interpretable para pitiriasis."""
        versicolor_score, versicolor_findings = PityriasisProtocolService._score_versicolor(payload)
        rosada_score, rosada_findings = PityriasisProtocolService._score_rosada(payload)
        alba_score, alba_findings = PityriasisProtocolService._score_alba(payload)

        scores = {
            "pitiriasis_versicolor": versicolor_score,
            "pitiriasis_rosada": rosada_score,
            "pitiriasis_alba": alba_score,
        }
        most_likely = PityriasisProtocolService._choose_most_likely(scores)
        red_flags = PityriasisProtocolService._build_urgent_red_flags(payload)

        all_differentials = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        differential_labels = [
            name
            for name, score_value in all_differentials
            if score_value >= 1
        ][:3]
        if "indeterminado" == most_likely and not differential_labels:
            differential_labels = ["pitiriasis_versicolor", "pitiriasis_rosada", "pitiriasis_alba"]

        if most_likely == "pitiriasis_versicolor":
            supporting_findings = versicolor_findings
        elif most_likely == "pitiriasis_rosada":
            supporting_findings = rosada_findings
        elif most_likely == "pitiriasis_alba":
            supporting_findings = alba_findings
        else:
            supporting_findings = (
                versicolor_findings[:1] + rosada_findings[:1] + alba_findings[:1]
            ) or ["Hallazgos no concluyentes para una pitiriasis especifica."]

        return PityriasisDifferentialRecommendation(
            most_likely_condition=most_likely,
            differential_diagnoses=differential_labels,
            supporting_findings=supporting_findings,
            recommended_tests=PityriasisProtocolService._build_recommended_tests(
                payload,
                most_likely,
                red_flags,
            ),
            initial_management=PityriasisProtocolService._build_initial_management(
                most_likely,
                red_flags,
            ),
            urgent_red_flags=red_flags,
            follow_up_recommendations=PityriasisProtocolService._build_follow_up_recommendations(
                most_likely,
                red_flags,
            ),
            human_validation_required=True,
            non_diagnostic_warning=(
                "Soporte operativo no diagnostico. "
                "Requiere validacion clinica/dermatologica humana."
            ),
        )
