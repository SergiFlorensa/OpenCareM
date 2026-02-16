# Fundacion de Ejecucion de Agentes

## Objetivo

Crear la base tecnica para ejecutar workflows agente con trazabilidad persistente y auditable.

## Que se implemento

1. Modelo `AgentRun`:
- Guarda una ejecucion completa de workflow.
- Campos clave: `status`, `run_input`, `run_output`, `error_message`, `total_cost_usd`, `total_latency_ms`.

2. Modelo `AgentStep`:
- Guarda cada paso del workflow.
- Campos clave: `step_input`, `step_output`, `decision`, `fallback_used`, `error_message`, `step_latency_ms`.

3. Endpoint de ejecucion:
- `POST /api/v1/agents/run`
- Flujo de trabajo soportado inicial: `task_triage_v1`
- Respuesta incluye resultado global y lista de pasos trazados.

## Flujo real de ejecucion

1. API recibe `workflow_name`, `title`, `description`.
2. Se crea un `AgentRun` en estado `running`.
3. Se ejecuta paso `triage_task` sobre `AITriageService`.
4. Si `confidence < 0.65`, aplica fallback seguro:
- `priority=medium`
- `category=general`
5. Se persiste `AgentStep` con decision/fallback.
6. Se cierra `AgentRun` como `completed` o `failed`.

## Por que esta estructura

- Permite depurar comportamiento no determinista paso a paso.
- Da base para evaluacion de agentes (consistencia, regresiones, fallbacks).
- Facilita observabilidad y auditoria sin depender de logs efimeros.

## Archivos tocados

- `app/models/agent_run.py`
- `app/services/agent_run_service.py`
- `app/api/agents.py`
- `app/schemas/agent.py`
- `alembic/versions/5dc1b6a8f4aa_add_agent_runs_and_steps_tables.py`
- `app/tests/test_agents_api.py`

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_agents_api.py`



