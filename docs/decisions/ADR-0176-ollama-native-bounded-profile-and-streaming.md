# ADR-0176: Perfil nativo acotado y streaming para Ollama por API

## Estado

Aceptado

## Contexto

El chat clinico local mostraba una diferencia clara frente al chat nativo de Ollama:

- el backend hacia peticiones HTTP a `/api/chat` y `/api/generate` que terminaban en `500`
- en los logs de Ollama se veian abortos por cierre de conexion del cliente
- las pruebas directas mostraron que, en este entorno, confiar en defaults runtime del API de Ollama era inestable

Ademas, el chat nativo de Ollama trabaja en modo streaming, mientras que el backend esperaba por defecto el JSON final completo.

## Decision

Se adopta para el proveedor Ollama en estilo nativo:

1. Un perfil explicito `ollama_bounded_native` en lugar de depender de defaults runtime del endpoint HTTP.
2. `options` explicitas para `num_predict`, `num_ctx`, `temperature` y `top_p`.
3. `keep_alive` explicito para evitar recargas innecesarias del runner.
4. `stream=true` en el perfil nativo y agregacion de chunks en el backend antes de devolver la respuesta final.

## Consecuencias

### Positivas

- El modo general vuelve a responder de forma consistente usando el mismo modelo local.
- Se reduce la diferencia entre el backend y el chat nativo de Ollama en el plano de transporte.
- La infraestructura queda preparada para seguir afinando prompts clinicos sin depender de defaults opacos.

### Limitaciones observadas

- Aunque el transporte mejora, una consulta clinica con prompt cargado y contexto interno puede seguir agotando tiempo en CPU local.
- Esto indica que el cuello de botella clinico restante no es solo el endpoint, sino el coste combinado de prompt + contexto + generacion.

## Validacion

- `pytest -q app/tests/test_clinical_chat_operational.py -k "llm_provider_native_style_uses_bounded_ollama_options or llm_provider_prefers_ollama_chat_endpoint_in_native_style or llm_provider_native_general_uses_quick_recovery_after_timeouts" -o addopts=""`
- `ruff check app/services/llm_chat_provider.py app/tests/test_clinical_chat_operational.py`
- Prueba real: `hola que tal` via `LLMChatProvider.generate_answer(...)` respondio correctamente con `llm_runtime_profile=ollama_bounded_native`

## Riesgos pendientes

- El flujo clinico nativo sigue necesitando simplificacion del prompt y/o particion de trabajo para CPU local.
- El streaming no sustituye por si solo una estrategia de compresion de contexto clinico.
