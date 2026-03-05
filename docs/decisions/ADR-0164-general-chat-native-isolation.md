# ADR-0164: Aislamiento del Modo General para Respuesta Nativa de Llama

## Estado

Aprobado

## Contexto

En consultas no clinicas, el chat estaba derivando a respuestas no nativas por dos causas:

- inyeccion de contexto clinico (`domain_catalog`/fuentes internas) en prompts generales,
- timeouts en modo nativo con caida a fallback estructurado.

Esto rompia la experiencia esperada frente a Ollama chat nativo.

## Decision

1. Aislar modo general:
   - en `response_mode=general` no se inyectan `matched_domains` ni `knowledge_sources` clinicas.
   - se evita fallback implicito a `critical_ops` en salida general.

2. Recuperacion por timeout orientada a conversacion:
   - en modo nativo-general, si fallan intentos primario/secundario, se permite quick-recovery con prompt neutral (no clinico).
   - se acota memoria conversacional efectiva para prompt general (`ultimos 2 turnos`) y se limita `num_predict`.

3. Validacion automatizada:
   - nuevo smoke e2e `app/scripts/smoke_native_chat.py` con criterios de pass/fail.

## Consecuencias

- Mejora fuerte en naturalidad de salida general.
- Menor contaminacion de contexto clinico en preguntas no medicas.
- Mantiene flujo clinico con RAG/fallback de seguridad sin cambios de contrato API.

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/scripts/smoke_native_chat.py app/tests/test_clinical_chat_operational.py app/tests/test_care_tasks_api.py`
- `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "llm_provider_native_general_uses_quick_recovery_after_timeouts or llm_provider_prefers_ollama_chat_endpoint_in_native_style" -o addopts=""`
- `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k "chat_message_supports_general_conversation_mode" -o addopts=""`
- `$env:DEBUG='false'; .\venv\Scripts\python.exe -m app.scripts.smoke_native_chat --seed 26 --turns 4` (`RESULT=PASS`)

## Riesgos pendientes

- En hardware local CPU, conversaciones muy largas pueden aumentar latencia.
- El modo clinico conserva fallback extractivo por seguridad cuando la sintesis LLM no es fiable.
