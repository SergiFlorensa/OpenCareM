# Drill de Alertas de Calidad Global

## Objetivo

Practicar alertas de calidad global sin crear casos manuales.

El script genera casos SCASEST auditados y actualiza automaticamente:

- `GET /api/v1/care-tasks/quality/scorecard`
- metricas `care_task_quality_audit_*`

## Script

- `app/scripts/simulate_global_quality_alerts.py`

## Requisitos

1. API en marcha (`uvicorn` o Docker).
2. Migraciones al dia:
   - `.\venv\Scripts\python.exe -m alembic upgrade head`

## Ejecucion local (venv)

```powershell
.\venv\Scripts\python.exe app\scripts\simulate_global_quality_alerts.py --mode match-low --count 12
```

## Modos

- `under`: empuja subida de `under_rate`.
- `over`: empuja subida de `over_rate`.
- `match-low`: mezcla controlada para bajar `match_rate`.

## Comandos utiles despues del drill

1. Scorecard:
   - `GET /api/v1/care-tasks/quality/scorecard`
2. Metricas:
   - `GET /metrics` y buscar `care_task_quality_audit_`
3. Prometheus:
   - `http://127.0.0.1:9090/alerts`
4. Grafana:
   - paneles `Calidad Global *` en `Resumen API Gestor de Tareas`

## Nota didactica

Las alertas usan ventana `for`, por eso pueden tardar 2-3 minutos en pasar a `firing`.
