# ADR-0098: RAG Gratuito Mejorado (Chunking Recursivo, Expansion de Consulta y Embeddings Resilientes)

- Fecha: 2026-02-23
- Estado: Aprobado

## Contexto

El objetivo operativo es elevar calidad/velocidad del chat clinico sin coste de
licencias ni APIs externas. Persistian tres problemas en entorno local:

- chunking insuficiente en bloques largos (perdida de contexto util en retrieval);
- baja recuperacion para consultas ambiguas o con sinonimia clinica;
- errores de embeddings en Ollama por exceso de longitud de entrada.

## Decision

Se implementa una mejora 100% OSS/local:

- `SemanticChunker` con division recursiva de bloques largos
  (lineas -> frases -> corte duro) y overlap real entre chunks;
- `HybridRetriever` con expansion lexical de consulta (HyDE-lite sin LLM
  externo) y ampliacion de terminos por dominio/especialidad;
- `OllamaEmbeddingService` con segmentacion por ventanas + mean pooling para
  textos largos, evitando fallback agresivo por `input length exceeds context`;
- `BasicGatekeeper` añade chequeo de relevancia de contexto (`context_relevance`)
  configurable.
- `ingest_clinical_docs` amplía mapeo por defecto para rutas
  `docs/pdf_raw/<especialidad>/`.

## Consecuencias

### Positivas

- Mayor recall en retrieval interno para dudas clinicas con sinonimos.
- Menos fallos de embeddings en documentos PDF extensos.
- Mejor continuidad semantica entre chunks por overlap efectivo.
- Mayor auditabilidad de calidad (faithfulness + context relevance).

### Riesgos

- La expansion lexical puede introducir ruido en queries poco especificas.
- El chunking mas fino incrementa numero de chunks y coste de indexacion local.

## Validacion

- `.\venv\Scripts\python.exe -m ruff check app/core/chunking.py app/services/embedding_service.py app/services/rag_retriever.py app/services/rag_orchestrator.py app/services/rag_gatekeeper.py app/core/config.py app/tests/test_chunking.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py app/tests/test_clinical_chat_operational.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_chunking.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py -q`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "gatekeeper_flags_low_faithfulness_as_risk or gatekeeper_flags_low_context_relevance_warning or uses_rag_when_enabled"`
