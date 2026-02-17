"""Dangerous tool catalog and risk assessment helpers."""

from __future__ import annotations

from dataclasses import dataclass

TOOL_GROUPS: dict[str, set[str]] = {
    "conversation": {"chat", "cases"},
    "clinical_actions": {"medication", "treatment"},
    "external_network": {"deep_search"},
    "sensitive_media": {"images"},
}
TOOL_GROUPS["dangerous"] = (
    TOOL_GROUPS["clinical_actions"]
    | TOOL_GROUPS["external_network"]
    | TOOL_GROUPS["sensitive_media"]
)
TOOL_GROUPS["all"] = set().union(*TOOL_GROUPS.values())


@dataclass(frozen=True)
class ToolRiskAssessment:
    """Risk snapshot for a selected tool mode."""

    tool_mode: str
    is_dangerous: bool
    risk_level: str
    categories: list[str]
    reasons: list[str]


def assess_tool_risk(
    *,
    tool_mode: str,
    response_mode: str,
    prompt_injection_detected: bool,
    use_web_sources: bool,
) -> ToolRiskAssessment:
    """Assess risk for the requested tool based on context."""
    categories: list[str] = []
    reasons: list[str] = []
    mode = (tool_mode or "").strip().lower()

    if mode in TOOL_GROUPS["clinical_actions"]:
        categories.append("clinical_actions")
        reasons.append("may_suggest_mutable_clinical_actions")
    if mode in TOOL_GROUPS["external_network"]:
        categories.append("external_network")
        reasons.append("may_trigger_external_network_lookup")
    if mode in TOOL_GROUPS["sensitive_media"]:
        categories.append("sensitive_media")
        reasons.append("may_handle_sensitive_media_context")

    risk_level = "low"
    if categories:
        risk_level = "medium"
    if mode in TOOL_GROUPS["clinical_actions"] and response_mode == "clinical":
        risk_level = "high"
    if mode in TOOL_GROUPS["external_network"] and use_web_sources:
        risk_level = "high"
    if prompt_injection_detected and categories:
        risk_level = "critical"
        reasons.append("prompt_injection_signal_present")

    return ToolRiskAssessment(
        tool_mode=mode,
        is_dangerous=mode in TOOL_GROUPS["dangerous"],
        risk_level=risk_level,
        categories=categories,
        reasons=reasons,
    )
