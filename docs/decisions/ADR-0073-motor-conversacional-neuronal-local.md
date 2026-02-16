# ADR-0073: Motor conversacional neuronal local con fallback

- Fecha: 2026-02-15
- Estado: Aprobado

## Contexto

La experiencia conversational del chat era funcional, pero insuficiente en
naturalidad y fluidez para uso intensivo por profesionales en guardia.

## Decision

Integrar proveedor neuronal local (`Ollama`) en el chat:

- inferencia local (sin coste por token cloud),
- prompt estructurado por modo (`general`/`clinical`),
- fallback rule-based cuando el modelo no responde.

## Consecuencias

### Positivas

- Respuestas mas naturales y legibles.
- Baja latencia en despliegue local con modelos cuantizados.
- Robustez operativa por fallback determinista.

### Riesgos

- Dependencia opcional de runtime LLM local.
- Variabilidad de salida del modelo frente a respuestas deterministas.

## Mitigaciones

- `CLINICAL_CHAT_LLM_ENABLED=false` por defecto.
- Trazabilidad explicita (`llm_used`, `llm_model`, `llm_latency_ms`).
- Politica de seguridad clinica y whitelist sin cambios.

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/services/llm_chat_provider.py app/services/clinical_chat_service.py app/schemas/clinical_chat.py app/api/care_tasks.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat`
