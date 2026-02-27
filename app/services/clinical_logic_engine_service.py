"""
Motor logico clinico determinista para reforzar seguridad y trazabilidad.

Implementa reglas estilo secuente (premisas -> acciones), detector basico de
contradicciones y resumen de estado epistemico (confirmado/reportado/inferido).
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any


class ClinicalLogicEngineService:
    """Evaluador logico local, sin dependencias externas."""

    _MAX_STRUCTURAL_STEPS = 8
    _MAX_STEP_VALUE = 32
    _MAX_GODEL_DIGITS = 150
    _PRIMES: tuple[int, ...] = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29)

    _RULES: list[dict[str, Any]] = [
        {
            "id": "nephro_hyperkalemia_critical",
            "domains": {"nephrology", "critical_ops"},
            "requires_any": {"oliguria", "anuria"},
            "condition": "k_ge_6",
            "priority": "critical",
            "actions": [
                "Activar ruta nefrologia critica.",
                "Solicitar ECG inmediato y monitorizacion continua.",
                "Escalar valoracion medica prioritaria por hiperkalemia.",
            ],
        },
        {
            "id": "obstetric_htn_severe",
            "domains": {"gynecology_obstetrics", "critical_ops"},
            "requires_any": {"cefalea", "fosfenos"},
            "condition": "ta_ge_160_110",
            "priority": "critical",
            "actions": [
                "Activar protocolo obstetrico de hipertension severa.",
                "Monitorizacion materno-fetal intensiva.",
                "Escalar equipo obstetrico de forma inmediata.",
            ],
        },
        {
            "id": "sepsis_shock_operational",
            "domains": {"sepsis", "critical_ops"},
            "requires_any": {"sepsis", "shock", "lactato"},
            "condition": "shock_or_hypotension",
            "priority": "high",
            "actions": [
                "Activar bundle operativo de sepsis (0-60 min).",
                "Control hemodinamico y reevaluacion seriada.",
            ],
        },
        {
            "id": "oncology_neutropenia_fever",
            "domains": {"oncology"},
            "requires_all": {"neutropenia", "fiebre"},
            "priority": "high",
            "actions": [
                "Activar ruta de neutropenia febril oncologica.",
                "Escalar evaluacion infecciosa y aislamiento segun protocolo.",
            ],
        },
        {
            "id": "pediatrics_measles_isolation",
            "domains": {"pediatrics_neonatology"},
            "requires_all": {"sarampion", "fiebre"},
            "priority": "high",
            "actions": [
                "Activar aislamiento respiratorio pediatrico.",
                "Escalar circuito de vigilancia epidemiologica.",
            ],
        },
    ]

    _CONTRADICTIONS: list[tuple[str, str, str]] = [
        ("sin fiebre", "fiebre", "Posible contradiccion: se reporta fiebre y ausencia de fiebre."),
        ("sin dolor", "dolor", "Posible contradiccion: se reporta dolor y ausencia de dolor."),
        (
            "sin sangrado",
            "sangrado",
            "Posible contradiccion: se reporta sangrado y ausencia de sangrado.",
        ),
        ("sin disnea", "disnea", "Posible contradiccion: se reporta disnea y ausencia de disnea."),
    ]

    _K_PATTERN = re.compile(r"\bk\+?\s*[:=]?\s*(\d+(?:[\.,]\d+)?)\b", flags=re.IGNORECASE)
    _TA_PATTERN = re.compile(r"\bta\s*(\d{2,3})\s*/\s*(\d{2,3})\b", flags=re.IGNORECASE)

    @classmethod
    def _normalize(cls, text: str) -> str:
        lowered = text.lower()
        normalized = unicodedata.normalize("NFD", lowered)
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return re.sub(r"\s+", " ", normalized).strip()

    @classmethod
    def _extract_k(cls, query: str) -> float | None:
        match = cls._K_PATTERN.search(query)
        if not match:
            return None
        return float(match.group(1).replace(",", "."))

    @classmethod
    def _extract_ta(cls, query: str) -> tuple[int, int] | None:
        match = cls._TA_PATTERN.search(query)
        if not match:
            return None
        return int(match.group(1)), int(match.group(2))

    @classmethod
    def _bounded_min_index(
        cls,
        *,
        values: list[str],
        max_index: int,
        predicate: Any,
    ) -> int | None:
        """Minimizacion acotada: retorna el primer indice que cumple predicado."""
        upper = min(len(values), max(0, max_index))
        for idx in range(upper):
            item = str(values[idx])
            if bool(predicate(item)):
                return idx
        return None

    @classmethod
    def _encode_godel_sequence(cls, sequence: list[int]) -> str | None:
        """Arithmetizacion acotada de una secuencia de enteros."""
        if not sequence:
            return None
        bounded = [
            min(cls._MAX_STEP_VALUE, max(0, int(value)))
            for value in sequence[: cls._MAX_STRUCTURAL_STEPS]
        ]
        code = 1
        for idx, value in enumerate(bounded):
            prime = cls._PRIMES[idx]
            code *= prime ** (value + 1)
            if len(str(code)) > cls._MAX_GODEL_DIGITS:
                return None
        return str(code)

    @classmethod
    def _decode_godel_sequence(cls, code: str, *, max_len: int | None = None) -> list[int]:
        """Decodifica secuencia desde codigo de Godel acotado."""
        if not code or not code.isdigit():
            return []
        remaining = int(code)
        if remaining <= 0:
            return []
        decoded: list[int] = []
        limit = min(
            len(cls._PRIMES),
            max_len if max_len is not None else cls._MAX_STRUCTURAL_STEPS,
        )
        for idx in range(limit):
            prime = cls._PRIMES[idx]
            exponent = 0
            while remaining % prime == 0:
                remaining //= prime
                exponent += 1
                if exponent > (cls._MAX_STEP_VALUE + 6):
                    break
            if exponent == 0:
                break
            decoded.append(max(0, exponent - 1))
        return decoded

    @staticmethod
    def _beta_function(*, d0: int, d1: int, i: int) -> int:
        """Funcion beta simplificada para huella estructural."""
        safe_d0 = max(2, int(d0))
        safe_d1 = max(0, int(d1))
        safe_i = max(0, int(i))
        return (1 + (safe_i + 1) * safe_d1) % safe_d0

    @classmethod
    def _count_clinical_evidence_items(
        cls,
        *,
        normalized_query: str,
        extracted_facts: list[str],
        memory_facts_used: list[str],
    ) -> int:
        signal_tokens = (
            "ta",
            "k ",
            "k+",
            "lactato",
            "shock",
            "fiebre",
            "dolor",
            "sangrado",
            "oliguria",
            "anuria",
            "disnea",
            "cefalea",
            "fosfenos",
            "neutropenia",
            "sarampion",
        )
        score = 0
        for token in signal_tokens:
            if token in normalized_query:
                score += 1
        for fact in [*extracted_facts, *memory_facts_used]:
            if fact.startswith(("termino:", "unit:", "comparator:", "logic_rule:", "risk_level:")):
                score += 1
        return score

    @classmethod
    def _resolve_consistency_status(
        cls,
        *,
        contradictions: list[str],
        triggered_rules: list[dict[str, Any]],
        evidence_items: int,
    ) -> tuple[str, bool, str]:
        if contradictions:
            return "inconsistent", True, "contradictory_input"
        if not triggered_rules and evidence_items < 3:
            return "insufficient_evidence", True, "insufficient_evidence"
        return "consistent", False, "none"

    @classmethod
    def _condition_ok(cls, *, condition: str | None, normalized_query: str, query: str) -> bool:
        if not condition:
            return True
        if condition == "k_ge_6":
            value = cls._extract_k(query)
            return value is not None and value >= 6.0
        if condition == "ta_ge_160_110":
            ta = cls._extract_ta(query)
            return ta is not None and ta[0] >= 160 and ta[1] >= 110
        if condition == "shock_or_hypotension":
            ta = cls._extract_ta(query)
            has_shock = "shock" in normalized_query
            has_low_ta = ta is not None and ta[0] <= 90
            return has_shock or has_low_ta
        return False

    @classmethod
    def analyze_query(
        cls,
        *,
        query: str,
        matched_domains: list[str],
        effective_specialty: str,
        extracted_facts: list[str],
        memory_facts_used: list[str],
    ) -> dict[str, Any]:
        normalized_query = cls._normalize(query)
        active_domains = set(matched_domains)
        active_domains.add(effective_specialty)

        triggered_rules: list[dict[str, Any]] = []
        for rule in cls._RULES:
            rule_domains = set(rule.get("domains", set()))
            if rule_domains and active_domains.isdisjoint(rule_domains):
                continue
            requires_all = {str(x) for x in rule.get("requires_all", set())}
            if requires_all and not all(term in normalized_query for term in requires_all):
                continue
            requires_any = {str(x) for x in rule.get("requires_any", set())}
            if requires_any and not any(term in normalized_query for term in requires_any):
                continue
            if not cls._condition_ok(
                condition=rule.get("condition"),
                normalized_query=normalized_query,
                query=query,
            ):
                continue
            triggered_rules.append(
                {
                    "id": str(rule["id"]),
                    "priority": str(rule["priority"]),
                    "actions": [str(item) for item in rule["actions"]],
                }
            )

        contradictions: list[str] = []
        for left, right, message in cls._CONTRADICTIONS:
            if left in normalized_query and right in normalized_query:
                contradictions.append(message)

        epistemic_facts = []
        for fact in [*extracted_facts, *memory_facts_used]:
            if fact.startswith(("termino:", "unit:", "comparator:")):
                epistemic_facts.append({"status": "reportado", "fact": fact})
            elif fact.startswith(("risk_level:", "risk_frame:", "evidencia_local:")):
                epistemic_facts.append({"status": "inferido", "fact": fact})
            elif fact.startswith(("clarify_question:", "clarify_turn:")):
                epistemic_facts.append({"status": "confirmado", "fact": fact})
            if len(epistemic_facts) >= 8:
                break

        recommended_actions: list[str] = []
        for rule in triggered_rules:
            for action in rule["actions"]:
                if action not in recommended_actions:
                    recommended_actions.append(action)
            if len(recommended_actions) >= 6:
                break

        sequence_ids = [index + 1 for index, _ in enumerate(recommended_actions[:6])]
        godel_code = cls._encode_godel_sequence(sequence_ids)
        godel_roundtrip_ok = False
        decoded_sequence: list[int] = []
        if godel_code:
            decoded_sequence = cls._decode_godel_sequence(
                godel_code, max_len=len(sequence_ids) or cls._MAX_STRUCTURAL_STEPS
            )
            godel_roundtrip_ok = decoded_sequence == sequence_ids
        beta_seed_0 = 97 + len(sequence_ids) * 7
        beta_seed_1 = sum((idx + 1) * value for idx, value in enumerate(sequence_ids))
        beta_signature = (
            "-".join(
                str(cls._beta_function(d0=beta_seed_0, d1=beta_seed_1, i=i))
                for i in range(min(3, len(sequence_ids) or 1))
            )
            if sequence_ids
            else "na"
        )
        first_escalation_index = cls._bounded_min_index(
            values=recommended_actions,
            max_index=6,
            predicate=lambda item: ("escalar" in cls._normalize(item)),
        )
        evidence_items = cls._count_clinical_evidence_items(
            normalized_query=normalized_query,
            extracted_facts=extracted_facts,
            memory_facts_used=memory_facts_used,
        )
        consistency_status, abstention_required, abstention_reason = (
            cls._resolve_consistency_status(
                contradictions=contradictions,
                triggered_rules=triggered_rules,
                evidence_items=evidence_items,
            )
        )

        return {
            "rules_triggered": triggered_rules,
            "recommended_actions": recommended_actions[:6],
            "contradictions": contradictions[:4],
            "epistemic_facts": epistemic_facts,
            "protocol_sequence_ids": sequence_ids,
            "protocol_sequence_code": godel_code,
            "protocol_sequence_roundtrip_ok": godel_roundtrip_ok,
            "protocol_sequence_decoded": decoded_sequence,
            "protocol_beta_signature": beta_signature,
            "first_escalation_step": (
                first_escalation_index + 1 if first_escalation_index is not None else None
            ),
            "consistency_status": consistency_status,
            "abstention_required": abstention_required,
            "abstention_reason": abstention_reason,
            "trace": {
                "logic_enabled": "1",
                "logic_rules_fired": str(len(triggered_rules)),
                "logic_contradictions": str(len(contradictions)),
                "logic_epistemic_facts": str(len(epistemic_facts)),
                "logic_consistency_status": consistency_status,
                "logic_abstention_required": "1" if abstention_required else "0",
                "logic_abstention_reason": abstention_reason,
                "logic_evidence_items": str(evidence_items),
                "logic_structural_steps": str(len(sequence_ids)),
                "logic_godel_code": godel_code or "none",
                "logic_godel_roundtrip": "1" if godel_roundtrip_ok else "0",
                "logic_beta_signature": beta_signature,
                "logic_first_escalation_step": (
                    str(first_escalation_index + 1)
                    if first_escalation_index is not None
                    else "none"
                ),
                "logic_rule_ids": (
                    ",".join(rule["id"] for rule in triggered_rules[:6])
                    if triggered_rules
                    else "none"
                ),
            },
        }
