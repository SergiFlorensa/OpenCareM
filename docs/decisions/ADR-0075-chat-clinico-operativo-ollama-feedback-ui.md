# ADR-0075: Refuerzo operativo del chat clinico con recomendaciones internas y UI simplificada

## Contexto
El chat clinico necesitaba mejorar continuidad conversacional, trazabilidad del uso LLM y utilidad operativa en consultas breves de seguimiento. Tambien hacia falta simplificar la UI para reducir friccion en guardia.

## Decision
- Reforzar el contexto enviado al LLM con:
  - ultimos turnos de sesion,
  - resultados reales de recomendaciones internas por endpoint,
  - metadatos de fuentes internas/externas.
- Mantener preferencia de `POST /api/chat` en Ollama con fallback a `POST /api/generate`.
- Registrar trazas operativas en cada respuesta (`llm_used`, `llm_model`, `llm_endpoint`, `llm_latency_ms`, `query_expanded`, `matched_endpoints`).
- Integrar `_fetch_recommendations` para inyectar recomendaciones internas de endpoints detectados en el razonamiento del chat.
- Simplificar frontend del chat con menus desplegables y panel de trazas clave visible.

## Consecuencias
### Positivas
- Mayor continuidad en follow-up y mejor respuesta contextual.
- Menor dependencia de plantillas de fallback genericas.
- Mejor depuracion clinica con trazas visibles en frontend.

### Costes / trade-offs
- Las recomendaciones internas sintetizadas son heuristicas y requieren validacion humana.
- La experiencia final sigue dependiendo de disponibilidad de Ollama local.

## Validacion
- `ruff check` en backend/frontend modificado.
- `pytest` focalizado en continuidad y trazabilidad de chat.
- `npm run build` para validar compilacion UI.
