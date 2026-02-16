# TM-040: Triaje de `CareTask` con traza de agente

## Que resuelve

Antes podiamos:

- Crear/editar `CareTask`.
- Ejecutar triaje de agente solo con `POST /api/v1/agents/run`.

Faltaba unir ambos flujos sobre el mismo recurso clinico-operativo.

Con este cambio ya existe:

- `POST /api/v1/care-tasks/{task_id}/triage`

Esto permite lanzar triaje directamente sobre un `CareTask` real y guardar la traza completa en `agent_runs` y `agent_steps`.

## Flujo funcional

1. Se busca el `CareTask` por `task_id`.
2. Si no existe, responde `404`.
3. Si existe, se ejecuta workflow `care_task_triage_v1`.
4. Se persiste corrida en `agent_runs` con contexto del caso:
   - `care_task_id`
   - `title`
   - `description`
   - `clinical_priority`
   - `specialty`
   - `sla_target_minutes`
   - `human_review_required`
5. Se persiste paso en `agent_steps` (`triage_care_task`).
6. Se devuelve respuesta corta para integracion:
   - `care_task_id`
   - `agent_run_id`
   - `workflow_name`
   - `triage`

## Ejemplo de uso

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/care-tasks/1/triage"
```

Respuesta esperada (resumen):

```json
{
  "care_task_id": 1,
  "agent_run_id": 12,
  "workflow_name": "care_task_triage_v1",
  "triage": {
    "priority": "high",
    "category": "ops",
    "confidence": 0.8,
    "reason": "...",
    "source": "rules_fallback"
  }
}
```

## Validacion ejecutada

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_agents_api.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests`

Resultado:

- `59 passed`

## Riesgos pendientes

- Aun no hay endpoint de aprobacion humana del resultado de triaje.
- Aun no se escribe un historial de cambios de prioridad sobre `CareTask` (auditoria funcional).
