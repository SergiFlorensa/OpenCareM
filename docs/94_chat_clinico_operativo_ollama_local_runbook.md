# 94. Chat Clinico Operativo: Ollama local, trazabilidad y seguridad

## Configuracion recomendada (`.env`)

```env
CLINICAL_CHAT_LLM_ENABLED=true
CLINICAL_CHAT_LLM_PROVIDER=ollama
CLINICAL_CHAT_LLM_BASE_URL=http://127.0.0.1:11434
CLINICAL_CHAT_LLM_MODEL=llama3.1:8b
CLINICAL_CHAT_LLM_NUM_CTX=4096
CLINICAL_CHAT_LLM_MAX_INPUT_TOKENS=3200
CLINICAL_CHAT_LLM_PROMPT_MARGIN_TOKENS=256
CLINICAL_CHAT_LLM_TEMPERATURE=0.2
CLINICAL_CHAT_LLM_TOP_P=0.9
CLINICAL_CHAT_LLM_TIMEOUT_SECONDS=15
CLINICAL_CHAT_LLM_MAX_OUTPUT_TOKENS=700
```

## Instalacion local de Ollama

1. Instalar Ollama segun SO desde documentacion oficial.
2. Levantar servicio local:
   - `ollama serve`
3. Descargar modelo recomendado para 16GB RAM:
   - `ollama pull llama3.1:8b`
4. Verificar modelo disponible:
   - `ollama list`

> Recomendacion operativa: con 16GB RAM evitar modelos >14B para no degradar latencia en guardia.

## Flujo de inferencia

- Endpoint preferido: `POST /api/chat`
- Fallback automatico: `POST /api/generate`
- Si el LLM falla/timeout, el sistema devuelve fallback operativo no diagnostico con:
  - prioridades,
  - riesgos,
  - checklist,
  - advertencia de validacion humana.

## Trazabilidad clinica visible

Cada respuesta debe exponer en `interpretability_trace`:

- `llm_used`
- `llm_model`
- `llm_endpoint`
- `llm_latency_ms`
- `query_expanded`
- `matched_endpoints`
- `llm_input_tokens_budget`
- `llm_input_tokens_estimated`
- `llm_prompt_truncated`
- `prompt_injection_detected`
- `quality_status`

## Politica web/RAG y whitelist

- Mantener `CLINICAL_CHAT_WEB_STRICT_WHITELIST=true`.
- Solo se usan dominios permitidos en `CLINICAL_CHAT_WEB_ALLOWED_DOMAINS`.
- Si no hay politica valida de seguridad clinica, evitar RAG web en despliegues productivos.
- Toda fuente web devuelta debe incluir `url` y `snippet`.

## Ejemplos de prompts clinicos

- "Paciente con sepsis y lactato 4, prioriza acciones 0-10 minutos."
- "resume"
- "y ahora?"
- "que hago si persiste hipotension?"

## Ejecucion de pruebas

- Backend lint: `python -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/tests/test_clinical_chat_operational.py`
- Tests chat: `python -m pytest -q app/tests/test_clinical_chat_operational.py`
- Frontend build: `cd frontend && npm run build`
