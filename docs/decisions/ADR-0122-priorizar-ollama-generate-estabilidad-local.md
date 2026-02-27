# ADR-0122: Priorizar Ollama /api/generate para estabilidad local del chat

- Fecha: 2026-02-25
- Estado: Aprobado

## Contexto

En ejecucion local se observaron fallos recurrentes `500` en `Ollama /api/chat` con latencias altas, provocando respuestas con `llm_used=false` y degradacion operativa aun con `CLINICAL_CHAT_LLM_ENABLED=true`.

## Decision

1. Cambiar el orden de invocacion del proveedor LLM para usar `Ollama /api/generate` como intento principal.
2. Mantener fallback a `/api/chat` y a `generate_quick_recovery` dentro del mismo presupuesto temporal.
3. Estandarizar trazabilidad LLM incluyendo `llm_enabled=true` cuando el subsistema LLM esta habilitado y `llm_primary_error` cuando falle el intento principal.

## Consecuencias

- Mejora esperada de robustez en entorno local CPU-only y menor incidencia de bucles `llm_used=false` por fallos de `/api/chat`.
- No cambia contrato externo de API.
- Se mantiene fallback seguro a respuesta basada en evidencia cuando LLM no responde.

## Validacion

- `ruff` sobre proveedor LLM y tests operacionales.
- `pytest` focal:
  - preferencia de endpoint `generate`.
  - no regresion de fallback RAG/LLM.
  - no regresion de flujo RAG e2e.

## Riesgos pendientes

- Si `/api/generate` tambien falla por recursos locales, se continuara en modo fallback estructurado sin LLM.
- Requiere reiniciar proceso uvicorn para asegurar carga de settings actualizados.
