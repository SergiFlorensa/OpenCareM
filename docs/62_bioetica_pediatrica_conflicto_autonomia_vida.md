# Soporte Bioetico Pediatrico en Urgencias (Operacion)

## Objetivo

Integrar en el motor medico-legal un soporte operativo para conflictos entre:

- autonomia parental por representacion
- preservacion de la vida e interes superior del menor

En escenarios de riesgo vital inminente.

No constituye consejo juridico definitivo ni reemplaza decision clinica humana.

## Endpoint aplicable

- `POST /api/v1/care-tasks/{task_id}/medicolegal/recommendation`

## Señales de entrada relevantes

- `patient_age_years < 18`
- `life_threatening_condition=true`
- `blood_transfusion_indicated=true`
- `parental_religious_refusal_life_saving_treatment=true`
- `legal_representatives_deceased` o `legal_representative_present=false`
- `immediate_judicial_authorization_available`

## Comportamiento operativo agregado

Cuando se detecta conflicto pediatrico critico:

- eleva `legal_risk_level` a `high`
- puede activar `life_preserving_override_recommended=true`
- expone `ethical_legal_basis` para justificar la ponderacion bioetica
- emite `urgency_summary` sintetico para decision de guardia
- agrega alertas criticas de interes superior del menor
- exige documentacion reforzada de proporcionalidad y estado de necesidad terapeutica
- sugiere no demorar soporte vital indicado por tramites externos en riesgo inminente
- fuerza checklist de trazabilidad temporal y justificativa

## Validacion recomendada

```powershell
.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k pediatric_life_saving_conflict
.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py
```
