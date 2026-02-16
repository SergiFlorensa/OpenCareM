"""
Simulador de calidad SCASEST para practicar alertas en Prometheus/Grafana.

Genera casos de manera controlada:
- under: IA menos severa que humano
- over: IA mas severa que humano
- mixed: mezcla de under y over
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def _http_json(method: str, url: str, payload: dict | None = None) -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _create_care_task(base_url: str, index: int) -> int:
    payload = {
        "title": f"Simulacion SCASEST #{index}",
        "description": "Caso sintetico para pruebas de alertas de calidad.",
        "clinical_priority": "high",
        "specialty": "cardiology",
        "sla_target_minutes": 30,
        "human_review_required": True,
        "completed": False,
    }
    response = _http_json("POST", f"{base_url}/api/v1/care-tasks/", payload)
    return int(response["id"])


def _run_scasest(base_url: str, task_id: int, mode: str) -> int:
    if mode == "under":
        recommendation_payload = {
            "chest_pain_typical": True,
            "dyspnea": True,
            "ecg_st_depression": True,
            "troponin_positive": False,
            "hemodynamic_instability": False,
            "ventricular_arrhythmias": False,
            "refractory_angina": False,
            "grace_score": 95,
        }
    else:
        recommendation_payload = {
            "chest_pain_typical": True,
            "dyspnea": True,
            "ecg_st_depression": True,
            "troponin_positive": True,
            "hemodynamic_instability": True,
            "ventricular_arrhythmias": False,
            "refractory_angina": True,
            "grace_score": 165,
        }

    response = _http_json(
        "POST",
        f"{base_url}/api/v1/care-tasks/{task_id}/scasest/recommendation",
        recommendation_payload,
    )
    return int(response["agent_run_id"])


def _audit_scasest(base_url: str, task_id: int, run_id: int, mode: str, reviewer: str) -> str:
    if mode == "under":
        audit_payload = {
            "agent_run_id": run_id,
            "human_validated_high_risk_scasest": True,
            "human_escalation_required": True,
            "human_immediate_antiischemic_strategy": True,
            "reviewed_by": reviewer,
            "reviewer_note": "Simulacion de under-risk para ejercicios de alertas.",
        }
    else:
        audit_payload = {
            "agent_run_id": run_id,
            "human_validated_high_risk_scasest": False,
            "human_escalation_required": False,
            "human_immediate_antiischemic_strategy": False,
            "reviewed_by": reviewer,
            "reviewer_note": "Simulacion de over-risk para ejercicios de alertas.",
        }

    response = _http_json(
        "POST",
        f"{base_url}/api/v1/care-tasks/{task_id}/scasest/audit",
        audit_payload,
    )
    return str(response["classification"])


def _print_summary(base_url: str, task_ids: list[int]) -> None:
    print("\nResumen por task:")
    for task_id in task_ids:
        summary = _http_json(
            "GET", f"{base_url}/api/v1/care-tasks/{task_id}/scasest/audit/summary"
        )
        print(f"- CareTask {task_id}: {summary}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera casos SCASEST audit para practicar alertas."
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="URL base de la API (por defecto: http://127.0.0.1:8000).",
    )
    parser.add_argument(
        "--mode",
        choices=["under", "over", "mixed"],
        default="mixed",
        help="Tipo de desviacion a generar.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=6,
        help="Numero de casos a generar.",
    )
    parser.add_argument(
        "--reviewer",
        default="simulador_alertas",
        help="Usuario revisor a registrar en auditorias.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    count = max(1, args.count)
    task_ids: list[int] = []

    try:
        for index in range(1, count + 1):
            current_mode = args.mode
            if args.mode == "mixed":
                current_mode = "under" if index % 2 else "over"

            task_id = _create_care_task(args.base_url, index=index)
            run_id = _run_scasest(args.base_url, task_id=task_id, mode=current_mode)
            classification = _audit_scasest(
                args.base_url,
                task_id=task_id,
                run_id=run_id,
                mode=current_mode,
                reviewer=args.reviewer,
            )
            task_ids.append(task_id)
            print(
                f"[ok] task_id={task_id} run_id={run_id} mode={current_mode} classification={classification}"
            )

        _print_summary(args.base_url, task_ids)
        print("\nHecho. Revisa ahora Prometheus/Grafana para ver cambios en tasas.")
        return 0
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"[error] HTTP {exc.code} en {exc.url}: {body}")
        return 1
    except urllib.error.URLError as exc:
        print(f"[error] No se pudo conectar con la API: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
