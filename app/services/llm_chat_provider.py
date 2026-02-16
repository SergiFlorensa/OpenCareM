"""
Proveedor LLM conversacional para chat clinico.

Implementa integracion opcional con Ollama local para mejorar naturalidad,
coherencia y latencia sin dependencias cloud de pago.
"""
from __future__ import annotations

import json
import time
from typing import Any
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from app.core.config import settings


class LLMChatProvider:
    """Genera respuesta conversacional usando modelo local (Ollama)."""

    @staticmethod
    def _compact_sources(sources: list[dict[str, str]], limit: int = 4) -> str:
        if not sources:
            return "- Sin fuentes adicionales"
        lines = []
        for source in sources[:limit]:
            title = source.get("title") or source.get("source") or "fuente"
            location = source.get("url") or source.get("source") or "catalogo"
            snippet = (source.get("snippet") or "").strip()
            line = f"- {title} ({location})"
            if snippet:
                line += f": {snippet[:160]}"
            lines.append(line)
        return "\n".join(lines)

    @staticmethod
    def _build_system_prompt(
        *,
        response_mode: str,
        effective_specialty: str,
        tool_mode: str,
    ) -> str:
        if response_mode == "clinical":
            return (
                "Eres un copiloto clinico-operativo para urgencias. "
                "Responde de forma clara, estructurada y accionable. "
                "No hagas diagnostico definitivo ni sustituyas juicio clinico humano. "
                "Especialidad activa: "
                f"{effective_specialty}. Herramienta activa: {tool_mode}. "
                "Sigue esta secuencia de hilos antes de responder: "
                "1) objetivo clinico, 2) contexto y memoria, 3) evidencia y fuentes, "
                "4) acciones priorizadas, 5) riesgos y verificacion humana."
            )
        return (
            "Eres un asistente conversacional profesional de baja latencia. "
            "Responde natural, directo y util, evitando relleno. "
            "Sigue estos hilos: 1) entender intencion, 2) usar contexto interno validado, "
            "3) responder claro, 4) cerrar con siguiente paso o pregunta de aclaracion. "
            "Si la consulta deriva a clinica, indica que puedes cambiar a modo clinico."
        )

    @staticmethod
    def _build_user_prompt(
        *,
        query: str,
        response_mode: str,
        matched_domains: list[str],
        matched_endpoints: list[str],
        memory_facts_used: list[str],
        patient_summary: dict[str, Any] | None,
        patient_history_facts_used: list[str],
        knowledge_sources: list[dict[str, str]],
        web_sources: list[dict[str, str]],
        recent_dialogue: list[dict[str, str]],
        endpoint_results: list[dict[str, Any]],
    ) -> str:
        lines: list[str] = [
            f"Consulta del profesional: {query}",
            f"Modo de respuesta: {response_mode}",
            "Dominios detectados: "
            + (", ".join(matched_domains) if matched_domains else "ninguno"),
        ]
        if matched_endpoints:
            lines.append("Endpoints operativos sugeridos:")
            for endpoint in matched_endpoints[:4]:
                lines.append(f"- {endpoint}")
        if memory_facts_used:
            lines.append("Memoria de sesion:")
            lines.append("- " + ", ".join(memory_facts_used[:6]))
        if patient_summary is not None and patient_summary.get("patient_interactions_count", 0) > 0:
            lines.append(
                "Contexto longitudinal paciente: "
                f"{patient_summary.get('patient_interactions_count', 0)} interacciones, "
                f"{patient_summary.get('patient_encounters_count', 0)} episodios."
            )
        if patient_history_facts_used:
            lines.append("Hechos longitudinales relevantes:")
            lines.append("- " + ", ".join(patient_history_facts_used[:6]))
        if recent_dialogue:
            lines.append("Dialogo previo de esta sesion:")
            for turn in recent_dialogue[-5:]:
                user_query = (turn.get("user_query") or "").strip()
                assistant_answer = (turn.get("assistant_answer") or "").strip()
                if user_query:
                    lines.append(f"- Profesional: {user_query[:180]}")
                if assistant_answer:
                    lines.append(f"- Copiloto: {assistant_answer[:220]}")
        if endpoint_results:
            lines.append("Resultados operativos reales de endpoints:")
            for result in endpoint_results[:4]:
                endpoint = str(result.get("endpoint") or "endpoint")
                compact_json = json.dumps(result.get("recommendation"), ensure_ascii=False)[:600]
                lines.append(f"- {endpoint}: {compact_json}")
<<<<<<< HEAD
=======
        lines.append(
            "Politica de fuentes: prioriza fuentes internas validadas; "
            "usa web solo como refuerzo en dominios permitidos."
        )
>>>>>>> origin/codex/improve-conversational-feedback-in-chat-wamorb
        lines.append("Fuentes internas:")
        lines.append(LLMChatProvider._compact_sources(knowledge_sources))
        lines.append("Fuentes web:")
        lines.append(LLMChatProvider._compact_sources(web_sources))
        lines.append("Responde en espanol.")
        return "\n".join(lines)

    @staticmethod
    def _request_ollama_json(
        *,
        endpoint: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        request_url = urljoin(settings.CLINICAL_CHAT_LLM_BASE_URL.rstrip("/") + "/", endpoint)
        request = Request(
            url=request_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=settings.CLINICAL_CHAT_LLM_TIMEOUT_SECONDS) as response:
            raw_payload = response.read().decode("utf-8", errors="ignore")
        return LLMChatProvider._parse_ollama_payload(raw_payload)

    @staticmethod
    def _build_chat_messages(
        *,
        system_prompt: str,
        user_prompt: str,
        recent_dialogue: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        for turn in recent_dialogue[-4:]:
            user_query = (turn.get("user_query") or "").strip()
            assistant_answer = (turn.get("assistant_answer") or "").strip()
            if user_query:
                messages.append({"role": "user", "content": user_query[:1200]})
            if assistant_answer:
                messages.append({"role": "assistant", "content": assistant_answer[:1600]})
        messages.append({"role": "user", "content": user_prompt})
        return messages

    @staticmethod
    def generate_answer(
        *,
        query: str,
        response_mode: str,
        effective_specialty: str,
        tool_mode: str,
        matched_domains: list[str],
        matched_endpoints: list[str],
        memory_facts_used: list[str],
        patient_summary: dict[str, Any] | None,
        patient_history_facts_used: list[str],
        knowledge_sources: list[dict[str, str]],
        web_sources: list[dict[str, str]],
        recent_dialogue: list[dict[str, str]],
        endpoint_results: list[dict[str, Any]],
    ) -> tuple[str | None, dict[str, str]]:
        """
        Ejecuta inferencia remota local en Ollama.

        Devuelve `(answer, trace_info)`; `answer=None` cuando falla.
        """
        if not settings.CLINICAL_CHAT_LLM_ENABLED:
            return None, {
                "llm_enabled": "false",
                "llm_used": "false",
                "llm_model": settings.CLINICAL_CHAT_LLM_MODEL,
            }

        started_at = time.perf_counter()
        system_prompt = LLMChatProvider._build_system_prompt(
            response_mode=response_mode,
            effective_specialty=effective_specialty,
            tool_mode=tool_mode,
        )
        user_prompt = LLMChatProvider._build_user_prompt(
            query=query,
            response_mode=response_mode,
            matched_domains=matched_domains,
            matched_endpoints=matched_endpoints,
            memory_facts_used=memory_facts_used,
            patient_summary=patient_summary,
            patient_history_facts_used=patient_history_facts_used,
            knowledge_sources=knowledge_sources,
            web_sources=web_sources,
            recent_dialogue=recent_dialogue,
            endpoint_results=endpoint_results,
        )
        prompt = f"[SYSTEM]\n{system_prompt}\n\n[USER]\n{user_prompt}\n\n[ASSISTANT]\n"
        common_options = {
            "temperature": settings.CLINICAL_CHAT_LLM_TEMPERATURE,
            "num_predict": settings.CLINICAL_CHAT_LLM_MAX_OUTPUT_TOKENS,
            "num_ctx": settings.CLINICAL_CHAT_LLM_NUM_CTX,
            "top_p": settings.CLINICAL_CHAT_LLM_TOP_P,
        }
        chat_payload = {
            "model": settings.CLINICAL_CHAT_LLM_MODEL,
            "messages": LLMChatProvider._build_chat_messages(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                recent_dialogue=recent_dialogue,
            ),
            "stream": False,
            "options": common_options,
        }
        generate_payload = {
            "model": settings.CLINICAL_CHAT_LLM_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": common_options,
        }
        chat_error: str | None = None
        try:
<<<<<<< HEAD
<<<<<<< HEAD
            parsed = LLMChatProvider._request_ollama_json(
                endpoint="api/chat",
                payload=chat_payload,
            )
            answer = str((parsed.get("message") or {}).get("content") or "").strip()
            if answer:
                latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
                return answer, {
                    "llm_used": "true",
                    "llm_provider": settings.CLINICAL_CHAT_LLM_PROVIDER,
                    "llm_model": settings.CLINICAL_CHAT_LLM_MODEL,
                    "llm_endpoint": "chat",
                    "llm_latency_ms": str(latency_ms),
                }
        except (URLError, TimeoutError, ValueError, OSError, json.JSONDecodeError) as exc:
            chat_error = exc.__class__.__name__

        try:
            parsed = LLMChatProvider._request_ollama_json(
                endpoint="api/generate",
                payload=generate_payload,
            )
            answer = str(parsed.get("response") or "").strip()
            if not answer:
                trace = {"llm_error": "empty_response", "llm_endpoint": "generate"}
                if chat_error:
                    trace["llm_chat_error"] = chat_error
                return None, trace
=======
=======
>>>>>>> origin/codex/improve-conversational-feedback-in-chat-wamorb
            parsed = LLMChatProvider._request_ollama_json(endpoint="api/chat", payload=chat_payload)
            answer = LLMChatProvider._extract_chat_answer(parsed)
            endpoint_used = "chat"
            if not answer:
                parsed = LLMChatProvider._request_ollama_json(
                    endpoint="api/generate",
                    payload=generate_payload,
                )
                answer = LLMChatProvider._extract_chat_answer(parsed)
                endpoint_used = "generate"
            if not answer:
                return None, {"llm_error": "empty_response", "llm_endpoint": endpoint_used}
>>>>>>> origin/codex/improve-conversational-feedback-in-chat-w21r6o
            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            trace = {
                "llm_used": "true",
                "llm_provider": settings.CLINICAL_CHAT_LLM_PROVIDER,
                "llm_model": settings.CLINICAL_CHAT_LLM_MODEL,
                "llm_endpoint": "generate",
                "llm_latency_ms": str(latency_ms),
            }
            if chat_error:
                trace["llm_chat_error"] = chat_error
            return answer, trace
        except (URLError, TimeoutError, ValueError, OSError, json.JSONDecodeError) as exc:
            latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
            trace = {
                "llm_used": "false",
                "llm_model": settings.CLINICAL_CHAT_LLM_MODEL,
                "llm_error": exc.__class__.__name__,
                "llm_latency_ms": str(latency_ms),
            }
<<<<<<< HEAD
<<<<<<< HEAD
            if chat_error:
                trace["llm_chat_error"] = chat_error
            return None, trace
=======
=======
>>>>>>> origin/codex/improve-conversational-feedback-in-chat-wamorb
    @staticmethod
    def _parse_ollama_payload(raw_payload: str) -> dict[str, Any]:
        """Parsea respuestas JSON y JSONL de Ollama de forma tolerante."""
        payload = raw_payload.strip()
        if not payload:
            raise ValueError("empty_payload")
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            # Algunos proxies/instancias devuelven una salida tipo JSONL.
            json_lines: list[dict[str, Any]] = []
            for line in payload.splitlines():
                candidate = line.strip()
                if not candidate:
                    continue
                if candidate.startswith("data:"):
                    candidate = candidate[5:].strip()
                if candidate == "[DONE]":
                    continue
                try:
                    json_lines.append(json.loads(candidate))
                except json.JSONDecodeError:
                    continue
            if not json_lines:
                raise
            combined_message = "".join(
                str(
                    (item.get("message") or {}).get("content")
                    or item.get("response")
                    or item.get("content")
                    or ""
                )
                for item in json_lines
            ).strip()
            merged = dict(json_lines[-1])
            if combined_message:
                if isinstance(merged.get("message"), dict):
                    merged["message"]["content"] = combined_message
                else:
                    merged["response"] = combined_message
            return merged

    @staticmethod
    def _extract_chat_answer(parsed_payload: dict[str, Any]) -> str:
        """Extrae contenido textual de respuestas heterogeneas de Ollama."""
        message = parsed_payload.get("message")
        if isinstance(message, dict):
            return str(message.get("content") or "").strip()
        if isinstance(message, str):
            return message.strip()
        return str(parsed_payload.get("response") or parsed_payload.get("content") or "").strip()
<<<<<<< HEAD
>>>>>>> origin/codex/improve-conversational-feedback-in-chat-w21r6o
=======
>>>>>>> origin/codex/improve-conversational-feedback-in-chat-wamorb
