# Flujo API de CareTasks

## Objetivo

Exponer un recurso `CareTask` en paralelo a `Task` para iniciar el pivot de dominio clinico-operativo sin romper compatibilidad.

## Endpoints

- `POST /api/v1/care-tasks/`
- `GET /api/v1/care-tasks/`
- `GET /api/v1/care-tasks/{task_id}`
- `PUT /api/v1/care-tasks/{task_id}`
- `DELETE /api/v1/care-tasks/{task_id}`
- `GET /api/v1/care-tasks/stats/count`

## Campos clave

- `clinical_priority`: `low|medium|high|critical`
- `specialty`: especialidad operativa responsable
- `sla_target_minutes`: tiempo objetivo de atencion
- `human_review_required`: si exige validacion humana

## Validaciones

- `clinical_priority` fuera del set permitido devuelve `400`.
- `sla_target_minutes` debe ser mayor que cero.

## Ejemplo rapido

```json
{
  "title": "Revisar cola anomala de laboratorio",
  "description": "Backlog pendiente de analisis",
  "clinical_priority": "high",
  "specialty": "lab",
  "sla_target_minutes": 60,
  "human_review_required": true,
  "completed": false
}
```

## Evidencia de validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py`



