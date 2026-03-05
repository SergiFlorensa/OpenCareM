# ADR-0165: Paridad de Runtime Nativo con Ollama para `llama3.2:3b`

## Estado

Aprobado

## Contexto

El chat general mostraba dos problemas frente a la experiencia nativa de Ollama:

- cortes de respuesta por limites de salida forzados (`num_predict` bajo),
- degradacion a fallback no nativo por timeouts y apertura de circuit breaker.

Ademas, la revision del modelo local (`ollama show llama3.2:3b`) confirma que el Modelfile define solo `stop` y no fija `temperature`, `num_predict`, `num_ctx` ni `top_p`.

## Decision

1. En modo nativo (`CLINICAL_CHAT_LLM_NATIVE_STYLE_ENABLED=true`) con proveedor `ollama`:
   - no enviar `options` en `api/chat` ni `api/generate`,
   - no enviar `keep_alive` forzado.
   - resultado: se usan los defaults reales del runtime Ollama.

2. En modo general nativo:
   - prompt base pasa a consulta directa (sin instruccion extra de brevedad),
   - se amplia presupuesto de timeout para CPU local,
   - no se abre circuit breaker por timeout en este modo para evitar caida persistente a fallback no nativo.

3. Se agrega test de regresion:
   - `test_llm_provider_native_style_uses_ollama_runtime_defaults`.

## Consecuencias

- Salida mas parecida al chat nativo de Ollama.
- Menos cortes y menos respuestas fallback en conversacion general.
- Latencia potencialmente mayor en hardware local al no limitar salida con `num_predict`.

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/services/llm_chat_provider.py app/tests/test_clinical_chat_operational.py`
- `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "llm_provider_native_style_uses_ollama_runtime_defaults or llm_provider_native_general_uses_quick_recovery_after_timeouts or llm_provider_prefers_ollama_chat_endpoint_in_native_style or llm_provider_recovers_after_primary_timeout" -o addopts=""`
- `$env:DEBUG='false'; .\venv\Scripts\python.exe -m app.scripts.smoke_native_chat --seed 26 --turns 4` (`RESULT=PASS`)

## Riesgos pendientes

- En prompts muy largos puede aumentar p95 de latencia en CPU local.
- Se mantiene fallback clinico de seguridad para flujos medicos cuando la sintesis LLM falla.
