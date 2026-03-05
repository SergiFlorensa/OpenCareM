# ADR-0163: Modo Unico de Chat y Prioridad de Respuesta Nativa (Llama)

## Estado

Aprobado

## Contexto

El comportamiento multi-modo y los forzados de formato estaban degradando la experiencia:

- respuestas rigidas para consultas simples,
- divergencia frente al estilo nativo observado en Ollama,
- fallback prematuro a plantillas.

Se requiere operar como un chat unico, con la inteligencia del modelo nativo, usando RAG interno
solo para enriquecer contenido y citas.

## Decision

1. Modo unico efectivo:
   - `tool_mode` efectivo se fija en `chat` en backend.
   - `response_mode` no se fuerza por herramienta; se decide por senal clinica del texto.

2. Priorizacion nativa en Ollama:
   - el proveedor LLM prioriza `api/chat` cuando `CLINICAL_CHAT_LLM_NATIVE_STYLE_ENABLED=true`.
   - se evita quick-recovery forzado en ese modo para no distorsionar estilo.

3. Enriquecimiento con RAG sin imponer plantilla:
   - si hay evidencia interna relevante, se pasa como contexto y se citan fuentes breves.
   - si la sintesis LLM falla, se reaprovecha el candidato RAG antes de fallback estructurado.

## Consecuencias

- Mayor coherencia con la experiencia nativa de `llama3.2:3b`.
- Menos salida plantillada/fuerza de estilo.
- Latencia potencialmente superior al perfil ultra-estricto previo (tradeoff aceptado).

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/tests/test_clinical_chat_operational.py app/tests/test_care_tasks_api.py app/core/config.py`
- `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "response_mode_is_not_forced_by_requested_tool or llm_provider_prefers_ollama_chat_endpoint_in_native_style or llm_provider_recovers_after_primary_timeout or uses_rag_candidate_when_llm_synthesis_fails or general_answer_for_simple_greeting_is_short_and_natural" -o addopts=""`
- `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_care_tasks_api.py -k "single_chat_mode_even_if_other_tool_is_requested or supports_general_conversation_mode" -o addopts=""`
- `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
- `npm --prefix frontend run build`

## Riesgos pendientes

- Si el modelo local activo no es `llama3.2:3b`, la percepcion de estilo seguira siendo distinta.
- Ajustes de timeout/contexto insuficientes pueden seguir provocando fallback en hardware limitado.
