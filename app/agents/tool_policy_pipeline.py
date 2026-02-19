"""Layered tool policy pipeline with allow/deny rules and group expansion."""

from __future__ import annotations

from dataclasses import dataclass

from app.security.dangerous_tools import TOOL_GROUPS


@dataclass(frozen=True)
class ToolPolicyLayer:
    """One policy layer that contributes allow/deny rules."""

    name: str
    allow_tools: set[str]
    deny_tools: set[str]
    allow_groups: set[str]
    deny_groups: set[str]


@dataclass(frozen=True)
class ToolPolicyContext:
    """Inputs required to evaluate a tool policy decision."""

    requested_tool_mode: str
    response_mode: str
    user_is_superuser: bool
    prompt_injection_detected: bool
    human_review_required: bool
    use_web_sources: bool
    include_protocol_catalog: bool


@dataclass(frozen=True)
class ToolPolicyDecision:
    """Result of the layered policy evaluation."""

    requested_tool_mode: str
    effective_tool_mode: str
    allowed: bool
    reason_code: str
    trace: list[str]
    allowlist: list[str]
    denylist: list[str]


class ToolPolicyPipeline:
    """Resolves effective tool mode through layered policies."""

    @staticmethod
    def _expand_groups(groups: set[str]) -> set[str]:
        expanded: set[str] = set()
        for group in groups:
            expanded.update(TOOL_GROUPS.get(group, set()))
        return expanded

    @classmethod
    def _build_layers(cls, ctx: ToolPolicyContext) -> list[ToolPolicyLayer]:
        layers: list[ToolPolicyLayer] = [
            ToolPolicyLayer(
                name="global",
                allow_tools={"chat", "cases"},
                deny_tools=set(),
                allow_groups=set(),
                deny_groups={"dangerous"},
            ),
        ]

        if ctx.user_is_superuser:
            layers.append(
                ToolPolicyLayer(
                    name="profile:superuser",
                    allow_tools=set(),
                    deny_tools=set(),
                    allow_groups={"all"},
                    deny_groups=set(),
                )
            )
        else:
            allow_groups: set[str] = set()
            if ctx.response_mode == "clinical":
                allow_groups.update({"clinical_actions", "sensitive_media"})
            if ctx.use_web_sources:
                allow_groups.add("external_network")
            layers.append(
                ToolPolicyLayer(
                    name="profile:clinician",
                    allow_tools=set(),
                    deny_tools=set(),
                    allow_groups=allow_groups,
                    deny_groups=set(),
                )
            )

        if not ctx.human_review_required:
            layers.append(
                ToolPolicyLayer(
                    name="context:no_human_review",
                    allow_tools=set(),
                    deny_tools=set(),
                    allow_groups=set(),
                    deny_groups={"clinical_actions"},
                )
            )
        if not ctx.include_protocol_catalog:
            layers.append(
                ToolPolicyLayer(
                    name="agent:catalog_disabled",
                    allow_tools=set(),
                    deny_tools={"treatment"},
                    allow_groups=set(),
                    deny_groups=set(),
                )
            )
        if ctx.prompt_injection_detected:
            layers.append(
                ToolPolicyLayer(
                    name="context:prompt_injection",
                    allow_tools=set(),
                    deny_tools=set(),
                    allow_groups=set(),
                    deny_groups={"dangerous"},
                )
            )
        return layers

    @classmethod
    def evaluate(cls, ctx: ToolPolicyContext) -> ToolPolicyDecision:
        requested = (ctx.requested_tool_mode or "chat").strip().lower()
        allowset: set[str] = set()
        denyset: set[str] = set()
        trace: list[str] = []

        for layer in cls._build_layers(ctx):
            layer_allow = set(layer.allow_tools) | cls._expand_groups(layer.allow_groups)
            layer_deny = set(layer.deny_tools) | cls._expand_groups(layer.deny_groups)
            # Regla de precedencia por capas:
            # - un allow explicito en capa posterior puede levantar un deny previo
            # - un deny explicito en capa posterior vuelve a bloquear la herramienta
            allowset.update(layer_allow)
            allowset.difference_update(layer_deny)
            denyset.update(layer_deny)
            denyset.difference_update(layer_allow)
            trace.append(
                f"tool_policy_layer={layer.name};"
                f"allow={','.join(sorted(layer_allow)) or 'none'};"
                f"deny={','.join(sorted(layer_deny)) or 'none'}"
            )

        if requested not in TOOL_GROUPS["all"]:
            return ToolPolicyDecision(
                requested_tool_mode=requested,
                effective_tool_mode="chat",
                allowed=False,
                reason_code="unknown_tool_mode",
                trace=[*trace, f"tool_policy_decision=deny_unknown:{requested}"],
                allowlist=sorted(allowset),
                denylist=sorted(denyset),
            )

        allowed = requested in allowset and requested not in denyset
        if allowed:
            reason = "allowed_by_policy"
            effective = requested
        elif requested in denyset:
            reason = "denied_by_policy"
            effective = "chat"
        else:
            reason = "denied_by_default"
            effective = "chat"

        trace.append(
            f"tool_policy_decision={'allow' if allowed else 'deny'};"
            f"requested={requested};effective={effective};reason={reason}"
        )
        return ToolPolicyDecision(
            requested_tool_mode=requested,
            effective_tool_mode=effective,
            allowed=allowed,
            reason_code=reason,
            trace=trace,
            allowlist=sorted(allowset),
            denylist=sorted(denyset),
        )
