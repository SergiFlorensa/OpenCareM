# ADR-0007: AI triage con estrategia rules-first

## Contexto

Queremos aÃ±adir IA Ãºtil al producto sin introducir complejidad prematura.
No existe aÃºn dataset etiquetado propio para entrenar un modelo confiable.

## Decision

Implementar un primer mÃ³dulo de triage con reglas explicables:

- endpoint dedicado `/api/v1/ai/triage-task`
- salida con `priority`, `category`, `confidence`, `reason`
- inferencia determinista basada en keywords

## Consecuencias

Beneficios:

- Funcionalidad Ãºtil inmediata.
- FÃ¡cil de testear y mantener.
- Base sÃ³lida para evolucionar a ML/LLM.

Costes:

- Menor capacidad semÃ¡ntica que un modelo entrenado.
- Necesidad de mantenimiento de reglas.

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_ai_api.py`



