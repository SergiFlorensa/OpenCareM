"""
Evalua un Regression Set de chat clinico contra el backend en ejecucion.

Uso:
  ./venv/Scripts/python.exe -m app.scripts.evaluate_chat_regression --dataset tmp/chat_regression_set.jsonl
"""
from __future__ import annotations

import argparse
import json
import math
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

TOKEN_PATTERN = re.compile(r"[a-z0-9]{3,}", flags=re.IGNORECASE)


def _tokenize(text: str) -> set[str]:
    return set(token.lower() for token in TOKEN_PATTERN.findall(str(text or "")))


def _token_f1(answer: str, expected_answer: str) -> float:
    a = _tokenize(answer)
    b = _tokenize(expected_answer)
    if not a or not b:
        return 0.0
    overlap = len(a.intersection(b))
    if overlap <= 0:
        return 0.0
    precision = overlap / len(a)
    recall = overlap / len(b)
    if (precision + recall) == 0:
        return 0.0
    return round((2 * precision * recall) / (precision + recall), 4)


def _contains_all_terms(text: str, terms: list[str]) -> bool:
    lowered = " ".join(str(text or "").lower().split())
    for term in terms:
        cleaned = str(term or "").strip().lower()
        if not cleaned:
            continue
        if cleaned not in lowered:
            return False
    return True


def _contains_any_forbidden(text: str, forbidden_terms: list[str]) -> bool:
    lowered = " ".join(str(text or "").lower().split())
    for term in forbidden_terms:
        cleaned = str(term or "").strip().lower()
        if cleaned and cleaned in lowered:
            return True
    return False


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(1, int(math.ceil(0.95 * len(ordered))))
    return float(ordered[rank - 1])


def _post_json(url: str, payload: dict[str, Any], *, timeout_seconds: int) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
        raw = response.read().decode("utf-8", errors="ignore")
    return json.loads(raw)


def _evaluate_row(
    row: dict[str, Any],
    *,
    base_url: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    care_task_id = int(row.get("care_task_id") or 0)
    payload = {
        "query": str(row.get("query") or ""),
        "session_id": f"regression-{str(row.get('id') or 'item')}",
        "tool_mode": "chat",
        "use_web_sources": False,
        "use_patient_history": False,
        "max_history_messages": 0,
        "max_patient_history_messages": 0,
        "max_internal_sources": 1,
        "max_web_sources": 1,
    }
    start = time.time()
    response = _post_json(
        f"{base_url}/api/v1/care-tasks/{care_task_id}/chat/messages",
        payload,
        timeout_seconds=timeout_seconds,
    )
    latency_ms = int((time.time() - start) * 1000)
    answer = str(response.get("answer") or "")
    expected_answer = str(row.get("expected_answer") or "")
    expected_domains = [str(item) for item in row.get("expected_domains") or [] if str(item)]
    matched_domains = [str(item) for item in response.get("matched_domains") or [] if str(item)]
    must_include_terms = [str(item) for item in row.get("must_include_terms") or [] if str(item)]
    forbidden_terms = [str(item) for item in row.get("forbidden_terms") or [] if str(item)]
    domain_hit = bool(set(expected_domains).intersection(set(matched_domains))) if expected_domains else True
    must_include_ok = _contains_all_terms(answer, must_include_terms) if must_include_terms else True
    forbidden_hit = _contains_any_forbidden(answer, forbidden_terms)
    return {
        "id": row.get("id"),
        "latency_ms": latency_ms,
        "token_f1": _token_f1(answer, expected_answer),
        "domain_hit": domain_hit,
        "must_include_ok": must_include_ok,
        "forbidden_hit": forbidden_hit,
        "error": None,
    }


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ok_rows = [row for row in rows if not row.get("error")]
    if not ok_rows:
        return {
            "rows_total": len(rows),
            "ok": 0,
            "errors": len(rows),
            "token_f1_avg": 0.0,
            "domain_hit_rate": 0.0,
            "must_include_rate": 0.0,
            "forbidden_leak_rate": 1.0,
            "latency_p95_ms": 0.0,
        }
    token_f1_avg = round(
        sum(float(row.get("token_f1") or 0.0) for row in ok_rows) / len(ok_rows), 4
    )
    domain_hit_rate = round(
        sum(1 for row in ok_rows if bool(row.get("domain_hit"))) / len(ok_rows), 4
    )
    must_include_rate = round(
        sum(1 for row in ok_rows if bool(row.get("must_include_ok"))) / len(ok_rows), 4
    )
    forbidden_leak_rate = round(
        sum(1 for row in ok_rows if bool(row.get("forbidden_hit"))) / len(ok_rows), 4
    )
    latency_p95_ms = int(_p95([float(row.get("latency_ms") or 0.0) for row in ok_rows]))
    return {
        "rows_total": len(rows),
        "ok": len(ok_rows),
        "errors": len(rows) - len(ok_rows),
        "token_f1_avg": token_f1_avg,
        "domain_hit_rate": domain_hit_rate,
        "must_include_rate": must_include_rate,
        "forbidden_leak_rate": forbidden_leak_rate,
        "latency_p95_ms": latency_p95_ms,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evalua regression set de chat clinico.")
    parser.add_argument("--dataset", default="tmp/chat_regression_set.jsonl", help="Dataset JSONL.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8010", help="Base URL API.")
    parser.add_argument("--timeout-seconds", type=int, default=45, help="Timeout por request.")
    parser.add_argument(
        "--output",
        default="tmp/chat_regression_eval_summary.json",
        help="Resumen JSON de salida.",
    )
    parser.add_argument("--min-f1", type=float, default=0.30, help="Umbral minimo token_f1_avg.")
    parser.add_argument(
        "--min-domain-hit-rate",
        type=float,
        default=0.70,
        help="Umbral minimo de domain_hit_rate.",
    )
    parser.add_argument(
        "--max-forbidden-leak-rate",
        type=float,
        default=0.0,
        help="Umbral maximo de leakage interno.",
    )
    parser.add_argument(
        "--min-must-include-rate",
        type=float,
        default=0.25,
        help="Umbral minimo para cobertura de terminos obligatorios.",
    )
    args = parser.parse_args()

    dataset_path = Path(str(args.dataset))
    if not dataset_path.exists():
        print(f"FALLO: no existe dataset {dataset_path}")
        return 2

    rows = [
        json.loads(line)
        for line in dataset_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    evaluated_rows: list[dict[str, Any]] = []
    for row in rows:
        try:
            evaluated_rows.append(
                _evaluate_row(
                    row,
                    base_url=str(args.base_url).rstrip("/"),
                    timeout_seconds=max(5, int(args.timeout_seconds)),
                )
            )
        except urllib.error.URLError as exc:
            evaluated_rows.append(
                {
                    "id": row.get("id"),
                    "latency_ms": 0,
                    "token_f1": 0.0,
                    "domain_hit": False,
                    "must_include_ok": False,
                    "forbidden_hit": False,
                    "error": f"URLError:{exc.reason}",
                }
            )
        except Exception as exc:  # noqa: BLE001
            evaluated_rows.append(
                {
                    "id": row.get("id"),
                    "latency_ms": 0,
                    "token_f1": 0.0,
                    "domain_hit": False,
                    "must_include_ok": False,
                    "forbidden_hit": False,
                    "error": str(exc),
                }
            )

    summary = _summarize(evaluated_rows)
    output_path = Path(str(args.output))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        "rows_total:",
        summary["rows_total"],
        "ok:",
        summary["ok"],
        "errors:",
        summary["errors"],
    )
    print("token_f1_avg:", summary["token_f1_avg"])
    print("domain_hit_rate:", summary["domain_hit_rate"])
    print("must_include_rate:", summary["must_include_rate"])
    print("forbidden_leak_rate:", summary["forbidden_leak_rate"])
    print("latency_p95_ms:", summary["latency_p95_ms"])

    failures: list[str] = []
    if float(summary["token_f1_avg"]) < float(args.min_f1):
        failures.append(f"token_f1_avg {summary['token_f1_avg']} < {args.min_f1}")
    if float(summary["domain_hit_rate"]) < float(args.min_domain_hit_rate):
        failures.append(
            f"domain_hit_rate {summary['domain_hit_rate']} < {args.min_domain_hit_rate}"
        )
    if float(summary["forbidden_leak_rate"]) > float(args.max_forbidden_leak_rate):
        failures.append(
            "forbidden_leak_rate "
            f"{summary['forbidden_leak_rate']} > {args.max_forbidden_leak_rate}"
        )
    if float(summary["must_include_rate"]) < float(args.min_must_include_rate):
        failures.append(
            f"must_include_rate {summary['must_include_rate']} < {args.min_must_include_rate}"
        )
    if failures:
        print("REGRESSION EVAL FALLO:")
        for item in failures:
            print(f"- {item}")
        return 1
    print("REGRESSION EVAL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
