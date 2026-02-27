# ADR-0126: Estabilización de latencia RAG con `k` conservador y menor pool léxico

## Estado
Aprobada (2026-02-25)

## Contexto
El benchmark mostraba latencias con cola larga (p95 alto) por consultas que
disparaban fan-out de recuperación (más chunks y pool de candidatos alto).

## Decisión
- Hacer `adaptive_k` más conservador:
  - short query: `base_k - 1`
  - long query: `base_k + 1`
  - high risk: subir como máximo a `base_k` si quedó por debajo.
  - soft cap final: `base_k + 1`.
- Reducir carga de recuperación/contexto por defecto:
  - `CLINICAL_CHAT_RAG_MAX_CHUNKS=2`
  - `CLINICAL_CHAT_RAG_MAX_CHUNKS_HARD=6`
  - `CLINICAL_CHAT_RAG_FTS_CANDIDATE_POOL=96`
  - `CLINICAL_CHAT_RAG_COMPRESS_MAX_CHARS=280`
  - `CLINICAL_CHAT_RAG_CONTEXTUAL_SPELL_MAX_CANDIDATES=12`

## Impacto esperado
- Menor varianza de latencia (especialmente p95/p99).
- Menor coste de CPU por request.
- Ligero riesgo de pérdida de recall en consultas muy amplias.

## Validación
- `ruff`:
  - `app/core/config.py`
  - `app/services/rag_orchestrator.py`
- `pytest`:
  - `app/tests/test_rag_orchestrator_optimizations.py`
  - subset provider en `app/tests/test_clinical_chat_operational.py`
  - `app/tests/test_settings_security.py`
- `evaluate_rag_retrieval` sin regresión material en dataset de control.

