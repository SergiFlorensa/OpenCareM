# Tablero de Tareas

## Formato de item

- ID:
- Objetivo:
- Alcance:
- Agentes involucrados:
- Estado: pendiente | en curso | bloqueado | completado
- Dependencias:
- Evidencia:

## Items activos

- ID: TM-203

- Objetivo: Implementar algoritmos discursivos explicitos en codigo (TextTiling, EDUs, cadenas lexicas, LCD con operaciones vectoriales y entity-grid) y conectarlos al reranking real del chat clinico.

- Alcance: `app/services/rag_orchestrator.py`, `app/tests/test_rag_orchestrator_optimizations.py`, contratos/docs.

- Agentes involucrados: orchestrator, api-agent, qa-agent.

- Estado: completado

- Dependencias: TM-202.

- Evidencia:

  - `./venv/Scripts/python.exe -m ruff check app/services/rag_orchestrator.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py`
  - `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
  - `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`

- ID: TM-202

- Objetivo: Mejorar coherencia de respuesta RAG clinica offline con reranking discursivo (RST heuristico, centering de entidades y coherencia local/LCD) sobre evidencia interna.

- Alcance: `.env.example`, `app/core/config.py`, `app/services/rag_orchestrator.py`, `app/tests/test_rag_orchestrator_optimizations.py`, `app/tests/test_settings_security.py`, contratos/docs.

- Agentes involucrados: orchestrator, api-agent, qa-agent.

- Estado: completado

- Dependencias: TM-201.

- Evidencia:

  - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/rag_orchestrator.py app/services/clinical_chat_service.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py`
  - `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
  - `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`

- ID: TM-201

- Objetivo: Reducir latencia y evitar fallback razonado en RAG clinico local con modo fact-only, early-goal test y memoizacion con poda por estado resoluble.

- Alcance: `.env.example`, `app/core/config.py`, `app/services/rag_orchestrator.py`, `app/services/clinical_chat_service.py`, `app/tests/test_rag_orchestrator_optimizations.py`, `app/tests/test_settings_security.py`, contratos/docs.

- Agentes involucrados: orchestrator, api-agent, qa-agent.

- Estado: completado

- Dependencias: TM-200.

- Evidencia:

  - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/rag_orchestrator.py app/services/clinical_chat_service.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py`
  - `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`

- ID: TM-200

- Objetivo: Endurecer pipeline RAG clinico con verificacion de evidencia tipo cross-encoder proxy, abstencion/fallback lexical y compresion iterativa por evidencialidad (ECoRAG-like), con citas granulares.

- Alcance: `.env.example`, `app/core/config.py`, `app/services/rag_orchestrator.py`, `app/services/rag_prompt_builder.py`, `app/tests/test_rag_orchestrator_optimizations.py`, `app/tests/test_settings_security.py`, contratos/docs.

- Agentes involucrados: orchestrator, api-agent, qa-agent.

- Estado: completado

- Dependencias: TM-199.

- Evidencia:

  - `./venv/Scripts/python.exe -m ruff check app/services/rag_orchestrator.py app/services/rag_prompt_builder.py app/core/config.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py`
  - `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`

- ID: TM-199

- Objetivo: Mejorar calidad de recuperacion/ensamblado del chat clinico con segmentacion multi-intento, reranking accionable y anclaje fino de fuentes (sin activar cambios de embeddings).

- Alcance: `.env.example`, `app/core/config.py`, `app/services/rag_orchestrator.py`, `app/services/clinical_chat_service.py`, `app/tests/test_rag_orchestrator_optimizations.py`, `app/tests/test_settings_security.py`, contratos/docs.

- Agentes involucrados: orchestrator, api-agent, qa-agent.

- Estado: completado

- Dependencias: TM-193, TM-194.

- Evidencia:

  - `./venv/Scripts/python.exe -m ruff check app/services/clinical_chat_service.py app/services/rag_orchestrator.py app/core/config.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py`
  - `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`

- ID: TM-197

- Objetivo: Modernizar UI del frontend de chat con stack de componentes actual (Tailwind + daisyUI + iconos), manteniendo funcionalidad anonima.

- Alcance: `frontend/src/App.tsx`, `frontend/src/styles.css`, `frontend/tailwind.config.js`, `frontend/postcss.config.js`, `frontend/package.json`, `frontend/package-lock.json`.

- Agentes involucrados: orchestrator, api-agent, qa-agent.

- Estado: completado

- Dependencias: TM-196.

- Evidencia:

  - `npm --prefix frontend install -D tailwindcss@3 postcss autoprefixer daisyui@latest`
  - `npm --prefix frontend install lucide-react@latest`
  - `npm --prefix frontend run build`

- ID: TM-196

- Objetivo: Eliminar requisito de credenciales en frontend de chat y permitir acceso directo anonimo.

- Alcance: `frontend/src/App.tsx`.

- Agentes involucrados: orchestrator, api-agent, qa-agent.

- Estado: completado

- Dependencias: TM-194.

- Evidencia:

  - `npm --prefix frontend run build`

- ID: TM-195

- Objetivo: Implementar Regression Sets de chat (continual learning offline) con export desde historial y evaluacion automatica contra backend para deteccion de regresiones.

- Alcance: `app/scripts/build_chat_regression_set.py`, `app/scripts/evaluate_chat_regression.py`, `app/tests/test_build_chat_regression_set_script.py`, `app/tests/test_evaluate_chat_regression_script.py`, contratos/docs.

- Agentes involucrados: orchestrator, data-agent, qa-agent.

- Estado: completado

- Dependencias: TM-194.

- Evidencia:

  - `.\venv\Scripts\python.exe -m py_compile app/scripts/build_chat_regression_set.py app/scripts/evaluate_chat_regression.py app/tests/test_build_chat_regression_set_script.py app/tests/test_evaluate_chat_regression_script.py`
  - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_build_chat_regression_set_script.py app/tests/test_evaluate_chat_regression_script.py -o addopts=""`
  - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m app.scripts.build_chat_regression_set --limit 40 --output tmp/chat_regression_set.jsonl`
  - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m app.scripts.evaluate_chat_regression --dataset tmp/chat_regression_set.jsonl --output tmp/chat_regression_eval_summary.json`

- ID: TM-194

- Objetivo: Incorporar capa CIR determinista para ambiguedad (pregunta de clarificacion proactiva) y sugerencias de siguiente consulta util (NQP-lite), manteniendo latencia y benchmark.

- Alcance: `app/services/clinical_chat_service.py`, `app/tests/test_clinical_chat_operational.py`.

- Agentes involucrados: orchestrator, api-agent, qa-agent.

- Estado: completado

- Dependencias: TM-144.

- Evidencia:

  - `.\venv\Scripts\python.exe -m py_compile app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
  - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "ambiguity_gate_triggers_for_short_low_context_query or ambiguity_gate_skips_structured_query or pick_clarification_question_prefers_domain_bank or next_query_suggestions_are_generated_for_domain or clarifying_answer_renders_suggestions_block or general_answer_suggests_domains_and_next_step_for_case_discovery or semantic_parser_and_dst_recovers_entity_from_history" -o addopts=""`
  - `.\venv\Scripts\python.exe tmp/run_chat_benchmark.py; .\venv\Scripts\python.exe tmp/summarize_chat_benchmark.py; .\venv\Scripts\python.exe tmp/check_acceptance.py`

- ID: TM-144

- Objetivo: Introducir DST ligero y parser semantico determinista para consultas multi-turno (entidad/intencion), con nota de seguridad en intencion de dosis sin evidencia numerica.

- Alcance: `app/services/clinical_chat_service.py`, `app/services/rag_orchestrator.py`, `app/tests/test_clinical_chat_operational.py`, `app/tests/test_rag_orchestrator_optimizations.py`.

- Agentes involucrados: orchestrator, api-agent, qa-agent.

- Estado: completado

- Dependencias: TM-143.

- Evidencia:

  - `.\venv\Scripts\python.exe -m py_compile app/services/clinical_chat_service.py app/services/rag_orchestrator.py app/tests/test_clinical_chat_operational.py app/tests/test_rag_orchestrator_optimizations.py`
  - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "history_attention_rewrite_prioritizes_relevant_turns or semantic_parser_and_dst_recovers_entity_from_history" -o addopts=""`
  - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -k "extractive_answer_adds_dose_safety_note_when_no_numeric_dose_found" -o addopts=""`
  - `.\venv\Scripts\python.exe tmp/run_chat_benchmark.py; .\venv\Scripts\python.exe tmp/summarize_chat_benchmark.py; .\venv\Scripts\python.exe tmp/check_acceptance.py`

- ID: TM-143

- Objetivo: Añadir HAM ligero para reescritura contextual y ranking híbrido extractivo+generativo proxy con penalización logarítmica.

- Alcance: `app/services/clinical_chat_service.py`, `app/services/rag_orchestrator.py`, `app/tests/test_clinical_chat_operational.py`, `app/tests/test_rag_orchestrator_optimizations.py`.

- Agentes involucrados: orchestrator, api-agent, qa-agent.

- Estado: completado

- Dependencias: TM-142.

- Evidencia:

  - `.\venv\Scripts\python.exe -m py_compile app/services/clinical_chat_service.py app/services/rag_orchestrator.py app/tests/test_clinical_chat_operational.py app/tests/test_rag_orchestrator_optimizations.py`
  - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "follow_up_query_expansion or contextual_query_rewrite_handles_coreference or history_attention_rewrite_prioritizes_relevant_turns or clean_evidence_snippet_removes_heading_noise" -o addopts=""`
  - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -k "extractive_answer_filters_non_clinical_noise or extractive_answer_prioritizes_query_overlap_over_noise_chunks or extractive_answer_coarse_to_fine_prefers_actionable_sentences or query_overlap_log_scaling_rewards_relevant_sentence or generative_proxy_score_prefers_well_formed_sentence" -o addopts=""`
  - `.\venv\Scripts\python.exe tmp/run_chat_benchmark.py; .\venv\Scripts\python.exe tmp/summarize_chat_benchmark.py; .\venv\Scripts\python.exe tmp/check_acceptance.py`

- ID: TM-142

- Objetivo: Implementar pipeline extractivo coarse-to-fine (relevancia→evidencia→centralidad con MMR ligero) para mejorar coherencia y accionabilidad.

- Alcance: `app/services/rag_orchestrator.py`, `app/tests/test_rag_orchestrator_optimizations.py`.

- Agentes involucrados: orchestrator, api-agent, qa-agent.

- Estado: completado

- Dependencias: TM-140.

- Evidencia:

  - `.\venv\Scripts\python.exe -m py_compile app/services/rag_orchestrator.py app/tests/test_rag_orchestrator_optimizations.py`
  - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -k "extractive_answer_filters_non_clinical_noise or extractive_answer_prioritizes_query_overlap_over_noise_chunks or extractive_answer_coarse_to_fine_prefers_actionable_sentences" -o addopts=""`
  - `.\venv\Scripts\python.exe tmp/run_chat_benchmark.py; .\venv\Scripts\python.exe tmp/summarize_chat_benchmark.py; .\venv\Scripts\python.exe tmp/check_acceptance.py`

- ID: TM-141

- Objetivo: Alinear CQU y retrieval: usar consulta reescrita contextual (`effective_query`) en llamada a RAG.

- Alcance: `app/services/clinical_chat_service.py`.

- Agentes involucrados: orchestrator, api-agent, qa-agent.

- Estado: completado

- Dependencias: TM-139.

- Evidencia:

  - `.\venv\Scripts\python.exe -m py_compile app/services/clinical_chat_service.py`
  - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "follow_up_query_expansion or contextual_query_rewrite_handles_coreference or clean_evidence_snippet_removes_heading_noise" -o addopts=""`

- ID: TM-140

- Objetivo: Mejorar calidad de respuesta RAG con ranking query-aware, filtrado de ruido documental y metrica de seguridad de fuga interna en benchmark.

- Alcance: `app/services/rag_orchestrator.py`, `app/services/clinical_chat_service.py`, `tmp/summarize_chat_benchmark.py`, `tmp/check_acceptance.py`, `app/tests/test_rag_orchestrator_optimizations.py`, `app/tests/test_clinical_chat_operational.py`.

- Agentes involucrados: orchestrator, api-agent, qa-agent.

- Estado: completado

- Dependencias: TM-139.

- Evidencia:

  - `.\venv\Scripts\python.exe -m py_compile app/services/rag_orchestrator.py app/services/clinical_chat_service.py tmp/summarize_chat_benchmark.py tmp/check_acceptance.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_clinical_chat_operational.py`
  - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -k "extractive_answer_filters_non_clinical_noise or extractive_answer_prioritizes_query_overlap_over_noise_chunks" -o addopts=""`
  - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "follow_up_query_expansion or contextual_query_rewrite_handles_coreference or clean_evidence_snippet_removes_heading_noise" -o addopts=""`

- ID: TM-139

- Objetivo: Mejorar CIR con reescritura contextual de consultas (elipsis/correferencia) para seguimiento multi-turno.

- Alcance: `app/services/clinical_chat_service.py`, `app/tests/test_clinical_chat_operational.py`.

- Agentes involucrados: orchestrator, api-agent, qa-agent.

- Estado: completado

- Dependencias: TM-138.

- Evidencia:

  - `.\venv\Scripts\python.exe -m py_compile app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
  - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "follow_up_query_expansion or contextual_query_rewrite_handles_coreference" -o addopts=""`

- ID: TM-137
- Objetivo: AÃƒÂ±adir quality gate de incertidumbre bayesiana (varianza posterior) con fail-fast controlado para evitar latencias inutiles y reforzar abstencion segura.
- Alcance: `app/core/config.py`, `app/services/clinical_math_inference_service.py`, `app/services/clinical_chat_service.py`, `.env`, `.env.example`.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-136.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/services/clinical_math_inference_service.py app/core/config.py`
  - `.\venv\Scripts\python.exe -m pytest app/tests/test_clinical_chat_operational.py::test_chat_e2e_uses_rag_when_enabled -q -o addopts=""`
  - `.\venv\Scripts\python.exe -m pytest app/tests/test_clinical_chat_operational.py::test_chat_e2e_uses_interrogatory_short_circuit_before_llm_or_rag -q -o addopts=""`

- ID: TM-136
- Objetivo: Implementar fallback clinico evidence-first cuando LLM entra en timeout/quality-gate para evitar respuesta generica.
- Alcance: `app/services/clinical_chat_service.py`, `app/services/chroma_retriever.py`, `app/services/embedding_service.py`.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-135.
- Evidencia:
  - `.\venv\Scripts\python.exe -m pytest app/tests/test_clinical_chat_operational.py::test_chat_e2e_uses_rag_when_enabled -q -o addopts=""`
  - `.\venv\Scripts\python.exe -m pytest app/tests/test_clinical_chat_operational.py::test_chat_e2e_uses_interrogatory_short_circuit_before_llm_or_rag -q -o addopts=""`

- ID: TM-135
- Objetivo: Consolidar UX de chat general eliminando especialidad visible en respuesta clinica y quitando sesgo de specialty del caso.
- Alcance: `app/services/clinical_chat_service.py`, `frontend/src/App.tsx`.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-134.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py frontend/src/App.tsx`

- ID: TM-134
- Objetivo: Aplicar reordenado de dominios por seÃƒÂ±al matematica y exponer incertidumbre (margen/entropia) en chat clinico.
- Alcance: `app/services/clinical_chat_service.py`, `app/services/clinical_math_inference_service.py`, `app/tests/test_clinical_chat_operational.py`, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-133.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_math_inference_service.py app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "math_inference_service or domain_rerank_uses_math_top_domain_when_confident"`

- ID: TM-133
- Objetivo: Integrar capa matematica de similitud (coseno + L2) y posterior Bayes local para priorizacion clinica en chat.
- Alcance: `app/services/clinical_math_inference_service.py`, `app/services/clinical_chat_service.py`, `app/services/__init__.py`, `app/tests/test_clinical_chat_operational.py`, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-132.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_math_inference_service.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_chat_operational.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "math_inference_service"`

- ID: TM-132
- Objetivo: Integrar contratos operativos por dominio (fase 1: nefrologia y ginecologia/obstetricia) en chat clinico con guard de fallback estructurado.
- Alcance: `app/services/clinical_protocol_contracts_service.py`, `app/services/clinical_chat_service.py`, `app/services/__init__.py`, `app/tests/test_clinical_chat_operational.py`, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-131.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_protocol_contracts_service.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_chat_operational.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "logic_engine or protocol_contract"`

- ID: TM-131
- Objetivo: Extender el motor logico clinico con codificacion estructural (Godel), consistencia formal y abstencion por evidencia insuficiente.
- Alcance: `app/services/clinical_logic_engine_service.py`, `app/services/clinical_chat_service.py`, `app/tests/test_clinical_chat_operational.py`, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-130.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_logic_engine_service.py app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "logic_engine"`

- ID: TM-130
- Objetivo: Integrar motor logico clinico determinista (reglas secuente + contradicciones + trazabilidad epistemica) en chat clinico.
- Alcance: `app/services/clinical_logic_engine_service.py`, `app/services/clinical_chat_service.py`, `app/services/__init__.py`, `app/tests/test_clinical_chat_operational.py`, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-127, TM-128.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_logic_engine_service.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_chat_operational.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "logic_engine or psychology or interrogatory"`

- ID: TM-129
- Objetivo: Habilitar ingesta nativa de PDF multipagina para RAG local.
- Alcance: `app/services/document_ingestion_service.py`, `app/scripts/ingest_clinical_docs.py`, `requirements.txt`, `app/tests/test_document_ingestion_service.py`, contratos/docs.
- Agentes involucrados: orchestrator, data-agent, qa-agent.
- Estado: completado
- Dependencias: TM-128.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/document_ingestion_service.py app/scripts/ingest_clinical_docs.py app/tests/test_document_ingestion_service.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_document_ingestion_service.py`

- ID: TM-128
- Objetivo: Incorporar evidencia local adjunta en el chat clinico para contexto multimodal minimo (texto/metadata de PDF-imagen-informe) sin servicios de pago.
- Alcance: `app/schemas/clinical_chat.py`, `app/services/clinical_chat_service.py`, `app/tests/test_clinical_chat_operational.py`, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-127.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/schemas/clinical_chat.py app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "local_evidence or psychology or interrogatory"`

- ID: TM-127
- Objetivo: Integrar capa de psicologia de decision clinica (Fechner + Prospect framing) para mejorar comunicacion de riesgo y trazabilidad.
- Alcance: `app/services/clinical_decision_psychology_service.py`, `app/services/clinical_chat_service.py`, `app/services/__init__.py`, `app/tests/test_clinical_chat_operational.py`, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-126.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_decision_psychology_service.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_chat_operational.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "psychology or interrogatory or quality_gate or rag_validation_warns"`

- ID: TM-126
- Objetivo: Implementar interrogatorio clinico activo (Bayes + DEIG) para reducir respuestas genericas y pedir datos faltantes antes de responder.
- Alcance: `app/services/diagnostic_interrogatory_service.py`, `app/services/clinical_chat_service.py`, `app/schemas/clinical_chat.py`, `app/tests/test_clinical_chat_operational.py`, contratos/docs asociados.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-125.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/diagnostic_interrogatory_service.py app/services/clinical_chat_service.py app/schemas/clinical_chat.py app/tests/test_clinical_chat_operational.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "interrogatory or quality_gate or rag_validation_warns"`

- ID: TM-125
- Objetivo: Blindar calidad en ruta RAG ante placeholders y validacion RAG en warning.
- Alcance: `app/services/clinical_chat_service.py`, `app/tests/test_clinical_chat_operational.py`.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-124.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "rag_validation_warns or rag_quality_gate_applies_to_rag_answer_too or quality_gate"`

- ID: TM-124
- Objetivo: Evitar fuga de respuestas RAG de baja calidad heredando `llm_trace` del orquestador y aplicando gates tambien en ruta RAG.
- Alcance: `app/services/clinical_chat_service.py`, `app/tests/test_clinical_chat_operational.py`.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-123.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "rag_quality_gate_applies_to_rag_answer_too or quality_gate"`

- ID: TM-123
- Objetivo: Mejorar profesionalidad de respuesta clinica con ciclo draft->verify->rewrite y quality gates anti-refusal/anti-truncado.
- Alcance: `app/services/llm_chat_provider.py`, `app/services/clinical_chat_service.py`, `.env`, `app/tests/test_clinical_chat_operational.py`.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-122.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/tests/test_clinical_chat_operational.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "quality_gate or rewrite or routing"`

- ID: TM-122
- Objetivo: Alinear enrutado de chat con todas las especialidades clinicas configuradas para evitar caida sistematica a `critical_ops`.
- Alcance: `app/services/clinical_chat_service.py` (catalogo de dominios, fallback, hints e indice de conocimiento por especialidad).
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-121.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "specialty or domain or routing"`

- ID: TM-121
- Objetivo: Priorizar enrutado por intencion clinica sobre especialidad base `emergency` y habilitar dominio ginecologia/obstetricia.
- Alcance: `app/services/clinical_chat_service.py`.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-119, TM-120.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py`

- ID: TM-120
- Objetivo: Curar fuentes oficiales externas (OMS/CDC/ECDC/Ministerio) para sarampion/tosferina e incorporarlas al RAG local.
- Alcance: `docs/86_fuentes_oficiales_sarampion_tosferina.md`, `app/scripts/ingest_clinical_docs.py`, indice RAG local.
- Agentes involucrados: orchestrator, data-agent, qa-agent.
- Estado: completado
- Dependencias: TM-119.
- Evidencia:
  - `.\venv\Scripts\python.exe -m app.scripts.ingest_clinical_docs --paths docs/86_fuentes_oficiales_sarampion_tosferina.md`
  - prueba de chat con `use_web_sources=true` y verificacion de `knowledge_sources`/`interpretability_trace`.

- ID: TM-119
- Objetivo: Reestructurar RAG clinico para reducir ruido no clinico y facilitar ingesta progresiva por especialidad.
- Alcance: `app/services/rag_orchestrator.py`, `app/services/document_ingestion_service.py`, `app/scripts/ingest_clinical_docs.py`, `docs/94_chat_clinico_operativo_ollama_local_runbook.md`, `app/tests/test_clinical_chat_operational.py`.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-118.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/rag_orchestrator.py app/services/document_ingestion_service.py app/scripts/ingest_clinical_docs.py app/tests/test_clinical_chat_operational.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py`
  - `.\venv\Scripts\python.exe -m app.scripts.ingest_clinical_docs --backfill-only`

- ID: TM-118
- Objetivo: Evitar respuestas clinicas genericas/cortas y reforzar auto-deteccion de consultas clinicas en lenguaje natural.
- Alcance: `app/services/clinical_chat_service.py`, `app/tests/test_clinical_chat_operational.py`, `agents/shared/*`, `docs/decisions/*`.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-117.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py`

- ID: TM-117
- Objetivo: Eliminar degradacion de chat local (sin fuentes + `llm_used=false` por timeout) en entorno de desarrollo.
- Alcance: `app/services/clinical_chat_service.py`, `app/services/llm_chat_provider.py`, `.env`, `agents/shared/*`, `docs/decisions/*`.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-110.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/tests/test_clinical_chat_operational.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py`
  - `.\venv\Scripts\python.exe` invocando `LLMChatProvider.generate_answer(...)` con `llm_used=true` y latencia ~6.8s.

- ID: TM-110
- Objetivo: Hacer el chat clinico totalmente automatico por intencion de texto, sin depender de especialidad manual.
- Alcance: `app/services/clinical_chat_service.py`, `app/schemas/clinical_chat.py`, `frontend/src/App.tsx`, `app/tests/test_clinical_chat_operational.py`.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-095, TM-098, TM-099.
- Evidencia:
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py`
  - `npm run build` en `frontend/`
  - Ajustes de contrato/documentacion en `agents/shared/api_contract.md`, `agents/shared/test_plan.md`, `docs/decisions/ADR-0083-chat-auto-routing-por-intencion-sin-especialidad-manual.md`.

- ID: TM-001
- Objetivo: Documentar setup MCP en Codex CLI y marco de agentes.
- Alcance: `docs/` + `agents/`.
- Agentes involucrados: orchestrator, mcp-agent, qa-agent.
- Estado: completado
- Dependencias: API y MCP server local operativos.
- Evidencia:
  - `codex mcp list`
  - `codex mcp get task-manager-api --json`
  - Estructura documental creada en `docs/` y `agents/`.

- ID: TM-002
- Objetivo: Implementar tests API y smoke MCP.
- Alcance: `app/tests/` y `mcp_server/client.py`.
- Agentes involucrados: orchestrator, qa-agent, mcp-agent.
- Estado: completado
- Dependencias: fixtures de DB aislada para FastAPI.
- Evidencia:
  - `.\venv\Scripts\python.exe -m pytest -q`
  - `4 passed`

- ID: TM-003
- Objetivo: Migrar gestion de esquema a Alembic.
- Alcance: `alembic/`, `alembic.ini`, decision arquitectonica y docs.
- Agentes involucrados: orchestrator, data-agent, qa-agent.
- Estado: completado
- Dependencias: modelo `Task` y metadata SQLAlchemy.
- Evidencia:
  - `alembic revision --autogenerate -m "init tasks table"`
  - `alembic upgrade head`
  - `alembic current`
  - `f1b3f75c533d (head)`
  - `docs/decisions/ADR-0001-alembic-schema-source-of-truth.md`

- ID: TM-004
- Objetivo: Eliminar deprecaciones de lifecycle y fijar config local de pytest/coverage.
- Alcance: `app/main.py` + `pytest.ini` + actualizacion de docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: suite de tests existente (`app/tests/`).
- Evidencia:
  - Migracion a `lifespan` en `app/main.py`
  - Config local en `pytest.ini`
  - `pytest -q` ejecutado en raiz del repo

- ID: TM-005
- Objetivo: Eliminar warning de Pydantic settings legacy.
- Alcance: `app/core/config.py` y actualizacion de docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: `pydantic-settings` v2.
- Evidencia:
  - Migracion de `class Config` a `SettingsConfigDict`
  - `pytest -q` ejecutado tras el cambio

- ID: TM-006
- Objetivo: Estabilizar flujo local de calidad (lint, format, type-check).
- Alcance: `pyproject.toml`, ajustes de formato/codigo y guia operativa.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: suite de tests y packaging local de `mcp_server`.
- Evidencia:
  - `ruff check app mcp_server`
  - `black --check app mcp_server`
  - `mypy app mcp_server`
  - `pytest -q`
  - `docs/06_quality_workflow.md`

- ID: TM-007
- Objetivo: Activar CI automatizado para calidad, migraciones y tests.
- Alcance: `.github/workflows/ci.yml` + documentacion de flujo.
- Agentes involucrados: orchestrator, devops-agent, qa-agent.
- Estado: completado
- Dependencias: TM-003 (Alembic) y TM-006 (quality tools).
- Evidencia:
  - `.github/workflows/ci.yml`
  - `docs/06_quality_workflow.md` (seccion CI)
  - `ruff`, `black`, `mypy`, `pytest` en verde local

- ID: TM-008
- Objetivo: Containerizar arranque local con Docker Compose (API + PostgreSQL).
- Alcance: `docker/Dockerfile`, `docker-compose.yml`, `.dockerignore`, docs de uso.
- Agentes involucrados: orchestrator, devops-agent, qa-agent.
- Estado: completado
- Dependencias: TM-003 (Alembic) y TM-007 (CI base).
- Evidencia:
  - `docker-compose.yml`
  - `docker/Dockerfile`
  - `docs/07_docker_compose_workflow.md`

- ID: TM-009
- Objetivo: Endurecer imagen Docker de API para entorno runtime.
- Alcance: `docker/Dockerfile` (multi-stage + non-root) y docs.
- Agentes involucrados: orchestrator, devops-agent, qa-agent.
- Estado: completado
- Dependencias: TM-008.
- Evidencia:
  - `docker build -f docker/Dockerfile -t task-manager-api:hardening-test .`
  - `docs/07_docker_compose_workflow.md` (seccion hardening)

- ID: TM-010
- Objetivo: Separar configuracion por entorno para local y Docker.
- Alcance: `.env.example`, `.env.docker`, `docker-compose.yml`, documentacion.
- Agentes involucrados: orchestrator, devops-agent, qa-agent.
- Estado: completado
- Dependencias: TM-008.
- Evidencia:
  - `.env.example`
  - `.env.docker`
  - `docker-compose.yml` usando `env_file`
  - `docs/08_environment_strategy.md`

- ID: TM-011
- Objetivo: Aplicar baseline de seguridad en configuracion de settings.
- Alcance: `app/core/config.py`, tests de seguridad y documentacion.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-010.
- Evidencia:
  - `app/core/config.py` con validaciones por entorno
  - `app/tests/test_settings_security.py`
  - `docs/09_security_baseline.md`

- ID: TM-012
- Objetivo: Crear fundacion de autenticacion JWT en capa core.
- Alcance: utilidades de seguridad, exports core y tests unitarios.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-011.
- Evidencia:
  - `app/core/security.py`
  - `app/tests/test_security_core.py`
  - `docs/10_auth_foundation.md`

- ID: TM-013
- Objetivo: Exponer flujo auth minimo en API.
- Alcance: `app/api/auth.py`, servicio auth, tests de endpoints y docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-012.
- Evidencia:
  - `app/api/auth.py`
  - `app/tests/test_auth_api.py`
  - `docs/11_auth_api_workflow.md`

- ID: TM-014
- Objetivo: Migrar auth de credenciales demo a usuarios persistentes.
- Alcance: modelo `User`, migraciones, auth service DB, tests y docs.
- Agentes involucrados: orchestrator, data-agent, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-013.
- Evidencia:
  - `app/models/user.py`
  - `alembic/versions/74e6f2319a21_add_users_table.py`
  - `app/services/auth_service.py` con consulta a DB
  - `app/tests/test_auth_api.py` sembrando usuario en test DB

- ID: TM-015
- Objetivo: Agregar registro de usuario con validacion de password.
- Alcance: endpoint `/auth/register`, servicio auth y pruebas de casos invalidos.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-014.
- Evidencia:
  - `app/api/auth.py` (`/auth/register`)
  - `app/core/security.py` (`validate_password_policy`)
  - `app/tests/test_auth_api.py` con casos de registro

- ID: TM-016
- Objetivo: Crear bootstrap seguro de primer admin por CLI.
- Alcance: migracion de rol admin, servicio bootstrap, script CLI y tests.
- Agentes involucrados: orchestrator, data-agent, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-015.
- Evidencia:
  - `app/scripts/bootstrap_admin.py`
  - `app/services/auth_service.py` (`bootstrap_first_admin`)
  - `app/tests/test_auth_bootstrap.py`
  - `docs/12_bootstrap_admin_cli.md`

- ID: TM-017
- Objetivo: Agregar control de permisos admin (RBAC v1) para endpoints protegidos.
- Alcance: dependencias auth, endpoint admin de usuarios, pruebas y documentacion.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-016.
- Evidencia:
  - `app/api/deps.py`
  - `app/api/auth.py` (`/auth/admin/users`)
  - `app/tests/test_auth_api.py`
  - `docs/13_admin_rbac.md`

- ID: TM-018
- Objetivo: Endurecer auth JWT con refresh tokens y rotacion.
- Alcance: modelo de sesion refresh, endpoints `/auth/refresh` y `/auth/logout`, pruebas y docs.
- Agentes involucrados: orchestrator, data-agent, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-017.
- Evidencia:
  - `app/models/auth_session.py`
  - `app/api/auth.py` (`/auth/refresh`, `/auth/logout`)
  - `app/tests/test_auth_api.py`
  - `docs/14_refresh_token_workflow.md`

- ID: TM-019
- Objetivo: Crear tests unitarios para `TaskService`.
- Alcance: cobertura de CRUD y conteo de tareas en capa servicio (sin HTTP).
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-018.
- Evidencia:
  - `app/tests/test_task_service_unit.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_task_service_unit.py`

- ID: TM-020
- Objetivo: Agregar script de smoke test MCP reproducible.
- Alcance: script CLI de smoke para tools MCP, ampliacion de test y documentacion.
- Agentes involucrados: orchestrator, mcp-agent, qa-agent.
- Estado: completado
- Dependencias: TM-019.
- Evidencia:
  - `mcp_server/smoke.py`
  - `app/tests/test_mcp_smoke.py`
  - `docs/15_mcp_smoke_runbook.md`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_mcp_smoke.py`

- ID: TM-021
- Objetivo: Documentar flujo de error handling de la API.
- Alcance: catalogo de errores HTTP, causas, ejemplos y pasos de diagnostico.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-020.
- Evidencia:
  - `docs/16_error_handling_workflow.md`

- ID: TM-022
- Objetivo: Agregar logging estructurado por request.
- Alcance: middleware con request_id, status_code, latencia y metodo/ruta.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-021.
- Evidencia:
  - `app/main.py`
  - `app/tests/test_request_logging.py`
  - `docs/17_request_logging.md`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_request_logging.py`

- ID: TM-023
- Objetivo: Exponer metricas Prometheus en endpoint dedicado.
- Alcance: instrumentacion HTTP, endpoint `/metrics`, pruebas y documentacion.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-022.
- Evidencia:
  - `app/main.py`
  - `app/tests/test_metrics_endpoint.py`
  - `docs/18_prometheus_metrics.md`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py`

- ID: TM-024
- Objetivo: Integrar Prometheus real en Docker Compose para scraping continuo.
- Alcance: servicio `prometheus`, config `prometheus.yml` y documentacion de uso.
- Agentes involucrados: orchestrator, devops-agent, qa-agent.
- Estado: completado
- Dependencias: TM-023.
- Evidencia:
  - `docker-compose.yml`
  - `ops/prometheus/prometheus.yml`
  - `docs/19_prometheus_compose_setup.md`
  - `docs/decisions/ADR-0004-prometheus-compose-scraping.md`

- ID: TM-025
- Objetivo: Integrar Grafana en Docker Compose con dashboard base.
- Alcance: servicio `grafana`, datasource hacia Prometheus y dashboard inicial para API.
- Agentes involucrados: orchestrator, devops-agent, qa-agent.
- Estado: completado
- Dependencias: TM-024.
- Evidencia:
  - `docker-compose.yml`
  - `ops/grafana/provisioning/datasources/datasource.yml`
  - `ops/grafana/provisioning/dashboards/dashboard.yml`
  - `ops/grafana/dashboards/task_manager_overview.json`
  - `docs/20_grafana_setup.md`
  - `docs/decisions/ADR-0005-grafana-compose-dashboard-baseline.md`

- ID: TM-026
- Objetivo: Mitigar brute force en login con rate limit por usuario+IP.
- Alcance: tabla de intentos, bloqueo temporal, settings, tests y documentacion.
- Agentes involucrados: orchestrator, api-agent, data-agent, qa-agent.
- Estado: completado
- Dependencias: TM-025.
- Evidencia:
  - `app/models/login_attempt.py`
  - `app/services/login_throttle_service.py`
  - `app/api/auth.py`
  - `app/tests/test_auth_api.py`
  - `docs/21_login_rate_limit.md`
  - `docs/decisions/ADR-0006-login-bruteforce-protection.md`

- ID: TM-027
- Objetivo: Agregar triage inteligente de tareas con recomendaciones explicables.
- Alcance: endpoint AI de sugerencia (`priority`, `category`, `confidence`, `reason`) + tests + docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-026.
- Evidencia:
  - `app/services/ai_triage_service.py`
  - `app/api/ai.py`
  - `app/tests/test_ai_api.py`
  - `docs/22_ai_task_triage.md`
  - `docs/decisions/ADR-0007-ai-triage-rules-first.md`

- ID: TM-028
- Objetivo: Crear skills de proyecto para potenciar agentes con workflows reutilizables.
- Alcance: skills de orquestacion, entrega API y observabilidad basados en guia oficial.
- Agentes involucrados: orchestrator, api-agent, devops-agent, qa-agent.
- Estado: completado
- Dependencias: TM-027.
- Evidencia:
  - `skills/tm-orchestrator-workflow/SKILL.md`
  - `skills/tm-api-change-delivery/SKILL.md`
  - `skills/tm-observability-ops/SKILL.md`
  - `docs/23_project_skills_playbook.md`

- ID: TM-029
- Objetivo: Crear fundacion de ejecucion de agentes con trazabilidad por pasos.
- Alcance: modelos `AgentRun` y `AgentStep`, endpoint `/api/v1/agents/run`, pruebas y documentacion.
- Agentes involucrados: orchestrator, api-agent, data-agent, qa-agent.
- Estado: completado
- Dependencias: TM-027.
- Evidencia:
  - `app/models/agent_run.py`
  - `app/services/agent_run_service.py`
  - `app/api/agents.py`
  - `alembic/versions/5dc1b6a8f4aa_add_agent_runs_and_steps_tables.py`
  - `app/tests/test_agents_api.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_agents_api.py`

- ID: TM-030
- Objetivo: Evolucionar triage AI a modo configurable rules/hybrid con provider opcional.
- Alcance: settings AI mode, servicio de provider LLM opcional, tests y documentacion.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-029.
- Evidencia:
  - `app/core/config.py` (`AI_TRIAGE_MODE`)
  - `app/services/llm_triage_provider.py`
  - `app/services/ai_triage_service.py`
  - `app/schemas/ai.py` (campo `source`)
  - `app/tests/test_ai_api.py`
  - `docs/25_ai_triage_hybrid_mode.md`
  - `docs/decisions/ADR-0010-ai-triage-hybrid-mode-with-safe-fallback.md`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_ai_api.py app/tests/test_agents_api.py`

- ID: TM-031
- Objetivo: Exponer historial de ejecuciones de agentes para operacion y debugging.
- Alcance: endpoints para listar corridas y ver detalle por `run_id`, tests y documentacion.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-030.
- Evidencia:
  - `app/api/agents.py` (`GET /agents/runs`, `GET /agents/runs/{run_id}`)
  - `app/services/agent_run_service.py` (consulta de historial)
  - `app/schemas/agent.py` (summary response)
  - `app/tests/test_agents_api.py` (list/detail/404)
  - `docs/26_agent_run_history_endpoints.md`
  - `docs/decisions/ADR-0011-agent-run-history-api.md`

- ID: TM-032
- Objetivo: Mejorar operacion con filtros de historial de corridas agente.
- Alcance: filtros por estado, workflow y ventana temporal en `GET /agents/runs`, con pruebas y docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-031.
- Evidencia:
  - `app/api/agents.py` (query params de filtro)
  - `app/services/agent_run_service.py` (filtro por estado/workflow/fechas)
  - `app/tests/test_agents_api.py` (tests de filtros)
  - `docs/27_agent_run_history_filters.md`
  - `docs/decisions/ADR-0012-agent-run-history-filtering.md`

- ID: TM-033
- Objetivo: Exponer resumen operativo de agentes para monitoreo rapido.
- Alcance: endpoint de summary con total runs, failed runs y fallback rate, mas pruebas y docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-032.
- Evidencia:
  - `app/services/agent_run_service.py` (`get_ops_summary`)
  - `app/api/agents.py` (`GET /agents/ops/summary`)
  - `app/tests/test_agents_api.py` (test de summary)
  - `docs/28_agent_ops_summary.md`
  - `docs/decisions/ADR-0013-agent-ops-summary-metrics.md`

- ID: TM-034
- Objetivo: Visualizar salud de agentes en Grafana con metricas Prometheus dedicadas.
- Alcance: metricas exportadas en `/metrics`, paneles de dashboard y documentacion operativa.
- Agentes involucrados: orchestrator, api-agent, devops-agent, qa-agent.
- Estado: completado
- Dependencias: TM-033.
- Evidencia:
  - `app/metrics/agent_metrics.py`
  - `app/main.py` (registro de metricas agentes)
  - `app/tests/test_metrics_endpoint.py` (metricas `agent_*`)
  - `ops/grafana/dashboards/task_manager_overview.json` (paneles de agentes)
  - `docs/29_agent_prometheus_grafana_metrics.md`
  - `docs/decisions/ADR-0014-agent-observability-metrics-in-prometheus.md`

- ID: TM-035
- Objetivo: Corregir visualizacion en Grafana para paneles de metricas agente.
- Alcance: activar consultas instantaneas en paneles stat/gauge y documentar recarga.
- Agentes involucrados: orchestrator, devops-agent.
- Estado: completado
- Dependencias: TM-034.
- Evidencia:
  - `ops/grafana/dashboards/task_manager_overview.json` (targets con `instant=true`)
  - `docs/29_agent_prometheus_grafana_metrics.md` (pasos de recarga)

- ID: TM-036
- Objetivo: Activar alertas basicas para salud de agentes.
- Alcance: reglas por `failed_runs` y `fallback_rate_percent`, documentacion operativa y validacion.
- Agentes involucrados: orchestrator, devops-agent, qa-agent.
- Estado: completado
- Dependencias: TM-035.
- Evidencia:
  - `ops/prometheus/alerts.yml`
  - `ops/prometheus/prometheus.yml` (`rule_files`)
  - `docker-compose.yml` (montaje de `alerts.yml`)
  - `docs/30_agent_alerts_baseline.md`
  - `docs/decisions/ADR-0015-agent-alerts-baseline.md`

- ID: TM-037
- Objetivo: Integrar Alertmanager para enrutar alertas de Prometheus.
- Alcance: configuracion base de Alertmanager, conexion desde Prometheus y documentacion operativa.
- Agentes involucrados: orchestrator, devops-agent.
- Estado: completado
- Dependencias: TM-036.
- Evidencia:
  - `ops/alertmanager/alertmanager.yml`
  - `ops/prometheus/prometheus.yml` (bloque `alerting`)
  - `docker-compose.yml` (servicio `alertmanager`)
  - `docs/31_alertmanager_integration.md`
  - `docs/decisions/ADR-0016-alertmanager-routing-baseline.md`

- ID: TM-038
- Objetivo: Iniciar pivot de dominio a Clinical Ops Copilot sin romper la base actual.
- Alcance: contratos API/Datos/QA/DevOps, roadmap incremental y guia didactica de Fase 1.
- Agentes involucrados: orchestrator, api-agent, data-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-037.
- Evidencia:
  - `docs/32_clinical_ops_pivot_phase1.md`
  - `docs/33_care_tasks_api_workflow.md`
  - `docs/05_roadmap.md` (seccion Clinical Ops)
  - `app/models/care_task.py`
  - `app/api/care_tasks.py`
  - `alembic/versions/a4c2d1e9b7f0_add_care_tasks_table.py`

- ID: TM-039
- Objetivo: Iniciar castellanizacion progresiva del repositorio (es-ES) sin romper compatibilidad.
- Alcance: mensajes visibles de API, documentacion reciente y estrategia global de migracion.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-038.
- Evidencia:
  - `app/api/care_tasks.py`
  - `app/api/auth.py`
  - `app/api/agents.py`
  - `app/api/ai.py`
  - `app/core/security.py`
  - `app/services/agent_run_service.py`
  - `app/services/ai_triage_service.py`
  - `app/services/auth_service.py`
  - `app/services/login_throttle_service.py`
  - `app/services/llm_triage_provider.py`
  - `app/scripts/bootstrap_admin.py`
  - `mcp_server/server.py`
  - `mcp_server/smoke.py`
  - `skills/` (skills y referencias traducidas)
  - `docs/` (encabezados y guias principales en espanol)
  - `docs/34_castellanizacion_repositorio.md`
  - `agents/shared/api_contract.md`
  - `agents/shared/data_contract.md`
  - `agents/shared/mcp_contract.md`
  - `agents/shared/test_plan.md`
  - `agents/shared/deploy_notes.md`




- ID: TM-040
- Objetivo: Conectar CareTask con trazabilidad de agente via endpoint de triage por recurso.
- Alcance: `POST /api/v1/care-tasks/{id}/triage`, servicio de ejecucion, pruebas y documentacion.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-038, TM-029, TM-033.
- Evidencia:
  - Implementacion en `app/api/care_tasks.py` y `app/services/agent_run_service.py`.
  - Pruebas en `app/tests/test_care_tasks_api.py`.
  - Documento operativo en `docs/35_care_task_agent_triage_workflow.md`.
  - Decision tecnica en `docs/decisions/ADR-0018-care-task-triage-via-resource-endpoint.md`.
  - Validacion: `.\venv\Scripts\python.exe -m pytest -q app/tests`.

- ID: TM-041
- Objetivo: Cerrar human-in-the-loop con aprobacion explicita de triaje en CareTask.
- Alcance: `POST /api/v1/care-tasks/{id}/triage/approve`, persistencia de revision, pruebas y docs.
- Agentes involucrados: orchestrator, api-agent, data-agent, qa-agent.
- Estado: completado
- Dependencias: TM-040.
- Evidencia:
  - Modelo y migracion de `care_task_triage_reviews`.
  - Endpoint en `app/api/care_tasks.py`.
  - Pruebas en `app/tests/test_care_tasks_api.py`.
  - Documento `docs/36_care_task_triage_human_approval.md`.
  - Decision tecnica en `docs/decisions/ADR-0019-human-in-the-loop-care-task-triage-approval.md`.
  - Validacion: `.\venv\Scripts\python.exe -m pytest -q app/tests`.

- ID: TM-042
- Objetivo: Integrar contexto operativo realista de urgencias para guiar agentes y flujos.
- Alcance: catalogos de areas/circuitos/roles/procedimientos/estandares y endpoints de consulta.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-041.
- Evidencia:
  - API `clinical-context` en `app/api/clinical_context.py`.
  - Servicio catalogo en `app/services/clinical_context_service.py`.
  - Pruebas en `app/tests/test_clinical_context_api.py`.
  - Documento `docs/37_contexto_operaciones_clinicas_urgencias_es.md`.
  - Decision tecnica en `docs/decisions/ADR-0020-clinical-context-catalog-api.md`.
  - Validacion: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_context_api.py`.
  - Regresion completa: `.\venv\Scripts\python.exe -m pytest -q app/tests`.

- ID: TM-043
- Objetivo: Incorporar recurso `TriageLevel` con estandar Manchester y SLA de respuesta.
- Alcance: schema, servicio, endpoint y pruebas para niveles 1-5.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-042.
- Evidencia:
  - Schema `TriageLevelResponse` en `app/schemas/clinical_context.py`.
  - Endpoint `GET /api/v1/clinical-context/triage-levels/manchester`.
  - Pruebas de integridad en `app/tests/test_clinical_context_api.py`.
  - Documento tecnico `docs/38_manchester_triage_levels.md`.
  - Decision tecnica `docs/decisions/ADR-0021-manchester-triage-levels-canonical-catalog.md`.
  - Validacion: `.\venv\Scripts\python.exe -m pytest -q app/tests`.

- ID: TM-044
- Objetivo: Auditar over-triage y under-triage comparando IA vs validacion humana.
- Alcance: modelo de auditoria, endpoints, metricas y pruebas.
- Agentes involucrados: orchestrator, data-agent, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-043.
- Evidencia:
  - Tabla `care_task_triage_audit_logs` y migracion `c1d4e8f92b30`.
  - Endpoints `POST/GET /care-tasks/{id}/triage/audit` y `GET /summary`.
  - Metricas Prometheus `triage_audit_*` en `/metrics`.
  - Documento `docs/39_triage_audit_logs.md`.
  - ADR `docs/decisions/ADR-0022-triage-audit-over-under-classification.md`.
  - Validacion: `.\venv\Scripts\python.exe -m pytest -q app/tests`.

- ID: TM-045
- Objetivo: Implementar motor de protocolo respiratorio para decisiones tempranas en urgencias.
- Alcance: recomendacion operativa (diagnostico/prueba/antiviral/aislamiento), endpoint y trazabilidad.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-044.
- Evidencia:
  - Servicio `app/services/respiratory_protocol_service.py`.
  - Endpoint `POST /api/v1/care-tasks/{id}/respiratory-protocol/recommendation`.
  - Workflow `respiratory_protocol_v1` persistido en `agent_runs` y `agent_steps`.
  - Metricas `respiratory_protocol_runs_total` y `respiratory_protocol_runs_completed_total` en `/metrics`.
  - Documento tecnico `docs/40_motor_protocolo_respiratorio.md`.
  - ADR `docs/decisions/ADR-0023-motor-protocolo-respiratorio-operativo.md`.
  - Validacion: `.\venv\Scripts\python.exe -m pytest -q app/tests`.

- ID: TM-046
- Objetivo: Implementar motor de humanizacion pediatrica neuro-oncologica con validacion humana obligatoria.
- Alcance: recomendacion operativa familiar/psicosocial/multidisciplinar, endpoint y trazabilidad.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-045.
- Evidencia:
  - Servicio `app/services/humanization_protocol_service.py`.
  - Schema `app/schemas/humanization_protocol.py`.
  - Endpoint `POST /api/v1/care-tasks/{id}/humanization/recommendation`.
  - Workflow `pediatric_neuro_onco_support_v1` persistido en `agent_runs` y `agent_steps`.
  - Metricas `pediatric_humanization_runs_total` y `pediatric_humanization_runs_completed_total` en `/metrics`.
  - Documento tecnico `docs/41_motor_humanizacion_pediatrica.md`.
  - ADR `docs/decisions/ADR-0024-motor-humanizacion-pediatrica-operativa.md`.
  - Validacion: `.\venv\Scripts\python.exe -m pytest -q app/tests`.

- ID: TM-047
- Objetivo: Implementar motor de screening operativo avanzado (geriatria, VIH/sepsis, COVID persistente y eficiencia long-acting).
- Alcance: recomendaciones interpretables, control de fatiga de alarmas, endpoint, trazabilidad y metricas.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-046.
- Evidencia:
  - Servicio `app/services/advanced_screening_service.py`.
  - Schema `app/schemas/advanced_screening.py`.
  - Endpoint `POST /api/v1/care-tasks/{id}/screening/recommendation`.
  - Workflow `advanced_screening_support_v1` persistido en `agent_runs` y `agent_steps`.
  - Metricas en `/metrics`: `advanced_screening_runs_total`, `advanced_screening_runs_completed_total`, `advanced_screening_alerts_generated_total`, `advanced_screening_alerts_suppressed_total`.
  - Documento `docs/42_motor_screening_operativo_avanzado.md`.
  - ADR `docs/decisions/ADR-0025-motor-screening-operativo-avanzado.md`.
  - Validacion: `.\venv\Scripts\python.exe -m pytest -q app/tests`.

- ID: TM-048
- Objetivo: Auditar calidad del screening avanzado comparando recomendacion IA operativa vs validacion humana.
- Alcance: persistencia de auditoria, endpoints de registro/listado/resumen y metricas de calidad por regla.
- Agentes involucrados: orchestrator, data-agent, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-047.
- Evidencia:
  - Modelo `app/models/care_task_screening_audit_log.py`.
  - Migracion `alembic/versions/d2a7c9b4e110_add_care_task_screening_audit_logs_table.py`.
  - Endpoints `POST/GET /care-tasks/{id}/screening/audit` y `GET /summary`.
  - Metricas `screening_audit_*` y `screening_rule_*_match_rate_percent` en `/metrics`.
  - Documento `docs/43_auditoria_calidad_screening.md`.
  - ADR `docs/decisions/ADR-0026-auditoria-calidad-screening-avanzado.md`.
  - Validacion: `.\venv\Scripts\python.exe -m pytest -q app/tests`.

- ID: TM-049
- Objetivo: Implementar motor de soporte de interpretacion radiografica de torax (operativo, no diagnostico).
- Alcance: endpoint de apoyo por patrones/signos, trazabilidad de workflow, metricas y pruebas.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-048.
- Evidencia:
  - Servicio `app/services/chest_xray_support_service.py`.
  - Schema `app/schemas/chest_xray_support.py`.
  - Endpoint `POST /api/v1/care-tasks/{id}/chest-xray/interpretation-support`.
  - Workflow `chest_xray_support_v1` en `agent_runs` y `agent_steps`.
  - Metricas `chest_xray_support_runs_total`, `chest_xray_support_runs_completed_total`, `chest_xray_support_critical_alerts_total`.
  - Documento `docs/44_soporte_interpretacion_rx_torax.md`.
  - ADR `docs/decisions/ADR-0027-soporte-operativo-interpretacion-rx-torax.md`.
  - Validacion: `.\venv\Scripts\python.exe -m pytest -q app/tests`.

- ID: TM-050
- Objetivo: Implementar motor de soporte medico-legal operativo para urgencias.
- Alcance: endpoint por CareTask, checklist legal, alertas criticas, trazabilidad en agente, metricas y pruebas.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-049.
- Evidencia:
  - Servicio `app/services/medicolegal_ops_service.py`.
  - Schema `app/schemas/medicolegal_ops.py`.
  - Endpoint `POST /api/v1/care-tasks/{id}/medicolegal/recommendation`.
  - Workflow `medicolegal_ops_support_v1` en `agent_runs` y `agent_steps`.
  - Metricas `medicolegal_ops_runs_total`, `medicolegal_ops_runs_completed_total`, `medicolegal_ops_critical_alerts_total`.
  - Documento `docs/45_motor_medico_legal_urgencias.md`.
  - ADR `docs/decisions/ADR-0028-soporte-operativo-medico-legal-urgencias.md`.
  - Validacion: `.\venv\Scripts\python.exe -m pytest -q app/tests`.

- ID: TM-051
- Objetivo: Auditar calidad del soporte medico-legal comparando recomendacion IA vs validacion humana.
- Alcance: persistencia de auditoria, endpoints de registro/listado/resumen y metricas de precision por regla.
- Agentes involucrados: orchestrator, data-agent, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-050.
- Evidencia:
  - Modelo `app/models/care_task_medicolegal_audit_log.py`.
  - Migracion `alembic/versions/e4b7a1d9c220_add_care_task_medicolegal_audit_logs_table.py`.
  - Endpoints `POST/GET /care-tasks/{id}/medicolegal/audit` y `GET /summary`.
  - Metricas `medicolegal_audit_*` y `medicolegal_rule_*_match_rate_percent` en `/metrics`.
  - Documento `docs/46_auditoria_calidad_medico_legal.md`.
  - ADR `docs/decisions/ADR-0029-auditoria-calidad-medico-legal.md`.
  - Validacion: `.\venv\Scripts\python.exe -m pytest -q app/tests`.

- ID: TM-052
- Objetivo: Implementar motor operativo de sepsis para urgencias.
- Alcance: endpoint por CareTask, reglas qSOFA/bundle/escalado, trazabilidad de workflow y metricas.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-051.
- Evidencia:
  - Servicio `app/services/sepsis_protocol_service.py`.
  - Schema `app/schemas/sepsis_protocol.py`.
  - Endpoint `POST /api/v1/care-tasks/{id}/sepsis/recommendation`.
  - Workflow `sepsis_protocol_support_v1` en `agent_runs` y `agent_steps`.
  - Metricas `sepsis_protocol_runs_total`, `sepsis_protocol_runs_completed_total`, `sepsis_protocol_critical_alerts_total`.
  - Documento `docs/47_motor_sepsis_urgencias.md`.
  - ADR `docs/decisions/ADR-0030-motor-operativo-sepsis-urgencias.md`.
  - Validacion: `.\venv\Scripts\python.exe -m pytest -q app/tests`.

- ID: TM-053
- Objetivo: Modelar flujo extremo-a-extremo de urgencias con etapas y transiciones trazables.
- Alcance: recurso `EmergencyEpisode`, endpoints de proceso, KPIs de tiempos y documentacion.
- Agentes involucrados: orchestrator, api-agent, data-agent, qa-agent.
- Estado: completado
- Dependencias: TM-052.
- Evidencia:
  - Modelo `app/models/emergency_episode.py`.
  - Migracion `alembic/versions/f7a4c2d9e111_add_emergency_episodes_table.py`.
  - Endpoints `POST/GET /emergency-episodes/*` y `/kpis`.
  - Servicio `app/services/emergency_episode_service.py` con reglas de transicion.
  - Pruebas `app/tests/test_emergency_episodes_api.py`.
  - Documento `docs/48_flujo_extremo_a_extremo_episodio_urgencias.md`.
  - ADR `docs/decisions/ADR-0031-flujo-extremo-a-extremo-episodio-urgencias.md`.
  - Validacion: `.\venv\Scripts\python.exe -m pytest -q app/tests`.

- ID: TM-054
- Objetivo: Implementar motor operativo de SCASEST para urgencias.
- Alcance: endpoint por CareTask, reglas de sospecha/riesgo alto, trazabilidad de workflow y metricas.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-053.
- Evidencia:
  - Servicio `app/services/scasest_protocol_service.py`.
  - Schema `app/schemas/scasest_protocol.py`.
  - Endpoint `POST /api/v1/care-tasks/{id}/scasest/recommendation`.
  - Workflow `scasest_protocol_support_v1` en `agent_runs` y `agent_steps`.
  - Metricas `scasest_protocol_runs_total`, `scasest_protocol_runs_completed_total`, `scasest_protocol_critical_alerts_total`.
  - Documento `docs/49_motor_scasest_urgencias.md`.
  - ADR `docs/decisions/ADR-0032-motor-operativo-scasest-urgencias.md`.
  - Validacion: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`.

- ID: TM-055
- Objetivo: Auditar calidad de soporte SCASEST comparando recomendacion IA vs validacion humana.
- Alcance: persistencia de auditoria, endpoints de registro/listado/resumen y metricas de precision por regla.
- Agentes involucrados: orchestrator, data-agent, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-054.
- Evidencia:
  - Modelo `app/models/care_task_scasest_audit_log.py`.
  - Migracion `alembic/versions/a9b3d5e7f210_add_care_task_scasest_audit_logs_table.py`.
  - Endpoints `POST/GET /care-tasks/{id}/scasest/audit` y `GET /summary`.
  - Metricas `scasest_audit_*` y `scasest_rule_*_match_rate_percent` en `/metrics`.
  - Documento `docs/50_auditoria_calidad_scasest.md`.
  - ADR `docs/decisions/ADR-0033-auditoria-calidad-scasest.md`.
  - Validacion: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`.

- ID: TM-056
- Objetivo: Operativizar observabilidad SCASEST con dashboard, alertas y runbook de respuesta.
- Alcance: paneles Grafana, reglas Prometheus y guia de actuacion.
- Agentes involucrados: orchestrator, devops-agent, qa-agent.
- Estado: completado
- Dependencias: TM-055.
- Evidencia:
  - Dashboard `ops/grafana/dashboards/task_manager_overview.json` actualizado con paneles SCASEST.
  - Reglas nuevas en `ops/prometheus/alerts.yml`: `ScasestAuditUnderRateHigh`, `ScasestAuditOverRateHigh`.
  - Runbook `docs/51_runbook_alertas_scasest.md`.
  - ADR `docs/decisions/ADR-0034-observabilidad-scasest-alertas-y-runbook.md`.

- ID: TM-057
- Objetivo: Facilitar practica de alertas SCASEST con simulador reproducible.
- Alcance: script de generacion de casos `under/over/mixed` y guia de uso.
- Agentes involucrados: orchestrator, qa-agent.
- Estado: completado
- Dependencias: TM-056.
- Evidencia:
  - Script `app/scripts/simulate_scasest_alerts.py`.
  - Guia `docs/52_scasest_alert_drill.md`.

- ID: TM-058
- Objetivo: Exponer scorecard global de calidad IA clinica para seguimiento operativo rapido.
- Alcance: agregar resumen unificado de auditorias (triaje/screening/medico-legal/SCASEST), endpoint API, metricas y documentacion.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-055, TM-056, TM-057.
- Evidencia:
  - Servicio: `CareTaskService.get_quality_scorecard`.
  - Endpoint: `GET /api/v1/care-tasks/quality/scorecard`.
  - Metricas: `care_task_quality_audit_*` en `/metrics`.
  - Pruebas:
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `52 passed`.

- ID: TM-059
- Objetivo: Operativizar scorecard global con alertas y paneles de observabilidad.
- Alcance: reglas Prometheus para calidad global, paneles Grafana y runbook de respuesta.
- Agentes involucrados: orchestrator, devops-agent, qa-agent.
- Estado: completado
- Dependencias: TM-058.
- Evidencia:
  - Alertas en `ops/prometheus/alerts.yml`:
    - `CareTaskQualityUnderRateHigh`
    - `CareTaskQualityOverRateHigh`
    - `CareTaskQualityMatchRateLow`
  - Paneles en `ops/grafana/dashboards/task_manager_overview.json`:
    - `Calidad Global Audit Total`
    - `Calidad Global Under Rate %`
    - `Calidad Global Over Rate %`
    - `Calidad Global Match Rate %`
  - Runbook: `docs/54_runbook_alertas_calidad_global.md`.

- ID: TM-060
- Objetivo: Facilitar drill reproducible para alertas de calidad global IA clinica.
- Alcance: script CLI para generar escenarios `under`/`over`/`match-low` y guia operativa.
- Agentes involucrados: orchestrator, qa-agent.
- Estado: completado
- Dependencias: TM-058, TM-059.
- Evidencia:
  - Script: `app/scripts/simulate_global_quality_alerts.py`.
  - Validacion: `.\venv\Scripts\python.exe -m py_compile app/scripts/simulate_global_quality_alerts.py`.
  - Guia: `docs/55_drill_alertas_calidad_global.md`.

- ID: TM-061
- Objetivo: Activar evaluacion continua con gate de calidad IA clinica en CI.
- Alcance: suite de regresion controlada para scorecard global, runner dedicado y paso obligatorio en pipeline.
- Agentes involucrados: orchestrator, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-058, TM-059, TM-060.
- Evidencia:
  - Test suite: `app/tests/test_quality_regression_gate.py`.
  - Runner: `app/scripts/run_quality_gate.py`.
  - CI gate: `.github/workflows/ci.yml` (paso `Gate de evaluacion continua`).
  - Validacion local:
    - `.\venv\Scripts\python.exe app\scripts\run_quality_gate.py`

- ID: TM-062
- Objetivo: Implementar soporte operativo de riesgo cardiovascular con auditoria y observabilidad.
- Alcance: endpoint de recomendacion, auditoria IA vs humano, metricas Prometheus y reglas de alerta.
- Agentes involucrados: orchestrator, api-agent, data-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-061.
- Evidencia:
  - Endpoint: `POST /api/v1/care-tasks/{id}/cardio-risk/recommendation`.
  - Auditoria: `POST/GET /api/v1/care-tasks/{id}/cardio-risk/audit` y `GET /summary`.
  - Modelo y migracion: `care_task_cardio_risk_audit_logs`, `alembic/versions/b1f4a2c9d330_add_care_task_cardio_risk_audit_logs_table.py`.
  - Metricas: `cardio_risk_support_*` y `cardio_risk_audit_*` en `/metrics`.
  - Alertas: `CardioRiskAuditUnderRateHigh`, `CardioRiskAuditOverRateHigh` en `ops/prometheus/alerts.yml`.

- ID: TM-063
- Objetivo: Implementar soporte operativo de reanimacion (BLS/ACLS) con auditoria y observabilidad.
- Alcance: endpoint de recomendacion, auditoria IA vs humano, metricas Prometheus y reglas de alerta.
- Agentes involucrados: orchestrator, api-agent, data-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-062.
- Evidencia:
  - Endpoint: `POST /api/v1/care-tasks/{id}/resuscitation/recommendation`.
  - Auditoria: `POST/GET /api/v1/care-tasks/{id}/resuscitation/audit` y `GET /summary`.
  - Modelo y migracion: `care_task_resuscitation_audit_logs`, `alembic/versions/c5e8a2f1d440_add_care_task_resuscitation_audit_logs_table.py`.
  - Metricas: `resuscitation_protocol_*` y `resuscitation_audit_*` en `/metrics`.
  - Alertas: `ResuscitationAuditUnderRateHigh`, `ResuscitationAuditOverRateHigh` en `ops/prometheus/alerts.yml`.
  - Pruebas: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py app/tests/test_quality_regression_gate.py` (`66 passed`).
  - Migraciones: `.\venv\Scripts\python.exe -m alembic upgrade head` y `.\venv\Scripts\python.exe -m alembic current` (`c5e8a2f1d440 (head)`).
  - Alertas Prometheus: `docker compose exec prometheus promtool check rules /etc/prometheus/alerts.yml` (`SUCCESS: 11 rules found`).

- ID: TM-064
- Objetivo: Operativizar alertas de reanimacion con drill reproducible, runbook y paneles Grafana.
- Alcance: script de simulacion de auditorias, guias operativas y paneles de observabilidad.
- Agentes involucrados: orchestrator, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-063.
- Evidencia:
  - Script: `app/scripts/simulate_resuscitation_alerts.py`.
  - Runbook: `docs/59_runbook_alertas_reanimacion.md`.
  - Drill: `docs/60_reanimacion_alert_drill.md`.
  - Dashboard: `ops/grafana/dashboards/task_manager_overview.json`.
  - Validacion local: `python -m py_compile app/scripts/simulate_resuscitation_alerts.py` y `python -m ruff check app/scripts/simulate_resuscitation_alerts.py` (OK).
  - Validacion dashboard: carga JSON de `ops/grafana/dashboards/task_manager_overview.json` (OK).
  - Riesgo pendiente: falta revalidar `promtool check rules` con Docker Desktop activo (`docker compose exec prometheus promtool check rules /etc/prometheus/alerts.yml`).

- ID: TM-065
- Objetivo: Extender soporte de reanimacion al contexto obstetrico critico con recomendaciones operativas y trazabilidad.
- Alcance: esquemas/servicio/API de resuscitation para embarazo, reglas especificas (DUL, regla 4-5 min, equipo obstetrico) y documentacion.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-063, TM-064.
- Evidencia:
  - Schemas: `app/schemas/resuscitation_protocol.py` (campos obstetricos opcionales).
  - Servicio: `app/services/resuscitation_protocol_service.py` (regla 4-5 min, DUL, magnesio, equipo obstetrico).
  - Prueba nueva: `test_run_resuscitation_support_obstetric_critical_window_actions` en `app/tests/test_care_tasks_api.py`.
  - Documentacion: `docs/58_motor_reanimacion_soporte_vital_urgencias.md`.
  - Decision: `docs/decisions/ADR-0040-extension-obstetrica-reanimacion-operativa.md`.
  - Contratos actualizados: `agents/shared/api_contract.md`, `agents/shared/data_contract.md`, `agents/shared/test_plan.md`, `agents/shared/deploy_notes.md`.
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/resuscitation_protocol.py app/services/resuscitation_protocol_service.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/resuscitation_protocol.py app/services/resuscitation_protocol_service.py app/tests/test_care_tasks_api.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k obstetric`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`65 passed`).

- ID: TM-066
- Objetivo: Integrar protocolo de terapia electrica en arritmias criticas dentro del motor de reanimacion.
- Alcance: recomendaciones de cardioversion/desfibrilacion, energia por ritmo, sedoanalgesia peri-procedimiento y checklist de seguridad pre-descarga.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-063, TM-065.
- Evidencia:
  - Schemas: `app/schemas/resuscitation_protocol.py` (PAS/PAD opcionales + nuevos bloques de salida).
  - Servicio: `app/services/resuscitation_protocol_service.py` (plan electrico, sedoanalgesia, checklist pre-descarga, alerta por presion de pulso estrecha).
  - Prueba nueva: `test_run_resuscitation_support_recommends_synchronized_cardioversion` en `app/tests/test_care_tasks_api.py`.
  - Documentacion: `docs/58_motor_reanimacion_soporte_vital_urgencias.md` y `docs/61_terapia_electrica_arritmias_criticas.md`.
  - Decision: `docs/decisions/ADR-0041-terapia-electrica-arritmias-reanimacion.md`.
  - Contratos actualizados: `agents/shared/api_contract.md`, `agents/shared/data_contract.md`, `agents/shared/test_plan.md`, `agents/shared/deploy_notes.md`.
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/resuscitation_protocol.py app/services/resuscitation_protocol_service.py app/tests/test_care_tasks_api.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/resuscitation_protocol.py app/services/resuscitation_protocol_service.py app/tests/test_care_tasks_api.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k cardioversion`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`66 passed`).

- ID: TM-067
- Objetivo: Integrar soporte bioetico pediatrico para conflicto entre autonomia parental y preservacion de la vida en urgencias.
- Alcance: ampliacion del motor medico-legal con reglas de menor en riesgo vital, rechazo de transfusion por representantes y activacion de deber de proteccion.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-050, TM-051.
- Evidencia:
  - Schema: `app/schemas/medicolegal_ops.py` (campos de conflicto bioetico pediatrico).
  - Servicio: `app/services/medicolegal_ops_service.py` (interes superior del menor, desamparo legal, estado de necesidad terapeutica).
  - Prueba nueva: `test_run_medicolegal_ops_pediatric_life_saving_conflict_prioritizes_protection` en `app/tests/test_care_tasks_api.py`.
  - Documentacion: `docs/45_motor_medico_legal_urgencias.md` y `docs/62_bioetica_pediatrica_conflicto_autonomia_vida.md`.
  - Decision: `docs/decisions/ADR-0042-soporte-bioetico-pediatrico-medicolegal.md`.
  - Contratos actualizados: `agents/shared/api_contract.md`, `agents/shared/data_contract.md`, `agents/shared/test_plan.md`, `agents/shared/deploy_notes.md`.
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/medicolegal_ops.py app/services/medicolegal_ops_service.py app/tests/test_care_tasks_api.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/medicolegal_ops.py app/services/medicolegal_ops_service.py app/tests/test_care_tasks_api.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k pediatric_life_saving_conflict`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`67 passed`).

- ID: TM-068
- Objetivo: Estructurar fundamento etico-legal explicito en soporte medico-legal pediatrico de urgencias.
- Alcance: ampliar salida de recomendacion con decision de override vital, bases de justificacion y urgencia operativa para trazabilidad clinico-juridica.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-067.
- Evidencia:
  - Schema: `app/schemas/medicolegal_ops.py` (`life_preserving_override_recommended`, `ethical_legal_basis`, `urgency_summary`).
  - Servicio: `app/services/medicolegal_ops_service.py` (decision de override vital, fundamento etico-legal estructurado y resumen operativo de urgencia).
  - Pruebas actualizadas: `app/tests/test_care_tasks_api.py` (caso base y conflicto pediatrico vital con aserciones de nuevas salidas).
  - Documentacion: `docs/45_motor_medico_legal_urgencias.md`, `docs/62_bioetica_pediatrica_conflicto_autonomia_vida.md`, `docs/01_current_state.md`.
  - Decision: `docs/decisions/ADR-0043-fundamento-etico-legal-estructurado-medicolegal.md`.
  - Contratos actualizados: `agents/shared/api_contract.md`, `agents/shared/data_contract.md`, `agents/shared/deploy_notes.md`, `agents/shared/test_plan.md`.
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/medicolegal_ops.py app/services/medicolegal_ops_service.py app/tests/test_care_tasks_api.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/medicolegal_ops.py app/services/medicolegal_ops_service.py app/tests/test_care_tasks_api.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k pediatric_life_saving_conflict`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`67 passed`).
  - Riesgos pendientes identificados:
    - El fundamento etico-legal es soporte operativo y no sustituye validacion de asesoria juridica institucional.
    - Persisten diferencias regulatorias por jurisdiccion; revisar despliegue real antes de uso asistencial.

- ID: TM-069
- Objetivo: Integrar soporte de diagnostico diferencial operativo para pitiriasis (versicolor, rosada y alba) con red flags de seguridad.
- Alcance: nuevo endpoint por CareTask, motor de reglas interpretables, traza de AgentRun y metricas operativas para observabilidad.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-044, TM-068.
- Evidencia:
  - Schema: `app/schemas/pityriasis_protocol.py`.
  - Servicio: `app/services/pityriasis_protocol_service.py` (clasificacion versicolor/rosada/alba y red flags).
  - Workflow: `AgentRunService.run_pityriasis_differential_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/pityriasis-differential/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `pityriasis_differential_runs_total`, `pityriasis_differential_runs_completed_total`, `pityriasis_differential_red_flags_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_pityriasis_differential_returns_recommendation_and_trace`
    - `test_run_pityriasis_differential_detects_red_flags`
    - `test_run_pityriasis_differential_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_pityriasis_differential_metrics`
  - Documentacion:
    - `docs/63_motor_diferencial_pitiriasis_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
  - Decision:
    - `docs/decisions/ADR-0044-soporte-diferencial-pitiriasis-operativo.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/pityriasis_protocol.py app/services/pityriasis_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/pityriasis_protocol.py app/services/pityriasis_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k pityriasis_differential`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k pityriasis_differential`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`71 passed`).
  - Riesgos pendientes identificados:
    - El motor es de soporte operativo y no sustituye diagnostico dermatologico presencial.
    - Los umbrales de reglas requieren validacion clinica local para minimizar falsos positivos/negativos.

- ID: TM-070
- Objetivo: Integrar soporte operativo diferencial para acne y rosacea con escalado terapeutico y seguridad farmacologica.
- Alcance: nuevo endpoint por CareTask, reglas interpretables de clasificacion/acceso terapeutico, checklist de monitorizacion de isotretinoina, trazas y metricas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-069.
- Evidencia:
  - Schema: `app/schemas/acne_rosacea_protocol.py`.
  - Servicio: `app/services/acne_rosacea_protocol_service.py` (diferencial acne/rosacea, severidad y red flags).
  - Workflow: `AgentRunService.run_acne_rosacea_differential_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/acne-rosacea/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `acne_rosacea_differential_runs_total`, `acne_rosacea_differential_runs_completed_total`, `acne_rosacea_differential_red_flags_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_acne_rosacea_differential_returns_recommendation_and_trace`
    - `test_run_acne_rosacea_differential_detects_fulminans_red_flag`
    - `test_run_acne_rosacea_differential_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_acne_rosacea_differential_metrics`
  - Documentacion:
    - `docs/64_motor_diferencial_acne_rosacea_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
  - Decision:
    - `docs/decisions/ADR-0045-soporte-diferencial-acne-rosacea-operativo.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/acne_rosacea_protocol.py app/services/acne_rosacea_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/acne_rosacea_protocol.py app/services/acne_rosacea_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k acne_rosacea_differential`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k acne_rosacea_differential`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`75 passed`).
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza diagnostico dermatologico presencial.
    - El checklist de isotretinoina no sustituye protocolos institucionales de farmacovigilancia.

- ID: TM-070-QA-VERIF
- Objetivo: Verificar cierre real de TM-070 con evidencia ejecutada en entorno local actual.
- Alcance: comprobacion de artefactos declarados + regresion focalizada y ampliada de API/metricas.
- Agentes involucrados: orchestrator, qa-agent.
- Estado: completado
- Dependencias: TM-070.
- Evidencia:
  - Artefactos verificados:
    - `app/schemas/acne_rosacea_protocol.py`
    - `app/services/acne_rosacea_protocol_service.py`
    - `app/services/agent_run_service.py`
    - `app/api/care_tasks.py`
    - `app/metrics/agent_metrics.py`
    - `docs/64_motor_diferencial_acne_rosacea_urgencias.md`
    - `docs/decisions/ADR-0045-soporte-diferencial-acne-rosacea-operativo.md`
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Pruebas ejecutadas:
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k acne_rosacea_differential` (`3 passed`)
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k acne_rosacea_differential` (`1 passed`)
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`75 passed`)
  - Riesgos pendientes identificados:
    - Se mantiene el riesgo clinico ya declarado en TM-070: motor de soporte, no sustituto de diagnostico presencial.
    - Se mantiene el riesgo operativo ya declarado en TM-070: checklist de isotretinoina no reemplaza farmacovigilancia institucional.

- ID: TM-071
- Objetivo: Integrar soporte operativo de trauma con curva trimodal, via aerea critica y riesgos sistÃƒÂ©micos.
- Alcance: nuevo endpoint por CareTask, reglas interpretables de trauma (trimodal/laringe/medula/aplastamiento/extremos de vida/hipotermia/Gustilo), trazas y metricas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-063, TM-065, TM-070.
- Evidencia:
  - Schema: `app/schemas/trauma_support_protocol.py`.
  - Servicio: `app/services/trauma_support_protocol_service.py` (curva trimodal, TECLA/TICLA, triada laringea, sindromes medulares, aplastamiento, hipotermia, Gustilo).
  - Workflow: `AgentRunService.run_trauma_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/trauma/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `trauma_support_runs_total`, `trauma_support_runs_completed_total`, `trauma_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_trauma_support_returns_recommendation_and_trace`
    - `test_run_trauma_support_detects_crush_risk_and_serial_ecg_requirement`
    - `test_run_trauma_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_trauma_support_metrics`
  - Documentacion:
    - `docs/65_motor_trauma_urgencias_trimodal.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
  - Decision:
    - `docs/decisions/ADR-0046-soporte-operativo-trauma-trimodal.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m ruff check app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/schemas/__init__.py app/services/__init__.py app/schemas/trauma_support_protocol.py app/services/trauma_support_protocol_service.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `$env:COVERAGE_FILE='.coverage.trauma_tmp'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py -k trauma_support`
    - Resultado: `4 passed`.
  - Riesgos pendientes identificados:
    - El motor de trauma es soporte operativo y no reemplaza protocolos institucionales de trauma mayor ni juicio clinico presencial.
    - Los umbrales y desencadenantes deben calibrarse por centro para minimizar sobre-alerta o infra-alerta.

- ID: TM-072
- Objetivo: Estructurar matriz clinica de trauma con diagnostico/tratamiento/fuente para consumo operativo.
- Alcance: ampliar contrato de trauma con `condition_matrix[]` y reglas de activacion para politrauma, choque hemorragico, neumotorax a tension, taponamiento, TCE, sindrome compartimental y quemaduras.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-071.
- Evidencia:
  - Schema ampliado: `app/schemas/trauma_support_protocol.py` (`TraumaConditionCard`, `condition_matrix`).
  - Servicio ampliado: `app/services/trauma_support_protocol_service.py` (cards estructuradas por condicion y fuente `CCM 2025 - Especialidad Urgencias`).
  - Prueba nueva:
    - `test_run_trauma_support_detects_tension_pneumothorax_and_tamponade`.
  - Prueba actualizada:
    - `test_run_trauma_support_returns_recommendation_and_trace` (validacion de `condition_matrix[0].source`).
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/test_plan.md`
    - `agents/shared/deploy_notes.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/trauma_support_protocol.py app/services/trauma_support_protocol_service.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py`
    - `$env:COVERAGE_FILE='.coverage.trauma_matrix_tmp'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py -k trauma_support`
    - Resultado: `5 passed`.
  - Riesgos pendientes identificados:
    - La matriz es soporte informativo-operativo y no sustituye guias locales ni criterio del equipo de trauma.
    - La presencia de signos aislados puede inducir sobre-clasificacion; requiere calibracion por centro.

- ID: TM-073
- Objetivo: Integrar soporte operativo critico transversal para SLA, soporte respiratorio, anafilaxia, toxicologia y banderas rojas de urgencias.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (tiempos operativos, decision de dispositivos, ruta dolor toracico/TEP, shock hemodinamico, antidotos, red flags), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-063, TM-071, TM-072.
- Evidencia:
  - Schema: `app/schemas/critical_ops_protocol.py`.
  - Servicio: `app/services/critical_ops_protocol_service.py` (SLA, soporte respiratorio, ruta TEP, anafilaxia, hemodinamica, toxicologia, red flags).
  - Workflow: `AgentRunService.run_critical_ops_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/critical-ops/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `critical_ops_support_runs_total`, `critical_ops_support_runs_completed_total`, `critical_ops_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_critical_ops_support_returns_recommendation_and_trace`
    - `test_run_critical_ops_support_detects_sla_breaches_and_red_flags`
    - `test_run_critical_ops_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_critical_ops_support_metrics`
  - Documentacion:
    - `docs/66_motor_operativo_critico_transversal_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
  - Decision:
    - `docs/decisions/ADR-0047-soporte-operativo-critico-transversal.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/critical_ops_protocol.py app/services/critical_ops_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/critical_ops_protocol.py app/services/critical_ops_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k critical_ops`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k critical_ops`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`84 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no sustituye diagnostico ni protocolos institucionales locales.
    - Los umbrales de disparo hemodinamicos/toxicologicos deben calibrarse por centro para evitar sobre-alerta.

- ID: TM-074
- Objetivo: Integrar soporte operativo neurologico para triaje vascular, diferenciales criticos y seguridad terapeutica.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (HSA/ictus, parkinsonismos, SGB, miastenia, anti-NMDA, biomarcadores y mielopatia), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-063, TM-073.
- Evidencia:
  - Schema: `app/schemas/neurology_support_protocol.py`.
  - Servicio: `app/services/neurology_support_protocol_service.py` (HSA/HSA perimesencefalica, codigo ictus con perfusion/penumbra, diferenciales neurologicos, seguridad en SGB y rutas autoinmunes).
  - Workflow: `AgentRunService.run_neurology_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/neurology/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `neurology_support_runs_total`, `neurology_support_runs_completed_total`, `neurology_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_neurology_support_returns_recommendation_and_trace`
    - `test_run_neurology_support_detects_contraindications_and_nmda_pattern`
    - `test_run_neurology_support_prioritizes_wakeup_pathway`
    - `test_run_neurology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_neurology_support_metrics`
  - Documentacion:
    - `docs/67_motor_operativo_neurologia_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
  - Decision:
    - `docs/decisions/ADR-0048-soporte-operativo-neurologia-urgencias.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/neurology_support_protocol.py app/services/neurology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/neurology_support_protocol.py app/services/neurology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k neurology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k neurology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`89 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza diagnostico neurologico/neuroquirurgico presencial.
    - Los umbrales de activacion (HSA/ictus/parkinsonismos autoinmunes) requieren calibracion y validacion local por centro.
    - La disponibilidad de TAC perfusion/angiografia/LCR condiciona la aplicabilidad de algunas recomendaciones.

- ID: TM-075
- Objetivo: Integrar soporte operativo gastro-hepato para urgencias vasculares, abdomen agudo y decisiones quirurgicas iniciales.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (trombosis portal, HDA cirrotico, gas portal/neumatosis, Courvoisier, diverticulitis, hernia crural, criterios quirurgicos, seguridad farmacologica EII, ERGE/PAF), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-073, TM-074.
- Evidencia:
  - Schema: `app/schemas/gastro_hepato_support_protocol.py`.
  - Servicio: `app/services/gastro_hepato_support_protocol_service.py` (trombosis portal, HDA cirrotico, red flags de imagen, decisiones quirurgicas, seguridad EII y soporte funcional/genetico).
  - Workflow: `AgentRunService.run_gastro_hepato_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/gastro-hepato/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `gastro_hepato_support_runs_total`, `gastro_hepato_support_runs_completed_total`, `gastro_hepato_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_gastro_hepato_support_returns_recommendation_and_trace`
    - `test_run_gastro_hepato_support_flags_surgery_and_pharmacology`
    - `test_run_gastro_hepato_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_gastro_hepato_support_metrics`
  - Documentacion:
    - `docs/68_motor_operativo_gastro_hepato_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
  - Decision:
    - `docs/decisions/ADR-0049-soporte-operativo-gastro-hepato-urgencias.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/gastro_hepato_support_protocol.py app/services/gastro_hepato_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/gastro_hepato_support_protocol.py app/services/gastro_hepato_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k gastro_hepato_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k gastro_hepato_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`93 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza decision de digestivo/cirugia.
    - Los umbrales de activacion para HDA/isquemia/decision quirurgica requieren calibracion local.
    - La aplicabilidad depende de disponibilidad local de Doppler, TAC y endoscopia urgente.

- ID: TM-076
- Objetivo: Integrar soporte operativo reuma-inmuno para triaje de riesgo vital, decision diagnostica y seguridad materno-fetal.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (TEP en LES, isquemia digital en esclerosis, arteritis temporal, miopatias inflamatorias, Behcet, pseudo-gota, espondiloartropatias, lupus neonatal, IgG4/SAF), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-073, TM-074, TM-075.
- Evidencia:
  - Schema: `app/schemas/rheum_immuno_support_protocol.py`.
  - Servicio: `app/services/rheum_immuno_support_protocol_service.py` (TEP en LES, isquemia digital, arteritis temporal, miopatias inflamatorias, Behcet, pseudo-gota, espondiloartropatias, seguridad materno-fetal e IgG4/SAF).
  - Workflow: `AgentRunService.run_rheum_immuno_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/rheum-immuno/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `rheum_immuno_support_runs_total`, `rheum_immuno_support_runs_completed_total`, `rheum_immuno_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_rheum_immuno_support_returns_recommendation_and_trace`
    - `test_run_rheum_immuno_support_flags_safety_maternal_and_data_domains`
    - `test_run_rheum_immuno_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_rheum_immuno_support_metrics`
  - Documentacion:
    - `docs/69_motor_operativo_reuma_inmuno_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
  - Decision:
    - `docs/decisions/ADR-0050-soporte-operativo-reuma-inmuno-urgencias.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/rheum_immuno_support_protocol.py app/services/rheum_immuno_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/rheum_immuno_support_protocol.py app/services/rheum_immuno_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k rheum_immuno_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k rheum_immuno_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`97 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza evaluacion reumatologica/inmunologica presencial.
    - La regla de exclusion de arteritis temporal por VSG normal es operativa y requiere correlacion clinica local.
    - La disponibilidad de ecocardiografia fetal, imagen articular y laboratorios condiciona aplicabilidad de algunas recomendaciones.

- ID: TM-077
- Objetivo: Integrar soporte operativo de psiquiatria para urgencias con triaje temporal, riesgo suicida infanto-juvenil y seguridad farmacologica en poblaciones especiales.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (estres agudo/TEPT/adaptativo, riesgo suicida adolescente, pronostico psicosis, bipolaridad en embarazo, insomnio geriatrico, anorexia y mecanismos de defensa), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-073, TM-074, TM-076.
- Evidencia:
  - Schema: `app/schemas/psychiatry_support_protocol.py`.
  - Servicio: `app/services/psychiatry_support_protocol_service.py` (triage temporal estres/TEPT, riesgo suicida infanto-juvenil, pronostico en psicosis, seguridad farmacologica en embarazo/geriatria y alertas internistas de TCA).
  - Workflow: `AgentRunService.run_psychiatry_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/psychiatry/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `psychiatry_support_runs_total`, `psychiatry_support_runs_completed_total`, `psychiatry_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_psychiatry_support_returns_recommendation_and_trace`
    - `test_run_psychiatry_support_enforces_elderly_insomnia_safety_flow`
    - `test_run_psychiatry_support_flags_pregnancy_and_metabolic_risk`
    - `test_run_psychiatry_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_psychiatry_support_metrics`
  - Documentacion:
    - `docs/70_motor_operativo_psiquiatria_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
  - Decision:
    - `docs/decisions/ADR-0051-soporte-operativo-psiquiatria-urgencias.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/psychiatry_support_protocol.py app/services/psychiatry_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/psychiatry_support_protocol.py app/services/psychiatry_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k psychiatry_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k psychiatry_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`102 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza valoracion psiquiatrica presencial.
    - La priorizacion temporal estres agudo/TEPT requiere calibracion local con protocolo institucional.
    - La orientacion psicodinamica en trastorno delirante es cualitativa y no sustituye entrevista clinica estructurada.

- ID: TM-078
- Objetivo: Integrar soporte operativo de hematologia para urgencias con foco en microangiopatias tromboticas, sangrado critico y seguridad postquirurgica.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (MAT/SHU/TIH, hemofilia con inhibidores, diferenciales de linfoma, anemia de Fanconi, seguridad en esplenectomia y quimerismo post-trasplante), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-075, TM-076, TM-077.
- Evidencia:
  - Schema: `app/schemas/hematology_support_protocol.py`.
  - Servicio: `app/services/hematology_support_protocol_service.py` (MAT/SHU/TIH, hemofilia con inhibidores, seguridad en esplenectomia y soporte onco-hematologico).
  - Workflow: `AgentRunService.run_hematology_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/hematology/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `hematology_support_runs_total`, `hematology_support_runs_completed_total`, `hematology_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_hematology_support_returns_recommendation_and_trace`
    - `test_run_hematology_support_flags_hemophilia_and_splenectomy_safety`
    - `test_run_hematology_support_flags_oncology_fanconi_and_transplant`
    - `test_run_hematology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_hematology_support_metrics`
  - Documentacion:
    - `docs/71_motor_operativo_hematologia_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
  - Decision:
    - `docs/decisions/ADR-0052-soporte-operativo-hematologia-urgencias.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/hematology_support_protocol.py app/services/hematology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/hematology_support_protocol.py app/services/hematology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k hematology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k hematology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`107 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza evaluacion hematologica presencial.
    - Las decisiones terapeuticas definitivas en MAT/TIH/hemofilia dependen de protocolo y recursos locales.
    - La clasificacion de linfoma es de apoyo y no sustituye biopsia/anatomia patologica.

- ID: TM-079
- Objetivo: Integrar soporte operativo de endocrinologia y metabolismo para urgencias con foco en emergencias bioquimicas, tiroides, hipofisis, suprarrenal y diabetes.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (errores innatos del metabolismo, SIADH, hiperprolactinemia, crisis suprarrenal, incidentaloma suprarrenal y seleccion farmacologica diabetologica), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-078.
- Evidencia:
  - Schema: `app/schemas/endocrinology_support_protocol.py`.
  - Servicio: `app/services/endocrinology_support_protocol_service.py` (hipoglucemia hipocetosica, SIADH, CMT, incidentaloma suprarrenal, DM1 y seguridad farmacologica).
  - Workflow: `AgentRunService.run_endocrinology_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/endocrinology/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `endocrinology_support_runs_total`, `endocrinology_support_runs_completed_total`, `endocrinology_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_endocrinology_support_returns_recommendation_and_trace`
    - `test_run_endocrinology_support_flags_thyroid_and_siadh_safety`
    - `test_run_endocrinology_support_flags_diabetes_and_confounders`
    - `test_run_endocrinology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_endocrinology_support_metrics`
  - Documentacion:
    - `docs/72_motor_operativo_endocrinologia_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
  - Decision:
    - `docs/decisions/ADR-0053-soporte-operativo-endocrinologia-urgencias.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/endocrinology_support_protocol.py app/services/endocrinology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/endocrinology_support_protocol.py app/services/endocrinology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k endocrinology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k endocrinology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`112 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza evaluacion endocrinologica presencial.
    - Los umbrales de SIADH/hipoglucemia e interpretacion de incidentaloma requieren ajuste por protocolo local.
    - La seleccion farmacologica en diabetes debe individualizarse por comorbilidades y contexto asistencial.

- ID: TM-080
- Objetivo: Integrar soporte operativo de nefrologia para urgencias con foco en FRA, sindrome renopulmonar, equilibrio acido-base y criterios de dialisis urgente.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (clasificacion prerrenal/parenquimatosa/obstructiva, AEIOU, nefroproteccion con iSGLT2, glomerulopatias y seguridad farmacologica), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-079.
- Evidencia:
  - Schema: `app/schemas/nephrology_support_protocol.py`.
  - Servicio: `app/services/nephrology_support_protocol_service.py` (FRA, sindrome renopulmonar, acido-base, AEIOU, iSGLT2 y seguridad RAAS).
  - Workflow: `AgentRunService.run_nephrology_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/nephrology/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `nephrology_support_runs_total`, `nephrology_support_runs_completed_total`, `nephrology_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_nephrology_support_returns_recommendation_and_trace`
    - `test_run_nephrology_support_flags_acid_base_and_aeiou`
    - `test_run_nephrology_support_flags_nephroprotection_and_interstitial_safety`
    - `test_run_nephrology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_nephrology_support_metrics`
  - Documentacion:
    - `docs/73_motor_operativo_nefrologia_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
  - Decision:
    - `docs/decisions/ADR-0054-soporte-operativo-nefrologia-urgencias.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/nephrology_support_protocol.py app/services/nephrology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/nephrology_support_protocol.py app/services/nephrology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k nephrology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k nephrology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`117 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza evaluacion nefrologica presencial.
    - La indicacion final de plasmaferesis/dialisis depende de protocolo y recursos locales.
    - La clasificacion del FRA requiere correlacion clinica y no debe usarse de forma aislada.

- ID: TM-081
- Objetivo: Integrar soporte operativo de neumologia para urgencias con foco en diferenciales por imagen, fisiologia ventilatoria, EPOC/asma grave y seguridad de decision intervencionista.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (NOC y diferenciales, control ventilatorio, escalado GOLD, biologicos en asma, LBA y riesgo quirurgico por VO2 max), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-080.
- Evidencia:
  - Schema: `app/schemas/pneumology_support_protocol.py`.
  - Servicio: `app/services/pneumology_support_protocol_service.py` (NOC y diferenciales por TAC, control ventilatorio, escalado EPOC/asma biologica, LBA y seguridad por VO2 max).
  - Workflow: `AgentRunService.run_pneumology_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/pneumology/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `pneumology_support_runs_total`, `pneumology_support_runs_completed_total`, `pneumology_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_pneumology_support_returns_recommendation_and_trace`
    - `test_run_pneumology_support_flags_safety_and_lba_context`
    - `test_run_pneumology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_pneumology_support_metrics`
  - Documentacion:
    - `docs/74_motor_operativo_neumologia_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
    - `docs/05_roadmap.md`
  - Decision:
    - `docs/decisions/ADR-0055-soporte-operativo-neumologia-urgencias.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/pneumology_support_protocol.py app/services/pneumology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/pneumology_support_protocol.py app/services/pneumology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k pneumology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k pneumology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`121 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza evaluacion neumologica presencial.
    - Las decisiones de lobectomia/radioterapia requieren comite local y funcionalismo completo.
    - La seleccion de biologicos debe individualizarse por fenotipo y disponibilidad institucional.

- ID: TM-082
- Objetivo: Integrar soporte operativo de geriatria para urgencias con foco en fragilidad, inmovilidad, delirium y optimizacion farmacologica START v3.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (cambios morfologicos del envejecimiento, balance nitrogenado negativo, delirium infeccioso y alertas START), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-081.
- Evidencia:
  - Schema: `app/schemas/geriatrics_support_protocol.py`.
  - Servicio: `app/services/geriatrics_support_protocol_service.py` (envejecimiento fisiologico, inmovilidad, delirium y START v3).
  - Workflow: `AgentRunService.run_geriatrics_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/geriatrics/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `geriatrics_support_runs_total`, `geriatrics_support_runs_completed_total`, `geriatrics_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_geriatrics_support_returns_recommendation_and_trace`
    - `test_run_geriatrics_support_flags_start_v3_and_tetanus_logic`
    - `test_run_geriatrics_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_geriatrics_support_metrics`
  - Documentacion:
    - `docs/75_motor_operativo_geriatria_fragilidad_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
    - `docs/05_roadmap.md`
  - Decision:
    - `docs/decisions/ADR-0056-soporte-operativo-geriatria-fragilidad-urgencias.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/geriatrics_support_protocol.py app/services/geriatrics_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/geriatrics_support_protocol.py app/services/geriatrics_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k geriatrics_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k geriatrics_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`125 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza valoracion geriatrica presencial.
    - El bloqueo de benzodiacepinas en delirium exige excepciones protocolizadas por equipo tratante.
    - La interpretacion de cambios morfologicos por edad requiere correlacion clinico-funcional.

- ID: TM-083
- Objetivo: Integrar soporte operativo de oncologia para urgencias con foco en inmuno-oncologia, toxicidades inmunomediadas, cardio-oncologia, neutropenia febril y respuesta en sarcomas.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (checkpoint inhibitors, biomarcadores dMMR/MSI, irAEs hepaticas, FEVI pre-tratamiento, criterios de neutropenia febril y necrosis post-neoadyuvancia), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-082.
- Evidencia:
  - Schema: `app/schemas/oncology_support_protocol.py`.
  - Servicio: `app/services/oncology_support_protocol_service.py` (checkpoint inhibitors, dMMR/MSI-high, irAEs hepaticas, FEVI y neutropenia febril).
  - Workflow: `AgentRunService.run_oncology_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/oncology/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `oncology_support_runs_total`, `oncology_support_runs_completed_total`, `oncology_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_oncology_support_returns_recommendation_and_trace`
    - `test_run_oncology_support_flags_cardio_and_sarcoma_branches`
    - `test_run_oncology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_oncology_support_metrics`
  - Documentacion:
    - `docs/76_motor_operativo_oncologia_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
    - `docs/05_roadmap.md`
  - Decision:
    - `docs/decisions/ADR-0057-soporte-operativo-oncologia-urgencias.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/oncology_support_protocol.py app/services/oncology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/oncology_support_protocol.py app/services/oncology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k oncology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k oncology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`129 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza valoracion oncologica presencial.
    - La gestion de irAEs requiere protocolos institucionales para escalado de inmunosupresion.
    - La decision final en neutropenia febril y cardio-oncologia depende de recursos locales y contexto clinico integral.

- ID: TM-084
- Objetivo: Integrar soporte operativo de anestesiologia y reanimacion para urgencias con foco en ISR y seleccion de bloqueos simpaticos por anatomia del dolor.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (indicaciones de ISR, SLAs de preoxigenacion/intubacion, alertas de seguridad de via aerea, via IV exclusiva y recomendacion de bloqueo del ganglio impar), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-083.
- Evidencia:
  - Schema: `app/schemas/anesthesiology_support_protocol.py`.
  - Servicio: `app/services/anesthesiology_support_protocol_service.py` (ISR de emergencia, seguridad de via aerea y bloqueos simpaticos por anatomia del dolor).
  - Workflow: `AgentRunService.run_anesthesiology_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/anesthesiology/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `anesthesiology_support_runs_total`, `anesthesiology_support_runs_completed_total`, `anesthesiology_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_anesthesiology_support_returns_recommendation_and_trace`
    - `test_run_anesthesiology_support_differential_blocks_and_safety`
    - `test_run_anesthesiology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_anesthesiology_support_metrics`
  - Documentacion:
    - `docs/77_motor_operativo_anestesiologia_reanimacion_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
    - `docs/05_roadmap.md`
  - Decision:
    - `docs/decisions/ADR-0058-soporte-operativo-anestesiologia-reanimacion-urgencias.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/anesthesiology_support_protocol.py app/services/anesthesiology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/anesthesiology_support_protocol.py app/services/anesthesiology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k anesthesiology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k anesthesiology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`133 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza valoracion anestesiologica presencial.
    - La ejecucion de ISR y bloqueos intervencionistas depende de protocolo y recursos locales.
    - La seleccion final del bloqueo requiere correlacion anatomica e imagen guiada por el equipo tratante.

- ID: TM-085
- Objetivo: Integrar soporte operativo de cuidados paliativos y paciente terminal para urgencias con foco en adecuacion terapeutica, seguridad opioide y delirium.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (rechazo vs adecuacion del esfuerzo, rutas de opioides en insuficiencia renal, dolor irruptivo, alerta de neurotoxicidad y decisiones de confort en demencia avanzada), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-084.
- Evidencia:
  - Schema: `app/schemas/palliative_support_protocol.py`.
  - Servicio: `app/services/palliative_support_protocol_service.py` (decision etico-legal, seguridad opioide renal, confort en demencia avanzada y delirium).
  - Workflow: `AgentRunService.run_palliative_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/palliative/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `palliative_support_runs_total`, `palliative_support_runs_completed_total`, `palliative_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_palliative_support_returns_recommendation_and_trace`
    - `test_run_palliative_support_flags_ethical_and_delirium_logic`
    - `test_run_palliative_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_palliative_support_metrics`
  - Documentacion:
    - `docs/78_motor_operativo_cuidados_paliativos_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
    - `docs/05_roadmap.md`
  - Decision:
    - `docs/decisions/ADR-0059-soporte-operativo-cuidados-paliativos-urgencias.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/palliative_support_protocol.py app/services/palliative_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/palliative_support_protocol.py app/services/palliative_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k palliative_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k palliative_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`137 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza valoracion paliativa presencial.
    - Las decisiones de final de vida requieren ajuste al marco normativo y protocolo local.
    - La rotacion opioide y el manejo de delirium requieren seguimiento clinico estrecho.

- ID: TM-086
- Objetivo: Integrar soporte operativo de urologia para urgencias con foco en infeccion renal critica, obstruccion urinaria, trauma genital y onco-urologia.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (PFE, FRA obstructivo, bloqueo de sondaje en fractura de pene, nefrectomia parcial en rinon unico y estrategia sistemica en prostata metastasica), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-085.
- Evidencia:
  - Schema: `app/schemas/urology_support_protocol.py`.
  - Servicio: `app/services/urology_support_protocol_service.py` (PFE, FRA obstructivo, trauma genital con bloqueo de sondaje y rutas onco-urologicas).
  - Workflow: `AgentRunService.run_urology_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/urology/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `urology_support_runs_total`, `urology_support_runs_completed_total`, `urology_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_urology_support_returns_recommendation_and_trace`
    - `test_run_urology_support_prioritizes_diversion_and_triple_therapy_safety`
    - `test_run_urology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_urology_support_metrics`
  - Documentacion:
    - `docs/79_motor_operativo_urologia_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
    - `docs/05_roadmap.md`
  - Decision:
    - `docs/decisions/ADR-0060-soporte-operativo-urologia-urgencias.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/urology_support_protocol.py app/services/urology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/urology_support_protocol.py app/services/urology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k urology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k urology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`141 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza valoracion urologica presencial.
    - La priorizacion de derivacion y revision quirurgica requiere protocolo local y disponibilidad de recursos.
    - La estrategia sistemica en prostata metastasica debe validarse en comite onco-urologico segun contexto institucional.

- ID: TM-087
- Objetivo: Integrar soporte operativo de reacciones por Anisakis simplex para urgencias con foco en deteccion de sospecha alergica y recomendaciones de prevencion al alta.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (latencia post-ingesta, urticaria/anafilaxia, solicitud de IgE especifica, riesgo por cocinado insuficiente y medidas termicas estandar), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-086.
- Evidencia:
  - Schema: `app/schemas/anisakis_support_protocol.py`.
  - Servicio: `app/services/anisakis_support_protocol_service.py` (disparo de sospecha alergica, diferencial digestivo/alergico, solicitud de IgE y prevencion termica al alta).
  - Workflow: `AgentRunService.run_anisakis_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/anisakis/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `anisakis_support_runs_total`, `anisakis_support_runs_completed_total`, `anisakis_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_anisakis_support_returns_recommendation_and_trace`
    - `test_run_anisakis_support_handles_digestive_profile_without_anaphylaxis`
    - `test_run_anisakis_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_anisakis_support_metrics`
  - Documentacion:
    - `docs/80_motor_operativo_anisakis_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
    - `docs/05_roadmap.md`
  - Decision:
    - `docs/decisions/ADR-0061-soporte-operativo-anisakis-urgencias.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/anisakis_support_protocol.py app/services/anisakis_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/anisakis_support_protocol.py app/services/anisakis_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k anisakis_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k anisakis_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`145 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza valoracion clinica/alergologica presencial.
    - La calidad del triaje depende de la trazabilidad real de ingesta, coccion y latencia sintomatica.
    - Las acciones terapeuticas inmediatas deben ajustarse al protocolo local de anafilaxia.

- ID: TM-088
- Objetivo: Integrar soporte operativo de epidemiologia clinica para urgencias con foco en metricas de riesgo, NNT, inferencia causal y clasificacion economica.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (incidencia acumulada vs densidad, calculo NNT en tanto por uno, interpretacion condicional del RR causal, criterios de Bradford Hill y coste-utilidad por QALY), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-087.
- Evidencia:
  - Schema: `app/schemas/epidemiology_support_protocol.py`.
  - Servicio: `app/services/epidemiology_support_protocol_service.py` (incidencia/prevalencia/densidad, NNT, RR causal condicional, Bradford Hill y coste-utilidad).
  - Workflow: `AgentRunService.run_epidemiology_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/epidemiology/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `epidemiology_support_runs_total`, `epidemiology_support_runs_completed_total`, `epidemiology_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_epidemiology_support_returns_recommendation_and_trace`
    - `test_run_epidemiology_support_flags_rr_and_nnt_safety_blocks`
    - `test_run_epidemiology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_epidemiology_support_metrics`
  - Documentacion:
    - `docs/81_motor_operativo_epidemiologia_clinica_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
    - `docs/05_roadmap.md`
  - Decision:
    - `docs/decisions/ADR-0062-soporte-operativo-epidemiologia-clinica-urgencias.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/epidemiology_support_protocol.py app/services/epidemiology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/epidemiology_support_protocol.py app/services/epidemiology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k epidemiology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k epidemiology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`149 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza analisis epidemiologico formal.
    - La inferencia causal depende de validez metodologica y control de sesgos del estudio real.
    - La interpretacion de coste-utilidad requiere contexto institucional de costos y utilidades.

- ID: TM-089
- Objetivo: Integrar soporte operativo de oftalmologia para urgencias con foco en triaje vascular retiniano, neuroftalmologia pupilar, superficie ocular, riesgo IFIS y clasificacion DMAE.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (OVCR/OACR por fondo de ojo, anisocoria simpatico/parasimpatico, reflejo aferente relativo, alerta farmacologica por tamsulosina e IFIS, y diferenciacion DMAE seca/humeda), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-088.
- Evidencia:
  - Schema: `app/schemas/ophthalmology_support_protocol.py`.
  - Servicio: `app/services/ophthalmology_support_protocol_service.py` (triaje vascular OVCR/OACR, neuroftalmologia pupilar, superficie ocular, IFIS y DMAE).
  - Workflow: `AgentRunService.run_ophthalmology_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/ophthalmology/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `ophthalmology_support_runs_total`, `ophthalmology_support_runs_completed_total`, `ophthalmology_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_ophthalmology_support_returns_recommendation_and_trace`
    - `test_run_ophthalmology_support_flags_neuro_and_anisocoria_logic`
    - `test_run_ophthalmology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_ophthalmology_support_metrics`
  - Documentacion:
    - `docs/82_motor_operativo_oftalmologia_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
    - `docs/05_roadmap.md`
  - Decision:
    - `docs/decisions/ADR-0063-soporte-operativo-oftalmologia-urgencias.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/ophthalmology_support_protocol.py app/services/ophthalmology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/ophthalmology_support_protocol.py app/services/ophthalmology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k ophthalmology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k ophthalmology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`153 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza valoracion oftalmologica presencial.
    - La regla OVCR/OACR depende de calidad descriptiva del fondo de ojo reportado en urgencias.
    - El endpoint no sustituye protocolizacion institucional de anti-VEGF, antiarritmicos o ruta neurovascular.

- ID: TM-090
- Objetivo: Integrar soporte operativo de inmunologia para urgencias con foco en inmunodeficiencias humorales, defensa innata pulmonar y diferencial Bruton/IgA/Hiper-IgM/CVID.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (perfil BTK/X-linked, ausencia CD19/CD20, patron de inmunoglobulinas, ventana de IgG materna, rol de macrofago alveolar y diferenciales humorales), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-089.
- Evidencia:
  - Schema: `app/schemas/immunology_support_protocol.py`.
  - Servicio: `app/services/immunology_support_protocol_service.py` (Bruton/BTK, defensa innata pulmonar y diferenciales humorales).
  - Workflow: `AgentRunService.run_immunology_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/immunology/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `immunology_support_runs_total`, `immunology_support_runs_completed_total`, `immunology_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_immunology_support_returns_recommendation_and_trace`
    - `test_run_immunology_support_differential_profiles_and_safety_blocks`
    - `test_run_immunology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_immunology_support_metrics`
  - Documentacion:
    - `docs/83_motor_operativo_inmunologia_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
    - `docs/05_roadmap.md`
  - Decision:
    - `docs/decisions/ADR-0064-soporte-operativo-inmunologia-urgencias.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/immunology_support_protocol.py app/services/immunology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/immunology_support_protocol.py app/services/immunology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k immunology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k immunology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`157 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza valoracion inmunologica presencial.
    - La calidad del triaje depende de disponibilidad y consistencia del perfil inmunologico de entrada.
    - El endpoint no sustituye protocolizacion institucional de inmunoglobulinas y manejo infeccioso.

- ID: TM-091
- Objetivo: Integrar soporte operativo de recurrencia genetica en osteogenesis imperfecta para priorizar alerta de mosaicismo germinal.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (dominancia COL1A1/COL1A2, recurrencia en progenitores sanos, descarte de de novo aislado, diferencial recesivo/penetrancia y trazabilidad de riesgo por fraccion germinal mutada), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-090.
- Evidencia:
  - Schema: `app/schemas/genetic_recurrence_support_protocol.py`.
  - Servicio: `app/services/genetic_recurrence_support_protocol_service.py` (priorizacion de mosaicismo germinal en recurrencia dominante y bloqueos de consistencia).
  - Workflow: `AgentRunService.run_genetic_recurrence_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/genetic-recurrence/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `genetic_recurrence_support_runs_total`, `genetic_recurrence_support_runs_completed_total`, `genetic_recurrence_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_genetic_recurrence_support_returns_recommendation_and_trace`
    - `test_run_genetic_recurrence_support_handles_mosaicism_fraction_and_consistency`
    - `test_run_genetic_recurrence_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_genetic_recurrence_support_metrics`
  - Documentacion:
    - `docs/84_motor_operativo_recurrencia_genetica_oi_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
    - `docs/05_roadmap.md`
  - Decision:
    - `docs/decisions/ADR-0065-soporte-operativo-recurrencia-genetica-oi-urgencias.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/genetic_recurrence_support_protocol.py app/services/genetic_recurrence_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/genetic_recurrence_support_protocol.py app/services/genetic_recurrence_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k genetic_recurrence`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k genetic_recurrence`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`161 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza diagnostico genetico formal.
    - La estimacion de riesgo de recurrencia depende de calidad de datos moleculares y contexto familiar.
    - La decision final requiere validacion por genetica clinica y obstetricia.

- ID: TM-092
- Objetivo: Integrar soporte operativo de ginecologia y obstetricia para urgencias con foco en oncogenetica hereditaria, ectopico, preeclampsia severa y seguridad farmacologica.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (Lynch/Amsterdam II, embarazo ectopico y ruptura, datacion CRL/CIR/STFF, varicela gestacional, preeclampsia posparto grave, anticoncepcion/diabetes gestacional y bloqueo de diureticos en linfedema cronico), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-091.
- Evidencia:
  - Schema: `app/schemas/gynecology_obstetrics_support_protocol.py`.
  - Servicio: `app/services/gynecology_obstetrics_support_protocol_service.py` (oncogenetica hereditaria, ectopico/rotura, datacion obstetrica y bloqueos de seguridad terapeutica).
  - Workflow: `AgentRunService.run_gynecology_obstetrics_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/gynecology-obstetrics/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `gynecology_obstetrics_support_runs_total`, `gynecology_obstetrics_support_runs_completed_total`, `gynecology_obstetrics_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_gynecology_obstetrics_support_returns_recommendation_and_trace`
    - `test_run_gynecology_obstetrics_support_blocks_unsafe_pharmacology`
    - `test_run_gynecology_obstetrics_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_gynecology_obstetrics_support_metrics`
  - Documentacion:
    - `docs/85_motor_operativo_ginecologia_obstetricia_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
    - `docs/05_roadmap.md`
  - Decision:
    - `docs/decisions/ADR-0066-soporte-operativo-ginecologia-obstetricia-urgencias.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/gynecology_obstetrics_support_protocol.py app/services/gynecology_obstetrics_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/gynecology_obstetrics_support_protocol.py app/services/gynecology_obstetrics_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k gynecology_obstetrics`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k gynecology_obstetrics`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`165 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza valoracion ginecologica/obstetrica presencial.
    - El rendimiento del triaje depende de calidad de la ecografia y antecedentes familiares registrados.
    - Las decisiones de alto impacto (preeclampsia grave, ectopico roto, profilaxis infecciosa) requieren validacion humana obligatoria y protocolo local.

- ID: TM-093
- Objetivo: Integrar soporte operativo de pediatria y neonatologia para urgencias con foco en sarampion, reanimacion neonatal, tosferina, invaginacion y sifilis congenita.
- Alcance: nuevo endpoint por CareTask con reglas interpretables (triada de sarampion y Koplik, validacion vacunal por edad, aislamiento respiratorio, objetivos SatO2 neonatal por minuto y CPAP 21%, profilaxis de contactos de tosferina, alertas de invaginacion y estigmas tardios de sifilis congenita), trazas de AgentRun y metricas operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-092.
- Evidencia:
  - Schema: `app/schemas/pediatrics_neonatology_support_protocol.py`.
  - Servicio: `app/services/pediatrics_neonatology_support_protocol_service.py` (sarampion, reanimacion neonatal, tosferina, invaginacion y sifilis congenita tardia).
  - Workflow: `AgentRunService.run_pediatrics_neonatology_support_workflow` en `app/services/agent_run_service.py`.
  - Endpoint: `POST /api/v1/care-tasks/{id}/pediatrics-neonatology/recommendation` en `app/api/care_tasks.py`.
  - Metricas: `pediatrics_neonatology_support_runs_total`, `pediatrics_neonatology_support_runs_completed_total`, `pediatrics_neonatology_support_critical_alerts_total` en `app/metrics/agent_metrics.py`.
  - Pruebas nuevas:
    - `test_run_pediatrics_neonatology_support_returns_recommendation_and_trace`
    - `test_run_pediatrics_neonatology_support_flags_critical_branches`
    - `test_run_pediatrics_neonatology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_pediatrics_neonatology_support_metrics`
  - Documentacion:
    - `docs/86_motor_operativo_pediatria_neonatologia_urgencias.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
    - `docs/05_roadmap.md`
  - Decision:
    - `docs/decisions/ADR-0067-soporte-operativo-pediatria-neonatologia-urgencias.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/pediatrics_neonatology_support_protocol.py app/services/pediatrics_neonatology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/pediatrics_neonatology_support_protocol.py app/services/pediatrics_neonatology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k pediatrics_neonatology`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k pediatrics_neonatology`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`169 passed`)
  - Riesgos pendientes identificados:
    - El motor es soporte operativo y no reemplaza valoracion pediatrica/neonatal presencial.
    - La calidad del triaje depende de la consistencia temporal de signos y saturaciones registradas.
    - Las decisiones de aislamiento, reanimacion y urgencia quirurgica requieren validacion humana obligatoria y protocolo local.

- ID: TM-094
- Objetivo: Integrar chat clinico-operativo persistente para profesionales sobre `CareTask` con memoria de sesion y trazabilidad.
- Alcance: nuevos endpoints de chat (`POST/GET /care-tasks/{id}/chat/*`), nueva tabla de memoria conversacional, workflow trazable en `agent_runs/agent_steps`, pruebas API y documentacion/contratos.
- Agentes involucrados: orchestrator, api-agent, data-agent, qa-agent.
- Estado: completado
- Dependencias: TM-093.
- Evidencia:
  - Modelo: `app/models/care_task_chat_message.py`.
  - Migracion: `alembic/versions/d4f6a9c8e221_add_care_task_chat_messages_table.py`.
  - Schema: `app/schemas/clinical_chat.py`.
  - Servicio: `app/services/clinical_chat_service.py`.
  - Workflow: `AgentRunService.run_care_task_clinical_chat_workflow` en `app/services/agent_run_service.py`.
  - Endpoints:
    - `POST /api/v1/care-tasks/{id}/chat/messages`
    - `GET /api/v1/care-tasks/{id}/chat/messages`
    - `GET /api/v1/care-tasks/{id}/chat/memory`
  - Pruebas nuevas:
    - `test_create_care_task_chat_message_persists_message_and_trace`
    - `test_list_care_task_chat_messages_and_memory_summary`
    - `test_create_care_task_chat_message_returns_404_when_task_not_found`
  - Documentacion:
    - `docs/87_chat_clinico_operativo_profesional.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
    - `docs/05_roadmap.md`
  - Decision:
    - `docs/decisions/ADR-0068-chat-clinico-operativo-memory-caretask.md`
  - Contratos actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/deploy_notes.md`
    - `agents/shared/test_plan.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/models/care_task_chat_message.py app/schemas/clinical_chat.py app/services/clinical_chat_service.py app/services/agent_run_service.py app/api/care_tasks.py app/tests/test_care_tasks_api.py alembic/versions/d4f6a9c8e221_add_care_task_chat_messages_table.py`
    - `.\venv\Scripts\python.exe -m ruff check app/models/care_task_chat_message.py app/schemas/clinical_chat.py app/services/clinical_chat_service.py app/services/agent_run_service.py app/api/care_tasks.py app/tests/test_care_tasks_api.py alembic/versions/d4f6a9c8e221_add_care_task_chat_messages_table.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat_message` (`3 passed, 126 deselected`)
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py` (`129 passed`)
    - `.\venv\Scripts\python.exe -m pytest -q` (`234 passed`)
  - Riesgos pendientes identificados:
    - El matching semantico inicial usa reglas por keywords y puede omitir sinonimos complejos.
    - La memoria de sesion puede heredar ruido si se registran consultas ambiguas.
    - El chat no diagnostica y requiere validacion clinica humana en cada decision.

- ID: TM-095
- Objetivo: Evolucionar chat clinico con modo por especialidad autenticada, contexto longitudinal por paciente y fuentes internas/web trazables.
- Alcance: `auth`, `care_tasks`, `clinical_chat`, migracion Alembic, pruebas API y actualizacion documental/contratos.
- Agentes involucrados: orchestrator, api-agent, data-agent, qa-agent.
- Estado: completado
- Dependencias: TM-094.
- Evidencia:
  - Migracion: `alembic/versions/e8a1c4b7d552_add_chat_specialty_patient_context_fields.py`.
  - Decision: `docs/decisions/ADR-0069-chat-clinico-especialidad-contexto-longitudinal-fuentes.md`.
  - Modelo usuario:
    - `users.specialty` en `app/models/user.py`.
  - Modelo caso:
    - `care_tasks.patient_reference` en `app/models/care_task.py`.
  - Modelo chat:
    - `effective_specialty`, `knowledge_sources`, `web_sources`, `patient_history_facts_used` en `app/models/care_task_chat_message.py`.
  - Endpoint/auth:
    - Chat de `care-tasks` ahora requiere usuario autenticado y usa especialidad de credencial por defecto.
    - Filtros por `patient_reference` en listado/estadisticas de `care-tasks`.
  - Servicio:
    - `app/services/clinical_chat_service.py` con:
      - especialidad efectiva por credencial,
      - resumen longitudinal por `patient_reference`,
      - indexado de fuentes internas en `docs/`,
      - consulta web opcional bajo demanda.
  - Pruebas nuevas/actualizadas:
    - `app/tests/test_auth_api.py`
    - `app/tests/test_care_tasks_api.py`
      - `test_chat_endpoints_require_authentication`
      - `test_chat_memory_aggregates_patient_history_across_tasks`
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/models/user.py app/models/care_task.py app/models/care_task_chat_message.py app/schemas/auth.py app/schemas/care_task.py app/schemas/clinical_chat.py app/services/auth_service.py app/services/care_task_service.py app/services/clinical_chat_service.py app/api/auth.py app/api/care_tasks.py app/tests/test_auth_api.py app/tests/test_care_tasks_api.py alembic/versions/e8a1c4b7d552_add_chat_specialty_patient_context_fields.py`
    - `.\venv\Scripts\python.exe -m ruff check app/models/user.py app/models/care_task.py app/models/care_task_chat_message.py app/schemas/auth.py app/schemas/care_task.py app/schemas/clinical_chat.py app/services/auth_service.py app/services/care_task_service.py app/services/clinical_chat_service.py app/api/auth.py app/api/care_tasks.py app/core/config.py app/tests/test_auth_api.py app/tests/test_care_tasks_api.py alembic/versions/e8a1c4b7d552_add_chat_specialty_patient_context_fields.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_auth_api.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py`
    - `.\venv\Scripts\python.exe -m pytest -q`
    - `.\venv\Scripts\python.exe -m alembic upgrade head`
    - `.\venv\Scripts\python.exe -m alembic current`
  - Riesgos pendientes identificados:
    - El indexado interno es lexical/rules-first; no sustituye embedding semantico ni RAG medico validado.
    - La busqueda web depende de disponibilidad externa y puede devolver fuentes no clinicas si no hay filtro institucional.
    - El contexto longitudinal depende de calidad de `patient_reference` y de la consistencia narrativa del registro.

- ID: TM-096
- Objetivo: Endurecer seguridad de informacion del chat con whitelist web estricta y sellado profesional de fuentes internas.
- Alcance: `clinical_chat`, nuevo modulo `knowledge_sources`, nuevas tablas de curacion y documentacion/contratos.
- Agentes involucrados: orchestrator, api-agent, data-agent, qa-agent.
- Estado: completado
- Dependencias: TM-095.
- Evidencia:
  - Migracion: `alembic/versions/c2f4a9e1b771_add_clinical_knowledge_sources_tables.py`.
  - Nuevos modelos:
    - `app/models/clinical_knowledge_source.py`
    - `app/models/clinical_knowledge_source_validation.py`
  - Nueva API:
    - `app/api/knowledge_sources.py`
      - `POST /api/v1/knowledge-sources/`
      - `GET /api/v1/knowledge-sources/`
      - `POST /api/v1/knowledge-sources/{id}/seal`
      - `GET /api/v1/knowledge-sources/{id}/validations`
      - `GET /api/v1/knowledge-sources/trusted-domains`
  - Endurecimiento chat:
    - `app/services/clinical_chat_service.py` filtra web por whitelist y prioriza fuentes internas validadas.
  - Politicas de confianza:
    - `app/core/config.py` + `.env.example` + `.env.docker` con settings de whitelist y validacion obligatoria.
  - Documentacion:
    - `docs/89_chat_fuentes_confiables_whitelist_sellado.md`
    - `docs/decisions/ADR-0070-chat-clinico-whitelist-y-sellado-fuentes.md`
  - Validacion:
    - `.\venv\Scripts\python.exe -m ruff check app/models/clinical_knowledge_source.py app/models/clinical_knowledge_source_validation.py app/models/__init__.py app/core/database.py app/services/knowledge_source_service.py app/services/clinical_chat_service.py app/api/knowledge_sources.py app/api/__init__.py app/main.py app/core/config.py app/tests/test_knowledge_sources_api.py app/tests/test_care_tasks_api.py alembic/versions/c2f4a9e1b771_add_clinical_knowledge_sources_tables.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_knowledge_sources_api.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat`
    - `.\venv\Scripts\python.exe -m pytest -q`
    - `.\venv\Scripts\python.exe -m alembic upgrade head`
    - `.\venv\Scripts\python.exe -m alembic current`
  - Resultado:
    - `241 passed`, head Alembic `c2f4a9e1b771`.
  - Riesgos pendientes identificados:
    - El sellado inicial depende de capacidad operativa de revisores clinicos.
    - El ranking de evidencia interna sigue siendo lexical; pendiente retrieval semantico validado.
    - La whitelist requiere mantenimiento continuo de dominios autorizados.

- ID: TM-097
- Objetivo: Definir playbook operativo de curacion/sellado de fuentes clinicas para uso por profesionales.
- Alcance: documentacion operativa y alineacion de runbook de despliegue.
- Agentes involucrados: orchestrator, qa-agent.
- Estado: completado
- Dependencias: TM-096.
- Evidencia:
  - Documento nuevo:
    - `docs/90_playbook_curacion_fuentes_clinicas.md`
  - Indices y estado actualizados:
    - `docs/README.md`
    - `docs/01_current_state.md`
    - `agents/shared/deploy_notes.md`
  - Riesgos pendientes identificados:
    - La adopcion del playbook depende de disciplina operativa del equipo.
    - Se requiere asignar responsables claros por especialidad para evitar backlog de sellado.

- ID: TM-098
- Objetivo: Implementar frontend MVP de chat clinico con interfaz moderna para simulacion de uso profesional.
- Alcance: nuevo workspace `frontend/` (Vite + React + TS), consumo de auth/care-tasks/chat, y documentacion de ejecucion.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-095, TM-096.
- Entregables:
  - Frontend MVP en `frontend/` con login, casos, chat, memoria y trazabilidad.
  - Documento funcional `docs/91_frontend_chat_clinico_mvp.md`.
  - Decision estructural `docs/decisions/ADR-0071-frontend-mvp-chat-vite-react.md`.
  - Ajuste CORS para desarrollo local (`localhost:5173` y `127.0.0.1:5173`).
- Evidencia:
  - `cd frontend && npm install`
  - `cd frontend && npm run build` (`built in ...`)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_settings_security.py` (`4 passed`)
- Riesgos pendientes identificados:
  - El MVP no incluye streaming ni panel de sellado de fuentes.
  - Si se altera contrato de `chat/messages` o `chat/memory`, hay que sincronizar frontend.

- ID: TM-099
- Objetivo: Evolucionar chat a experiencia tipo assistant con herramientas y modo hibrido general/clinico.
- Alcance: `frontend/src/App.tsx`, `frontend/src/styles.css`, `app/schemas/clinical_chat.py`, `app/services/clinical_chat_service.py`, `app/api/care_tasks.py` y documentacion de contratos.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-098.
- Entregables:
  - Frontend v2 tipo assistant con barra de herramientas y controles de modo conversacional.
  - Chat backend hibrido (`general`/`clinical`) con deteccion por senales clinicas y herramienta elegida.
  - Contrato de chat actualizado (`conversation_mode`, `tool_mode`, `response_mode`).
  - Documentacion y ADR de la evolucion (`docs/92_*`, `ADR-0072`).
- Evidencia:
  - `cd frontend && npm run build` (`built in ...`)
  - `.\venv\Scripts\python.exe -m ruff check app/schemas/clinical_chat.py app/services/clinical_chat_service.py app/api/care_tasks.py app/tests/test_care_tasks_api.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat` (`7 passed, 126 deselected`)
- Riesgos pendientes identificados:
  - El modo general sigue siendo rule-based; no hay modelo generativo dedicado en local.
  - El modo `images` funciona como selector de flujo, no como pipeline multimodal completo.

- ID: TM-100
- Objetivo: Integrar motor conversacional neuronal local de baja latencia con fallback seguro.
- Alcance: `app/services/llm_chat_provider.py`, `app/services/clinical_chat_service.py`, configuracion LLM en settings/env y documentacion operativa.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-099.
- Entregables:
  - Proveedor LLM local `Ollama` integrado en chat sin romper contratos existentes.
  - Trazabilidad de uso y latencia del LLM en `interpretability_trace`.
  - Documento tecnico `docs/93_motor_conversacional_neuronal_open_source.md`.
  - Decision estructural `docs/decisions/ADR-0073-motor-conversacional-neuronal-local.md`.
- Evidencia:
  - `cd frontend && npm run build` (`built in ...`)
  - `.\venv\Scripts\python.exe -m ruff check app/services/llm_chat_provider.py app/services/clinical_chat_service.py app/schemas/clinical_chat.py app/api/care_tasks.py app/tests/test_care_tasks_api.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat` (`7 passed, 126 deselected`)
- Riesgos pendientes identificados:
  - El rendimiento final depende del modelo local seleccionado y hardware disponible.
  - Requiere operacion de runtime Ollama en entornos donde se active `CLINICAL_CHAT_LLM_ENABLED=true`.

- ID: TM-101
- Objetivo: Corregir continuidad conversacional del chat para mantener hilo entre turnos.
- Alcance: `app/services/clinical_chat_service.py`, `app/services/llm_chat_provider.py`, `app/tests/test_care_tasks_api.py`.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-099, TM-100.
- Entregables:
  - Reutilizacion de contexto real de dialogo previo en el prompt LLM.
  - Filtro de hechos de control (`modo_respuesta`, `herramienta`) fuera de memoria reutilizable.
  - Fallback rule-based con referencia explicita al turno previo para mantener continuidad.
  - Test de regresion para verificar que memoria de sesion no reutiliza hechos de control.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/tests/test_care_tasks_api.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k "chat_continuity_filters_control_facts_from_memory or chat_message"` (`6 passed`)
- Riesgos pendientes identificados:
  - La continuidad semantica fuerte sigue dependiendo de la calidad del modelo local configurado.
  - Si el usuario cambia `session_id`, el hilo se reinicia por diseno.

- ID: TM-102
- Objetivo: Elevar calidad conversacional local (100% gratis) para equipos de 16GB RAM.
- Alcance: `app/services/clinical_chat_service.py`, `app/services/llm_chat_provider.py`, `app/core/config.py`, `.env.example`, `.env.docker`, `app/tests/test_care_tasks_api.py`, documentacion de contratos y despliegue.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-100, TM-101.
- Entregables:
  - Continuidad contextual en consultas de seguimiento (`query_expanded`) para mejorar matching de dominio.
  - Uso preferente de `POST /api/chat` de Ollama con historial corto por sesion y fallback a `POST /api/generate`.
  - Fallback clinico reestructurado a formato operativo accionable (menos plantilla fija, mas plan por pasos).
  - Ajustes de configuracion LLM para perfil local (`num_ctx`, `top_p`) compatibles con 16GB RAM.
  - Test de regresion para seguimiento contextual.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/core/config.py app/tests/test_care_tasks_api.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k "chat_continuity_filters_control_facts_from_memory or chat_follow_up_query_reuses_previous_context_for_domain_matching or chat_message"` (`7 passed`)
- Riesgos pendientes identificados:
  - Calidad final depende del modelo local elegido y de la disponibilidad de Ollama en runtime.
  - Con 16GB RAM, modelos >14B pueden degradar latencia y experiencia de guardia.

- ID: TM-103
- Objetivo: Mejorar feedback conversacional clinico con trazabilidad LLM y UI simplificada.
- Alcance: `app/services/clinical_chat_service.py`, `app/services/llm_chat_provider.py`, `frontend/src/App.tsx`, `frontend/src/styles.css`, `.env.example`, `.env.docker`, pruebas y docs operativas.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-100, TM-101, TM-102.
- Entregables:
  - Inyeccion de recomendaciones internas de endpoints en contexto LLM.
  - Trazabilidad operativa reforzada (`llm_*`, `query_expanded`, `matched_endpoints`) en respuesta y UI.
  - UI de chat concentrada en menus desplegables con opciones avanzadas plegables.
  - Runbook interno de Ollama local y politicas de whitelist.
- Evidencia:
  - `python -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/tests/test_clinical_chat_operational.py frontend/src/App.tsx`
  - `python -m pytest -q app/tests/test_clinical_chat_operational.py`
  - `cd frontend && npm run build`
- Riesgos pendientes identificados:
  - La sintesis de recomendaciones internas por endpoint es heuristica y no sustituye llamada clinica directa del especialista.
  - Si Ollama local no esta disponible, el sistema cae a fallback operativo no diagnostico.


- ID: TM-105
- Objetivo: Corregir parseo de respuestas Ollama para evitar fallback clinico por error de decode.
- Alcance: `app/services/llm_chat_provider.py`, `app/tests/test_clinical_chat_operational.py`, contratos API/QA/DevOps y ADR.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-103, TM-104.
- Entregables:
  - Parser tolerante para respuestas Ollama JSON, JSONL y lineas `data:` (SSE-like).
  - Extraccion robusta de texto de respuesta para `/api/chat` y fallback `/api/generate`.
  - Tests de regresion para payload chunked y SSE.
- Evidencia:
  - `python -m ruff check app/services/llm_chat_provider.py app/tests/test_clinical_chat_operational.py`
  - `python -m pytest -q app/tests/test_clinical_chat_operational.py -k "ollama or e2e or follow_up"`
- Riesgos pendientes identificados:
  - Si `CLINICAL_CHAT_LLM_BASE_URL` apunta a un proxy no compatible, puede requerir ajuste adicional de autenticacion/cabeceras.


- ID: TM-106
- Objetivo: Evitar respuestas generales con volcado tecnico/JSON en saludos o consultas exploratorias.
- Alcance: `app/services/clinical_chat_service.py`, `app/tests/test_clinical_chat_operational.py`, contratos de handoff y ADR.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-105.
- Entregables:
  - Sanitizacion de respuesta general para no exponer snippets JSON crudos en modo conversacional.
  - Recomendaciones internas por endpoint solo en modo clinico (no en greeting general).
  - Test de regresion para saludo con consulta de casos.
- Evidencia:
  - `python -m ruff check app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
  - `python -m pytest -q app/tests/test_clinical_chat_operational.py -k "general_answer or parse_ollama or e2e"`
- Riesgos pendientes identificados:
  - Consultas ambiguas muy cortas pueden requerir una repregunta del usuario para activar modo clinico y detalle protocolario.


- ID: TM-107
- Objetivo: Reforzar calidad conversacional humana con hilos de razonamiento y politica de fuentes.
- Alcance: `app/services/clinical_chat_service.py`, `app/services/llm_chat_provider.py`, `app/tests/test_clinical_chat_operational.py`, contratos y ADR.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-106.
- Entregables:
  - Respuesta general guiada por hilos (intencion, contexto, fuentes, accion) con cierre de repregunta util.
  - Enumeracion de dominios disponibles para consultas exploratorias en lugar de blobs tecnicos.
  - Politica de fuentes (`internal first`) visible en trazas y prompt LLM.
- Evidencia:
  - `python -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/tests/test_clinical_chat_operational.py`
  - `python -m pytest -q app/tests/test_clinical_chat_operational.py`
- Riesgos pendientes identificados:
  - Sin base de conocimiento clinica ampliada, el tono mejora pero la profundidad depende del catalogo interno disponible.

- ID: TM-108
- Objetivo: Endurecer chat local open source sin pago (anti-inyeccion, presupuesto de contexto y metricas de calidad).
- Alcance: `app/services/clinical_chat_service.py`, `app/services/llm_chat_provider.py`, `app/schemas/clinical_chat.py`, `app/api/care_tasks.py`, `app/core/config.py`, `.env.example`, `.env.docker`, `app/tests/test_clinical_chat_operational.py`, `app/tests/test_care_tasks_api.py`, contratos compartidos y ADR.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-107.
- Entregables:
  - Guardas anti-prompt-injection y delimitacion explicita de input usuario.
  - Control de presupuesto de contexto/tokens para prompts de Ollama.
  - Metricas automaticas locales por turno: `answer_relevance`, `context_relevance`, `groundedness`.
  - Limpieza de conflictos de merge pendientes para recuperar estabilidad del repo.
- Evidencia:
  - `python -m py_compile app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/schemas/clinical_chat.py app/api/care_tasks.py app/core/config.py app/tests/test_clinical_chat_operational.py app/tests/test_care_tasks_api.py`
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/schemas/clinical_chat.py app/api/care_tasks.py app/core/config.py app/tests/test_clinical_chat_operational.py app/tests/test_care_tasks_api.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py` (`9 passed`)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat` (`9 passed, 126 deselected`)
- Riesgos pendientes identificados:
  - Las metricas iniciales son heuristicas lexicales y requieren calibracion progresiva con casos asistenciales reales.
  - La sanitizacion reduce superficie de inyeccion, pero no sustituye auditoria clinica ni validacion humana.

- ID: TM-109
- Objetivo: Adaptar el blueprint OSS de agentes a utilidad interna (sin suscripciones, sin movil y sin canales externos) con scripts operativos y guias alineadas al repo.
- Alcance: `docs/94_chat_clinico_operativo_ollama_local_runbook.md`, nuevo playbook de adaptacion OSS, `agents/shared/*_contract.md`, `agents/shared/test_plan.md`, `agents/shared/deploy_notes.md`, `docs/decisions/`.
- Agentes involucrados: orchestrator, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-108.
- Entregables:
  - Documento de adaptacion interna con alcance incluido/excluido.
  - Flujo base de comandos (`dev`, `build`, `check`, `test`, `test-e2e`) adaptado al stack actual.
  - Politica de pre-commit sobre staged files y setup de onboarding reproducible.
  - Decision estructural ADR sobre recorte de alcance (sin pagos ni canales moviles/mensajeria).
- Evidencia:
  - Nuevos archivos:
    - `.pre-commit-config.yaml`
    - `scripts/dev_workflow.ps1`
    - `scripts/setup_hooks.ps1`
    - `docs/96_adaptacion_blueprint_agentes_oss_interno.md`
    - `docs/decisions/ADR-0080-adaptacion-blueprint-agentes-oss-interno-sin-canales-externos.md`
  - Documentacion actualizada:
    - `docs/94_chat_clinico_operativo_ollama_local_runbook.md`
    - `docs/06_quality_workflow.md`
    - `docs/05_roadmap.md`
    - `docs/01_current_state.md`
    - `docs/README.md`
  - Contratos/handoffs actualizados:
    - `agents/shared/api_contract.md`
    - `agents/shared/data_contract.md`
    - `agents/shared/mcp_contract.md`
    - `agents/shared/test_plan.md`
    - `agents/shared/deploy_notes.md`
  - Validacion ejecutada:
    - `.\venv\Scripts\python.exe -m pre_commit validate-config` (OK)
    - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev_workflow.ps1 -Action check` (falla por deuda previa E501 fuera de TM-109)
    - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev_workflow.ps1 -Action test-e2e` (`18 passed, 126 deselected`)
    - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup_hooks.ps1` (OK)
- Riesgos pendientes identificados:
  - Existe deuda previa de lint (`E501`) en archivos historicos; `-Action check` seguira fallando hasta sanearla.
  - Riesgo de deriva documental si no se mantiene sincronia entre runbook, contratos y estado actual.
  - Riesgo de friccion inicial del equipo hasta adoptar hooks y flujo de calidad automatizado.

- ID: TM-110
- Objetivo: Sanear deuda de lint `E501` para dejar `scripts/dev_workflow.ps1 -Action check` en verde.
- Alcance: `app/api/agents.py`, `app/schemas/ai.py`, `app/scripts/bootstrap_admin.py`, `app/scripts/simulate_global_quality_alerts.py`, `app/scripts/simulate_scasest_alerts.py`, `app/services/ai_triage_service.py`, `mcp_server/smoke.py`, contratos QA/TASK_BOARD.
- Agentes involucrados: orchestrator, qa-agent.
- Estado: completado
- Dependencias: TM-109.
- Entregables:
  - Correccion de lineas largas sin cambiar comportamiento.
  - Validacion de lint/formato (`ruff` + `black --check`) en verde.
- Evidencia:
  - Correcciones E501 aplicadas en archivos objetivo.
  - `.\venv\Scripts\python.exe -m ruff check app mcp_server` (OK).
  - `.\venv\Scripts\python.exe -m black --check app mcp_server` (OK, 153 files unchanged).
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev_workflow.ps1 -Action check`:
    - `ruff check` OK
    - `black --check` OK
    - falla en `mypy` por deuda historica de tipado (459 errores) no introducida en TM-110.
- Riesgos pendientes identificados:
  - `-Action check` no queda totalmente verde hasta definir estrategia de saneamiento mypy.
  - Riesgo bajo de regresion por formateo accidental en bloques sensibles de logs/mensajes.

- ID: TM-111
- Objetivo: Mejorar UX del fallback clinico para evitar salida tecnica (JSON crudo y continuidad social no relevante).
- Alcance: `app/services/clinical_chat_service.py`, `app/tests/test_clinical_chat_operational.py`.
- Agentes involucrados: orchestrator, qa-agent.
- Estado: completado
- Dependencias: TM-109, TM-110.
- Entregables:
  - Fallback clinico sin volcado de snippets JSON crudos en la respuesta al usuario.
  - Continuidad clinica solo cuando el ultimo turno previo tiene senal clinica.
  - Hechos tecnicos con prefijo (`termino:`, `umbral:`) fuera de la narrativa visible.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py` (OK).
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "clinical_fallback or general_answer or follow_up_query_expansion"` (`5 passed, 6 deselected`).
- Riesgos pendientes identificados:
  - Al ocultar detalles tecnicos en la respuesta, el usuario depende mas de `interpretability_trace` para auditoria fina.

- ID: TM-112
- Objetivo: Implementar hardening v2 de chat clinico con aislamiento de contenido externo, pipeline de politicas de herramientas y auditoria de seguridad accionable.
- Alcance: `app/services/clinical_chat_service.py`, `app/services/llm_chat_provider.py`, nuevos modulos `app/security/*` y `app/agents/*`, esquemas de chat, pruebas de API/servicio, contratos compartidos y ADR.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: en curso
- Dependencias: TM-108, TM-111.
- Entregables:
  - Aislamiento de contenido no confiable (marcadores y saneo anti-breakout).
  - Catalogo de herramientas peligrosas con deny-by-default para superficies de mayor riesgo.
  - Pipeline de politicas por capas (global/perfil/agente/contexto) con traza de decision.
  - Auditoria de seguridad por turno con findings y remediaciones.
- Evidencia:
  - Pendiente al cierre de implementacion.
- Riesgos pendientes identificados:
  - El lock de escritura de sesion en proceso local no coordina procesos distribuidos sin backend compartido.
  - Las politicas iniciales requeriran calibracion con feedback real de uso clinico.

- ID: TM-113
- Objetivo: Auditar cambios RAG pendientes, recuperar estabilidad del endpoint de chat e integrar RAG hibrido con fallback seguro en runtime.
- Alcance: `app/services/clinical_chat_service.py`, `app/services/rag_*.py`, `app/services/embedding_service.py`, `app/core/config.py`, `app/api/care_tasks.py`, `app/models/*`, migracion Alembic RAG y documentacion/contratos asociados.
- Agentes involucrados: orchestrator, api-agent, data-agent, qa-agent.
- Estado: completado
- Dependencias: TM-112.
- Entregables:
  - Correccion del endpoint de chat para evitar desempaquetado invalido.
  - Integracion efectiva de RAG en `create_message` con trazabilidad y fallback.
  - Limpieza de calidad (ruff) en nuevos modulos RAG para permitir commit.
  - Ajuste de precedencia en pipeline de politicas para respetar habilitacion clinica contextual.
  - Validacion focalizada de tests de chat.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check ...` (modulos afectados, OK).
  - `.\venv\Scripts\python.exe -m py_compile ...` (modulos afectados, OK).
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py` (`12 passed`).
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat` (`9 passed, 126 deselected`).
  - `docs/decisions/ADR-0081-chat-rag-hibrido-local-fallback-seguro.md`.
- Riesgos pendientes identificados:
  - Si no hay chunks ingeridos en DB, RAG caera a fallback rule/LLM sin contexto documental.
  - El retrieval vectorial sobre SQLite puede degradar latencia al crecer el corpus sin indice ANN.

- ID: TM-114
- Objetivo: Integrar backend opcional LlamaIndex y capa opcional NeMo Guardrails en chat RAG local, con fallback seguro sin romper flujo actual.
- Alcance: `app/core/config.py`, `app/services/rag_orchestrator.py`, nuevos servicios `app/services/llamaindex_retriever.py` y `app/services/nemo_guardrails_service.py`, `app/services/clinical_chat_service.py`, tests operativos de chat, contratos y documentacion.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-113.
- Entregables:
  - Selector de backend retrieval (`legacy|llamaindex`) por variable de entorno.
  - Integracion opcional de NeMo Guardrails para moderacion/revision de salida.
  - Trazabilidad explicita de uso/fallback en `interpretability_trace`.
  - Compatibilidad backward con pipeline existente si dependencias opcionales no estan instaladas.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/core/config.py app/services/llamaindex_retriever.py app/services/nemo_guardrails_service.py app/services/rag_orchestrator.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_chat_operational.py app/tests/test_nemo_guardrails_service.py app/tests/test_settings_security.py` (OK).
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_settings_security.py` (`6 passed`).
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_nemo_guardrails_service.py` (`2 passed`).
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py` (`14 passed`).
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat` (`9 passed, 126 deselected`).
- Riesgos pendientes identificados:
  - `llama-index` y `nemoguardrails` pueden incrementar latencia en equipos modestos; se recomienda activar por flag y medir.
  - Si no se instalan dependencias opcionales o falta config de rails, el sistema opera en modo fail-open (sin bloqueo).

- ID: TM-115
- Objetivo: Integrar backend opcional Chroma para retrieval RAG local sin pagos y sin romper pipelines existentes.
- Alcance: `app/core/config.py`, `app/services/chroma_retriever.py`, `app/services/rag_orchestrator.py`, `.env*`, dependencias opcionales, tests de chat y documentacion/contratos.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-114.
- Entregables:
  - Nuevo backend retrieval `chroma` seleccionable por `CLINICAL_CHAT_RAG_RETRIEVER_BACKEND`.
  - Fallback automatico a `legacy` cuando Chroma no esta disponible o no devuelve resultados.
  - Trazabilidad `chroma_*` en `interpretability_trace` para auditoria operativa.
  - Cobertura en tests operativos para ruta `chroma` y fallback.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check ...` (modulos tocados, OK).
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_settings_security.py` (OK).
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py` (OK).
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat` (OK).
- Riesgos pendientes identificados:
  - Crear coleccion Chroma en memoria por consulta simplifica integracion, pero puede penalizar latencia en corpus grandes.
  - Para rendimiento maximo, se recomienda evolucionar a estrategia de sincronizacion persistente de embeddings en Chroma.

- ID: TM-116
- Objetivo: Redisenar frontend del chat clinico para UX minimalista, intuitiva y segura en contexto de urgencias.
- Alcance: `frontend/src/App.tsx`, `frontend/src/styles.css`, `docs/01_current_state.md`, `docs/README.md`, contratos compartidos de API/QA/Deploy.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-103, TM-115.
- Entregables:
  - Nueva UI minimalista con sidebar operativa (historial, quick-actions, fuentes y controles).
  - Chat con avatares diferenciados, typing visible, render progresivo (typewriter) y feedback por turno (thumbs up/down).
  - Seccion expandible por respuesta para `Fuentes y referencias` trazadas exactamente desde RAG.
  - Indicador visual de nivel de confianza derivado de trazas de calidad (`groundedness`).
  - Disclaimer medico fijo y visible en todo momento.
- Evidencia:
  - `cd frontend && npm run build` (OK)
- Riesgos pendientes identificados:
  - El streaming es visual (typewriter en frontend) y depende de recibir respuesta completa del backend; no sustituye SSE chunked real.
  - El indicador de confianza usa heuristica de `groundedness`; requiere calibracion asistencial continua.


- ID: TM-138
- Objetivo: Integrar capa de triaje SVM (margen + hinge loss) para clasificacion operativa y trazabilidad en chat clinico.
- Alcance: `app/services/clinical_svm_triage_service.py`, `app/services/clinical_chat_service.py`, `app/services/__init__.py`, `app/tests/test_clinical_chat_operational.py`.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-137.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_svm_triage_service.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_chat_operational.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "svm_triage_service_flags_critical_hyperkalemia_case or uses_rag_when_enabled"`

- ID: TM-139
- Objetivo: Incorporar pipeline de riesgo clinico (imputacion+escalado+logistica+anomalias) para priorizacion probabilistica local.
- Alcance: `app/services/clinical_risk_pipeline_service.py`, `app/services/clinical_chat_service.py`, `app/services/__init__.py`, `app/tests/test_clinical_chat_operational.py`.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-138.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_risk_pipeline_service.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_chat_operational.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "risk_pipeline_service_estimates_probability_and_anomaly or svm_triage_service_flags_critical_hyperkalemia_case or uses_rag_when_enabled"`

- ID: TM-140
- Objetivo: Fase posterior (menos prioritario): SRL/Correferencia extendida, DPO/RLHF y capa de voz ASR/TTS.
- Alcance: backlog de investigacion y diseno; sin cambios de codigo en esta fase.
- Agentes involucrados: orchestrator, research-agent.
- Estado: pendiente
- Dependencias: TM-139.
- Evidencia:
  - Backlog registrado para siguiente iteracion.

- ID: TM-141
- Objetivo: Mejorar velocidad y robustez RAG local con retrieval hibrido paralelo y quality gate de fidelidad minimo.
- Alcance: `app/core/config.py`, `app/services/rag_retriever.py`, `app/services/rag_gatekeeper.py`, `.env`, `.env.example`, `app/tests/test_clinical_chat_operational.py`.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-139.
- Entregables:
  - Retrieval hibrido con scoring vectorial+keyword en paralelo sobre el mismo pool de chunks.
  - Quality gate de fidelidad con umbral configurable (`CLINICAL_CHAT_RAG_FAITHFULNESS_MIN_RATIO`).
  - Flags runtime nuevas para activar paralelismo y calibrar fidelidad minima.
  - Test unitario para validar bloqueo por baja fidelidad.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/core/config.py app/services/rag_gatekeeper.py app/services/rag_retriever.py app/tests/test_clinical_chat_operational.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "gatekeeper_flags_low_faithfulness_as_risk or uses_rag_when_enabled"`
- Riesgos pendientes identificados:
  - El score de fidelidad por solape lexical puede penalizar respuestas clinicas correctas parafraseadas.
  - El paralelismo puede no aportar ganancia en corpus muy pequenos y sumar overhead de hilos.

- ID: TM-142
- Objetivo: Mejorar RAG local sin coste con chunking recursivo+overlap real, expansion de consulta medica y resiliencia de embeddings largos.
- Alcance: `app/core/chunking.py`, `app/services/embedding_service.py`, `app/services/rag_retriever.py`, `app/services/rag_orchestrator.py`, `app/services/rag_gatekeeper.py`, `app/scripts/ingest_clinical_docs.py`, `app/core/config.py`, `.env`, `.env.example`, tests asociados.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-141.
- Entregables:
  - Chunking recursivo para bloques sobredimensionados (linea/frase/corte duro) y uso real de overlap.
  - Embeddings por ventanas con mean pooling para evitar `input length exceeds context`.
  - Expansion de consulta tipo HyDE-lite (sin servicios externos) y ampliacion de terminos por dominio/especialidad.
  - Gatekeeper con chequeo adicional de relevancia de contexto (`context_relevance`).
  - Mapeo por defecto de `docs/pdf_raw/<especialidad>/` en ingesta para no pasar `--specialty-map` manualmente.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/core/chunking.py app/services/embedding_service.py app/services/rag_retriever.py app/services/rag_orchestrator.py app/services/rag_gatekeeper.py app/scripts/ingest_clinical_docs.py app/core/config.py app/tests/test_chunking.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py app/tests/test_clinical_chat_operational.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_chunking.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py -q`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "gatekeeper_flags_low_faithfulness_as_risk or gatekeeper_flags_low_context_relevance_warning or uses_rag_when_enabled"`
- Riesgos pendientes identificados:
  - La expansion lexical puede introducir ruido en consultas muy ambiguas (requiere calibracion de diccionario).
  - El split por caracteres para embeddings largos prioriza robustez operativa frente a segmentacion linguistica perfecta.

- ID: TM-143
- Objetivo: Mejorar robustez/calidad del retrieval con `adaptive k`, rerank MMR, compresion de contexto y evaluacion offline de retrieval.
- Alcance: `app/core/config.py`, `app/services/rag_orchestrator.py`, `app/services/rag_prompt_builder.py`, `app/scripts/evaluate_rag_retrieval.py`, `app/tests/test_rag_orchestrator_optimizations.py`, `app/tests/test_settings_security.py`.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-142.
- Entregables:
  - Seleccion adaptativa de `k` por longitud/senal de riesgo (`rag_adaptive_k_*`).
  - Reranking MMR configurable para reducir redundancia de chunks (`rag_mmr_*`).
  - Compresion de contexto previa a prompt para bajar ruido/tokens (`rag_context_compressed*`).
  - Script local de evaluacion retrieval (recall@k, MRR, nDCG, context_relevance) sin coste.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/core/config.py app/services/rag_orchestrator.py app/services/rag_prompt_builder.py app/scripts/evaluate_rag_retrieval.py app/tests/test_chunking.py app/tests/test_rag_retriever.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_chunking.py app/tests/test_rag_retriever.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled or gatekeeper_flags_low_context_relevance_warning" -o addopts=""`
- Riesgos pendientes identificados:
  - MMR depende de embeddings disponibles en chunk; si faltan, cae a orden base (trazado como `rag_mmr_reason=missing_vectors`).
  - La compresion lexical puede omitir frases utiles cuando la consulta es demasiado corta/generica.

- ID: TM-144
- Objetivo: Integrar retrieval booleano con indice invertido local (FTS5 SQLite) para reducir latencia y evitar escaneo completo de chunks.
- Alcance: `app/services/rag_retriever.py`, `app/core/config.py`, `.env`, `.env.example`, `app/tests/test_rag_retriever.py`, `app/tests/test_settings_security.py`, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, data-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-143.
- Entregables:
  - Bootstrap automatico de indice invertido FTS5 (`document_chunks_fts`) con triggers de sincronizacion sobre `document_chunks`.
  - Generacion de candidatos por postings booleanos (AND/OR/NOT) y heuristica de interseccion por menor DF.
  - Fallback automatico a `full_scan` cuando FTS no esta disponible.
  - Nuevos flags de runtime para candidate retrieval (`CLINICAL_CHAT_RAG_FTS_CANDIDATE_*`).
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""`
  - `.\venv\Scripts\python.exe - <<'PY' ... HybridRetriever()._ensure_sqlite_fts_index(...) + MATCH checks + _fetch_candidate_chunks(...) ... PY` (OK: `candidate_strategy=fts_postings_boolean`, `candidate_chunks_pool=14`)
- Riesgos pendientes identificados:
  - FTS5 depende de build SQLite local; si no esta disponible, cae a `full_scan` con mayor latencia.
  - El parser booleano es simplificado (secuencial) y no implementa precedencia completa de parentesis.
  - El primer `rebuild` de FTS5 puede costar tiempo en frio en corpus grandes; ocurre una vez por proceso.

- ID: TM-145
- Objetivo: Completar retrieval booleano avanzado con precedencia/parÃ©ntesis, soporte de frases y correcciÃ³n ortogrÃ¡fica ligera sin coste.
- Alcance: `app/services/rag_retriever.py`, `app/core/config.py`, `.env`, `.env.example`, `app/tests/test_rag_retriever.py`, `app/tests/test_settings_security.py`, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-144.
- Entregables:
  - Parser booleano con precedencia (`NOT > AND > OR`) y parÃ©ntesis.
  - Soporte de frases (`"..."`) en candidate retrieval FTS.
  - CorrecciÃ³n ortogrÃ¡fica ligera por distancia de ediciÃ³n sobre vocabulario FTS.
  - Nuevas trazas opcionales de parser/spell en `interpretability_trace`.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""`
  - `.\venv\Scripts\python.exe - <<'PY' ... _fetch_candidate_chunks(query='\"neutropenia febril\" AND oncolgia NOT pediatria', ...) ... PY` (OK: `candidate_boolean_parser=precedence_v1`, `candidate_phrase_terms=1`, `candidate_spell_corrections=oncolgia->oncologia`)
- Riesgos pendientes identificados:
  - CorrecciÃ³n ortogrÃ¡fica puede introducir falsos positivos semÃ¡nticos en tÃ©rminos clÃ­nicos raros.
  - Consultas con lÃ³gica booleana muy compleja pueden degradar latencia del candidate stage.
  - Operador `NOT` depende de universo acotado por `candidate_pool`, por lo que no representa exclusion absoluta de todo el corpus.

- ID: TM-146
- Objetivo: Extender retrieval con proximidad (/k) y skip pointers para interseccion acelerada manteniendo semantica booleana.
- Alcance: `app/services/rag_retriever.py`, `app/core/config.py`, `.env`, `.env.example`, `app/tests/test_rag_retriever.py`, `app/tests/test_settings_security.py`, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-145.
- Entregables:
  - Soporte de operador de proximidad `/k` mapeado a `NEAR(...)` en FTS.
  - Interseccion con skip pointers (`sqrt(P)`) para listas largas.
  - Nuevos flags runtime para calibrar skip pointers.
  - Ajuste de fallback: consultas booleanas validas sin match no degradan a union amplia.
- Evidencia:
  - `.\venv\Scripts\python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""`
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""`
  - `.\venv\Scripts\python.exe - <<'PY' ... _fetch_candidate_chunks(query='"neutropenia febril" /4 oncolgia AND NOT pediatria', ...) ... PY` (OK: `candidate_spell_corrections=oncolgia->oncologia`, `candidate_strategy=fts_postings_boolean`)
- Riesgos pendientes identificados:
  - El operador `/k` se resuelve como `NEAR(...)` binario por pares, no como parser de proximidad n-aria compleja.
  - Skip pointers aportan mas valor en listas largas; en listas cortas hay overhead marginal.

- ID: TM-147
- Objetivo: Extender retrieval lexical con comodines (`*`), filtro k-gram/Jaccard y respaldo fonetico Soundex para mejorar recall sin romper latencia.
- Alcance: `app/services/rag_retriever.py`, `app/core/config.py`, `.env`, `.env.example`, `app/tests/test_rag_retriever.py`, `app/tests/test_settings_security.py`, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-146.
- Entregables:
  - Soporte de token wildcard `*` en parser booleano y expansion sobre vocabulario FTS.
  - Filtro de candidatos por similitud k-gram + Jaccard antes de aplicar Levenshtein.
  - Respaldo fonetico con Soundex para terminos fuera de vocabulario cercano.
  - Gating de correccion: solo se intenta spell cuando postings del termino <= umbral configurable.
  - Nuevos flags runtime para wildcard/k-gram/soundex.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""`
- Riesgos pendientes identificados:
  - Expansion wildcard agresiva puede introducir ruido en consultas muy cortas con `*`.
  - Soundex es util para nombres/terminos foneticos, pero puede mezclar terminos clinicos tecnicos no homofonos.

- ID: TM-148
- Objetivo: Añadir correccion ortografica sensible al contexto (bigramas en corpus) para priorizar sugerencias mas coherentes sin coste externo.
- Alcance: `app/services/rag_retriever.py`, `app/core/config.py`, `.env`, `.env.example`, `app/tests/test_rag_retriever.py`, `app/tests/test_settings_security.py`, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-147.
- Entregables:
  - Mapa de contexto por operando en query booleana (`left/right neighbor`).
  - Ranking de sugerencias por distancia + soporte contextual (frases de 2 terminos en FTS).
  - Limite de candidatos contextuales para mantener latencia controlada.
  - Nuevas trazas de observabilidad para modo contextual.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""`
- Riesgos pendientes identificados:
  - El score contextual basado en bigramas locales puede sesgar correcciones hacia terminologia dominante del corpus.
  - En corpus pequeños, el soporte contextual puede ser bajo y prevalecera Levenshtein/doc_freq.

- ID: TM-149
- Objetivo: Reducir latencia I/O en retrieval con cache de diccionario FTS en memoria (prefijos/wildcard/spell) con TTL y limites configurables.
- Alcance: `app/services/rag_retriever.py`, `app/core/config.py`, `.env`, `.env.example`, `app/tests/test_rag_retriever.py`, `app/tests/test_settings_security.py`, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-148.
- Entregables:
  - Cache de vocabulario FTS (`term->doc_freq`) en memoria con recarga por TTL.
  - Lookup por prefijo con estructura ordenada (`bisect`) y fallback a DB cuando no hay cache.
  - Integracion de cache en wildcard y spell correction.
  - Trazas de observabilidad para hits cache vs DB.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""`
- Riesgos pendientes identificados:
  - Cache de vocabulario puede quedar temporalmente desalineada frente a ingestas muy frecuentes hasta vencer TTL.
  - Limitar `VOCAB_CACHE_MAX_TERMS` demasiado bajo puede reducir recall en wildcard/spell para vocabularios muy grandes.

- ID: TM-150
- Objetivo: Mejorar eficiencia de retrieval con cache de postings comprimida (gap+VB/gamma) y agregar script de dimensionamiento Heaps/Zipf.
- Alcance: `app/services/rag_retriever.py`, `app/core/config.py`, `.env`, `.env.example`, `app/scripts/estimate_rag_index_stats.py`, `app/tests/test_rag_retriever.py`, `app/tests/test_settings_security.py`, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-149.
- Entregables:
  - Cache LRU de postings con TTL y codificacion compacta por gaps.
  - Codificacion/decodificacion Variable Byte (VB) y opcion Gamma para pruebas.
  - Trazas de hits/miss/eviction de cache de postings.
  - Script de estimacion estadistica de corpus (Heaps/Zipf) para dimensionamiento.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/scripts/estimate_rag_index_stats.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""`
  - `./venv/Scripts/python.exe -m app.scripts.estimate_rag_index_stats --chunk-limit 200 --top 10`
- Riesgos pendientes identificados:
  - Gamma comprime mejor pero decodifica mas lento; mantener `vb` como default en produccion CPU-bound.
  - Cache de postings puede crecer en memoria si los limites se configuran altos respecto a RAM disponible.

- ID: TM-151
- Objetivo: Mejorar ranking lexical de RAG con tf-idf por zonas, coseno normalizado y penalizacion pivotada por longitud.
- Alcance: `app/services/rag_retriever.py`, `app/core/config.py`, `.env`, `.env.example`, `app/tests/test_rag_retriever.py`, `app/tests/test_settings_security.py`, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-150.
- Entregables:
  - Scorer keyword reemplazado por `tfidf_zone_cosine_pivoted`.
  - Ponderacion por zonas (`title`, `section`, `body`, `keywords`, `custom_questions`) configurable.
  - Normalizacion pivotada por longitud para reducir sesgo de chunk largo.
  - Mezcla hibrida vector+keyword usando score normalizado real (no solo ranking posicional).
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""`
- Riesgos pendientes identificados:
  - El `idf` se estima sobre el pool candidato (rapido) y no sobre toda la coleccion, por lo que puede variar entre consultas.
  - Si se sobrepondera `title/section`, puede bajar recall en chunks validos con evidencia solo en `body`.

- ID: TM-152
- Objetivo: Acelerar y robustecer ranking lexical con poda por idf, bonus de proximidad y calidad estatica, manteniendo costo cero.
- Alcance: `app/services/rag_retriever.py`, `app/core/config.py`, `.env`, `.env.example`, `app/tests/test_rag_retriever.py`, `app/tests/test_settings_security.py`, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-151.
- Entregables:
  - Poda de terminos de consulta por `idf` (inexact top-k orientado a velocidad).
  - Bonus de proximidad por ventana minima sobre `chunk_text`.
  - Calidad estatica `g(d)` para net-score lexical.
  - Ranking por niveles (tier1/tier2) usando umbral de calidad.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""`
- Riesgos pendientes identificados:
  - La calidad estatica `g(d)` es heuristica local; requiere calibracion con feedback real para evitar sesgos por fuente.
  - El bonus de proximidad depende de tokenizacion simple; puede degradarse en queries muy largas o con variaciones morfologicas.

- ID: TM-153
- Objetivo: Implantar evaluacion IR clinica completa offline (P/R/F1, P@k, MAP, MRR, nDCG, Kappa opcional y A/B offline) sobre retrieval RAG.
- Alcance: `app/scripts/evaluate_rag_retrieval.py`, `app/tests/test_evaluate_rag_retrieval.py`, contratos/docs.
- Agentes involucrados: orchestrator, qa-agent, api-agent.
- Estado: completado
- Dependencias: TM-152.
- Entregables:
  - Script de evaluacion ampliado con metricas base y de ranking.
  - Soporte de relevancia graduada (`graded_relevance`) y binaria (`expected_doc_ids` / `expected_terms`).
  - Kappa de Cohen opcional desde `assessor_labels`.
  - Comparativa A/B offline entre estrategias (`--strategy` y `--ab-strategy`).
  - Reporte por consulta con KWIC top1 para auditoria visual.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/scripts/evaluate_rag_retrieval.py app/tests/test_evaluate_rag_retrieval.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_evaluate_rag_retrieval.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py app/tests/test_evaluate_rag_retrieval.py -o addopts=""`
  - `./venv/Scripts/python.exe -m app.scripts.evaluate_rag_retrieval --dataset tmp/rag_eval.jsonl --k 8 --precision-ks 1,3,5 --strategy auto`
- Riesgos pendientes identificados:
  - En modo fallback por `expected_terms`, recall/AP se estiman sobre top-k observable (util para iteracion, no reemplaza gold de doc_id).
  - Kappa depende de la calidad y cantidad de pares de etiquetado humano en `assessor_labels`.

- ID: TM-154
- Objetivo: Mejorar recall semantico con expansion global por tesauro local y pseudo-relevance feedback (Rocchio simplificado) sin costo.
- Alcance: `app/services/rag_retriever.py`, `app/core/config.py`, `.env`, `.env.example`, `docs/clinical_thesaurus_es_en.json`, `app/tests/test_rag_retriever.py`, `app/tests/test_settings_security.py`, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-152, TM-153.
- Entregables:
  - Expansion global por tesauro local JSON (cacheado con TTL).
  - Expansion PRF (blind feedback) sobre top-k pseudo-relevante con pesos tipo Rocchio (`beta/gamma`).
  - Integracion en `search_keyword` y `search_hybrid` con trazas de expansion.
  - Tesauro inicial clinico ES/EN en `docs/clinical_thesaurus_es_en.json`.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""`
  - smoke python local con `search_hybrid("leucemia ...")` verificando trazas `retrieval_query_expansion_global_terms`.
- Riesgos pendientes identificados:
  - PRF puede inducir deriva si los primeros resultados son pobres (query drift).
  - El tesauro local requiere curacion continua por especialidad para evitar sinonimos ambiguos.

- ID: TM-155
- Objetivo: Consolidar retrieval probabilistico (BM25 + bonus BIM) en el scorer lexical con trazabilidad operativa para auditoria.
- Alcance: app/services/rag_retriever.py, app/core/config.py, .env, .env.example, app/tests/test_rag_retriever.py, app/tests/test_settings_security.py, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-154.
- Entregables:
  - Blend probabilistico BM25 configurable (k1, b, blend) sobre ranking lexical tf-idf por zonas.
  - Bonus BIM configurable para reforzar terminos discriminativos.
  - Trazas estables de config probabilistica incluso cuando no hay candidatos.
  - Trazas de contribucion media probabilistica en top-k.
- Evidencia:
  - ./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py
  - ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py app/tests/test_evaluate_rag_retrieval.py -o addopts=""
  - ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""
- Riesgos pendientes identificados:
  - BM25 se calcula sobre el pool candidato y no sobre el corpus completo, por lo que el score relativo puede fluctuar por consulta.
  - Si blend o bim_bonus_weight se elevan demasiado, se puede penalizar evidencia correcta pero poco repetida en chunks cortos.

- ID: TM-156
- Objetivo: Integrar ranking probabilistico por Query Likelihood Model (unigrama) con suavizado configurable para mejorar recall bajo incertidumbre lexical.
- Alcance: app/services/rag_retriever.py, app/core/config.py, .env, .env.example, app/tests/test_rag_retriever.py, app/tests/test_settings_security.py, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-155.
- Entregables:
  - Capa QLM unigrama con suavizado Dirichlet/Jelinek-Mercer configurable.
  - Blend QLM sobre score lexical existente (tf-idf por zonas + BM25/BIM).
  - Trazas operativas QLM: qlm_enabled, smoothing, mu/lambda, blend y qlm_top_avg.
  - Pruebas unitarias de suavizado y de inclusion de QLM en metodo de ranking.
- Evidencia:
  - ./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py
  - ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py app/tests/test_evaluate_rag_retrieval.py -o addopts=""
  - ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""
- Riesgos pendientes identificados:
  - El modelo QLM se estima sobre candidate pool, no sobre corpus completo; los scores son relativos por consulta.
  - Un blend alto de QLM puede sobre-suavizar y diluir señales fuertes de coincidencia exacta en consultas muy cortas.

- ID: TM-157
- Objetivo: Integrar clasificacion supervisada Naive Bayes para rerank de dominio clinico en chat y mejorar validez de enrutado bajo incertidumbre.
- Alcance: app/services/clinical_naive_bayes_service.py, app/services/clinical_chat_service.py, app/services/__init__.py, app/core/config.py, .env, .env.example, app/tests/test_clinical_naive_bayes_service.py, app/tests/test_clinical_chat_operational.py, app/tests/test_settings_security.py, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-156.
- Entregables:
  - Servicio local de clasificacion NB (multinomial/bernoulli) con smoothing Laplace y scoring en log.
  - Seleccion de features configurable (chi2, MI o sin filtro).
  - Rerank de dominio en chat cuando NB tiene confianza minima y la capa matematica esta incierta.
  - Trazabilidad operativa nb_* y hechos de memoria nb_top_domain, nb_top_probability.
  - Parametrizacion de runtime por settings/env para activar modelo y umbrales sin coste externo.
- Evidencia:
  - ./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/clinical_naive_bayes_service.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_naive_bayes_service.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py
  - ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_naive_bayes_service.py -o addopts=""
  - ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "test_chat_domain_rerank_uses_naive_bayes_when_math_uncertain" -o addopts=""
  - ./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -k "nb_ or naive_bayes or invalid_nb" -o addopts=""
- Riesgos pendientes identificados:
  - La fase de entrenamiento usa catalogo local pseudo-etiquetado por keywords; requiere dataset clinico etiquetado para calibracion de precision/recall por especialidad.
  - Al aumentar numero de dominios, la probabilidad maxima de NB baja; el umbral de confianza necesita recalibracion periodica (actual: 0.25) para evitar infra-rerank o sobre-rerank.

- ID: TM-158
- Objetivo: Completar evaluacion de clasificacion Naive Bayes con macropromediado y micropromediado.
- Alcance: app/services/clinical_naive_bayes_service.py, app/tests/test_clinical_naive_bayes_service.py, contratos/docs.
- Agentes involucrados: orchestrator, qa-agent.
- Estado: completado
- Dependencias: TM-157.
- Entregables:
  - Metodo `evaluate_predictions` con precision/recall/F1 por clase.
  - Agregados `macro_precision`, `macro_recall`, `macro_f1`.
  - Agregados `micro_precision`, `micro_recall`, `micro_f1`.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/clinical_naive_bayes_service.py app/tests/test_clinical_naive_bayes_service.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_naive_bayes_service.py -o addopts=""`
- Riesgos pendientes identificados:
  - Las metricas macro/micro dependen de gold labels; sin dataset etiquetado amplio, solo sirven como control local de regresion.
- ID: TM-159
- Objetivo: Integrar clasificacion en espacio vectorial (Rocchio + kNN) para enrutado clinico semantico, con evaluacion macro/micro y matriz de confusion.
- Alcance: app/services/clinical_vector_classification_service.py, app/services/clinical_chat_service.py, app/services/__init__.py, app/core/config.py, .env, .env.example, app/tests/test_clinical_vector_classification_service.py, app/tests/test_clinical_chat_operational.py, app/tests/test_settings_security.py, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-158.
- Entregables:
  - Servicio vectorial local con Rocchio (centroides tf-idf normalizados) y kNN (votacion ponderada por similitud).
  - Modo `hybrid` para combinar Rocchio y kNN.
  - Integracion en chat con rerank de dominio bajo incertidumbre matematica y trazas `vector_*`.
  - Evaluacion con matriz de confusion + precision/recall/F1 por clase y macro/micro promedio.
  - Parametros runtime gratuitos en settings/env (`method`, `k`, `min_confidence`).
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/clinical_vector_classification_service.py app/services/clinical_chat_service.py app/services/__init__.py app/core/config.py app/tests/test_clinical_vector_classification_service.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_vector_classification_service.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "vector_when_math_uncertain" -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -k "vector_" -o addopts=""`
- Riesgos pendientes identificados:
  - El entrenamiento sigue siendo pseudo-supervisado sobre catalogo interno; necesita dataset etiquetado para calibracion clinica robusta.
  - kNN incrementa costo de inferencia frente a Rocchio; mantener `rocchio` como default para latencia estable.
- ID: TM-160
- Objetivo: Integrar clasificacion SVM lineal OVA para rerank de dominio clinico y corregir sesgo por bias en inferencia.
- Alcance: app/services/clinical_svm_domain_service.py, app/services/clinical_chat_service.py, app/core/config.py, .env, .env.example, app/tests/test_clinical_svm_domain_service.py, app/tests/test_clinical_chat_operational.py, app/tests/test_settings_security.py, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-159.
- Entregables:
  - Servicio SVM de dominio (`ClinicalSVMDomainService`) con entrenamiento one-vs-rest y trazas `svm_domain_*`.
  - Integracion de rerank en chat bajo incertidumbre matematica.
  - Ajuste de inferencia para usar componente discriminativo (`w·x`) y calibracion de logits para evitar dominancia del bias.
  - Evaluacion de clasificacion con matriz de confusion y metricas macro/micro.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/clinical_svm_domain_service.py app/services/clinical_chat_service.py app/core/config.py app/tests/test_clinical_svm_domain_service.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_svm_domain_service.py app/tests/test_clinical_chat_operational.py -k "svm_domain" -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -k "svm_domain" -o addopts=""`
- Riesgos pendientes identificados:
  - El entrenamiento sigue pseudo-supervisado sobre catalogo interno y puede no generalizar igual en dominios con terminologia escasa.
  - La calibracion de probabilidad por escala fija (`_INFERENCE_LOGIT_SCALE`) requiere ajuste cuando cambie significativamente el numero/distribucion de dominios.

- ID: TM-161
- Objetivo: Integrar clustering plano (k-means + EM opcional) para priorizar dominios clinicos bajo incertidumbre.
- Alcance: app/services/clinical_flat_clustering_service.py, app/services/clinical_chat_service.py, app/services/__init__.py, app/core/config.py, .env, .env.example, app/tests/test_clinical_flat_clustering_service.py, app/tests/test_clinical_chat_operational.py, app/tests/test_settings_security.py, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-160.
- Entregables:
  - Servicio de clustering plano con seleccion de K por AIC, k-means y refinamiento EM opcional.
  - Metricas de calidad de clustering: Purity, NMI, Rand Index y F-measure.
  - Rerank de dominios candidatos del chat con trazas `cluster_*`.
  - Configuracion runtime gratuita para metodo, rango K, iteraciones y umbral de confianza.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/clinical_flat_clustering_service.py app/services/clinical_chat_service.py app/services/__init__.py app/core/config.py app/tests/test_clinical_flat_clustering_service.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_flat_clustering_service.py app/tests/test_clinical_chat_operational.py -k "cluster" -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -k "cluster" -o addopts=""`
- Riesgos pendientes identificados:
  - Seleccion de K por AIC aproximado puede requerir ajuste en corpus con distribucion muy irregular.
  - El clustering depende del catalogo pseudo-etiquetado; cambios fuertes de dominios pueden exigir recalibrar umbrales.

- ID: TM-162
- Objetivo: Integrar clustering jerarquico (HAC/divisive/buckshot) para priorizacion de dominios clinicos bajo incertidumbre.
- Alcance: app/services/clinical_hierarchical_clustering_service.py, app/services/clinical_chat_service.py, app/services/__init__.py, app/core/config.py, .env, .env.example, app/tests/test_clinical_hierarchical_clustering_service.py, app/tests/test_clinical_chat_operational.py, app/tests/test_settings_security.py, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-161.
- Entregables:
  - Servicio de clustering jerarquico con metodos `hac_single|hac_complete|hac_average|divisive|buckshot`.
  - Seleccion de K por calidad de clustering en rango configurable.
  - Etiquetado diferencial basico de clusters y trazas operativas `hcluster_*`.
  - Rerank de dominio en chat con gate por confianza y opcion de activacion solo bajo incertidumbre matematica.
  - Configuracion runtime sin coste externo para metodo, rango K y parametros buckshot.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/clinical_hierarchical_clustering_service.py app/services/clinical_chat_service.py app/services/__init__.py app/core/config.py app/tests/test_clinical_hierarchical_clustering_service.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_hierarchical_clustering_service.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py -k "hcluster or hierarchical" -o addopts=""`
- Riesgos pendientes identificados:
  - HAC completo sobre muestras grandes incrementa coste O(N^2 logN); mantener recorte por catalogo y K acotado.
  - El etiquetado diferencial de clusters es heuristico y debe interpretarse como apoyo, no verdad clinica.

- ID: TM-163
- Objetivo: Integrar LSI (SVD truncada) en retrieval lexical para reforzar busqueda semantica y reducir gap terminologico.
- Alcance: app/services/rag_retriever.py, app/core/config.py, .env, .env.example, app/tests/test_rag_retriever.py, app/tests/test_settings_security.py, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-156.
- Entregables:
  - Capa LSI sobre pool candidato con proyeccion de consulta por folding-in y similitud coseno en espacio latente.
  - Blend configurable del score LSI con scoring lexical existente.
  - Trazas `keyword_search_lsi_*` para auditoria de componentes, vocabulario, doc_count y score medio top.
  - Parametros runtime `CLINICAL_CHAT_RAG_LSI_*` con validaciones.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -k "lsi or qlm or bm25 or tfidf" -o addopts=""`
- Riesgos pendientes identificados:
  - SVD se calcula por consulta sobre candidate pool; en pools grandes puede aumentar latencia.
  - El fold-in sin reentrenamiento global puede degradar calidad semantica si cambia mucho la distribucion del corpus.

- ID: TM-164
- Objetivo: Endurecer `web_sources` con calidad web operacional (deduplicacion near-duplicate, filtro anti-spam y ranking por autoridad/relevancia).
- Alcance: `app/services/clinical_chat_service.py`, `app/tests/test_clinical_chat_operational.py`, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-163.
- Entregables:
  - Pipeline de filtrado web con:
    - canonizacion de URL para eliminar duplicados obvios.
    - deteccion de near-duplicates por shingles + MinHash (umbral configurable en codigo).
    - filtro heuristico de spam/clickbait.
    - score combinado de autoridad de dominio + relevancia lexical de consulta.
  - Nuevas trazas en `interpretability_trace`:
    - `web_search_enabled`
    - `web_search_candidates_total`
    - `web_search_whitelist_filtered_out`
    - `web_search_spam_filtered_out`
    - `web_search_duplicate_filtered_out`
    - `web_search_quality_sorted`
    - `web_search_near_duplicate_threshold`
    - `web_search_avg_quality_top`
    - `web_search_results`
    - `web_search_error` (si aplica).
  - Tests unitarios nuevos para spam/duplicados y manejo de fallo de request web.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "web_source_quality_filter or fetch_web_sources_returns_error_trace_when_request_fails" -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "test_chat_e2e_uses_rag_when_enabled" -o addopts=""`
- Riesgos pendientes identificados:
  - El score de autoridad es heuristico (no PageRank real) y requiere ajuste con telemetria real de uso.
  - La deteccion de cloaking no se resuelve completamente sin fetch/render de pagina final; se aplica mitigacion parcial por heuristicas.

- ID: TM-165
- Objetivo: Implementar crawler web clinico local (polite) con robots.txt, frontier priorizada por autoridad, deduplicacion y checkpoint para frescura de corpus.
- Alcance: `app/services/web_crawler_service.py`, `app/scripts/crawl_clinical_web.py`, `app/tests/test_web_crawler_service.py`, `app/services/__init__.py`, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-164.
- Entregables:
  - Servicio `WebCrawlerService` con:
    - seeds + URL frontier (front queues por prioridad + back queues por host)
    - cortesia por host (1 conexion activa por host + delay adaptativo)
    - cache DNS local y cache de `robots.txt`
    - parser HTML para texto + enlaces
    - deduplicacion por URL canonica y near-duplicate de contenido (shingles + MinHash)
    - checkpoint JSON de estado para reanudacion.
  - Script `python -m app.scripts.crawl_clinical_web` para ejecucion operativa.
  - Persistencia de salida en `docs/web_raw/<host>/*.md` + `crawl_manifest.jsonl`.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/web_crawler_service.py app/scripts/crawl_clinical_web.py app/tests/test_web_crawler_service.py app/services/__init__.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_web_crawler_service.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "test_chat_e2e_uses_rag_when_enabled" -o addopts=""`
- Riesgos pendientes identificados:
  - No hay scheduler distribuido ni particion por documento entre nodos; esta version es single-node.
  - Deteccion de spider-traps es heuristica basica; faltan reglas avanzadas de patrones infinitos.
  - Robots se respeta por host, pero sin politicas especificas por path-rate externas.

- ID: TM-166
- Objetivo: Integrar analisis de enlaces web (anchor text + PageRank + Topic-PageRank + HITS) para mejorar autoridad y trazabilidad de `web_sources` en chat clinico.
- Alcance: `app/services/web_link_analysis_service.py`, `app/services/clinical_chat_service.py`, `app/services/web_crawler_service.py`, `app/scripts/build_web_link_analysis.py`, `app/tests/test_web_link_analysis_service.py`, `app/tests/test_web_crawler_service.py`, `app/tests/test_clinical_chat_operational.py`, `app/core/config.py`, `app/tests/test_settings_security.py`, `app/services/__init__.py`, contratos/docs.
- Agentes involucrados: orchestrator, api-agent, data-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-165.
- Entregables:
  - Servicio `WebLinkAnalysisService` con:
    - construccion de snapshot desde `crawl_manifest.jsonl`.
    - calculo de PageRank global y Topic-Specific PageRank por iteracion de potencia.
    - calculo HITS (autoridad/hub) global y base-set orientado a consulta.
    - agregacion de terminos de anchor text por URL destino.
    - scoring runtime de candidatos web (`link_score`) con cache de snapshot.
  - Crawler enriquecido para persistir en manifiesto:
    - `outgoing_links`
    - `outgoing_anchor_texts`
    - `outgoing_edges` (url+anchor)
  - Integracion en chat:
    - blend configurable entre `quality_score` base y `link_score`.
    - trazas nuevas `web_search_link_analysis_*`.
  - Script operativo:
    - `python -m app.scripts.build_web_link_analysis`
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/web_link_analysis_service.py app/services/web_crawler_service.py app/services/clinical_chat_service.py app/scripts/build_web_link_analysis.py app/tests/test_web_link_analysis_service.py app/tests/test_web_crawler_service.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py app/core/config.py app/services/__init__.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_web_link_analysis_service.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_web_crawler_service.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "web_source_quality" -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -k "web_link_analysis" -o addopts=""`
  - `./venv/Scripts/python.exe -m app.scripts.build_web_link_analysis --help`
- Riesgos pendientes identificados:
  - HITS orientado a consulta se calcula sobre base-set acotado (heuristico), no sobre todo el grafo web.
  - La calidad del score de enlaces depende de la frescura del snapshot; requiere reconstruccion periodica tras nuevo crawl.
  - Si el manifiesto no incluye anchors suficientes, la senal de `anchor_relevance` pierde discriminacion.

- ID: TM-167
- Objetivo: Endurecer benchmark local de chat para evitar falsos negativos por timeout de cliente al medir LLM/RAG en entorno local.
- Alcance: `tmp/run_chat_benchmark.py`, validacion con `tmp/summarize_chat_benchmark.py`.
- Agentes involucrados: orchestrator, qa-agent.
- Estado: en curso
- Dependencias: API local levantada y login funcional.
- Evidencia:
  - `./venv/Scripts/python.exe tmp/run_chat_benchmark.py`
  - `./venv/Scripts/python.exe tmp/summarize_chat_benchmark.py`
- Riesgos pendientes identificados:
  - Si el endpoint excede 180s de forma sostenida, el problema es de backend/LLM, no del script.

- ID: TM-167 (cierre)
- Objetivo: Endurecer latencia y fallback del chat para evitar timeouts y asegurar respuesta util ante fallo LLM en RAG.
- Alcance: `app/services/llm_chat_provider.py`, `app/services/rag_orchestrator.py`, `app/services/clinical_chat_service.py`, `app/tests/test_clinical_chat_operational.py`.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-166.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/llm_chat_provider.py app/services/rag_orchestrator.py app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "rag_orchestrator_keeps_sources_when_generation_fails or chat_e2e_skips_second_llm_when_rag_failed_generation" -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "test_chat_e2e_uses_rag_when_enabled" -o addopts=""`
- Riesgos pendientes identificados:
  - Si Ollama supera de forma sostenida el budget configurado (`CLINICAL_CHAT_LLM_TIMEOUT_SECONDS`), habra fallback estructurado con evidencia en lugar de respuesta neuronal.

- ID: TM-168
- Objetivo: Romper bucle de `llm_used=false` en entorno local priorizando endpoint Ollama estable y trazabilidad explicita de estado LLM.
- Alcance: `app/services/llm_chat_provider.py`, `app/tests/test_clinical_chat_operational.py`.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-167.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/llm_chat_provider.py app/tests/test_clinical_chat_operational.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "test_llm_provider_prefers_ollama_generate_endpoint or rag_orchestrator_keeps_sources_when_generation_fails or chat_e2e_skips_second_llm_when_rag_failed_generation" -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "test_chat_e2e_uses_rag_when_enabled" -o addopts=""`
- Riesgos pendientes identificados:
  - Si `/api/generate` tambien falla por recursos locales, el sistema seguira en fallback de evidencia (seguro pero menos natural).
  - Requiere reinicio de uvicorn para cargar settings actuales y evitar leer config en memoria desactualizada.

- ID: TM-169
- Objetivo: Evitar `llm_used=false` por timeout en LLM local repartiendo presupuesto temporal entre intentos y asegurando recovery intra-request.
- Alcance: `app/services/llm_chat_provider.py`, `app/tests/test_clinical_chat_operational.py`.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: completado
- Dependencias: TM-168.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/llm_chat_provider.py app/tests/test_clinical_chat_operational.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "test_llm_provider_prefers_ollama_generate_endpoint or test_llm_provider_recovers_after_primary_timeout" -o addopts=""`
- Riesgos pendientes identificados:
  - En hardware muy limitado, aun puede caer a fallback de evidencia si ningun intento devuelve dentro del budget total.

- ID: TM-170
- Objetivo: Estabilizar chat local no pago en CPU usando perfil LLM ligero para evitar timeouts y mantener RAG activo.
- Alcance: `.env`, `.env.example`.
- Agentes involucrados: orchestrator, devops-agent, qa-agent.
- Estado: completado
- Dependencias: TM-169.
- Evidencia:
  - Ajuste de perfil LLM: `phi3:mini`, timeout/contexto/tokens reducidos, quality gates activos.
- Riesgos pendientes identificados:
  - Requiere `ollama pull phi3:mini` y reinicio de uvicorn para aplicar.
  - Calidad semantica depende de cobertura del corpus RAG.


- ID: TM-171
- Objetivo: Dejar RAG estable con PDFs nuevos, sin bloqueos por timeout y con salida limpia cuando LLM no responde.
- Alcance: `app/services/rag_orchestrator.py`, `app/services/llm_chat_provider.py`, `app/services/rag_retriever.py`, `app/services/clinical_chat_service.py`, `app/scripts/ingest_clinical_docs.py`, `app/core/config.py`, `.env`, `.env.example`, tests asociados.
- Agentes involucrados: orchestrator, api-agent, data-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-170.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/llm_chat_provider.py app/services/rag_orchestrator.py app/services/rag_retriever.py app/services/clinical_chat_service.py app/scripts/ingest_clinical_docs.py app/tests/test_clinical_chat_operational.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_rag_retriever.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "rag_orchestrator_uses_extractive_fallback_when_generation_fails or llm_provider_circuit_breaker_short_circuits_after_failures" -o addopts=""`
  - `./venv/Scripts/python.exe -m app.scripts.ingest_clinical_docs --paths docs/pdf_raw --backfill-specialty --skip-ollama-embeddings`
  - `./venv/Scripts/python.exe -m app.scripts.evaluate_rag_retrieval --dataset tmp/rag_eval.jsonl --k 8`
- Riesgos pendientes identificados:
  - El backend en ejecucion debe reiniciarse para cargar estos cambios en memoria.
  - El corpus PDF crecio de forma significativa; conviene monitorizar `candidate_chunks_pool` y tiempos de retrieval en produccion.

- ID: TM-172
- Objetivo: Reducir latencia de ingesta incremental PDF evitando reprocesado de archivos ya presentes en BD por `source_file`.
- Alcance: `app/scripts/ingest_clinical_docs.py`.
- Agentes involucrados: orchestrator, data-agent, qa-agent.
- Estado: completado
- Dependencias: TM-171.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/scripts/ingest_clinical_docs.py`
  - `./venv/Scripts/python.exe -m app.scripts.ingest_clinical_docs --paths docs/pdf_raw --backfill-specialty`
- Riesgos pendientes identificados:
  - Si un archivo cambia manteniendo el mismo `source_file`, la ruta incremental lo omite; usar `--force-reprocess-existing-paths` para reingesta completa.

- ID: TM-173
- Objetivo: Optimizar latencia del chat RAG local con presupuesto temporal por request y contexto LLM mas denso.
- Alcance: `app/core/config.py`, `app/services/rag_orchestrator.py`, `app/services/llm_chat_provider.py`, `app/schemas/clinical_chat.py`, `.env`, `.env.example`, tests.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-171, TM-172.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/llm_chat_provider.py app/services/rag_orchestrator.py app/schemas/clinical_chat.py app/tests/test_rag_orchestrator_optimizations.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "llm_provider_build_chat_messages_respects_token_budget or llm_provider_prefers_ollama_generate_endpoint or llm_provider_recovers_after_primary_timeout or llm_provider_circuit_breaker_short_circuits_after_failures" -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -o addopts=""`
- Riesgos pendientes identificados:
  - En casos de alta complejidad, el contexto reducido puede requerir ampliar limites por request para preservar exhaustividad.

- ID: TM-174
- Objetivo: Reducir p95/p99 de latencia en chat RAG local acotando fan-out de retrieval y contexto por request.
- Alcance: `app/services/rag_orchestrator.py`, `app/core/config.py`, `.env`, `.env.example`, `app/tests/test_rag_orchestrator_optimizations.py`.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-173.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/rag_orchestrator.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "llm_provider_build_chat_messages_respects_token_budget or llm_provider_prefers_ollama_generate_endpoint or llm_provider_recovers_after_primary_timeout or llm_provider_circuit_breaker_short_circuits_after_failures" -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -o addopts=""`
  - `./venv/Scripts/python.exe -m app.scripts.evaluate_rag_retrieval --dataset tmp/rag_eval.jsonl --k 8`
- Riesgos pendientes identificados:
  - consultas extremadamente amplias pueden requerir override manual de `max_internal_sources`/`max_history_messages` para preservar recall contextual.

- ID: TM-175
- Objetivo: Reducir p95 de latencia en consultas complejas con fast-path de retrieval y tuning agresivo de expansi?n l?xica.
- Alcance: `app/services/rag_orchestrator.py`, `app/core/config.py`, `.env`, `.env.example`, `app/tests/test_rag_orchestrator_optimizations.py`.
- Agentes involucrados: orchestrator, api-agent, qa-agent, devops-agent.
- Estado: completado
- Dependencias: TM-174.
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/rag_orchestrator.py app/tests/test_rag_orchestrator_optimizations.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -o addopts=""`
  - `./venv/Scripts/python.exe -m app.scripts.evaluate_rag_retrieval --dataset tmp/rag_eval.jsonl --k 8`
- Riesgos pendientes identificados:
  - en consultas de exploraci?n amplia puede requerirse elevar l?mites por request para maximizar recall.


## TM-176

- Objetivo:
  - Cortar cascada de latencia cuando RAG falla en retrieval y estabilizar recall en consultas largas.
- Alcance:
  - `app/services/clinical_chat_service.py`
  - `app/core/config.py`
  - `.env`
  - `.env.example`
  - `app/tests/test_clinical_chat_operational.py`
- Agentes involucrados:
  - orchestrator, api-agent, qa-agent.
- Estado:
  - completado
- Dependencias:
  - TM-175
- Evidencia:
  - pendiente de ejecucion de pruebas.

## TM-176 - Cierre

- Estado:
  - completado
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/clinical_chat_service.py app/core/config.py app/tests/test_clinical_chat_operational.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "failed_retrieval or failed_generation" -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`

## TM-177

- Objetivo:
  - Priorizar calidad de respuesta: reparar automaticamente salidas degradadas con fallback evidence-first anclado en fuentes RAG.
- Alcance:
  - `app/services/clinical_chat_service.py`
  - `app/tests/test_clinical_chat_operational.py`
  - `.env`
  - `.env.example`
- Agentes involucrados:
  - orchestrator, api-agent, qa-agent.
- Estado:
  - en curso
- Dependencias:
  - TM-176
- Evidencia:
  - pendiente de ejecucion de pruebas.

## TM-177 - Cierre

- Estado:
  - completado
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py app/core/config.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py::test_chat_e2e_repairs_degraded_answer_with_evidence_first -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "failed_retrieval or failed_generation" -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py app/tests/test_rag_orchestrator_optimizations.py -o addopts=""`

## TM-178

- Objetivo:
  - Aplicar mejoras del diagnostico para elevar calidad y cerrar brechas de observabilidad (p95 correcto + gate de aceptacion).
- Alcance:
  - `app/services/rag_orchestrator.py`
  - `app/services/clinical_chat_service.py`
  - `tmp/summarize_chat_benchmark.py`
  - `tmp/check_acceptance.py`
- Agentes involucrados:
  - orchestrator, api-agent, qa-agent.
- Estado:
  - completado
- Dependencias:
  - TM-177
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_orchestrator.py app/services/clinical_chat_service.py app/tests/test_rag_orchestrator_optimizations.py tmp/summarize_chat_benchmark.py tmp/check_acceptance.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py::test_build_rag_sources_prioritizes_high_score_before_source_type -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "quality_repair or failed_retrieval" -o addopts=""`
  - `./venv/Scripts/python.exe tmp/summarize_chat_benchmark.py`
  - `./venv/Scripts/python.exe tmp/check_acceptance.py`

## TM-179

- Objetivo:
  - Recuperar uso de LLM en benchmark y bajar p95 sin romper estabilidad de retrieval.
- Alcance:
  - `app/core/config.py`
  - `.env`
  - `.env.example`
  - `tmp/summarize_chat_benchmark.py`
- Agentes involucrados:
  - orchestrator, api-agent, qa-agent.
- Estado:
  - en curso
- Dependencias:
  - TM-178
- Evidencia:
  - pendiente

## TM-180

- Objetivo:
  - Habilitar backend LLM `llama_cpp` (local, sin pago) como alternativa operativa a Ollama.
- Alcance:
  - `app/core/config.py`
  - `app/services/llm_chat_provider.py`
  - `app/tests/test_settings_security.py`
  - `app/tests/test_clinical_chat_operational.py`
- Agentes involucrados:
  - orchestrator, api-agent, qa-agent.
- Estado:
  - completado
- Dependencias:
  - TM-179
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/llm_chat_provider.py app/tests/test_settings_security.py app/tests/test_clinical_chat_operational.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py app/tests/test_clinical_chat_operational.py -k "llama_cpp or parse_ollama_payload_supports_sse_data_lines or llm_provider_prefers_ollama_generate_endpoint" -o addopts=""`

## TM-181

- Objetivo:
  - Reconfigurar el runtime local para usar `llama.cpp` de forma estable en benchmark, reduciendo `TimeoutError`/`CircuitOpen`.
- Alcance:
  - `.env`
  - `.env.example`
  - `agents/shared/TASK_BOARD.md`
  - `agents/shared/api_contract.md`
  - `agents/shared/test_plan.md`
  - `agents/shared/deploy_notes.md`
  - `docs/decisions/ADR-0133-llama-cpp-runtime-tuning-local.md`
- Agentes involucrados:
  - orchestrator, api-agent, qa-agent, devops-agent.
- Estado:
  - completado
- Dependencias:
  - TM-180
- Evidencia:
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py::test_allows_llama_cpp_provider app/tests/test_clinical_chat_operational.py::test_extract_llama_cpp_answer_openai_compatible_payload -o addopts=""`

## TM-182

- Objetivo:
  - Reducir `TimeoutError/BudgetExhausted` en benchmark con `llama.cpp` mediante tuning de presupuesto y complejidad de retrieval.
- Alcance:
  - `.env`
  - `.env.example`
- Estado:
  - completado
- Evidencia:
  - pendiente de benchmark post-restart.

## TM-183

- Objetivo:
  - Habilitar Plan B real: chat asincrono con pausa/reanudacion para evitar timeout del request HTTP en inferencia local CPU.
- Alcance:
  - `app/services/clinical_chat_async_service.py`
  - `app/api/care_tasks.py`
  - `app/schemas/clinical_chat.py`
  - `app/schemas/__init__.py`
  - `app/services/__init__.py`
  - `app/tests/test_care_tasks_api.py`
  - `docs/decisions/ADR-0135-chat-asincrono-pausa-reanudacion.md`
- Agentes involucrados:
  - orchestrator, api-agent, qa-agent.
- Estado:
  - completado
- Dependencias:
  - TM-182
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/clinical_chat_async_service.py app/api/care_tasks.py app/schemas/clinical_chat.py app/schemas/__init__.py app/services/__init__.py app/tests/test_care_tasks_api.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_care_tasks_api.py -k "chat_message_async" -o addopts=""`

- ID: TM-138
- Objetivo: Endurecer Plan B de latencia/calidad con enrutado determinista simple/complex, safe-wrapper explicito por umbral de evidencia y limite de utilizacion de contexto LLM.
- Alcance: `app/core/config.py`, `app/services/llm_chat_provider.py`, `app/services/rag_orchestrator.py`, `app/services/rag_gatekeeper.py`, `app/tests/test_rag_orchestrator_optimizations.py`, `app/tests/test_clinical_chat_operational.py`, `app/tests/test_settings_security.py`, `.env.example`.
- Agentes involucrados: orchestrator, api-agent, qa-agent.
- Estado: en curso
- Dependencias: TM-135, TM-136, TM-137.
- Evidencia:
  - Pendiente de ejecucion.

- ID: TM-138
- Estado: completado
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/llm_chat_provider.py app/services/rag_gatekeeper.py app/services/rag_orchestrator.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""` (10 passed)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "llm_provider_build_chat_messages_respects_token_budget" -o addopts=""` (1 passed)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -k "invalid_llm_context_utilization_ratio or invalid_simple_route_max_chunks_vs_hard_limit" -o addopts=""` (2 passed)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -o addopts=""` (77 passed)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "llm_provider" -o addopts=""` (4 passed)

## TM-184

- Objetivo:
  - Estabilizar chat clinico en frontend con modo extractivo forzado y reducir `failed_retrieval` mediante reintento sin filtro de especialidad.
- Alcance:
  - `app/core/config.py`
  - `app/services/rag_orchestrator.py`
  - `app/services/clinical_chat_service.py`
  - `app/tests/test_rag_orchestrator_optimizations.py`
  - `app/tests/test_clinical_chat_operational.py`
  - `.env`
  - `.env.example`
- Agentes involucrados:
  - orchestrator, api-agent, qa-agent, devops-agent.
- Estado:
  - completado
- Dependencias:
  - TM-183
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/rag_orchestrator.py app/services/clinical_chat_service.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_clinical_chat_operational.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "force_extractive_only or rag_failed_retrieval or rag_failed_generation" -o addopts=""`
- Riesgos pendientes identificados:
  - menor fluidez conversacional al priorizar salida extractiva sobre generativa.
  - si la evidencia recuperada es pobre, aumentaran respuestas de abstencion/plan base seguro.

## TM-185

- Objetivo:
  - Reducir `failed_retrieval` en consultas naturales largas evitando vacios por parser booleano con `AND` implicitos.
- Alcance:
  - `app/services/rag_retriever.py`
  - `app/tests/test_rag_retriever.py`
  - `docs/decisions/ADR-0138-rag-boolean-relaxed-union-natural-language.md`
- Agentes involucrados:
  - orchestrator, qa-agent.
- Estado:
  - completado
- Dependencias:
  - TM-184
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/tests/test_rag_retriever.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py -k "fetch_candidate_chunks_relaxes_non_explicit_boolean_when_intersection_is_empty or fetch_candidate_chunks_keeps_strict_no_match_for_explicit_boolean" -o addopts=""`
  - verificacion manual de `HybridRetriever.search_hybrid(...)`: queries 1/2/5 recuperan chunks con `candidate_strategy=fts_boolean_relaxed_union`.
- Riesgos pendientes identificados:
  - union relajada puede ampliar recall con algo mas de ruido semantico en consultas ambiguas.
  - requiere reinicio de `uvicorn` para validar impacto en benchmark HTTP.

## TM-186

- Objetivo:
  - Aplicar patron HybridRAG offline-first con QA shortcut para reducir latencia sin depender de LLM en runtime.
- Alcance:
  - `app/core/config.py`
  - `app/services/rag_orchestrator.py`
  - `app/tests/test_rag_orchestrator_optimizations.py`
  - `app/tests/test_settings_security.py`
  - `.env`
  - `.env.example`
  - `docs/decisions/ADR-0139-hybridrag-qa-shortcut-offline-first.md`
- Agentes involucrados:
  - orchestrator, qa-agent, devops-agent.
- Estado:
  - completado
- Dependencias:
  - TM-185
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/rag_orchestrator.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -k "qa_shortcut" -o addopts=""`
  - smoke local `_match_precomputed_qa_chunks(...)` con BD real.
- Riesgos pendientes identificados:
  - cobertura desigual de `custom_questions` por especialidad; en dominios con baja cobertura el shortcut no impacta.
  - requiere reinicio de `uvicorn` para aplicar config y validar benchmark HTTP.

## TM-187

- Objetivo:
  - Elevar cobertura RAG en todas las especialidades y preparar parser PDF configurable con backend MinerU (fail-open) para ingesta robusta.
- Alcance:
  - `app/services/rag_orchestrator.py`
  - `app/services/rag_retriever.py`
  - `app/core/chunking.py`
  - `app/scripts/ingest_clinical_docs.py`
  - `app/services/pdf_parser_service.py`
  - `app/services/document_ingestion_service.py`
  - `app/core/config.py`
  - `.env.example`
  - `.env.docker`
  - `app/tests/test_rag_orchestrator_optimizations.py`
  - `app/tests/test_chunking.py`
  - `app/tests/test_ingest_clinical_docs_script.py`
  - `app/tests/test_pdf_parser_service.py`
  - `app/tests/test_settings_security.py`
- Agentes involucrados:
  - orchestrator, api-agent, data-agent, qa-agent, devops-agent.
- Estado:
  - completado
- Dependencias:
  - TM-186
- Evidencia:
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_ingest_clinical_docs_script.py app/tests/test_chunking.py app/tests/test_pdf_parser_service.py app/tests/test_document_ingestion_service.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_orchestrator.py app/scripts/ingest_clinical_docs.py app/tests/test_ingest_clinical_docs_script.py app/services/pdf_parser_service.py app/services/document_ingestion_service.py app/tests/test_pdf_parser_service.py app/tests/test_chunking.py -q`
- Riesgos pendientes identificados:
  - Si MinerU no esta desplegado, se usa fallback `pypdf` (sin OCR avanzado ni tablas OTSL reales).
  - El filtro anti-ruido puede excluir algun fragmento util si un documento mezcla texto clinico con bloques tecnicos.

## TM-188

- Objetivo:
  - Implementar hardening de ingesta PDF/RAG: para_blocks estructurados, limpieza de artefactos, orden de lectura, chunking tipado (tabla/formula/texto), OCR selectivo configurable y telemetria.
- Alcance:
  - `app/services/pdf_parser_service.py`
  - `app/services/document_ingestion_service.py`
  - `app/core/chunking.py`
  - `app/core/config.py`
  - `app/scripts/ingest_clinical_docs.py`
  - `.env.example`
  - `.env.docker`
  - `app/tests/test_pdf_parser_service.py`
  - `app/tests/test_document_ingestion_service.py`
  - `app/tests/test_chunking.py`
  - `app/tests/test_settings_security.py`
- Agentes involucrados:
  - orchestrator, api-agent, data-agent, qa-agent, devops-agent.
- Estado:
  - completado
- Dependencias:
  - TM-187
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/pdf_parser_service.py app/services/document_ingestion_service.py app/core/chunking.py app/core/config.py app/scripts/ingest_clinical_docs.py app/tests/test_pdf_parser_service.py app/tests/test_document_ingestion_service.py app/tests/test_chunking.py app/tests/test_settings_security.py -q`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_pdf_parser_service.py app/tests/test_document_ingestion_service.py app/tests/test_chunking.py app/tests/test_settings_security.py app/tests/test_ingest_clinical_docs_script.py -o addopts=""`
- Riesgos pendientes identificados:
  - `para_blocks` depende del contrato real del servicio MinerU desplegado; se mantiene fallback robusto a campos alternativos.
  - sin GPU/servicio MinerU activo, el parser avanzado no se ejecuta y cae a `pypdf`.

## TM-189

- Objetivo:
  - Endurecer ingesta y evaluacion offline RAG con quality gates deterministas por documento y acceptance por umbrales (global + por especialidad).
- Alcance:
  - `app/scripts/ingest_clinical_docs.py`
  - `app/scripts/evaluate_rag_retrieval.py`
  - `app/tests/test_ingest_clinical_docs_script.py`
  - `app/tests/test_evaluate_rag_retrieval.py`
  - `agents/shared/TASK_BOARD.md`
  - `agents/shared/api_contract.md`
  - `agents/shared/data_contract.md`
  - `agents/shared/test_plan.md`
  - `agents/shared/deploy_notes.md`
  - `docs/01_current_state.md`
  - `docs/decisions/ADR-0142-quality-gates-ingesta-y-aceptacion-offline-rag.md`
- Agentes involucrados:
  - orchestrator, data-agent, qa-agent.
- Estado:
  - completado
- Dependencias:
  - TM-188
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/scripts/ingest_clinical_docs.py app/scripts/evaluate_rag_retrieval.py app/tests/test_ingest_clinical_docs_script.py app/tests/test_evaluate_rag_retrieval.py -q`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_ingest_clinical_docs_script.py app/tests/test_evaluate_rag_retrieval.py -o addopts=""`
- Riesgos pendientes identificados:
  - Umbrales muy estrictos pueden descartar documentos clinicos breves pero utiles; ajustar por corpus.
  - Las metricas de aceptacion por especialidad dependen de cobertura real del dataset offline (`query/specialty`).

## TM-190

- Objetivo:
  - Cumplir benchmark end-to-end (`run_chat_benchmark + summarize + check_acceptance`) en modo RAG extractivo local sin LLM.
- Alcance:
  - `app/services/clinical_chat_service.py`
  - `app/services/rag_orchestrator.py`
  - `app/services/rag_retriever.py`
- Agentes involucrados:
  - orchestrator, api-agent, qa-agent.
- Estado:
  - completado
- Dependencias:
  - TM-189
- Evidencia:
  - `./venv/Scripts/python.exe tmp/run_chat_benchmark.py`
  - `./venv/Scripts/python.exe tmp/summarize_chat_benchmark.py`
  - `./venv/Scripts/python.exe tmp/check_acceptance.py`
  - Resultado: `BENCHMARK OK - criterios cumplidos.`
- Riesgos pendientes identificados:
  - El modo `keyword_only` se activa para consultas complejas en extractivo forzado; puede perder recall semantico en preguntas ambiguas.
  - Las metricas de calidad son heuristicas lexicales; requieren vigilancia periodica para evitar sobreajuste a benchmark fijo.

## TM-191

- Objetivo:
  - Reducir cola de latencia en RAG con enrutado adaptativo matematico (complejidad + presupuesto) manteniendo benchmark en verde.
- Alcance:
  - `app/services/rag_orchestrator.py`
  - `app/services/rag_retriever.py`
  - `.env`
- Agentes involucrados:
  - orchestrator, api-agent, qa-agent.
- Estado:
  - completado
- Dependencias:
  - TM-190
- Evidencia:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_orchestrator.py app/services/rag_retriever.py app/services/clinical_chat_service.py -q`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""`
  - `./venv/Scripts/python.exe tmp/run_chat_benchmark.py`
  - `./venv/Scripts/python.exe tmp/summarize_chat_benchmark.py`
  - `./venv/Scripts/python.exe tmp/check_acceptance.py`
  - Resultado: `BENCHMARK OK - criterios cumplidos` con `latency_ok_p95_ms=2719.0`.
- Riesgos pendientes identificados:
  - `llm_used_true_rate` sigue bajo en consultas complejas por politica de presupuesto.
  - consultas muy generales pueden activar safe-wrapper antes de LLM.

- ID: TM-192
- Objetivo: Endurecer salida clinica para ocultar detalles internos (endpoints/backend/comandos) en respuestas de chat.
- Alcance: app/services/clinical_chat_service.py, app/services/rag_orchestrator.py
- Agentes involucrados: codex
- Estado: en curso
- Dependencias: TM-137
- Evidencia: filtros de snippet y de fuentes internas aplicados.


## TM-193

- Objetivo:
  - Integrar backend RAG opcional basado en Elasticsearch (`elastic`) con fallback automatico a `legacy`.
- Alcance:
  - `app/services/elastic_retriever.py`
  - `app/services/rag_orchestrator.py`
  - `app/core/config.py`
  - `.env.example`
  - `app/tests/test_clinical_chat_operational.py`
  - `app/tests/test_settings_security.py`
- Agentes involucrados:
  - orchestrator, api-agent, qa-agent, devops-agent.
- Estado:
  - completado
- Dependencias:
  - TM-191
- Evidencia:
  - backend `elastic` integrado en selector RAG + fallback `legacy`.
  - settings y docs actualizados.
  - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/elastic_retriever.py app/services/rag_orchestrator.py app/tests/test_settings_security.py app/tests/test_clinical_chat_operational.py`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -o addopts=""`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "elastic_backend or falls_back_to_legacy_when_elastic_empty" -o addopts=""`
- ID: TM-138

- Objetivo: Eliminar requisito de autenticacion en endpoints de chat clinico para permitir uso inmediato desde frontend sin login.

- Alcance: `app/api/deps.py`, `app/api/care_tasks.py`, `app/services/clinical_chat_async_service.py`.

- Agentes involucrados: orchestrator, api-agent, qa-agent.

- Estado: completado

- Dependencias: TM-137.

- Evidencia:

  - `.\venv\Scripts\python.exe -m py_compile app/api/deps.py app/api/care_tasks.py app/services/clinical_chat_async_service.py`

## TM-198

- Objetivo:
  - Preparar commit consolidado de cambios pendientes excluyendo artefactos/codigo de embeddings para revision posterior.
- Alcance:
  - `agents/shared/TASK_BOARD.md`
  - `.gitignore`
  - staging/commit del worktree actual (excepto embeddings).
- Agentes involucrados:
  - orchestrator.
- Estado:
  - en curso
- Dependencias:
  - TM-193
- Evidencia:
  - `git add -A`
  - `git reset -- app/services/embedding_service.py docs/decisions/ADR-0098-rag-gratuito-chunking-expansion-resiliencia-embeddings.md`
  - `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -o addopts=""`
  - `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_care_tasks_api.py -k "chat_message_async" -o addopts=""`
- Riesgos pendientes identificados:
  - excluir temporalmente cambios de embeddings puede dejar optimizaciones de retrieval diferidas a un commit posterior.
