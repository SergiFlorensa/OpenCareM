"""
Smoke test end-to-end para validar modo nativo conversacional de Llama.

Ejecuta turnos generales aleatorios contra `/api/v1/care-tasks/{id}/chat/messages`
usando `TestClient` (sin levantar uvicorn) y falla si detecta degradacion a
fallback estructurado no nativo.
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass

from fastapi.testclient import TestClient

from app.main import app

GENERAL_QUERY_POOL = [
    "hola",
    "que tal estas hoy?",
    "recomiendame una pelicula de ciencia ficcion",
    "explicame en tres puntos que es git",
    "hola, conoces la ciudad de reus en tarragona?",
    "que te gusta de reus",
    "donde ir a comer en Reus?",
    "Que mes recomiendas visitarlo? tiene la playa cerca?",
    "dame una receta facil de pasta para cenar",
    "que puedo ver este fin de semana en madrid?",
    "como puedo mejorar mi concentracion al estudiar?",
    "diferencia entre cpu y gpu en lenguaje sencillo",
]


@dataclass
class TurnResult:
    query: str
    status_code: int
    response_mode: str
    matched_domains: list[str]
    llm_used: str
    llm_endpoint: str
    answer: str
    failed_rules: list[str]


def _trace_value(trace: list[str], key: str) -> str:
    prefix = f"{key}="
    for item in trace:
        text = str(item)
        if text.startswith(prefix):
            return text[len(prefix) :]
    return ""


def _looks_truncated(answer: str) -> bool:
    text = answer.strip()
    if len(text) < 40:
        return False
    if text.endswith((".", "!", "?", "…", ":", ";", ")", "]", "}", "\"", "'")):
        return False
    tokens = text.lower().split()
    if len(tokens) < 10:
        return False
    trailing_tokens = {
        "a",
        "de",
        "del",
        "la",
        "el",
        "y",
        "o",
        "que",
        "con",
        "por",
        "para",
        "en",
        "cuando",
        "como",
        "unos",
        "unas",
        "un",
        "una",
    }
    return tokens[-1].strip(",.;:!?") in trailing_tokens


def run_smoke(*, seed: int, turns: int) -> tuple[list[TurnResult], bool]:
    rng = random.Random(seed)
    selected_queries = rng.sample(GENERAL_QUERY_POOL, k=min(turns, len(GENERAL_QUERY_POOL)))

    client = TestClient(app)
    create_task_response = client.post(
        "/api/v1/care-tasks/",
        json={
            "title": "Smoke native llama",
            "description": "validacion conversacional nativa",
            "clinical_priority": "medium",
            "specialty": "general",
            "sla_target_minutes": 90,
            "human_review_required": False,
            "completed": False,
        },
    )
    create_task_response.raise_for_status()
    task_id = int(create_task_response.json()["id"])

    session_id = f"smoke-native-{seed}"
    results: list[TurnResult] = []
    ok = True

    for query in selected_queries:
        response = client.post(
            f"/api/v1/care-tasks/{task_id}/chat/messages",
            json={
                "query": query,
                "session_id": session_id,
                "tool_mode": "chat",
                "use_web_sources": False,
                "use_patient_history": False,
                "max_history_messages": 8,
                "max_patient_history_messages": 0,
                "max_internal_sources": 3,
                "max_web_sources": 1,
            },
        )
        content_type = response.headers.get("content-type", "")
        payload = (
            response.json()
            if content_type.startswith("application/json")
            else {}
        )
        trace = list(payload.get("interpretability_trace") or [])
        answer = str(payload.get("answer") or "")
        response_mode = str(payload.get("response_mode") or "")
        matched_domains = [str(item) for item in list(payload.get("matched_domains") or [])]
        llm_used = _trace_value(trace, "llm_used")
        llm_endpoint = _trace_value(trace, "llm_endpoint")

        failed_rules: list[str] = []
        if response.status_code != 200:
            failed_rules.append("http_status_not_200")
        if response_mode != "general":
            failed_rules.append("response_mode_not_general")
        if matched_domains:
            failed_rules.append("matched_domains_should_be_empty_in_general_mode")
        if llm_used != "true":
            failed_rules.append("llm_not_used")
        if answer.startswith("Resumen operativo basado en evidencia interna"):
            failed_rules.append("structured_clinical_fallback_detected")
        if "Modo conversacional general activo" in answer:
            failed_rules.append("legacy_general_template_detected")
        if not answer.strip():
            failed_rules.append("empty_answer")
        if _looks_truncated(answer):
            failed_rules.append("answer_maybe_truncated")

        if failed_rules:
            ok = False

        results.append(
            TurnResult(
                query=query,
                status_code=int(response.status_code),
                response_mode=response_mode,
                matched_domains=matched_domains,
                llm_used=llm_used,
                llm_endpoint=llm_endpoint,
                answer=answer,
                failed_rules=failed_rules,
            )
        )

    return results, ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test nativo de chat general")
    parser.add_argument("--seed", type=int, default=26, help="Seed para seleccionar queries")
    parser.add_argument(
        "--turns",
        type=int,
        default=4,
        help="Numero de turnos generales a probar",
    )
    args = parser.parse_args()

    results, ok = run_smoke(seed=args.seed, turns=max(1, int(args.turns)))
    print(f"Smoke native chat | seed={args.seed} | turns={len(results)}")
    for index, item in enumerate(results, start=1):
        print(f"--- turno {index}")
        print(f"query={item.query}")
        print(
            "status={status} mode={mode} matched_domains={domains} llm_used={llm_used} "
            "llm_endpoint={endpoint}".format(
                status=item.status_code,
                mode=item.response_mode,
                domains=item.matched_domains,
                llm_used=item.llm_used,
                endpoint=item.llm_endpoint or "na",
            )
        )
        preview = item.answer.replace("\n", " | ")[:220]
        print(f"answer={preview}")
        if item.failed_rules:
            print("failed_rules=" + ",".join(item.failed_rules))

    if ok:
        print("RESULT=PASS")
        return 0
    print("RESULT=FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
