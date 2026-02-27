# ADR-0139: HybridRAG local con QA shortcut offline-first

- Fecha: 2026-02-26
- Estado: aceptada
- Alcance: `app/services/rag_orchestrator.py`, `app/core/config.py`

## Contexto

El stack local (CPU, sin GPU) sufre latencia en inferencia LLM y variabilidad en consultas
largas. El documento `hybrid.md` propone un patron HybridRAG: resolver primero por
matching de Q/A pre-generadas y dejar el resto para fallback extractivo.

El sistema ya tenia `custom_questions` en `document_chunks`, pero no existia una etapa
de matching dedicada antes del retrieval pesado.

## Decision

Se agrega una etapa `QA shortcut` previa al retrieval dominio/hibrido:

1. Normaliza la query y busca candidatos en `custom_questions` (mas pistas de
   `section_path`, `keywords` y preview de `chunk_text`).
2. Puntua por cobertura lexica y bonus de estructura/especialidad.
3. Si supera umbral, corta por la ruta rapida y usa esos chunks para la respuesta
   extractiva con trazabilidad.
4. Si no hay match confiable, continua flujo actual (domain/hybrid) sin bloqueo.

Configuracion nueva:

- `CLINICAL_CHAT_RAG_QA_SHORTCUT_ENABLED`
- `CLINICAL_CHAT_RAG_QA_SHORTCUT_MIN_SCORE`
- `CLINICAL_CHAT_RAG_QA_SHORTCUT_TOP_K`
- `CLINICAL_CHAT_RAG_QA_SHORTCUT_MAX_CANDIDATES`

## Consecuencias

- Reduce costo de retrieval en casos con preguntas recurrentes o bien cubiertas por
  `custom_questions`.
- Mantiene seguridad operacional: sin match confiable, no inventa; cae al flujo RAG
  existente y al fallback extractivo/safe-wrapper.
- Riesgo conocido: cobertura parcial si el banco de `custom_questions` es pobre en ciertas
  especialidades; requiere mejorar ingesta/curacion para explotar todo el valor del atajo.

## Validacion

- `ruff` sobre config/orchestrator/tests.
- `pytest` de `app/tests/test_rag_orchestrator_optimizations.py` (14 passed).
- `pytest` de `app/tests/test_settings_security.py -k qa_shortcut` (2 passed).
