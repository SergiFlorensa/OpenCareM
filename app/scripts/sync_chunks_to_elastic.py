"""
Sincroniza chunks clinicos desde SQLite a un indice Elasticsearch.

Uso:
  ./venv/Scripts/python.exe -m app.scripts.sync_chunks_to_elastic --recreate-index
"""
from __future__ import annotations

import argparse
import base64
import json
import ssl
from typing import Any
from urllib import error, request

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.document_chunk import DocumentChunk


def _build_headers(*, ndjson: bool = False) -> dict[str, str]:
    content_type = "application/x-ndjson" if ndjson else "application/json"
    headers = {"Content-Type": content_type}
    api_key = str(settings.CLINICAL_CHAT_RAG_ELASTIC_API_KEY or "").strip()
    username = str(settings.CLINICAL_CHAT_RAG_ELASTIC_USERNAME or "").strip()
    password = str(settings.CLINICAL_CHAT_RAG_ELASTIC_PASSWORD or "").strip()
    if api_key:
        headers["Authorization"] = f"ApiKey {api_key}"
    elif username:
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {token}"
    return headers


def _ssl_context() -> ssl.SSLContext | None:
    if settings.CLINICAL_CHAT_RAG_ELASTIC_VERIFY_TLS:
        return None
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def _http_request(
    *,
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    ndjson_payload: str | None = None,
    timeout_seconds: int,
) -> tuple[int, str]:
    if payload is not None and ndjson_payload is not None:
        raise ValueError("payload y ndjson_payload son excluyentes")
    data = None
    ndjson_mode = ndjson_payload is not None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    elif ndjson_payload is not None:
        data = ndjson_payload.encode("utf-8")
    req = request.Request(
        url=url,
        method=method.upper(),
        data=data,
        headers=_build_headers(ndjson=ndjson_mode),
    )
    try:
        with request.urlopen(req, timeout=timeout_seconds, context=_ssl_context()) as response:
            body = response.read().decode("utf-8")
            return int(response.status), body
    except error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8")
        except Exception:
            body = ""
        return int(exc.code), body


def _ensure_index(
    *,
    base_url: str,
    index_name: str,
    timeout_seconds: int,
    recreate: bool,
) -> None:
    index_url = f"{base_url}/{index_name}"
    if recreate:
        _http_request(
            method="DELETE",
            url=index_url,
            timeout_seconds=timeout_seconds,
        )
    status, _body = _http_request(
        method="HEAD",
        url=index_url,
        timeout_seconds=timeout_seconds,
    )
    if status == 200:
        return
    mapping = {
        "mappings": {
            "properties": {
                "chunk_id": {"type": "long"},
                "document_id": {"type": "long"},
                "chunk_index": {"type": "integer"},
                "chunk_text": {"type": "text"},
                "text": {"type": "text"},
                "content": {"type": "text"},
                "section_path": {"type": "text"},
                "source_file": {"type": "keyword"},
                "specialty": {"type": "keyword"},
                "tokens_count": {"type": "integer"},
                "keywords": {"type": "keyword"},
                "keywords_text": {"type": "text"},
                "custom_questions": {"type": "text"},
                "custom_questions_text": {"type": "text"},
                "semantic_content": {"type": "text"},
            }
        }
    }
    status, body = _http_request(
        method="PUT",
        url=index_url,
        payload=mapping,
        timeout_seconds=timeout_seconds,
    )
    if status not in {200, 201}:
        raise RuntimeError(
            f"No se pudo crear indice Elastic ({status}): {body[:300]}"
        )


def _build_bulk_payload(chunks: list[DocumentChunk], *, index_name: str) -> str:
    lines: list[str] = []
    for chunk in chunks:
        source_file = ""
        if chunk.document is not None and chunk.document.source_file:
            source_file = str(chunk.document.source_file)
        keywords = [str(item).strip() for item in (chunk.keywords or []) if str(item).strip()]
        questions = [
            str(item).strip() for item in (chunk.custom_questions or []) if str(item).strip()
        ]
        doc = {
            "chunk_id": int(chunk.id),
            "document_id": int(chunk.document_id),
            "chunk_index": int(chunk.chunk_index),
            "chunk_text": str(chunk.chunk_text or ""),
            "text": str(chunk.chunk_text or ""),
            "content": str(chunk.chunk_text or ""),
            "section_path": str(chunk.section_path or ""),
            "source_file": source_file,
            "specialty": str(chunk.specialty or ""),
            "tokens_count": int(chunk.tokens_count or 0),
            "keywords": keywords,
            "keywords_text": " ".join(keywords),
            "custom_questions": questions,
            "custom_questions_text": " ".join(questions),
            "semantic_content": str(chunk.chunk_text or ""),
        }
        lines.append(json.dumps({"index": {"_index": index_name, "_id": str(chunk.id)}}))
        lines.append(json.dumps(doc, ensure_ascii=False))
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Sincroniza document_chunks a Elasticsearch.")
    parser.add_argument(
        "--index",
        default=settings.CLINICAL_CHAT_RAG_ELASTIC_INDEX,
        help="Nombre del indice Elastic destino.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Tamano de lote para _bulk.",
    )
    parser.add_argument(
        "--recreate-index",
        action="store_true",
        help="Recrea el indice antes de cargar los datos.",
    )
    parser.add_argument(
        "--specialty",
        default="",
        help="Filtra sincronizacion por especialidad exacta (opcional).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo calcula volumen de registros, no escribe en Elastic.",
    )
    args = parser.parse_args()

    base_url = str(settings.CLINICAL_CHAT_RAG_ELASTIC_URL or "").rstrip("/")
    if not base_url:
        raise RuntimeError("CLINICAL_CHAT_RAG_ELASTIC_URL no puede estar vacio.")
    if args.batch_size < 20:
        raise RuntimeError("--batch-size debe ser >= 20.")

    timeout_seconds = int(settings.CLINICAL_CHAT_RAG_ELASTIC_TIMEOUT_SECONDS)
    index_name = str(args.index).strip()
    if not index_name:
        raise RuntimeError("--index no puede estar vacio.")

    _ensure_index(
        base_url=base_url,
        index_name=index_name,
        timeout_seconds=timeout_seconds,
        recreate=bool(args.recreate_index),
    )

    session = SessionLocal()
    try:
        last_id = 0
        total_seen = 0
        total_indexed = 0
        normalized_specialty = str(args.specialty or "").strip().lower()
        while True:
            query = session.query(DocumentChunk).filter(DocumentChunk.id > last_id)
            if normalized_specialty:
                query = query.filter(DocumentChunk.specialty == normalized_specialty)
            rows = (
                query.order_by(DocumentChunk.id.asc()).limit(int(args.batch_size)).all()
            )
            if not rows:
                break
            total_seen += len(rows)
            last_id = int(rows[-1].id)
            if args.dry_run:
                continue
            bulk_payload = _build_bulk_payload(rows, index_name=index_name)
            status, body = _http_request(
                method="POST",
                url=f"{base_url}/_bulk?refresh=false",
                ndjson_payload=bulk_payload,
                timeout_seconds=timeout_seconds,
            )
            if status not in {200, 201}:
                raise RuntimeError(
                    f"Error en _bulk ({status}): {body[:500]}"
                )
            parsed = json.loads(body or "{}")
            if parsed.get("errors"):
                raise RuntimeError(
                    "Elastic reporto errores en _bulk. Revisa el payload/mapping."
                )
            total_indexed += len(rows)
            print(f"indexed_batch={len(rows)} total_indexed={total_indexed}")

        if not args.dry_run:
            _http_request(
                method="POST",
                url=f"{base_url}/{index_name}/_refresh",
                timeout_seconds=timeout_seconds,
            )
        print(
            "sync_done "
            f"seen={total_seen} indexed={total_indexed} "
            f"dry_run={1 if args.dry_run else 0} index={index_name}"
        )
    finally:
        session.close()


if __name__ == "__main__":
    main()
