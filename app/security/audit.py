"""Security audit findings for chat turns."""

from __future__ import annotations

from dataclasses import dataclass

from app.security.dangerous_tools import ToolRiskAssessment


@dataclass(frozen=True)
class SecurityFinding:
    """A single actionable audit finding."""

    code: str
    severity: str
    message: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "remediation": self.remediation,
        }


def audit_chat_security(
    *,
    prompt_injection_signals: list[str],
    risk: ToolRiskAssessment,
    tool_policy_allowed: bool,
    tool_policy_reason: str,
    response_mode: str,
    internal_sources_count: int,
    validated_sources_required: bool,
    use_web_sources: bool,
) -> list[SecurityFinding]:
    """Produce security findings for one chat turn."""
    findings: list[SecurityFinding] = []

    if prompt_injection_signals:
        findings.append(
            SecurityFinding(
                code="prompt_injection_signal",
                severity="critical" if risk.is_dangerous else "warn",
                message=(
                    "Prompt injection signals detected in user content: "
                    + ", ".join(prompt_injection_signals[:4])
                ),
                remediation=(
                    "Keep strict delimiters, avoid auto-escalation, and require "
                    "human validation before executing risky actions."
                ),
            )
        )

    if risk.is_dangerous and not tool_policy_allowed:
        findings.append(
            SecurityFinding(
                code="dangerous_tool_blocked",
                severity="info",
                message=(
                    f"Tool '{risk.tool_mode}' was blocked by policy "
                    f"(reason={tool_policy_reason or 'policy'})."
                ),
                remediation=(
                    "Use safer mode ('chat' or 'cases') or adjust policy " "with explicit approval."
                ),
            )
        )
    elif risk.is_dangerous and tool_policy_allowed:
        findings.append(
            SecurityFinding(
                code="dangerous_tool_allowed",
                severity="warn" if risk.risk_level == "high" else "info",
                message=(f"Risky tool '{risk.tool_mode}' allowed under " "current context."),
                remediation=(
                    "Review output with clinician-in-the-loop and verify "
                    "protocol before operational use."
                ),
            )
        )

    if response_mode == "clinical" and validated_sources_required and internal_sources_count == 0:
        findings.append(
            SecurityFinding(
                code="missing_validated_internal_sources",
                severity="critical",
                message=("Clinical response has no validated internal source " "evidence."),
                remediation=(
                    "Escalate for professional review and curate validated " "internal knowledge."
                ),
            )
        )

    if use_web_sources:
        findings.append(
            SecurityFinding(
                code="web_sources_used",
                severity="info",
                message="Web sources were enabled for this turn.",
                remediation=(
                    "Confirm domains are whitelisted and cross-check " "with internal protocols."
                ),
            )
        )

    if not findings:
        findings.append(
            SecurityFinding(
                code="security_baseline_ok",
                severity="info",
                message="No relevant chat security findings in this turn.",
                remediation=("Continue monitoring traces and periodic policy audit."),
            )
        )

    return findings
