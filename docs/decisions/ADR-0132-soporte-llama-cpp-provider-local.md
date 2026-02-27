# ADR-0132: Soporte local de `llama_cpp` como proveedor LLM alternativo

- Fecha: 2026-02-25
- Estado: Aprobada

## Contexto
El flujo con Ollama presento `TimeoutError` + `CircuitOpen` y `llm_used_true_rate=0.0` en benchmark. Se requiere alternativa local sin coste por token.

## Decision
1. Extender `CLINICAL_CHAT_LLM_PROVIDER` para admitir `llama_cpp`.
2. Implementar cliente OpenAI-compatible para `POST /v1/chat/completions`.
3. Mantener compatibilidad total con ruta Ollama existente.

## Consecuencias
- Permite comparar estabilidad real entre motores locales sin cambiar contrato HTTP externo.
- Mantiene costo cero (sin API de pago).

## Validacion
- Tests de settings y parseo de respuesta OpenAI-compatible.
