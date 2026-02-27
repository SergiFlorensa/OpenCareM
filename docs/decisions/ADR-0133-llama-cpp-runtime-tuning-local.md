# ADR-0133: Tuning de runtime local con `llama.cpp` para estabilidad de chat clinico

- Fecha: 2026-02-25
- Estado: Aprobada

## Contexto
Con `ollama` se observaban `TimeoutError` y apertura de circuito (`CircuitOpen`) en benchmark, con degradacion de calidad al caer en respuestas de fallback.

## Decision
Se fija `llama.cpp` como proveedor local base en configuracion:
1. `CLINICAL_CHAT_LLM_PROVIDER=llama_cpp`
2. `CLINICAL_CHAT_LLM_BASE_URL=http://127.0.0.1:8080`
3. `CLINICAL_CHAT_LLM_MODEL=Phi-3-mini-4k-instruct-q4.gguf`
4. `CLINICAL_CHAT_LLM_TIMEOUT_SECONDS=18`
5. `CLINICAL_CHAT_LLM_CIRCUIT_BREAKER_FAILURE_THRESHOLD=4`
6. `CLINICAL_CHAT_LLM_CIRCUIT_BREAKER_OPEN_SECONDS=20`
7. `CLINICAL_CHAT_RAG_LLM_MIN_REMAINING_BUDGET_MS=400`

## Consecuencias
- Menor probabilidad de fallo por timeout transitorio del motor local.
- Menos activacion prematura de circuito abierto.
- Mantiene costo cero y despliegue offline/local.

## Validacion
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py::test_allows_llama_cpp_provider app/tests/test_clinical_chat_operational.py::test_extract_llama_cpp_answer_openai_compatible_payload -o addopts=""`
