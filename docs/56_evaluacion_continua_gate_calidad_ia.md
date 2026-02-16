# Evaluacion Continua y Gate de Calidad IA Clinica

## Problema que resuelve

Hasta ahora teniamos observabilidad y alertas en runtime, pero faltaba una barrera preventiva en CI para detectar regresiones antes del despliegue.

Este gate evita que cambios en reglas, servicios o contratos degraden silenciosamente la calidad global medida por:

- `under_rate_percent`
- `over_rate_percent`
- `match_rate_percent`
- `quality_status`

## Que se implementa

- Suite dedicada de regresion:
  - `app/tests/test_quality_regression_gate.py`
- Runner ejecutable para equipo y CI:
  - `app/scripts/run_quality_gate.py`
- Paso obligatorio en pipeline:
  - `.github/workflows/ci.yml` (step `Gate de evaluacion continua`)

## Cobertura funcional del gate

La suite ejecuta dos escenarios sinteticos reproducibles:

1. **Escenario controlado (debe pasar)**
   - 12 auditorias SCASEST:
     - 10 `match`
     - 1 `under`
     - 1 `over`
   - Umbrales exigidos:
     - `under_rate_percent <= 10`
     - `over_rate_percent <= 20`
     - `match_rate_percent >= 80`
   - Estado esperado:
     - `quality_status = "atencion"`

2. **Escenario degradado (debe detectar degradacion)**
   - 12 auditorias `under_scasest_risk`
   - Validacion esperada:
     - `under_rate_percent > 10`
     - `quality_status = "degradado"`

## Como ejecutarlo en local

```powershell
.\venv\Scripts\python.exe app\scripts\run_quality_gate.py
```

## Impacto operativo

- Si el gate falla en CI, el cambio no pasa.
- Esto protege contra regresiones de calidad clinico-operativa antes de llegar a produccion.

## Riesgos pendientes

- El gate actual usa un escenario sintetico sobre dominio SCASEST; conviene ampliar el dataset a triaje/screening/medico-legal en una siguiente iteracion.
