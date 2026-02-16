# AI Triage Hybrid Mode

## Objetivo

Evolucionar el triage de tareas desde modo solo reglas a un modo configurable:

- `rules`: comportamiento 100% determinista.
- `hybrid`: intenta provider tipo LLM y cae a reglas si no hay salida usable.

## Que cambia tecnicamente

1. Nuevo setting:
- `AI_TRIAGE_MODE` en `app/core/config.py`
- Valores validos: `rules` o `hybrid`

2. Provider opcional:
- `app/services/llm_triage_provider.py`
- En esta fase es un provider simulado/determinista para practicar arquitectura sin red externa.

3. Contrato de salida actualizado:
- `TaskTriageResponse` agrega `source`:
  - `rules`
  - `llm`
  - `rules_fallback`

## Flujo de decision

1. Si `AI_TRIAGE_MODE=rules`:
- Siempre usa reglas explicables.

2. Si `AI_TRIAGE_MODE=hybrid`:
- Intenta provider LLM.
- Si retorna recomendacion con confianza suficiente, usa `source=llm`.
- Si no retorna o no es confiable, aplica reglas con `source=rules_fallback`.

## Por que es util

- Practicas una arquitectura real de agentes (provider + fallback + trazabilidad).
- Mantienes seguridad operativa: nunca te quedas sin respuesta.
- Te prepara para enchufar proveedor real (OpenAI/Azure/etc.) sin rediseÃ±ar el servicio.

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_ai_api.py`


