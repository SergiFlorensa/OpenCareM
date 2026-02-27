# ADR-0145: Backend RAG `elastic` opcional con fallback a `legacy`

- Fecha: 2026-02-27
- Estado: aceptado
- Alcance: `app/core/config.py`, `app/services/elastic_retriever.py`, `app/services/rag_orchestrator.py`, `.env.example`, pruebas RAG/settings.

## Contexto

El stack actual ya tiene backends `legacy|llamaindex|chroma`, pero en consultas multi-especialidad se requiere una opcion de retrieval externo con latencia estable, filtros por especialidad y resaltado de evidencia sin depender de generacion LLM.

## Decision

Se agrega backend `elastic` como opcion de `CLINICAL_CHAT_RAG_RETRIEVER_BACKEND`:

1. Nuevo servicio `ElasticRetriever` (fail-safe):
   - consulta `_search` contra Elasticsearch via HTTP nativo (sin dependencia obligatoria adicional),
   - intento inicial de consulta hibrida con clausula `semantic`,
   - retry automatico a consulta lexical cuando `semantic` no este soportado,
   - normalizacion de hits a formato compatible con `RAGContextAssembler`.
2. Integracion en `RAGOrchestrator`:
   - selector de backend ampliado a `legacy|llamaindex|chroma|elastic`,
   - fallback obligatorio a `legacy` si `elastic` no devuelve chunks.
3. Configuracion nueva en `Settings`:
   - URL, indice, timeout, pool, campos de texto, campo semantico, TLS y auth opcional.

## Consecuencias

- Positivas:
  - retrieval mas flexible en despliegues con Elasticsearch.
  - mantenimiento del comportamiento existente por fallback a `legacy`.
  - no rompe instalaciones sin Elasticsearch.
- Riesgos:
  - si el indice Elastic no esta alineado (`specialty.keyword`, campos texto), caera a fallback lexical/legacy.
  - backend adicional implica mas superficie operativa (URL/auth/TLS).

## Validacion

- `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/elastic_retriever.py app/services/rag_orchestrator.py app/tests/test_settings_security.py app/tests/test_clinical_chat_operational.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "elastic_backend or falls_back_to_legacy_when_elastic_empty" -o addopts=""`

