# Triaje IA de Tareas

Este mÃ³dulo aÃ±ade una primera capacidad de IA prÃ¡ctica: sugerir prioridad y categorÃ­a de una tarea.

## Objetivo

- Acelerar planificaciÃ³n inicial de tareas.
- Tener recomendaciones explicables (no caja negra).
- Crear base para evolucionar luego a modelos ML/LLM.

## Endpoint

- `POST /api/v1/ai/triage-task`

Entrada:

```json
{
  "title": "Fix production bug in auth",
  "description": "Critical error when users login"
}
```

Salida:

```json
{
  "priority": "high",
  "category": "bug",
  "confidence": 0.85,
  "reason": "Detected bug-related keywords. Urgency keywords indicate high priority."
}
```

## Por quÃ© este enfoque (reglas explicables)

En esta primera versiÃ³n no usamos modelo externo.
Razones:

1. MÃ¡s fÃ¡cil de entender y depurar.
2. Sin coste de API externa.
3. Comportamiento determinista para tests.
4. Buena base para comparar cuando aÃ±adamos ML real.

## LÃ³gica actual

- Detecta palabras clave para inferir `category`:
  - `bug`, `ops`, `docs`, `analysis`, `dev`, `general`
- Ajusta `priority`:
  - `high` para urgencia y categorÃ­as crÃ­ticas (`bug`, `ops`)
  - `low` para `docs` y `analysis`
  - `medium` como valor por defecto
- Devuelve `confidence` y `reason` legibles.

## Archivos principales

- `app/schemas/ai.py`
- `app/services/ai_triage_service.py`
- `app/api/ai.py`
- `app/tests/test_ai_api.py`

## ValidaciÃ³n

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_ai_api.py`

## EvoluciÃ³n sugerida (siguiente nivel)

1. AÃ±adir opciÃ³n `AI_TRIAGE_MODE=rules|ml|llm`.
2. Entrenar clasificador supervisado con histÃ³rico de tareas.
3. Guardar feedback humano para mejorar precisiÃ³n.


