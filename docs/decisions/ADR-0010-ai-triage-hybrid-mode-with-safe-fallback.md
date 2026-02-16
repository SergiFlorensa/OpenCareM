# ADR-0010: AI triage configurable en modo hybrid con fallback seguro

## Contexto

El triage actual es rules-first y funciona bien, pero para practicar patrones de ofertas actuales necesitamos una capa que permita integrar LLM sin comprometer estabilidad.

## Decision

Introducir `AI_TRIAGE_MODE` con dos estrategias:

- `rules`: solo reglas deterministas.
- `hybrid`: intenta provider LLM opcional y, si falla/no responde, hace fallback a reglas.

Agregar campo `source` en la respuesta de triage para observabilidad de decision.

## Consecuencias

Beneficios:

- Arquitectura preparada para proveedor real sin reescribir endpoint.
- Fallback explicito que evita degradacion silenciosa.
- Mejor trazabilidad operativa de decisiones AI.

Costes:

- Mas ramificaciones de logica y tests.
- Necesidad de definir umbrales/criterios de confianza para provider real.

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_ai_api.py`



