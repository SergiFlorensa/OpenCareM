"""
Simulador de calidad global IA clinica para practicar alertas en Prometheus/Grafana.

Genera casos con auditoria SCASEST y evalua el scorecard global:
- under: IA menos severa que humano
- over: IA mas severa que humano
- match-low: mezcla con baja coincidencia IA vs humano
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
        "title": f"Simulacion Calidad Global #{index}",
        "description": "Caso sintetico para practicar alertas de calidad global.",
        "clinical_priority": "high",
        "specialty": "cardiology",
        "sla_target_minutes": 30,
        "human_review_required": True,
        "completed": False,
    }
    response = _http_json("POST", f"{base_url}/api/v1/care-tasks/", payload)
    return int(response["id"])


def _run_scasest(base_url: str, task_id: int, mode: str) -> int:
    # En `under`, forzamos recomendacion IA moderada para luego auditar humano en alto riesgo.
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
        # En `over` y `match-low`, forzamos recomendacion IA de alto riesgo.
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


def _build_mode_for_match_low(index: int) -> str:
    # Aproximadamente 75% divergencia y 25% match para empujar match-rate < 80%.
    if index % 4 == 0:
        return "match"
    return "under" if index % 2 else "over"


def _audit_scasest(
    base_url: str,
    task_id: int,
    run_id: int,
    mode: str,
    reviewer: str,
) -> str:
    if mode == "under":
        audit_payload = {
            "agent_run_id": run_id,
            "human_validated_high_risk_scasest": True,
            "human_escalation_required": True,
            "human_immediate_antiischemic_strategy": True,
            "reviewed_by": reviewer,
            "reviewer_note": "Simulacion global: under-risk.",
        }
    elif mode == "over":
        audit_payload = {
            "agent_run_id": run_id,
            "human_validated_high_risk_scasest": False,
            "human_escalation_required": False,
            "human_immediate_antiischemic_strategy": False,
            "reviewed_by": reviewer,
            "reviewer_note": "Simulacion global: over-risk.",
        }
    else:
        audit_payload = {
            "agent_run_id": run_id,
            "human_validated_high_risk_scasest": True,
            "human_escalation_required": True,
            "human_immediate_antiischemic_strategy": True,
            "reviewed_by": reviewer,
            "reviewer_note": "Simulacion global: match.",
        }

    response = _http_json(
        "POST",
        f"{base_url}/api/v1/care-tasks/{task_id}/scasest/audit",
        audit_payload,
    )
    return str(response["classification"])


def _print_global_scorecard(base_url: str) -> None:
    scorecard = _http_json("GET", f"{base_url}/api/v1/care-tasks/quality/scorecard")
    print("\nScorecard global:")
    print(
        {
            "total_audits": scorecard.get("total_audits"),
            "matches": scorecard.get("matches"),
            "under_rate_percent": scorecard.get("under_rate_percent"),
            "over_rate_percent": scorecard.get("over_rate_percent"),
            "match_rate_percent": scorecard.get("match_rate_percent"),
            "quality_status": scorecard.get("quality_status"),
        }
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera casos para practicar alertas de calidad global IA."
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="URL base de la API (por defecto: http://127.0.0.1:8000).",
    )
    parser.add_argument(
        "--mode",
        choices=["under", "over", "match-low"],
        default="match-low",
        help="Patron global a generar.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=12,
        help="Numero de casos a generar.",
    )
    parser.add_argument(
        "--reviewer",
        default="simulador_calidad_global",
        help="Usuario revisor a registrar en auditorias.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    count = max(1, args.count)
    generated = 0

    try:
        for index in range(1, count + 1):
            if args.mode == "match-low":
                current_mode = _build_mode_for_match_low(index)
            else:
                current_mode = args.mode

            run_mode = "under" if current_mode == "under" else "over"
            task_id = _create_care_task(args.base_url, index=index)
            run_id = _run_scasest(args.base_url, task_id=task_id, mode=run_mode)
            classification = _audit_scasest(
                args.base_url,
                task_id=task_id,
                run_id=run_id,
                mode=current_mode,
                reviewer=args.reviewer,
            )
            generated += 1
            print(
                "[ok] "
                f"task_id={task_id} run_id={run_id} "
                f"mode={current_mode} classification={classification}"
            )

        print(f"\nGenerados: {generated} casos.")
        _print_global_scorecard(args.base_url)
        print("\nHecho. Revisa ahora Prometheus/Grafana para alertas de calidad global.")
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
