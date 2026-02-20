"""
Integracion opcional de NeMo Guardrails para salida de chat clinico.

Funciona en modo fail-safe: si guardrails no esta disponible, el flujo
puede continuar con la respuesta original segun configuracion.
"""
from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

from app.core.config import settings


class NeMoGuardrailsService:
    """Aplica validacion/reescritura de respuesta con NeMo Guardrails."""

    _rails_cache: dict[str, Any] = {}

    @classmethod
    def apply_output_guardrails(
        cls,
        *,
        query: str,
        answer: str,
        response_mode: str,
        effective_specialty: str,
        tool_mode: str,
        knowledge_sources: list[dict[str, str]],
        web_sources: list[dict[str, str]],
    ) -> tuple[str, dict[str, str]]:
        if not settings.CLINICAL_CHAT_GUARDRAILS_ENABLED:
            return answer, {"guardrails_status": "skipped_disabled"}
        if not answer.strip():
            return answer, {"guardrails_status": "skipped_empty_answer"}

        rails, load_trace = cls._load_rails()
        if rails is None:
            trace = {"guardrails_status": "fallback_unavailable"}
            trace.update(load_trace)
            return cls._handle_fail_open(answer=answer, trace=trace)

        prompt = cls._build_guardrails_prompt(
            query=query,
            answer=answer,
            response_mode=response_mode,
            effective_specialty=effective_specialty,
            tool_mode=tool_mode,
            knowledge_sources=knowledge_sources,
            web_sources=web_sources,
        )
        started_at = time.perf_counter()
        try:
            raw_result = cls._run_rails_generation(rails, prompt)
            guarded_answer = cls._extract_text(raw_result).strip()
            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            if not guarded_answer:
                trace = {
                    "guardrails_status": "fallback_empty_response",
                    "guardrails_latency_ms": str(latency_ms),
                }
                trace.update(load_trace)
                return cls._handle_fail_open(answer=answer, trace=trace)
            status = "applied_rewrite" if guarded_answer != answer else "applied_passthrough"
            trace = {
                "guardrails_status": status,
                "guardrails_latency_ms": str(latency_ms),
            }
            trace.update(load_trace)
            return guarded_answer, trace
        except Exception as exc:  # pragma: no cover - defensivo
            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            trace = {
                "guardrails_status": "fallback_exception",
                "guardrails_error": exc.__class__.__name__,
                "guardrails_latency_ms": str(latency_ms),
            }
            trace.update(load_trace)
            return cls._handle_fail_open(answer=answer, trace=trace)

    @classmethod
    def _handle_fail_open(cls, *, answer: str, trace: dict[str, str]) -> tuple[str, dict[str, str]]:
        if settings.CLINICAL_CHAT_GUARDRAILS_FAIL_OPEN:
            trace["guardrails_fail_mode"] = "open"
            return answer, trace
        trace["guardrails_fail_mode"] = "closed"
        return (
            "No pude validar la seguridad de la respuesta. "
            "Reintenta o escala a revision clinica humana.",
            trace,
        )

    @classmethod
    def _load_rails(cls) -> tuple[Any | None, dict[str, str]]:
        config_path = cls._resolve_config_path(settings.CLINICAL_CHAT_GUARDRAILS_CONFIG_PATH)
        trace = {"guardrails_config_path": str(config_path)}
        if not config_path.exists():
            trace["guardrails_error"] = "config_path_missing"
            return None, trace
        if not config_path.is_dir():
            trace["guardrails_error"] = "config_path_not_dir"
            return None, trace

        cache_key = str(config_path)
        cached = cls._rails_cache.get(cache_key)
        if cached is not None:
            trace["guardrails_loaded"] = "cache"
            return cached, trace

        try:
            from nemoguardrails import LLMRails, RailsConfig
        except Exception as exc:  # pragma: no cover - depende de extras opcionales
            trace["guardrails_error"] = exc.__class__.__name__
            return None, trace

        try:
            config = RailsConfig.from_path(cache_key)
            rails = LLMRails(config)
            cls._rails_cache[cache_key] = rails
            trace["guardrails_loaded"] = "fresh"
            return rails, trace
        except Exception as exc:  # pragma: no cover - defensivo
            trace["guardrails_error"] = exc.__class__.__name__
            return None, trace

    @staticmethod
    def _resolve_config_path(raw_path: str) -> Path:
        path = Path(raw_path)
        if path.is_absolute():
            return path
        project_root = Path(__file__).resolve().parents[2]
        return project_root / path

    @staticmethod
    def _run_rails_generation(rails: Any, prompt: str) -> Any:
        try:
            result = rails.generate(messages=[{"role": "user", "content": prompt}])
        except TypeError:
            result = rails.generate(prompt=prompt)
        if asyncio.iscoroutine(result):
            try:
                return asyncio.run(result)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                try:
                    return loop.run_until_complete(result)
                finally:
                    loop.close()
        return result

    @staticmethod
    def _extract_text(payload: Any) -> str:
        if payload is None:
            return ""
        if isinstance(payload, str):
            return payload
        if isinstance(payload, dict):
            direct_keys = ("content", "bot_response", "response", "output", "text")
            for key in direct_keys:
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value
            messages = payload.get("messages")
            if isinstance(messages, list):
                for message in reversed(messages):
                    if isinstance(message, dict):
                        content = message.get("content")
                        role = str(message.get("role") or "").lower()
                        if (
                            isinstance(content, str)
                            and content.strip()
                            and role in {"assistant", "bot"}
                        ):
                            return content
        if isinstance(payload, list):
            for item in reversed(payload):
                text = NeMoGuardrailsService._extract_text(item)
                if text:
                    return text
        return str(payload)

    @staticmethod
    def _compact_sources(sources: list[dict[str, str]], limit: int = 3) -> str:
        if not sources:
            return "- sin fuentes"
        lines: list[str] = []
        for source in sources[:limit]:
            title = str(source.get("title") or source.get("source") or "fuente")
            locator = str(source.get("source") or source.get("url") or "")
            lines.append(f"- {title} ({locator})")
        return "\n".join(lines)

    @staticmethod
    def _build_guardrails_prompt(
        *,
        query: str,
        answer: str,
        response_mode: str,
        effective_specialty: str,
        tool_mode: str,
        knowledge_sources: list[dict[str, str]],
        web_sources: list[dict[str, str]],
    ) -> str:
        return "\n".join(
            [
                "Evalua y corrige, solo si es necesario, la respuesta clinico-operativa propuesta.",
                "Reglas obligatorias:",
                "1) Mantener tono profesional, claro y accionable.",
                "2) No inventar datos ni afirmar certezas no sustentadas.",
                "3) No dar diagnostico definitivo; incluir verificacion clinica humana.",
                "4) Mantener coherencia con la consulta del profesional.",
                "Si la respuesta ya cumple, devuelvela sin cambios.",
                f"Modo: {response_mode}",
                f"Especialidad activa: {effective_specialty}",
                f"Herramienta activa: {tool_mode}",
                "Consulta del profesional:",
                query,
                "Respuesta propuesta:",
                answer,
                "Fuentes internas disponibles:",
                NeMoGuardrailsService._compact_sources(knowledge_sources),
                "Fuentes web disponibles:",
                NeMoGuardrailsService._compact_sources(web_sources),
                "Devuelve unicamente la respuesta final en espanol, sin JSON ni etiquetas.",
            ]
        )
