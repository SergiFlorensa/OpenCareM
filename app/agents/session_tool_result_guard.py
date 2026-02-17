"""Guards tool results before adding them to chat memory/transcript."""

from __future__ import annotations

import json
from typing import Any


class SessionToolResultGuard:
    """Sanitizes and limits tool results for persistence and display."""

    @staticmethod
    def _compact_text(value: Any, *, max_chars: int) -> str:
        text = str(value or "").strip()
        text = " ".join(text.split())
        return text[:max_chars]

    @staticmethod
    def _compact_recommendation(
        payload: Any,
        *,
        max_chars: int = 600,
    ) -> dict[str, Any]:
        if not isinstance(payload, dict):
            return {}
        compact: dict[str, Any] = {}
        for key, value in payload.items():
            safe_key = SessionToolResultGuard._compact_text(key, max_chars=80)
            if isinstance(value, list):
                compact[safe_key] = [
                    SessionToolResultGuard._compact_text(item, max_chars=140) for item in value[:5]
                ]
                continue
            if isinstance(value, dict):
                compact[safe_key] = {
                    SessionToolResultGuard._compact_text(
                        k, max_chars=60
                    ): SessionToolResultGuard._compact_text(
                        v,
                        max_chars=140,
                    )
                    for k, v in list(value.items())[:5]
                }
                continue
            compact[safe_key] = SessionToolResultGuard._compact_text(value, max_chars=180)
        raw = json.dumps(compact, ensure_ascii=False)
        if len(raw) <= max_chars:
            return compact
        return {"summary": raw[:max_chars]}

    @staticmethod
    def sanitize(
        results: list[dict[str, Any]],
        *,
        max_items: int = 4,
        max_snippet_chars: int = 280,
    ) -> list[dict[str, Any]]:
        """Return bounded, consistent tool results."""
        safe_results: list[dict[str, Any]] = []
        for item in results[: max(1, max_items)]:
            endpoint = SessionToolResultGuard._compact_text(item.get("endpoint"), max_chars=160)
            title = SessionToolResultGuard._compact_text(
                item.get("title") or "Recomendacion interna",
                max_chars=120,
            )
            snippet = SessionToolResultGuard._compact_text(
                item.get("snippet"),
                max_chars=max_snippet_chars,
            )
            recommendation = SessionToolResultGuard._compact_recommendation(
                item.get("recommendation"),
            )
            safe_results.append(
                {
                    "type": "internal_recommendation",
                    "endpoint": endpoint,
                    "title": title,
                    "source": endpoint or "internal",
                    "snippet": snippet,
                    "recommendation": recommendation,
                }
            )
        return safe_results
