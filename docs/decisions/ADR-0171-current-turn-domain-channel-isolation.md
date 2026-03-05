# ADR-0171: Aislamiento por canal del dominio actual en chat clinico

## Contexto

El chat clinico ya corregia parte de la deriva de dominio entre turnos y priorizaba `evidence_first` cuando el LLM o el RAG extractivo fallaban. Aun quedaba un problema operativo: una consulta del turno actual podia entrar en el dominio correcto pero arrastrar fragmentos de otro canal o de PDFs demasiado especificos del mismo dominio.

Caso observado:

- turno 1: oncologia
- turno 2: `Paciente con dolor abdominal: datos clave y escalado`

Aunque `effective_specialty` y `matched_domains` ya resolvian `gastro_hepato`, el ensamblado final podia aceptar:

- un `rag_candidate` extractivo degradado, o
- una mezcla de `knowledge_sources` donde sobrevivian PDFs especificos como `Colestasis`

Eso producia respuestas con contenido ajeno a la intencion real del turno.

## Decision

Se introduce aislamiento explicito de fuentes por dominio del turno actual en `ClinicalChatService` y `RAGOrchestrator`:

1. Nuevo filtro `_filter_knowledge_sources_for_current_turn(...)`.
2. El filtro usa `matched_domains` del turno para conservar solo fuentes alineadas con ese canal.
3. Si la consulta es generica-operativa y el turno resuelve a un unico dominio, se priorizan fuentes operativas `.md` y se descartan PDFs especificos del mismo canal cuando existe un motor operativo mejor alineado.
4. El filtro se aplica:
   - despues de construir `knowledge_sources` iniciales,
   - despues de mezclar `rag_sources`.
5. En `RAGOrchestrator`, antes de construir `rag_sources` y montar el prompt del LLM, se filtran `chunk_dicts` del turno actual para conservar el canal correcto y, en consultas operativas genericas de dominio unico, priorizar motores `.md` frente a PDFs especificos.
6. El fallback `evidence_first` se habilita tambien cuando existe `rag_candidate_answer` y `knowledge_sources`, aunque `rag_chunks_retrieved` no venga informado, para no aceptar extractivos degradados por omision de metadata.

## Consecuencias

- Cada turno se resuelve con su canal actual siempre que el routing de dominio sea correcto.
- Cambios de tema entre turnos ya no contaminan el ensamblado final con bloques o fuentes de la conversacion anterior.
- Para consultas genericas operativas, el sistema favorece el motor operativo de la especialidad y evita snippets PDF demasiado concretos tanto en el ensamblado final como en el contexto que recibe el LLM.
- No cambia el contrato HTTP ni el modelo de datos.

## Riesgos

- Si `matched_domains` identifica mal el dominio, el aislamiento consolidara un canal equivocado en vez de corregirlo.
- En consultas verdaderamente compuestas el sistema sigue permitiendo varios bloques; si se requiere aislamiento total incluso en prompts compuestos, habra que descomponer la query antes del retrieval.

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "current_turn_keeps_only_current_domain_channel or filter_knowledge_sources_for_current_turn_prefers_operational_md_in_single_domain or prefers_evidence_first_when_rag_is_extractive_after_llm_failure" -o addopts=""`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -k "filter_chunks_for_current_turn_domain_prefers_operational_md_for_single_domain or build_rag_sources_prefers_operational_docs_over_pdf_when_scores_tie or extractive_answer_prefers_operational_doc_for_generic_symptom_query" -o addopts=""`
- `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
- `.\venv\Scripts\python.exe -m ruff check app/services/rag_orchestrator.py app/tests/test_rag_orchestrator_optimizations.py`
- Sonda `TestClient` con cambio de tema entre turnos:
  - turno 1 oncologia,
  - turno 2 dolor abdominal,
  - resultado: `effective_specialty=gastro_hepato`, `matched_domains=gastro_hepato`, `internal_sources=1`, `rag_current_turn_domain_filter=1`, salida final sin `Oncologia` ni `Colestasis`.
