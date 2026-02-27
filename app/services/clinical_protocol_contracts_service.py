"""
Contratos operativos clinicos deterministas por dominio.

Objetivo:
- Estandarizar respuesta operativa por especialidad con pasos 0-10 / 10-60.
- Exigir datos minimos para cierre seguro.
- Forzar fallback estructurado cuando hay inconsistencia o evidencia insuficiente.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any


class ClinicalProtocolContractsService:
    """Evaluador de contratos operativos locales (sin dependencias externas)."""

    _K_PATTERN = re.compile(r"\bk\+?\s*[:=]?\s*(\d+(?:[\.,]\d+)?)\b", flags=re.IGNORECASE)
    _TA_PATTERN = re.compile(r"\bta\s*(\d{2,3})\s*/\s*(\d{2,3})\b", flags=re.IGNORECASE)

    _CONTRACTS: dict[str, dict[str, Any]] = {
        "nephrology": {
            "id": "nephrology_hyperkalemia_ops_v1",
            "title": "Contrato operativo nefrologia critica",
            "trigger_terms": ("oliguria", "anuria", "renal", "hiperkalemia", "k ", "k+"),
            "required_data": {
                "ecg_changes": {
                    "label": "ECG inmediato con cambios por hiperkalemia",
                    "keywords": ("ecg", "ondas t", "qrs", "bradiarritmia"),
                },
                "diuresis_quantified": {
                    "label": "Diuresis cuantificada (ml/kg/h)",
                    "keywords": ("diuresis", "ml/kg/h", "anuria", "oliguria"),
                },
                "creatinine_trend": {
                    "label": "Tendencia de creatinina (basal vs actual)",
                    "keywords": ("creatinina", "basal", "fra", "deterioro renal"),
                },
            },
            "steps_0_10": (
                "Monitorizacion continua y ECG inmediato.",
                "Revisar estabilidad hemodinamica y riesgo electrico por hiperkalemia.",
                "Activar circuito de nefrologia critica.",
            ),
            "steps_10_60": (
                "Completar analitica urgente y tendencia renal/electrolitica.",
                "Reevaluacion seriada de ritmo, diuresis y perfusion.",
                "Preparar escalado a soporte avanzado segun respuesta clinica.",
            ),
            "escalation_criteria": (
                "Cambios ECG por hiperkalemia o deterioro hemodinamico.",
                "Anuria persistente o progresion de deterioro renal agudo.",
                "Sospecha de necesidad de terapia de reemplazo renal urgente.",
            ),
            "safety_blockers": (
                "No cerrar plan sin ECG y analitica urgente en hiperkalemia sospechada.",
            ),
        },
        "gynecology_obstetrics": {
            "id": "gyne_obstetric_hypertensive_ops_v1",
            "title": "Contrato operativo gineco-obstetrico hipertensivo",
            "trigger_terms": (
                "gestante",
                "embarazo",
                "obstetric",
                "cefalea",
                "fosfenos",
                "preeclampsia",
                "eclampsia",
            ),
            "required_data": {
                "ta_repeat": {
                    "label": "Doble toma de TA severa en ventana corta",
                    "keywords": ("ta", "hipertension", "160/110"),
                },
                "organ_damage": {
                    "label": "Datos de dano de organo (plaquetas, creatinina, enzimas)",
                    "keywords": ("plaquetas", "creatinina", "transaminasas", "proteinuria"),
                },
                "maternal_fetal_status": {
                    "label": "Estado materno-fetal monitorizado",
                    "keywords": ("monitorizacion", "fetal", "materno"),
                },
            },
            "steps_0_10": (
                "Activar protocolo obstetrico de riesgo hipertensivo.",
                "Monitorizacion materna y fetal continua.",
                "Escalar evaluacion obstetrica prioritaria.",
            ),
            "steps_10_60": (
                "Consolidar analitica de dano de organo y reevaluar TA.",
                "Actualizar riesgo de progresion a eclampsia.",
                "Coordinar circuito de seguridad materno-fetal segun respuesta.",
            ),
            "escalation_criteria": (
                "TA severa persistente o sintomas neurologicos progresivos.",
                "Sospecha de eclampsia inminente o deterioro materno-fetal.",
                "Sangrado activo o inestabilidad hemodinamica.",
            ),
            "safety_blockers": (
                "No cerrar plan sin reevaluacion de TA y dano de organo.",
            ),
        },
    }

    @classmethod
    def _normalize(cls, text: str) -> str:
        lowered = text.lower()
        normalized = unicodedata.normalize("NFD", lowered)
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return re.sub(r"\s+", " ", normalized).strip()

    @classmethod
    def _extract_k(cls, text: str) -> float | None:
        match = cls._K_PATTERN.search(text)
        if not match:
            return None
        return float(match.group(1).replace(",", "."))

    @classmethod
    def _extract_ta(cls, text: str) -> tuple[int, int] | None:
        match = cls._TA_PATTERN.search(text)
        if not match:
            return None
        return int(match.group(1)), int(match.group(2))

    @classmethod
    def _resolve_domain(cls, *, effective_specialty: str, matched_domains: list[str]) -> str | None:
        normalized_specialty = cls._normalize(effective_specialty)
        if normalized_specialty in cls._CONTRACTS:
            return normalized_specialty
        for domain in matched_domains:
            normalized = cls._normalize(domain)
            if normalized in cls._CONTRACTS:
                return normalized
        return None

    @classmethod
    def _has_any_term(cls, normalized_blob: str, terms: tuple[str, ...]) -> bool:
        return any(cls._normalize(term) in normalized_blob for term in terms)

    @classmethod
    def evaluate(
        cls,
        *,
        query: str,
        effective_specialty: str,
        matched_domains: list[str],
        extracted_facts: list[str],
        memory_facts_used: list[str],
        logic_assessment: dict[str, Any] | None,
    ) -> dict[str, Any]:
        domain = cls._resolve_domain(
            effective_specialty=effective_specialty,
            matched_domains=matched_domains,
        )
        if not domain:
            return {
                "contract_applied": False,
                "trace": {
                    "contract_enabled": "0",
                    "contract_domain": "none",
                    "contract_id": "none",
                    "contract_state": "not_applicable",
                    "contract_has_trigger": "0",
                    "contract_missing_data_count": "0",
                    "contract_force_fallback": "0",
                },
            }

        contract = cls._CONTRACTS[domain]
        normalized_query = cls._normalize(query)
        normalized_facts = cls._normalize(" ".join([*extracted_facts, *memory_facts_used]))
        normalized_blob = f"{normalized_query} {normalized_facts}".strip()

        trigger_terms = tuple(str(item) for item in contract.get("trigger_terms", ()))
        has_trigger = cls._has_any_term(normalized_blob, trigger_terms)

        missing_data: list[str] = []
        required_data = dict(contract.get("required_data", {}))
        for rule in required_data.values():
            label = str(rule.get("label") or "dato requerido")
            keywords = tuple(str(item) for item in rule.get("keywords", ()))
            if not cls._has_any_term(normalized_blob, keywords):
                missing_data.append(label)

        if domain == "nephrology":
            k_value = cls._extract_k(query)
            if k_value is not None and k_value >= 6.0:
                has_trigger = True
        if domain == "gynecology_obstetrics":
            ta = cls._extract_ta(query)
            if ta is not None and ta[0] >= 160 and ta[1] >= 110:
                has_trigger = True

        logic_contradictions = len((logic_assessment or {}).get("contradictions", []))
        logic_inconsistent = (
            str((logic_assessment or {}).get("consistency_status") or "consistent")
            == "inconsistent"
        )

        state = "ready"
        force_fallback = False
        if logic_contradictions > 0 or logic_inconsistent:
            state = "blocked_contradiction"
            force_fallback = True
        elif missing_data and has_trigger:
            state = "needs_data"
            force_fallback = True
        elif missing_data and not has_trigger:
            state = "partial"
            force_fallback = False

        return {
            "contract_applied": True,
            "contract_domain": domain,
            "contract_id": str(contract["id"]),
            "contract_title": str(contract["title"]),
            "contract_state": state,
            "has_trigger": has_trigger,
            "force_structured_fallback": force_fallback,
            "missing_data": missing_data[:5],
            "steps_0_10": [str(item) for item in contract.get("steps_0_10", ())][:6],
            "steps_10_60": [str(item) for item in contract.get("steps_10_60", ())][:6],
            "escalation_criteria": [
                str(item) for item in contract.get("escalation_criteria", ())
            ][:6],
            "safety_blockers": [str(item) for item in contract.get("safety_blockers", ())][:4],
            "trace": {
                "contract_enabled": "1",
                "contract_domain": domain,
                "contract_id": str(contract["id"]),
                "contract_state": state,
                "contract_has_trigger": "1" if has_trigger else "0",
                "contract_missing_data_count": str(len(missing_data)),
                "contract_force_fallback": "1" if force_fallback else "0",
            },
        }
