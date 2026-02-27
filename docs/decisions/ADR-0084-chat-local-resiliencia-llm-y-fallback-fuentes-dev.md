# ADR-0084: Resiliencia de chat local (LLM timeout + fallback de fuentes en desarrollo)

## Estado

Aprobado.

## Contexto

En entorno local se observaban dos fallos recurrentes:

1. `llm_used=false` por `TimeoutError` en cascada (intento `api/chat` seguido de `api/generate`), elevando latencia percibida.
2. Respuestas sin evidencia interna cuando no existian fuentes validadas en base de datos, pese a tener documentacion local en `docs/`.

## Decision

1. Mantener contrato de API sin cambios, pero ajustar comportamiento operativo:
   - En `ENVIRONMENT=development`, habilitar fallback a catalogo interno documental cuando no hay fuentes validadas.
2. Endurecer estrategia de inferencia local del proveedor LLM:
   - `keep_alive` para evitar cold starts repetidos.
   - ruta de recuperacion rapida (`generate_quick_recovery`) ante fallos de los caminos principales.
3. Perfil local por `.env` orientado a CPU:
   - timeout mas tolerante para no cortar carga inicial.
   - salida maxima mas acotada para reducir latencia.

## Consecuencias

- Positivas:
  - Menos respuestas degradadas en practica local.
  - Menos frecuencia de `llm_used=false` por timeout.
  - Mejor continuidad de pruebas sin requerir infraestructura adicional.
- Riesgos:
  - El fallback de catalogo en desarrollo no equivale a curacion/sellado formal de fuentes validadas.
  - La ruta de recuperacion rapida prioriza disponibilidad frente a profundidad de respuesta.

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/tests/test_clinical_chat_operational.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py`
- Verificacion directa de `LLMChatProvider.generate_answer(...)` con `llm_used=true` en local.
