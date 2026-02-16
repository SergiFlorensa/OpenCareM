# TM-043: Niveles de triaje Manchester (recurso base)

## Objetivo

Estandarizar una referencia unica de prioridad de triaje para:

- agentes,
- frontend,
- pruebas,
- analitica de SLA.

## Endpoint

- `GET /api/v1/clinical-context/triage-levels/manchester`

## Niveles incluidos

- Nivel 1 - Rojo - Inmediato - `0 min`
- Nivel 2 - Naranja - Emergencia - `10 min`
- Nivel 3 - Amarillo - Urgencia - `30 min`
- Nivel 4 - Verde - Menor urgencia - `120 min`
- Nivel 5 - Azul - No urgente - `240 min`

## Que habilita desde ahora

1. Comparar tiempos reales vs SLA por nivel.
2. Usar un vocabulario unico para recomendaciones IA.
3. Evitar reglas inconsistentes entre backend y frontend.

## Limites

- Este recurso no emite diagnostico.
- Solo define prioridad operativa y ventanas objetivo.
- La decision final sigue siendo humana.

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_context_api.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests`

Resultado:

- `68 passed`
