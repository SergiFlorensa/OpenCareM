# Chat LlamaIndex + Chroma + NeMo Guardrails (Opcional, Local y OSS)

## Objetivo

Extender el chat clinico con:

- backend RAG opcional `llamaindex|chroma` para retrieval semantico local,
- capa opcional de validacion/reescritura de salida con NeMo Guardrails,
- fallback seguro al flujo existente (`legacy`) cuando no haya extras o fallen.

## Alcance tecnico

- Nuevos retrievers:
  - `app/services/llamaindex_retriever.py`
  - `app/services/chroma_retriever.py`
- Nueva capa guardrails: `app/services/nemo_guardrails_service.py`.
- Integracion en:
  - `app/services/rag_orchestrator.py` (selector de backend retrieval),
  - `app/services/clinical_chat_service.py` (post-procesado guardrails).
- Configuracion en `app/core/config.py` y `.env*`.

## Dependencias opcionales

Instalar solo si se activan estas capacidades:

```bash
pip install -r requirements.optional-rag-guardrails.txt
```

## Variables de entorno

- `CLINICAL_CHAT_RAG_RETRIEVER_BACKEND=legacy|llamaindex|chroma`
- `CLINICAL_CHAT_RAG_LLAMAINDEX_CANDIDATE_POOL=120`
- `CLINICAL_CHAT_RAG_CHROMA_CANDIDATE_POOL=200`
- `CLINICAL_CHAT_GUARDRAILS_ENABLED=true|false`
- `CLINICAL_CHAT_GUARDRAILS_CONFIG_PATH=app/guardrails`
- `CLINICAL_CHAT_GUARDRAILS_FAIL_OPEN=true|false`

## Comportamiento esperado

1. Si `RAG_RETRIEVER_BACKEND=legacy`:
   - no cambia el comportamiento respecto al estado previo.
2. Si `RAG_RETRIEVER_BACKEND=llamaindex`:
   - intenta retrieval con LlamaIndex,
   - si no hay resultado/error/no dependencia, cae a `legacy` automaticamente.
3. Si `RAG_RETRIEVER_BACKEND=chroma`:
   - intenta retrieval con Chroma local,
   - si no hay resultado/error/no dependencia, cae a `legacy` automaticamente.
4. Si `GUARDRAILS_ENABLED=true`:
   - intenta validar/reescribir respuesta final,
   - si falta config/dependencia/error y `FAIL_OPEN=true`, devuelve respuesta original.

## Trazabilidad nueva

`interpretability_trace` puede incluir:

- `rag_retriever_backend=...`
- `rag_retriever_fallback=legacy_hybrid`
- `llamaindex_available=...`
- `llamaindex_error=...`
- `chroma_available=...`
- `chroma_chunks_found=...`
- `chroma_error=...`
- `guardrails_status=...`
- `guardrails_loaded=...`
- `guardrails_fail_mode=open|closed`

## Validacion

- `ruff check` sobre modulos cambiados.
- `pytest -q app/tests/test_settings_security.py`
- `pytest -q app/tests/test_nemo_guardrails_service.py`
- `pytest -q app/tests/test_clinical_chat_operational.py`
- `pytest -q app/tests/test_care_tasks_api.py -k chat`

## Riesgos pendientes

- `llamaindex`, `chroma` y `nemoguardrails` pueden elevar latencia en hardware limitado.
- Guardrails en modo `fail_open` prioriza disponibilidad sobre bloqueo estricto.
