# ADR-0076: Parser robusto para respuestas Ollama (JSON/JSONL/SSE-like)

## Contexto

En ejecuciones reales del chat clinico, algunas respuestas del runtime local de Ollama
llegaban en formatos no estrictamente JSON unico (p. ej. lineas JSONL o prefijos
`data:` por intermediacion de proxy). El parser estricto provocaba excepciones de
decode y activaba fallback operativo, aun cuando el contenido del modelo era valido.

## Decision

Adoptar parseo tolerante en `LLMChatProvider` para:

- aceptar JSON unico como caso principal;
- soportar JSONL concatenando fragmentos de contenido;
- soportar lineas prefijadas con `data:` y marcador `[DONE]`;
- extraer texto final desde `message.content`, `response` o `content`.

## Consecuencias

- Reduce falsos negativos de integracion LLM y evita caer en fallback por formato de framing.
- Mantiene compatibilidad del contrato publico (sin cambios de payload API).
- Riesgo residual: proxies con autenticacion/cabeceras especiales pueden requerir ajuste
  adicional fuera del parser.
