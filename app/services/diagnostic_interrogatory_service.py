"""
Servicio de interrogatorio clinico activo (fase 1).

Implementa un ciclo simplificado inspirado en MedClarify:
1) candidatos con prior
2) actualizacion bayesiana con evidencia observada
3) seleccion de pregunta con score DEIG = IG + divergencia + concentracion
"""

from __future__ import annotations

import math
import unicodedata
from typing import Any


class DiagnosticInterrogatoryService:
    """Selecciona preguntas de aclaracion para reducir incertidumbre operativa."""

    _WEIGHTS = {"alpha": 0.5, "beta": 0.35, "gamma": 0.15}

    _DOMAIN_PROFILES: dict[str, dict[str, Any]] = {
        "nephrology": {
            "candidates": [
                {
                    "id": "aki_prerrenal",
                    "label": "FRA prerrenal",
                    "prior": 0.24,
                    "cluster": "renal_hemodynamic",
                    "likelihoods": {
                        "hypotension": 0.82,
                        "volume_depletion": 0.80,
                        "creatinine_rise": 0.65,
                        "hyperkalemia": 0.45,
                    },
                },
                {
                    "id": "aki_obstructive",
                    "label": "FRA obstructiva",
                    "prior": 0.20,
                    "cluster": "renal_obstructive",
                    "likelihoods": {
                        "anuria_or_oliguria": 0.80,
                        "hydronephrosis_signs": 0.82,
                        "lumbar_colic": 0.72,
                        "creatinine_rise": 0.70,
                    },
                },
                {
                    "id": "aki_intrinsic",
                    "label": "FRA intrinseca",
                    "prior": 0.20,
                    "cluster": "renal_parenchymal",
                    "likelihoods": {
                        "creatinine_rise": 0.82,
                        "urine_abnormal_sediment": 0.78,
                        "proteinuria_hematuria": 0.72,
                        "hyperkalemia": 0.62,
                    },
                },
                {
                    "id": "severe_hyperkalemia",
                    "label": "Hiperkalemia severa con riesgo electrico",
                    "prior": 0.21,
                    "cluster": "electrolyte_critical",
                    "likelihoods": {
                        "hyperkalemia": 0.90,
                        "ecg_changes": 0.83,
                        "muscle_weakness": 0.62,
                        "creatinine_rise": 0.62,
                    },
                },
                {
                    "id": "urologic_complication",
                    "label": "Complicacion urologica con afectacion renal",
                    "prior": 0.15,
                    "cluster": "urologic_related",
                    "likelihoods": {
                        "lumbar_colic": 0.80,
                        "fever_or_sepsis_signals": 0.66,
                        "anuria_or_oliguria": 0.60,
                        "hydronephrosis_signs": 0.75,
                    },
                },
            ],
            "feature_keywords": {
                "anuria_or_oliguria": ("oliguria", "anuria", "diuresis baja"),
                "hyperkalemia": ("k ", "k+", "potasio", "hiperkal", "6.2"),
                "lumbar_colic": ("dolor lumbar", "colico renal", "flanco"),
                "hypotension": ("tas", "hipotension", "pam"),
                "volume_depletion": ("deshidrat", "hipovolem", "vomito", "diarrea"),
                "creatinine_rise": ("creatinina", "urea", "fra", "filtro glomerular"),
                "ecg_changes": ("ecg", "electrocardiograma", "ondas t", "qrs"),
                "muscle_weakness": ("debilidad", "paresia"),
                "hydronephrosis_signs": ("hidronefrosis", "obstruccion", "eco renal"),
                "urine_abnormal_sediment": ("sedimento", "cilindros"),
                "proteinuria_hematuria": ("proteinuria", "hematuria"),
                "fever_or_sepsis_signals": ("fiebre", "sepsis", "escalofrios"),
            },
            "question_bank": [
                {
                    "id": "q_nephro_ecg",
                    "feature": "ecg_changes",
                    "type": "discriminator",
                    "text": (
                        "Dispones de ECG inmediato y hay cambios compatibles con "
                        "hiperkalemia (T picudas, QRS ancho o bradiarritmia)?"
                    ),
                },
                {
                    "id": "q_nephro_creatinine",
                    "feature": "creatinine_rise",
                    "type": "discriminator",
                    "text": "Cual es creatinina actual y evolucion respecto a basal en 24-48h?",
                },
                {
                    "id": "q_nephro_diuresis",
                    "feature": "anuria_or_oliguria",
                    "type": "discriminator",
                    "text": "Puedes cuantificar diuresis por hora y en 6 horas (ml/kg/h)?",
                },
                {
                    "id": "q_nephro_obstruction",
                    "feature": "hydronephrosis_signs",
                    "type": "exploratory",
                    "text": (
                        "Hay ecografia renal/vesical con signos de obstruccion "
                        "(hidronefrosis o retencion)?"
                    ),
                },
                {
                    "id": "q_nephro_acidbase",
                    "feature": "volume_depletion",
                    "type": "exploratory",
                    "text": (
                        "Hay datos de hipovolemia o perdidas "
                        "(vomitos/diarrea/deshidratacion) que orienten a causa prerrenal?"
                    ),
                },
            ],
        },
        "gynecology_obstetrics": {
            "candidates": [
                {
                    "id": "severe_preeclampsia",
                    "label": "Preeclampsia con criterios de severidad",
                    "prior": 0.30,
                    "cluster": "hypertensive_obstetric",
                    "likelihoods": {
                        "severe_hypertension": 0.90,
                        "neurologic_symptoms": 0.82,
                        "proteinuria_organ_damage": 0.75,
                    },
                },
                {
                    "id": "eclampsia_risk",
                    "label": "Riesgo de eclampsia inminente",
                    "prior": 0.20,
                    "cluster": "hypertensive_obstetric",
                    "likelihoods": {
                        "severe_hypertension": 0.84,
                        "neurologic_symptoms": 0.88,
                        "seizure_or_warning": 0.72,
                    },
                },
                {
                    "id": "obstetric_bleeding",
                    "label": "Sangrado obstetrico agudo",
                    "prior": 0.18,
                    "cluster": "hemorrhagic_obstetric",
                    "likelihoods": {
                        "vaginal_bleeding": 0.90,
                        "hemodynamic_instability": 0.75,
                    },
                },
                {
                    "id": "ectopic_pregnancy",
                    "label": "Embarazo ectopico complicado",
                    "prior": 0.17,
                    "cluster": "early_pregnancy",
                    "likelihoods": {
                        "beta_hcg_positive": 0.88,
                        "pelvic_pain": 0.84,
                        "vaginal_bleeding": 0.72,
                    },
                },
                {
                    "id": "non_obstetric_cause",
                    "label": "Causa no obstetrica a descartar",
                    "prior": 0.15,
                    "cluster": "non_obstetric",
                    "likelihoods": {
                        "abdominal_pain": 0.72,
                        "fever_or_sepsis_signals": 0.64,
                    },
                },
            ],
            "feature_keywords": {
                "severe_hypertension": ("ta 168", "ta 170", "ta >160", "hipertension severa"),
                "neurologic_symptoms": ("cefalea intensa", "fosfenos", "escotomas"),
                "proteinuria_organ_damage": ("proteinuria", "plaquetas", "transaminasas"),
                "seizure_or_warning": ("convulsion", "eclampsia"),
                "vaginal_bleeding": ("sangrado vaginal", "metrorragia"),
                "hemodynamic_instability": ("hipotension", "taquicardia", "shock"),
                "beta_hcg_positive": ("beta-hcg", "hcg positiva"),
                "pelvic_pain": ("dolor pelvico", "dolor abdominal bajo"),
                "abdominal_pain": ("dolor abdominal",),
                "fever_or_sepsis_signals": ("fiebre", "sepsis"),
            },
            "question_bank": [
                {
                    "id": "q_gyn_bp_confirm",
                    "feature": "severe_hypertension",
                    "type": "discriminator",
                    "text": (
                        "Puedes confirmar dos tomas de TA severa separadas y su "
                        "tendencia en 15-30 minutos?"
                    ),
                },
                {
                    "id": "q_gyn_neuro",
                    "feature": "neurologic_symptoms",
                    "type": "discriminator",
                    "text": (
                        "Presenta cefalea refractaria, fosfenos persistentes o "
                        "datos neurologicos progresivos?"
                    ),
                },
                {
                    "id": "q_gyn_proteinuria",
                    "feature": "proteinuria_organ_damage",
                    "type": "exploratory",
                    "text": (
                        "Hay proteinuria significativa o dano de organo "
                        "(plaquetas, creatinina, transaminasas)?"
                    ),
                },
                {
                    "id": "q_gyn_bleeding",
                    "feature": "vaginal_bleeding",
                    "type": "exploratory",
                    "text": "Existe sangrado vaginal activo o incremento del sangrado inicial?",
                },
            ],
        },
    }

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        return normalized.lower().strip()

    @classmethod
    def _extract_observed_features(
        cls,
        *,
        query: str,
        profile: dict[str, Any],
        memory_facts_used: list[str],
        patient_history_facts_used: list[str],
        extracted_facts: list[str],
    ) -> set[str]:
        normalized_query = cls._normalize(query)
        memory_blob = cls._normalize(
            " ".join(memory_facts_used + patient_history_facts_used + extracted_facts)
        )
        observed: set[str] = set()
        for feature, keywords in profile.get("feature_keywords", {}).items():
            for keyword in keywords:
                normalized_keyword = cls._normalize(keyword)
                if normalized_keyword and (
                    normalized_keyword in normalized_query or normalized_keyword in memory_blob
                ):
                    observed.add(feature)
                    break
        return observed

    @staticmethod
    def _normalize_distribution(values: dict[str, float]) -> dict[str, float]:
        total = sum(max(0.0, value) for value in values.values())
        if total <= 0:
            uniform = 1 / max(1, len(values))
            return {key: uniform for key in values}
        return {key: max(0.0, value) / total for key, value in values.items()}

    @staticmethod
    def _entropy(distribution: dict[str, float]) -> float:
        entropy = 0.0
        for value in distribution.values():
            if value > 0:
                entropy -= value * math.log2(value)
        return entropy

    @staticmethod
    def _simpson_diversity(distribution: dict[str, float]) -> float:
        return 1.0 - sum(value * value for value in distribution.values())

    @classmethod
    def _build_posterior(
        cls,
        *,
        candidates: list[dict[str, Any]],
        observed_features: set[str],
    ) -> dict[str, float]:
        raw: dict[str, float] = {}
        for candidate in candidates:
            candidate_id = str(candidate["id"])
            score = float(candidate.get("prior", 0.2))
            likelihoods = dict(candidate.get("likelihoods", {}))
            for feature in observed_features:
                likelihood = float(likelihoods.get(feature, 0.5))
                score *= min(0.95, max(0.05, likelihood))
            raw[candidate_id] = score
        return cls._normalize_distribution(raw)

    @classmethod
    def _hypothetical_update(
        cls,
        *,
        current_posterior: dict[str, float],
        candidates: list[dict[str, Any]],
        feature: str,
        answer_yes: bool,
    ) -> dict[str, float]:
        candidates_by_id = {str(item["id"]): item for item in candidates}
        updated: dict[str, float] = {}
        for candidate_id, prior in current_posterior.items():
            likelihoods = dict(candidates_by_id.get(candidate_id, {}).get("likelihoods", {}))
            base_likelihood = float(likelihoods.get(feature, 0.5))
            factor = base_likelihood if answer_yes else (1 - base_likelihood)
            updated[candidate_id] = prior * min(0.95, max(0.05, factor))
        return cls._normalize_distribution(updated)

    @staticmethod
    def _top_two(
        distribution: dict[str, float],
    ) -> tuple[tuple[str, float], tuple[str, float] | None]:
        ranked = sorted(distribution.items(), key=lambda item: item[1], reverse=True)
        if not ranked:
            return ("none", 0.0), None
        top = ranked[0]
        second = ranked[1] if len(ranked) > 1 else None
        return top, second

    @classmethod
    def _semantic_divergence(
        cls,
        *,
        yes_distribution: dict[str, float],
        no_distribution: dict[str, float],
        candidates: list[dict[str, Any]],
    ) -> float:
        candidates_by_id = {str(item["id"]): item for item in candidates}
        yes_top = max(yes_distribution, key=yes_distribution.get)
        no_top = max(no_distribution, key=no_distribution.get)
        yes_cluster = str(candidates_by_id.get(yes_top, {}).get("cluster", "unknown"))
        no_cluster = str(candidates_by_id.get(no_top, {}).get("cluster", "unknown"))
        if yes_cluster == no_cluster:
            return 0.2
        return 1.0

    @classmethod
    def _rank_questions_by_deig(
        cls,
        *,
        questions: list[dict[str, str]],
        posterior: dict[str, float],
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        entropy_before = cls._entropy(posterior)
        concentration = cls._simpson_diversity(posterior)
        alpha = cls._WEIGHTS["alpha"]
        beta = cls._WEIGHTS["beta"]
        gamma = cls._WEIGHTS["gamma"]

        ranked: list[dict[str, Any]] = []
        for question in questions:
            feature = str(question["feature"])
            yes_distribution = cls._hypothetical_update(
                current_posterior=posterior,
                candidates=candidates,
                feature=feature,
                answer_yes=True,
            )
            no_distribution = cls._hypothetical_update(
                current_posterior=posterior,
                candidates=candidates,
                feature=feature,
                answer_yes=False,
            )
            expected_entropy = 0.5 * cls._entropy(yes_distribution) + 0.5 * cls._entropy(
                no_distribution
            )
            info_gain = max(0.0, entropy_before - expected_entropy)
            divergence = cls._semantic_divergence(
                yes_distribution=yes_distribution,
                no_distribution=no_distribution,
                candidates=candidates,
            )
            deig = alpha * info_gain + beta * divergence + gamma * concentration
            ranked.append(
                {
                    **question,
                    "deig": round(deig, 4),
                    "ig": round(info_gain, 4),
                    "div": round(divergence, 4),
                    "con": round(concentration, 4),
                }
            )

        ranked.sort(
            key=lambda item: (float(item["deig"]), item.get("type") == "discriminator"),
            reverse=True,
        )
        return ranked

    @classmethod
    def _extract_asked_features_from_history(cls, recent_messages: list[Any]) -> set[str]:
        asked: set[str] = set()
        for message in recent_messages:
            for fact in list(getattr(message, "extracted_facts", []) or []):
                normalized_fact = cls._normalize(str(fact))
                if normalized_fact.startswith("clarify_question:"):
                    asked.add(normalized_fact.split("clarify_question:", 1)[1].strip())
        return asked

    @classmethod
    def propose_next_question(
        cls,
        *,
        query: str,
        effective_specialty: str,
        matched_domains: list[str],
        extracted_facts: list[str],
        memory_facts_used: list[str],
        patient_history_facts_used: list[str],
        recent_messages: list[Any],
        max_turns: int,
        confidence_threshold: float,
    ) -> dict[str, Any]:
        specialty = cls._normalize(effective_specialty)
        domain = specialty if specialty in cls._DOMAIN_PROFILES else ""
        if not domain:
            for domain_candidate in matched_domains:
                normalized_candidate = cls._normalize(domain_candidate)
                if normalized_candidate in cls._DOMAIN_PROFILES:
                    domain = normalized_candidate
                    break
        if not domain:
            return {"should_ask": False, "reason": "domain_not_supported"}

        profile = cls._DOMAIN_PROFILES[domain]
        asked_features = cls._extract_asked_features_from_history(recent_messages)
        observed_features = cls._extract_observed_features(
            query=query,
            profile=profile,
            memory_facts_used=memory_facts_used,
            patient_history_facts_used=patient_history_facts_used,
            extracted_facts=extracted_facts,
        )
        posterior = cls._build_posterior(
            candidates=list(profile["candidates"]),
            observed_features=observed_features,
        )
        (top_id, top_probability), second = cls._top_two(posterior)
        top_gap = float(top_probability - (second[1] if second else 0.0))
        turns_used = len(asked_features)

        if turns_used >= max_turns:
            return {
                "should_ask": False,
                "reason": "max_turns_reached",
                "top_candidate": top_id,
                "top_probability": round(top_probability, 4),
            }

        if top_probability >= confidence_threshold or top_gap >= 0.35:
            return {
                "should_ask": False,
                "reason": "confidence_sufficient",
                "top_candidate": top_id,
                "top_probability": round(top_probability, 4),
                "top_gap": round(top_gap, 4),
            }

        candidate_questions: list[dict[str, str]] = []
        for question in list(profile.get("question_bank", [])):
            feature = cls._normalize(str(question.get("feature", "")))
            if not feature:
                continue
            if feature in observed_features or feature in asked_features:
                continue
            candidate_questions.append(question)

        if not candidate_questions:
            return {
                "should_ask": False,
                "reason": "no_informative_question",
                "top_candidate": top_id,
                "top_probability": round(top_probability, 4),
            }

        ranked = cls._rank_questions_by_deig(
            questions=candidate_questions,
            posterior=posterior,
            candidates=list(profile["candidates"]),
        )
        best = ranked[0]
        entropy_before = cls._entropy(posterior)
        expected_entropy_after = max(0.0, entropy_before - float(best["ig"]))

        return {
            "should_ask": True,
            "domain": domain,
            "question": str(best["text"]),
            "question_feature": str(best["feature"]),
            "question_type": str(best.get("type") or "discriminator"),
            "turn_index": turns_used + 1,
            "max_turns": max_turns,
            "top_candidate": top_id,
            "top_probability": round(top_probability, 4),
            "top_gap": round(top_gap, 4),
            "entropy_before": round(entropy_before, 4),
            "expected_entropy_after": round(expected_entropy_after, 4),
            "deig_score": float(best["deig"]),
            "ig": float(best["ig"]),
            "div": float(best["div"]),
            "con": float(best["con"]),
            "posterior_topk": [
                {"candidate_id": candidate_id, "probability": round(probability, 4)}
                for candidate_id, probability in sorted(
                    posterior.items(), key=lambda item: item[1], reverse=True
                )[:5]
            ],
            "reason": "need_clarifying_data",
        }
