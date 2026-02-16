# ADR-0013: Resumen operativo para corridas de agentes

## Contexto

Con historial y filtros ya disponibles, faltaba una vista agregada para detectar degradacion sin inspeccionar corrida por corrida.

## Decision

Agregar endpoint `GET /api/v1/agents/ops/summary` con metricas agregadas:

- `total_runs`
- `completed_runs`
- `failed_runs`
- `fallback_steps`
- `fallback_rate_percent`

Permitir filtro opcional por `workflow_name`.

## Consecuencias

Beneficios:

- Lectura rapida de salud del sistema de agentes.
- Base para paneles y alertas en Grafana.

Costes:

- Se debe mantener definicion clara de metricas (por run vs por step).

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_agents_api.py`



