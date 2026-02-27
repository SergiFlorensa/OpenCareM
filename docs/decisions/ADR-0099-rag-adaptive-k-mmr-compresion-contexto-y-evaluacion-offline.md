# ADR-0099: RAG local con Adaptive-K, MMR, Compresion de Contexto y Evaluacion Offline

- Fecha: 2026-02-23
- Estado: Aprobado

## Contexto

Tras TM-142, el retrieval mejoro recall pero quedaban dos problemas practicos:

- se recuperaban pocos chunks para consultas largas o de alto riesgo;
- se enviaba contexto redundante al LLM, elevando latencia y ruido.

Adicionalmente, faltaba una forma sencilla de medir retrieval sin coste.

## Decision

Se introducen mejoras OSS/local en el pipeline RAG:

- `adaptive k` en `RAGOrchestrator` con limites min/max configurables y ajuste por:
  - longitud de consulta;
  - senales clinicas de alto riesgo.
- rerank por MMR (Maximal Marginal Relevance) para priorizar diversidad de evidencia y
  reducir duplicados semanticos.
- compresion de contexto por solape lexical con la consulta antes de inyectar chunks al prompt.
- script offline `app/scripts/evaluate_rag_retrieval.py` para medir:
  - `recall_at_k`
  - `mrr`
  - `ndcg`
  - `context_relevance`

## Consecuencias

### Positivas

- mejor cobertura en consultas complejas sin subir costes externos;
- menos redundancia en contexto enviado al LLM;
- mejor trazabilidad de retrieval con nuevas claves `rag_adaptive_k_*`, `rag_mmr_*`,
  `rag_context_compressed*`;
- evaluacion repetible de retrieval sobre dataset JSONL interno.

### Riesgos

- MMR depende de embeddings disponibles por chunk; si faltan, cae a orden base;
- compresion lexical puede omitir detalle util en consultas demasiado generales.

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/core/config.py app/services/rag_orchestrator.py app/services/rag_prompt_builder.py app/scripts/evaluate_rag_retrieval.py app/tests/test_chunking.py app/tests/test_rag_retriever.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_chunking.py app/tests/test_rag_retriever.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled or gatekeeper_flags_low_context_relevance_warning" -o addopts=""`
