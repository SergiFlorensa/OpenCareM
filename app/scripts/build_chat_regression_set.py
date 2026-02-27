"""
Construye un Regression Set de chat clinico a partir del historial persistido.

Uso:
  ./venv/Scripts/python.exe -m app.scripts.build_chat_regression_set --limit 300
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from app.core.database import SessionLocal
from app.models.care_task_chat_message import CareTaskChatMessage

FORBIDDEN_TERMS = ("/api/v1", "app/", "venv", "agent_run", "workflow", "tool_mode")
TOKEN_PATTERN = re.compile(r"[a-z0-9]{4,}", flags=re.IGNORECASE)
STOPWORDS = {
    "paciente",
    "caso",
    "prioriza",
    "acciones",
    "minutos",
    "urgencias",
    "manejo",
    "inicial",
    "operativo",
    "rutas",
    "chat",
}


def _normalize(text: str) -> str:
    return " ".join(str(text or "").lower().split())


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(str(text or ""))]


def _has_forbidden_leak(text: str) -> bool:
    lowered = _normalize(text)
    return any(term in lowered for term in FORBIDDEN_TERMS)


def _derive_must_include_terms(query: str, *, max_terms: int = 4) -> list[str]:
    terms: list[str] = []
    for token in _tokenize(query):
        if token in STOPWORDS:
            continue
        if token in terms:
            continue
        terms.append(token)
        if len(terms) >= max(1, int(max_terms)):
            break
    return terms


def _is_regression_candidate(
    message: CareTaskChatMessage,
    *,
    min_query_chars: int,
    min_answer_chars: int,
) -> bool:
    query = str(message.user_query or "").strip()
    answer = str(message.assistant_answer or "").strip()
    if len(query) < min_query_chars:
        return False
    if len(answer) < min_answer_chars:
        return False
    if not (message.knowledge_sources or []):
        return False
    if "pregunta de aclaracion" in _normalize(answer):
        return False
    if _has_forbidden_leak(answer):
        return False
    return True


def _message_to_regression_item(message: CareTaskChatMessage) -> dict[str, Any]:
    query = str(message.user_query or "").strip()
    answer = str(message.assistant_answer or "").strip()
    matched_domains = [str(item) for item in (message.matched_domains or []) if str(item).strip()]
    return {
        "id": f"chatmsg-{int(message.id)}",
        "care_task_id": int(message.care_task_id),
        "session_id": str(message.session_id or ""),
        "query": query,
        "expected_answer": answer,
        "expected_domains": matched_domains[:3],
        "must_include_terms": _derive_must_include_terms(query, max_terms=4),
        "forbidden_terms": list(FORBIDDEN_TERMS),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporta Regression Set de chat clinico.")
    parser.add_argument(
        "--output",
        default="tmp/chat_regression_set.jsonl",
        help="Archivo JSONL destino.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=250,
        help="Numero maximo de mensajes evaluados (recientes primero).",
    )
    parser.add_argument("--care-task-id", type=int, default=0, help="Filtra por care_task_id.")
    parser.add_argument("--session-id", default="", help="Filtra por session_id exacto.")
    parser.add_argument("--specialty", default="", help="Filtra por especialidad efectiva.")
    parser.add_argument(
        "--min-query-chars",
        type=int,
        default=10,
        help="Longitud minima de consulta para incluir item.",
    )
    parser.add_argument(
        "--min-answer-chars",
        type=int,
        default=160,
        help="Longitud minima de respuesta para incluir item.",
    )
    args = parser.parse_args()

    output_path = Path(str(args.output))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    session = SessionLocal()
    try:
        query = session.query(CareTaskChatMessage).order_by(
            CareTaskChatMessage.created_at.desc(),
            CareTaskChatMessage.id.desc(),
        )
        if int(args.care_task_id) > 0:
            query = query.filter(CareTaskChatMessage.care_task_id == int(args.care_task_id))
        if str(args.session_id or "").strip():
            query = query.filter(CareTaskChatMessage.session_id == str(args.session_id).strip())
        if str(args.specialty or "").strip():
            query = query.filter(
                CareTaskChatMessage.effective_specialty == str(args.specialty).strip().lower()
            )

        rows = query.limit(max(1, int(args.limit))).all()
        exported: list[dict[str, Any]] = []
        for message in rows:
            if not _is_regression_candidate(
                message,
                min_query_chars=max(3, int(args.min_query_chars)),
                min_answer_chars=max(60, int(args.min_answer_chars)),
            ):
                continue
            exported.append(_message_to_regression_item(message))

        with output_path.open("w", encoding="utf-8") as handle:
            for item in exported:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")

        print(
            "regression_set_done "
            f"rows_seen={len(rows)} rows_exported={len(exported)} output={output_path}"
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
