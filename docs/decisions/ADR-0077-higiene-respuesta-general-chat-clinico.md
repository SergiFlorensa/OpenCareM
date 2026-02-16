# ADR-0077: Higiene de respuesta general para evitar volcado tecnico

## Contexto

En consultas de saludo o exploratorias en modo general (p. ej. "hola, tienes informacion de casos?"),
el fallback podia incluir snippets tecnicos crudos (JSON de recomendaciones internas),
lo que degradaba UX y confundia al profesional.

## Decision

- En `response_mode=general` priorizar respuesta conversacional breve y legible.
- No exponer snippets internos con formato JSON en salida general.
- Inyectar recomendaciones de endpoints al contexto solo cuando `response_mode=clinical`.

## Consecuencias

- Mejora claridad y tono conversacional en preguntas iniciales.
- Reduce ruido tecnico en UI para usuarios no tecnicos en primer turno.
- Riesgo: consultas muy ambiguas pueden requerir una repregunta para activar detalle clinico.
