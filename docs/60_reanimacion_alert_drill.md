# Drill de Alertas de Reanimacion

## Objetivo

Practicar alertas de calidad de reanimacion sin preparar casos manuales.

El script genera:

- `CareTask`,
- recomendacion de reanimacion,
- auditoria IA vs humano,

con patrones `under`, `over` o `mixed`.

## Script

- `app/scripts/simulate_resuscitation_alerts.py`

## Requisitos

1. API en marcha (`uvicorn` o Docker).
2. Migraciones al dia:
   - `.\venv\Scripts\python.exe -m alembic upgrade head`

## Ejecucion local (venv)

```powershell
.\venv\Scripts\python.exe app\scripts\simulate_resuscitation_alerts.py --mode mixed --count 8
```

## Ejecucion con URL especifica

```powershell
.\venv\Scripts\python.exe app\scripts\simulate_resuscitation_alerts.py --base-url http://127.0.0.1:8000 --mode under --count 6
```

## Modos

- `under`: fuerza casos donde IA queda menos severa que humano.
- `over`: fuerza casos donde IA queda mas severa que humano.
- `mixed`: alterna `under/over`.

## Que validar despues

1. Prometheus:
   - `resuscitation_audit_under_rate_percent`
   - `resuscitation_audit_over_rate_percent`
2. Alertas:
   - `ResuscitationAuditUnderRateHigh`
   - `ResuscitationAuditOverRateHigh`
3. Grafana:
   - `Reanimacion Runs Total`
   - `Reanimacion Under Rate %`
   - `Reanimacion Over Rate %`
   - `Reanimacion Shock Match %`

## Nota didactica

Si no salta alerta al instante, recuerda que las reglas usan `for: 2m`.
