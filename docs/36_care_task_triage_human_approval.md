# TM-041: Aprobacion humana de triaje en `CareTask`

## Idea clave (en simple)

El agente recomienda.
La persona decide.
Y esa decision queda guardada de forma auditable.

## Que se implemento

- Endpoint:
  - `POST /api/v1/care-tasks/{task_id}/triage/approve`
- Tabla nueva:
  - `care_task_triage_reviews`

Con esto cerramos el ciclo `human-in-the-loop`:

1. El agente hace triaje.
2. Una persona lo aprueba o rechaza.
3. El sistema guarda quien decidio, que decidio y sobre que corrida.

## Payload de entrada

```json
{
  "agent_run_id": 12,
  "approved": true,
  "reviewer_note": "Validado por operacion clinica",
  "reviewed_by": "supervisor_guardia"
}
```

## Validaciones de negocio

- Si el `CareTask` no existe: `404`.
- Si `agent_run_id` no existe: `404`.
- Si el run no es de tipo `care_task_triage_v1`: `400`.
- Si el run pertenece a otro `CareTask`: `400`.

## Persistencia

`care_task_triage_reviews` guarda:

- `care_task_id`
- `agent_run_id` (unico por corrida)
- `approved`
- `reviewer_note`
- `reviewed_by`
- `created_at`, `updated_at`

Si se vuelve a llamar para el mismo `agent_run_id`, se actualiza la revision existente.

## Validacion ejecutada

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_agents_api.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests`

Resultado:

- `62 passed`

## Por que importa

Sin esta pieza, el sistema era solo recomendador.
Con esta pieza, el sistema ya es operacionalmente responsable:

- hay control humano explicito,
- hay trazabilidad legal/tecnica,
- y hay base para auditoria real.
