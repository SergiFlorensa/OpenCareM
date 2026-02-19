# Chat RAG Hibrido Local

## Objetivo

Elevar el chat clinico para responder con mayor grounding en documentacion interna
y trazabilidad operativa, sin romper el fallback existente.

## Alcance tecnico

- Integracion de `RAGOrchestrator` en `ClinicalChatService.create_message`.
- Retrieval hibrido (`vector + keyword`) con filtros de dominio/especialidad.
- Augment de `knowledge_sources` con fragmentos RAG para que el LLM cite evidencia.
- Gatekeeper basico para detectar riesgo de respuesta generica/no fundamentada.
- Auditoria de consultas RAG en `rag_queries_audit`.
- Script de ingesta de markdown/txt:
  - `app/scripts/ingest_clinical_docs.py`

## Componentes

- `app/models/clinical_document.py`
- `app/models/document_chunk.py`
- `app/models/rag_query_audit.py`
- `app/services/document_ingestion_service.py`
- `app/services/embedding_service.py`
- `app/services/rag_retriever.py`
- `app/services/rag_prompt_builder.py`
- `app/services/rag_gatekeeper.py`
- `app/services/rag_orchestrator.py`
- `alembic/versions/d8c3f2e1a445_add_rag_tables.py`

## Configuracion

Variables nuevas:

- `CLINICAL_CHAT_RAG_ENABLED`
- `CLINICAL_CHAT_RAG_MAX_CHUNKS`
- `CLINICAL_CHAT_RAG_VECTOR_WEIGHT`
- `CLINICAL_CHAT_RAG_KEYWORD_WEIGHT`
- `CLINICAL_CHAT_RAG_EMBEDDING_MODEL`
- `CLINICAL_CHAT_RAG_ENABLE_GATEKEEPER`

## Flujo operativo recomendado

1. Aplicar migraciones:

```bash
alembic upgrade head
```

2. Ingerir documentos internos:

```bash
python -m app.scripts.ingest_clinical_docs --paths docs agents/shared
```

3. Activar RAG en entorno:

```env
CLINICAL_CHAT_RAG_ENABLED=true
```

4. Probar endpoint:

- `POST /api/v1/care-tasks/{task_id}/chat/messages`

## Validacion ejecutada

- `ruff check` sobre archivos modificados.
- `pytest -q app/tests/test_clinical_chat_operational.py`
- `pytest -q app/tests/test_care_tasks_api.py -k chat`

## Riesgos pendientes

- Sin ingesta previa, RAG no aporta chunks y cae a fallback.
- En SQLite el retrieval vectorial es lineal; con corpus grande puede aumentar latencia.
- Las metricas de validacion del gatekeeper son heuristicas y requieren calibracion continua.
