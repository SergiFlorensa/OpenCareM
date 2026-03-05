# ADR-0162: Estilo Nativo LLM y Fallback Prioritario a Candidato RAG

## Estado

Aprobado

## Contexto

El chat estaba devolviendo salidas rigidas ("plantilla operativa") en escenarios donde el
modelo local fallaba o quedaba sobrecondicionado por prompts extensos. El equipo requiere:

- mantener respuesta del LLM en estilo nativo (similar a Ollama chat),
- combinar esa respuesta con evidencia interna cuando exista,
- evitar caer demasiado pronto en plantillas estructuradas.

## Decision

Se adopta una estrategia de ensamblado por capas:

1. Se incorpora flag de configuracion `CLINICAL_CHAT_LLM_NATIVE_STYLE_ENABLED=true`:
   - modo general: prompt casi passthrough,
   - modo clinico: instrucciones minimas + uso de evidencia interna.

2. En flujo clinico con RAG:
   - cuando RAG devuelve respuesta sin telemetria `llm_*`, se bufferiza como
     `rag_candidate` y se inyecta como contexto interno para sintesis LLM.

3. Si el segundo pase LLM falla:
   - se prioriza `rag_candidate` como respuesta final,
   - solo despues se usa fallback evidence-first o plantilla estructurada.

## Consecuencias

- Mejora naturalidad de salida cuando el LLM esta disponible.
- Se conserva utilidad de RAG cuando el LLM no responde.
- Menor frecuencia de mensajes rigidos en smalltalk y consultas generales.

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/llm_chat_provider.py app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
- `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "native_prompt_keeps_general_query_passthrough or general_answer_does_not_dump_json_snippet_for_social_query or general_answer_for_simple_greeting_is_short_and_natural or general_answer_suggests_domains_and_next_step_for_case_discovery or uses_rag_candidate_when_llm_synthesis_fails" -o addopts=""`
- `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
- `npm --prefix frontend run build`

## Riesgos pendientes

- Si el modelo configurado en `.env` no coincide con el esperado por el usuario (por ejemplo
  `qwen` vs `llama3.2`), la percepcion de estilo seguira siendo distinta aunque el pipeline este
  corregido.
- Con timeouts demasiado bajos (`CLINICAL_CHAT_LLM_TIMEOUT_SECONDS`), aumentaran los casos de
  fallback a `rag_candidate`.
