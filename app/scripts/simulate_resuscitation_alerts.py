"""
Simulador de calidad de reanimacion para practicar alertas en Prometheus/Grafana.

Genera casos controlados:
- under: IA menos severa que humano
- over: IA mas severa que humano
- mixed: alterna under y over
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
        "title": f"Simulacion Reanimacion #{index}",
        "description": "Caso sintetico para pruebas de alertas de calidad en reanimacion.",
        "clinical_priority": "critical",
        "specialty": "emergency",
        "sla_target_minutes": 5,
        "human_review_required": True,
        "completed": False,
    }
    response = _http_json("POST", f"{base_url}/api/v1/care-tasks/", payload)
    return int(response["id"])


def _run_resuscitation(base_url: str, task_id: int, mode: str) -> int:
    if mode == "under":
        recommendation_payload = {
            "context_type": "tachyarrhythmia_with_pulse",
            "rhythm": "af",
            "has_pulse": True,
            "hypotension": False,
            "altered_mental_status": False,
            "shock_signs": False,
            "ischemic_chest_pain": False,
            "acute_heart_failure": False,
            "door_ecg_minutes": 8,
            "symptom_onset_minutes": 40,
        }
    else:
        recommendation_payload = {
            "context_type": "cardiac_arrest",
            "rhythm": "vf",
            "has_pulse": False,
            "compression_depth_cm": 5.2,
            "compression_rate_per_min": 110,
            "interruption_seconds": 8,
            "etco2_mm_hg": 16,
            "door_ecg_minutes": 4,
            "symptom_onset_minutes": 20,
        }

    response = _http_json(
        "POST",
        f"{base_url}/api/v1/care-tasks/{task_id}/resuscitation/recommendation",
        recommendation_payload,
    )
    return int(response["agent_run_id"])


def _audit_resuscitation(base_url: str, task_id: int, run_id: int, mode: str, reviewer: str) -> str:
    if mode == "under":
        audit_payload = {
            "agent_run_id": run_id,
            "human_validated_severity_level": "critical",
            "human_shock_recommended": True,
            "human_reversible_causes_completed": True,
            "human_airway_plan_adequate": True,
            "reviewed_by": reviewer,
            "reviewer_note": "Simulacion de under-risk en reanimacion.",
        }
    else:
        audit_payload = {
            "agent_run_id": run_id,
            "human_validated_severity_level": "medium",
            "human_shock_recommended": False,
            "human_reversible_causes_completed": False,
            "human_airway_plan_adequate": False,
            "reviewed_by": reviewer,
            "reviewer_note": "Simulacion de over-risk en reanimacion.",
        }

    response = _http_json(
        "POST",
        f"{base_url}/api/v1/care-tasks/{task_id}/resuscitation/audit",
        audit_payload,
    )
    return str(response["classification"])


def _print_summary(base_url: str, task_ids: list[int]) -> None:
    print("\nResumen por task:")
    for task_id in task_ids:
        summary = _http_json(
            "GET", f"{base_url}/api/v1/care-tasks/{task_id}/resuscitation/audit/summary"
        )
        print(f"- CareTask {task_id}: {summary}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera casos de reanimacion auditados para practicar alertas."
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
        default="simulador_reanimacion",
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
            run_id = _run_resuscitation(args.base_url, task_id=task_id, mode=current_mode)
            classification = _audit_resuscitation(
                args.base_url,
                task_id=task_id,
                run_id=run_id,
                mode=current_mode,
                reviewer=args.reviewer,
            )
            task_ids.append(task_id)
            print(
                "[ok] "
                f"task_id={task_id} run_id={run_id} "
                f"mode={current_mode} classification={classification}"
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
