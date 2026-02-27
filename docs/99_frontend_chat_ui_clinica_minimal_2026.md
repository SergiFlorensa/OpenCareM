# Frontend Chat UI Clinica Minimal 2026

## Problema

La UI anterior mostraba demasiados paneles simultaneos y elevaba carga cognitiva en escenarios de urgencias.

## Objetivo

Reducir friccion visual y aumentar velocidad operativa sin perder transparencia de trazabilidad RAG/LLM.

## Cambios aplicados

- Rediseno completo de `frontend/src/App.tsx` y `frontend/src/styles.css`.
- Sidebar unica con:
  - historial de casos,
  - quick-actions clinicas,
  - fuentes disponibles,
  - controles (nuevo chat, exportar, feedback).
- Timeline de chat minimalista con:
  - avatares diferenciados (usuario/IA),
  - typing indicator,
  - render progresivo typewriter,
  - feedback por respuesta (thumbs up/down),
  - bloque expandible `Fuentes y referencias` por turno.
- Indicador de nivel de confianza (alto/medio/bajo) derivado de `groundedness` en trazas.
- Footer medico fijo y visible con disclaimer de seguridad clinica.
- Responsive prioritario para tablet/desktop y modo oscuro automatico por `prefers-color-scheme`.

## Contrato y compatibilidad

- Sin cambios en endpoints ni payload de API.
- El frontend consume los campos ya existentes (`history`, `memory`, `interpretability_trace`, `knowledge_sources`, `web_sources`).

## Validacion

- `cd frontend && npm run build` (OK).

## Riesgos pendientes

- El streaming actual es visual (typewriter) tras respuesta completa; no implementa SSE chunked real desde backend.
- El indicador de confianza requiere calibracion continua para evitar sobreinterpretacion clinica.
