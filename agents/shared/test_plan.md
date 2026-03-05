# Plan de Pruebas

## Smoke tests minimos

- Salud API:
  - `GET /health` devuelve `200`.
- Tareas API:
  - Crear, listar, actualizar y eliminar tarea.
- MCP:
  - Registrar servidor con `codex mcp add`.
  - Verificar con `codex mcp list`.
  - Ejecutar al menos una operacion de lectura y una de escritura.

## Evidencia

- Resultado TM-197:

  - Frontend migrado a stack visual moderno:
    - TailwindCSS + daisyUI (componentes),
    - lucide-react (iconografia).
  - UI renovada con layout dashboard, panel lateral de casos, chat bubbles modernas, badges/toasts y micro-animacion.
  - Validacion:
    - `npm --prefix frontend run build`

- Resultado TM-196:

  - Frontend de chat en modo anonimo sin pantalla de login.
  - Se elimina uso de token/bearer y carga directa de casos/conversacion.
  - Validacion:
    - `npm --prefix frontend run build`

- Resultado TM-195:

  - Regression Set de chat:
    - script de construccion desde historial persistido: `app/scripts/build_chat_regression_set.py`.
    - script de evaluacion contra backend: `app/scripts/evaluate_chat_regression.py`.
  - Metricas de regresion:
    - `token_f1_avg`, `domain_hit_rate`, `must_include_rate`, `forbidden_leak_rate`, `latency_p95_ms`.
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/scripts/build_chat_regression_set.py app/scripts/evaluate_chat_regression.py app/tests/test_build_chat_regression_set_script.py app/tests/test_evaluate_chat_regression_script.py`
    - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_build_chat_regression_set_script.py app/tests/test_evaluate_chat_regression_script.py -o addopts=""`
    - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m app.scripts.build_chat_regression_set --limit 40 --output tmp/chat_regression_set.jsonl`
    - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m app.scripts.evaluate_chat_regression --dataset tmp/chat_regression_set.jsonl --output tmp/chat_regression_eval_summary.json`

- Resultado TM-194:

  - Capa CIR determinista de ambiguedad integrada en chat clinico:
    - clasificacion heuristica (`_assess_query_ambiguity`) para decidir clarificacion proactiva.
    - banco de preguntas por dominio/intencion (`_pick_clarification_question`).
    - sugerencias NQP-lite (`_build_next_query_suggestions`) y topic-shift controlado en respuesta general.
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
    - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "ambiguity_gate_triggers_for_short_low_context_query or ambiguity_gate_skips_structured_query or pick_clarification_question_prefers_domain_bank or next_query_suggestions_are_generated_for_domain or clarifying_answer_renders_suggestions_block or general_answer_suggests_domains_and_next_step_for_case_discovery or semantic_parser_and_dst_recovers_entity_from_history" -o addopts=""`
    - `.\venv\Scripts\python.exe tmp/run_chat_benchmark.py; .\venv\Scripts\python.exe tmp/summarize_chat_benchmark.py; .\venv\Scripts\python.exe tmp/check_acceptance.py`

- Resultado TM-144:

  - DST ligero y parser semantico determinista:
    - `intent`: `dose_lookup`, `follow_up_plan`, `safety_check`, `management_plan`, `general`.
    - `entity`: extraccion por patron (`dosis de X`) + lexicon medico basico.
  - En follow-up de dosis, la `effective_query` incluye entidad foco para mejorar retrieval.
  - En lector extractivo: si hay intencion de dosis y no aparece evidencia numerica, añade nota de seguridad (abstencion parcial).
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/services/clinical_chat_service.py app/services/rag_orchestrator.py app/tests/test_clinical_chat_operational.py app/tests/test_rag_orchestrator_optimizations.py`
    - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "history_attention_rewrite_prioritizes_relevant_turns or semantic_parser_and_dst_recovers_entity_from_history" -o addopts=""`
    - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -k "extractive_answer_adds_dose_safety_note_when_no_numeric_dose_found" -o addopts=""`
    - `.\venv\Scripts\python.exe tmp/run_chat_benchmark.py; .\venv\Scripts\python.exe tmp/summarize_chat_benchmark.py; .\venv\Scripts\python.exe tmp/check_acceptance.py`

- Resultado TM-143:

  - Reescritura contextual con HAM ligero:
    - selecciona turnos de historial por `overlap + recencia exponencial + foco clinico`.
    - evita depender solo del ultimo turno.
  - Ranking hibrido en lector extractivo:
    - `extractive_relevance` + `generative_proxy` (tau=0.6, delta=0.4),
    - overlap con penalizacion logaritmica para queries largas.
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/services/clinical_chat_service.py app/services/rag_orchestrator.py app/tests/test_clinical_chat_operational.py app/tests/test_rag_orchestrator_optimizations.py`
    - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "follow_up_query_expansion or contextual_query_rewrite_handles_coreference or history_attention_rewrite_prioritizes_relevant_turns or clean_evidence_snippet_removes_heading_noise" -o addopts=""`
    - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -k "extractive_answer_filters_non_clinical_noise or extractive_answer_prioritizes_query_overlap_over_noise_chunks or extractive_answer_coarse_to_fine_prefers_actionable_sentences or query_overlap_log_scaling_rewards_relevant_sentence or generative_proxy_score_prefers_well_formed_sentence" -o addopts=""`
    - `.\venv\Scripts\python.exe tmp/run_chat_benchmark.py; .\venv\Scripts\python.exe tmp/summarize_chat_benchmark.py; .\venv\Scripts\python.exe tmp/check_acceptance.py`

- Resultado TM-142:

  - `RAGOrchestrator._build_extractive_answer` usa flujo coarse-to-fine:
    - Stage 1: relevancia a consulta,
    - Stage 2: evidencia accionable,
    - Stage 3: centralidad + seleccion MMR ligera.
  - Mejora de snippets para evitar frases no clinicas y reducir redundancia.
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/services/rag_orchestrator.py app/tests/test_rag_orchestrator_optimizations.py`
    - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -k "extractive_answer_filters_non_clinical_noise or extractive_answer_prioritizes_query_overlap_over_noise_chunks or extractive_answer_coarse_to_fine_prefers_actionable_sentences" -o addopts=""`
    - `.\venv\Scripts\python.exe tmp/run_chat_benchmark.py; .\venv\Scripts\python.exe tmp/summarize_chat_benchmark.py; .\venv\Scripts\python.exe tmp/check_acceptance.py`

- Resultado TM-141:

  - `process_query_with_rag(...)` recibe `effective_query` (consulta reescrita con contexto) en lugar de `safe_query`.
  - Esto asegura que la reescritura CQU impacte realmente en retrieval multi-turno.
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/services/clinical_chat_service.py`
    - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "follow_up_query_expansion or contextual_query_rewrite_handles_coreference or clean_evidence_snippet_removes_heading_noise" -o addopts=""`

- Resultado TM-140:

  - RAG extractivo ahora prioriza snippets con mayor solape semantico con la consulta y filtra ruido de cabeceras tecnicas.
  - Limpieza adicional de snippets en respuesta evidence-first para evitar fragmentos tipo "Motor Operativo..." y bloques no clinicos.
  - Benchmark agrega metricas proxy de validacion/safety:
    - `proxy_token_f1_avg`
    - `proxy_exact_match_rate`
    - `internal_leak_rate`
    - `abstention_rate`
  - Acceptance agrega control de fuga interna: `internal_leak_rate <= 0.0`.
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/services/rag_orchestrator.py app/services/clinical_chat_service.py tmp/summarize_chat_benchmark.py tmp/check_acceptance.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_clinical_chat_operational.py`
    - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -k "extractive_answer_filters_non_clinical_noise or extractive_answer_prioritizes_query_overlap_over_noise_chunks" -o addopts=""`
    - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "follow_up_query_expansion or contextual_query_rewrite_handles_coreference or clean_evidence_snippet_removes_heading_noise" -o addopts=""`

- Resultado TM-139:

  - Reescritura contextual de consulta en chat multi-turno para preguntas de seguimiento y correferencia (ej. `y su dosis?`).
  - El query efectivo pasa a formato descontextualizado: `Contexto clinico previo ... + Consulta de seguimiento ...`.
  - Validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
    - `$env:DEBUG='false'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "follow_up_query_expansion or contextual_query_rewrite_handles_coreference" -o addopts=""`

- Resultado TM-138:

  - Endpoints de chat (`/chat/messages`, `/chat/messages/async`, `/chat/memory`, `/chat/messages` listado y estado async) accesibles sin bearer.

  - Compatibilidad mantenida: si hay token valido, se asocia `authenticated_user`; si no, sesion anonima.

  - Validacion:

    - `.\venv\Scripts\python.exe -m py_compile app/api/deps.py app/api/care_tasks.py app/services/clinical_chat_async_service.py`

- Resultado TM-134:
  - Reordenado de dominios por top-domain matematico cuando la confianza es suficiente.
  - Nuevas trazas de incertidumbre (`math_margin_top2`, `math_entropy`, `math_uncertainty_level`, `math_abstention_recommended`).
  - Validacion:
    - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_math_inference_service.py app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "math_inference_service or domain_rerank_uses_math_top_domain_when_confident"`

- Resultado TM-133:
  - Capa matematica local integrada en chat (similitud coseno + distancia L2 + posterior Bayes).
  - Trazabilidad `math_*` por turno y bloque matematico en fallback clinico.
  - Validacion:
    - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_math_inference_service.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_chat_operational.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "math_inference_service"`

- Resultado TM-132:
  - Contratos operativos por dominio (fase 1: nefrologia y ginecologia/obstetricia) integrados en chat.
  - Guard de fallback estructurado cuando el contrato exige datos faltantes.
  - Validacion:
    - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_protocol_contracts_service.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_chat_operational.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "logic_engine or protocol_contract"`

- Resultado TM-131:
  - Logica formal extendida integrada en chat (firma estructural Godel + consistencia + abstencion).
  - Validacion:
    - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_logic_engine_service.py app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "logic_engine"`

- Resultado TM-130:
  - Motor logico clinico integrado en chat (reglas + contradicciones + estado epistemico).
  - Validacion:
    - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_logic_engine_service.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_chat_operational.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "logic_engine or psychology or interrogatory"`

- Resultado TM-129:
  - Ingesta nativa de PDF multipagina habilitada para pipeline documental RAG.
  - Validacion:
    - `.\venv\Scripts\python.exe -m ruff check app/services/document_ingestion_service.py app/scripts/ingest_clinical_docs.py app/tests/test_document_ingestion_service.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_document_ingestion_service.py`

- Resultado TM-128:
  - Chat clinico acepta `local_evidence` y la inyecta en fuentes internas del turno.
  - Trazabilidad nueva por turno: `local_evidence_items`, `local_evidence_modalities`.
  - Validacion:
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/clinical_chat.py app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "local_evidence or psychology or interrogatory"`

- Resultado TM-126:
  - Interrogatorio clinico activo Bayes+DEIG integrado de forma opcional en chat.
  - Short-circuit de aclaracion evita invocacion LLM/RAG cuando faltan datos criticos.
  - Request de chat ampliado con flags de control del interrogatorio.
  - Validacion:
    - `.\venv\Scripts\python.exe -m ruff check app/services/diagnostic_interrogatory_service.py app/services/clinical_chat_service.py app/schemas/clinical_chat.py app/tests/test_clinical_chat_operational.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "interrogatory or quality_gate or rag_validation_warns"`

- Resultado TM-127:
  - Capa psicologica de decision integrada (Fechner + Prospect framing) en chat clinico.
  - Nuevas trazas de riesgo perceptual y framing de comunicacion.
  - Validacion:
    - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_decision_psychology_service.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_chat_operational.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "psychology or interrogatory or quality_gate or rag_validation_warns"`

- Resultado TM-123:
  - Ciclo `draft->verify->rewrite` implementado para respuesta clinica LLM.
  - Gate de calidad ampliado para rechazar respuestas de rechazo generico y respuestas truncadas.
  - Ajuste runtime local en `.env` para reducir truncado (`timeout`, `max_output`, `max_input`, `num_ctx`).
  - Validacion:
    - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/tests/test_clinical_chat_operational.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "quality_gate or rewrite or routing"`

- Resultado TM-124:
  - La ruta RAG ahora propaga `llm_trace` y queda sometida a los mismos gates de calidad/grounding.
  - Cobertura de regresion para respuesta RAG mala:
    - `test_chat_e2e_quality_gate_applies_to_rag_answer_too`
  - Validacion:
    - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "rag_quality_gate_applies_to_rag_answer_too or quality_gate"`

- Resultado TM-125:
  - Se rechazan placeholders genericos en salida LLM (`[Informacion ...]`) y salidas con parentesis no balanceados.
  - Si `rag_validation_status=warning` en ruta RAG, se fuerza fallback estructurado.
  - Validacion:
    - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "rag_validation_warns or rag_quality_gate_applies_to_rag_answer_too or quality_gate"`

- Resultado TM-120:
  - Curacion de fuentes oficiales en `docs/86_fuentes_oficiales_sarampion_tosferina.md`.
  - Ingesta puntual validada:
    - `.\venv\Scripts\python.exe -m app.scripts.ingest_clinical_docs --paths docs/86_fuentes_oficiales_sarampion_tosferina.md`
  - Prueba funcional esperada:
    - consulta clinica pediatrica con `use_web_sources=true` debe reflejar el documento en `knowledge_sources`.

- Fecha: 2026-02-05
- Comando: `.\venv\Scripts\python.exe -m pytest -q`
- Resultado: `4 passed`
- Cobertura: configuracion local aplicada en `pytest.ini`.
- Comandos Alembic validados:
  - `alembic revision --autogenerate -m "init tasks table"`
  - `alembic upgrade head`
  - `alembic current`
- Resultado Alembic: `f1b3f75c533d (head)`.
- Comandos de regresion TM-004:
  - `pytest -q`
- Resultado TM-004:
  - Tests OK con configuracion local `pytest.ini`.
  - Sin warnings deprecados de `on_event` en FastAPI.
- Resultado TM-005:
  - Settings migrados a `SettingsConfigDict`.
  - Sin warning de `class Config` deprecado en Pydantic settings.
- Resultado TM-006:
  - `ruff check app mcp_server` OK.
  - `black --check app mcp_server` OK.
  - `mypy app mcp_server` OK.
  - `pytest -q` OK (`4 passed`).
- Resultado TM-007:
  - Flujo CI creado en `.github/workflows/ci.yml`.
  - Secuencia de checks alineada con validacion local.
- Resultado TM-009:
  - Build de imagen endurecida completada.
  - Compose config valida tras cambios.
- Resultado TM-010:
  - Separacion de variables por entorno aplicada.
  - Compose usando `env_file` validado con `docker compose config`.
- Resultado TM-011:
  - Validaciones de seguridad de settings aplicadas.
  - Tests dedicados de seguridad de configuracion agregados.
- Resultado TM-012:
  - Utilidades JWT/hash implementadas en capa core.
  - Tests de seguridad core agregados y en verde.
- Resultado TM-013:
  - Endpoints `/auth/login` y `/auth/me` implementados.
  - Tests de API auth agregados y en verde.
- Resultado TM-014:
  - Auth ahora valida usuarios persistentes en tabla `users`.
  - Migraciones y tests actualizados para modelo de usuario.
- Resultado TM-015:
  - Registro de usuario habilitado con validacion de password.
  - Tests cubren exito, username duplicado y password debil.
- Resultado TM-016:
  - Bootstrap de primer admin implementado por CLI.
  - Tests cubren caso de exito y bloqueo si ya existen usuarios.
- Resultado TM-017:
  - RBAC admin v1 implementado para endpoint de usuarios.
  - Tests cubren acceso sin token (401), sin rol admin (403) y con admin (200).
  - Comando validado: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_auth_api.py`.
- Resultado TM-018:
  - Refresh token con rotacion y logout implementados.
  - Tests cubren rotacion, bloqueo de reuso y revocacion de sesion.
  - Comando validado: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_auth_api.py`.
- Resultado TM-019:
  - Tests unitarios de `TaskService` agregados en capa de servicio.
  - Cobertura funcional: create/get/list/update/delete/count.
  - Comando validado: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_task_service_unit.py`.
- Resultado TM-020:
  - Script de smoke MCP agregado para ejecucion manual reproducible.
  - Smoke test ampliado para incluir `openapi_schema`.
  - Comando validado: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_mcp_smoke.py`.
- Resultado TM-021:
  - Flujo de gestion de errores documentado con catalogo por codigo de estado.
  - Incluye runbook de diagnostico y ejemplos de respuesta.
  - Referencia: `docs/16_error_handling_workflow.md`.
- Resultado TM-022:
  - Middleware de request logging implementado con `request_id` y latencia.
  - Header `X-Request-ID` validado en respuestas.
  - Comando validado: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_request_logging.py`.
- Resultado TM-023:
  - Endpoint `/metrics` de Prometheus habilitado en FastAPI.
  - Tests validan exposicion del endpoint y presencia de metricas HTTP.
  - Comando validado: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py`.
- Resultado TM-024:
  - Servicio Prometheus agregado a Docker Compose con scraping a `api:8000/metrics`.
  - Config declarada en `ops/prometheus/prometheus.yml`.
  - Validacion de estructura con `docker compose config`.
- Resultado TM-025:
  - Servicio Grafana agregado a Docker Compose con provisioning automatico.
  - Datasource Prometheus y dashboard base versionados en `ops/grafana/`.
  - Validacion de estructura con `docker compose config`.
- Resultado TM-026:
  - Login protegido con limite temporal por `username + IP`.
  - Tests cubren bloqueo por intentos fallidos y reseteo tras login valido.
  - Comando validado: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_auth_api.py`.
- Resultado TM-027:
  - Endpoint AI de triage de tareas agregado con salida explicable.
  - Tests cubren casos bug/docs/default.
  - Comando validado: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_ai_api.py`.
- Resultado TM-028:
  - Skills de proyecto creados y validados con `quick_validate.py`.
  - Cobertura de orquestacion, entrega API y observabilidad.
  - Referencia: `docs/23_project_skills_playbook.md`.
- Resultado TM-029:
  - Fundacion de ejecucion agente con traza persistente por paso implementada.
  - Endpoint `POST /api/v1/agents/run` validado con casos de exito y fallback.
  - Comando validado: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_agents_api.py`.
  - Regresion completa validada: `.\venv\Scripts\python.exe -m pytest -q`.
- Resultado TM-030:
  - Modo AI configurable (`rules`/`hybrid`) implementado con provider opcional.
  - Respuesta de triage enriquecida con `source` para trazabilidad de decision.
  - Comando validado: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_ai_api.py app/tests/test_agents_api.py`.
  - Lint validado: `.\venv\Scripts\python.exe -m ruff check app alembic`.
- Resultado TM-031:
  - Historial de corridas agente expuesto con listado y detalle por `run_id`.
  - Cobertura de tests para list/detail/404 en `app/tests/test_agents_api.py`.
  - Comando validado: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_agents_api.py`.
- Resultado TM-032:
  - Filtros operativos en historial (`status`, `workflow_name`, `created_from`, `created_to`, `limit`).
  - Tests de filtros por estado/workflow y ventana temporal agregados.
  - Comando validado: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_agents_api.py`.
- Resultado TM-033:
  - Resumen operativo agregado en `GET /agents/ops/summary`.
  - Cobertura de test para agregados (`total_runs`, `failed_runs`, `fallback_rate_percent`).
  - Comando validado: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_agents_api.py`.
- Resultado TM-034:
  - Metricas Prometheus de agentes agregadas al endpoint `/metrics`.
  - Dashboard Grafana actualizado con paneles de salud de agentes.
  - Comando validado: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py`.
- Resultado TM-035:
  - Paneles `stat/gauge` de agentes ajustados a consulta instantanea (`instant=true`).
  - Dashboard incrementado a version `4` para forzar refresco de provisioning.
  - Referencia: `ops/grafana/dashboards/task_manager_overview.json`.
- Resultado TM-036:
  - Reglas de alerta de agentes agregadas en Prometheus (`failed_runs`, `fallback_rate`).
  - Compose monta `ops/prometheus/alerts.yml` para carga automatica.
  - Validacion esperada en runtime: `http://127.0.0.1:9090/rules` y `http://127.0.0.1:9090/alerts`.
- Resultado TM-037:
  - Alertmanager agregado en Compose y enlazado desde Prometheus.
  - Config baseline en `ops/alertmanager/alertmanager.yml`.
  - Validacion esperada en runtime: `http://127.0.0.1:9093/#/alerts`.

- Plan TM-038:
  - Validar consistencia documental del pivot (`docs/05_roadmap.md`, `docs/32_clinical_ops_pivot_phase1.md`).
  - Confirmar que no hay roturas de contrato en endpoints existentes.
  - Ejecutar regresion rapida: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_agents_api.py app/tests/test_ai_api.py`.
- Resultado TM-038:
  - Migracion aplicada: `.\venv\Scripts\alembic.exe upgrade head`.
  - CRUD `care-tasks` validado en `app/tests/test_care_tasks_api.py`.
  - Regresion de agentes/ai en verde.
- Resultado TM-039 (fase inicial):
  - Mensajes visibles de `care-tasks` traducidos a espanol.
  - Guia de estrategia creada en `docs/34_castellanizacion_repositorio.md`.
  - Regresion validada: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_agents_api.py app/tests/test_ai_api.py`.
- Resultado TM-039 (cierre de fase):
  - Traduccion ampliada en docs, contratos compartidos, skills y mensajes visibles de API/MCP.
  - Ajuste de pruebas a nuevos mensajes en espanol.
  - Regresion validada: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_auth_api.py app/tests/test_auth_bootstrap.py app/tests/test_security_core.py app/tests/test_tasks_api.py app/tests/test_care_tasks_api.py app/tests/test_ai_api.py app/tests/test_agents_api.py app/tests/test_mcp_smoke.py`.
  - Resultado: `42 passed`.
  - Regresion completa validada: `.\venv\Scripts\python.exe -m pytest -q app/tests`.
  - Resultado final: `57 passed`.

- Plan TM-040:
  - Crear `care-task` y ejecutar `POST /api/v1/care-tasks/{id}/triage`.
  - Validar que la respuesta incluya `agent_run_id`, `workflow_name` y `triage`.
  - Validar que `agent_runs` y `agent_steps` persistan la traza con `workflow_name=care_task_triage_v1`.
  - Ejecutar regresion enfocada: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_agents_api.py`.
- Resultado TM-040:
  - Endpoint `POST /api/v1/care-tasks/{id}/triage` validado con caso de exito y 404.
  - Persistencia validada en `agent_runs` y `agent_steps` (`workflow_name=care_task_triage_v1`).
  - Regresion enfocada: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_agents_api.py`.
  - Regresion completa: `.\venv\Scripts\python.exe -m pytest -q app/tests`.
  - Resultado final: `59 passed`.

- Plan TM-041:
  - Ejecutar `POST /care-tasks/{id}/triage/approve` sobre una corrida valida.
  - Validar errores de negocio: run inexistente y run de otro `care_task`.
  - Ejecutar regresion enfocada y completa.
- Resultado TM-041:
  - Endpoint de aprobacion humana implementado y validado.
  - Tabla `care_task_triage_reviews` incluida para auditoria de decision.
  - Regresion enfocada: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_agents_api.py`.
  - Regresion completa: `.\venv\Scripts\python.exe -m pytest -q app/tests`.
  - Resultado final: `62 passed`.

- Plan TM-042:
  - Exponer API de contexto clinico-operativo (`/clinical-context/*`).
  - Validar areas, circuitos, roles, procedimientos y estandares.
  - Verificar `404` en consulta de procedimiento inexistente.
- Resultado TM-042:
  - Endpoints `clinical-context` implementados y enrutados.
  - Pruebas dedicadas en `app/tests/test_clinical_context_api.py`.
  - Regresion foco: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_context_api.py`.
  - Regresion completa: `.\venv\Scripts\python.exe -m pytest -q app/tests`.
  - Resultado final: `67 passed`.

- Plan TM-043:
  - Publicar recurso `TriageLevel` para estandar Manchester.
  - Validar integridad de niveles 1..5, colores y SLA objetivo.
  - Ejecutar regresion de contexto y suite completa.
- Resultado TM-043:
  - Endpoint `GET /clinical-context/triage-levels/manchester` implementado.
  - Prueba dedicada en `app/tests/test_clinical_context_api.py`.
  - Regresion foco: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_context_api.py`.
  - Regresion completa: `.\venv\Scripts\python.exe -m pytest -q app/tests`.
  - Resultado final: `68 passed`.

- Plan TM-044:
  - Crear auditoria persistida IA vs humano para clasificar over/under-triage.
  - Exponer endpoints de registro, historial y resumen.
  - Exponer metricas Prometheus `triage_audit_*`.
- Resultado TM-044:
  - Endpoints de auditoria implementados en `care-tasks`.
  - Metricas de auditoria visibles en `/metrics`.
  - Regresion foco: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`.
  - Regresion completa: `.\venv\Scripts\python.exe -m pytest -q app/tests`.
  - Resultado final: `71 passed`.

- Plan TM-045:
  - Implementar motor respiratorio operativo en servicio dedicado.
  - Exponer `POST /care-tasks/{id}/respiratory-protocol/recommendation`.
  - Persistir traza en `agent_runs/agent_steps` con `workflow_name=respiratory_protocol_v1`.
  - Exponer metricas `respiratory_protocol_runs_*` en `/metrics`.
- Resultado TM-045:
  - Endpoint y servicio respiratorio implementados.
  - Workflow respiratorio trazable persistido en `agent_runs`.
  - Metricas respiratorias visibles en `/metrics`.
  - Regresion foco: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`.
  - Regresion completa: `.\venv\Scripts\python.exe -m pytest -q app/tests`.

- Plan TM-046:
  - Implementar motor de humanizacion pediatrica en servicio dedicado.
  - Exponer `POST /care-tasks/{id}/humanization/recommendation`.
  - Persistir traza en `agent_runs/agent_steps` con `workflow_name=pediatric_neuro_onco_support_v1`.
  - Exponer metricas `pediatric_humanization_runs_*` en `/metrics`.
- Resultado TM-046:
  - Endpoint y servicio de humanizacion pediatrica implementados.
  - Workflow trazable persistido en `agent_runs`.
  - Metricas de humanizacion visibles en `/metrics`.
  - Regresion foco: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`.
  - Regresion completa: `.\venv\Scripts\python.exe -m pytest -q app/tests`.

- Plan TM-047:
  - Implementar motor de screening operativo avanzado con reglas interpretables.
  - Exponer `POST /care-tasks/{id}/screening/recommendation`.
  - Persistir traza en `agent_runs/agent_steps` con `workflow_name=advanced_screening_support_v1`.
  - Exponer metricas de ejecucion y fatiga de alertas en `/metrics`.
- Resultado TM-047:
  - Endpoint y servicio de screening avanzado implementados.
  - Workflow trazable persistido en `agent_runs`.
  - Metricas de screening visibles en `/metrics`.
- Plan TM-050:
  - Ejecutar `POST /care-tasks/{id}/medicolegal/recommendation` con escenario normal y escenario critico.
  - Verificar persistencia de traza en `agent_runs/agent_steps` (`workflow_name=medicolegal_ops_support_v1`).
  - Verificar metricas Prometheus `medicolegal_ops_*` en `/metrics`.
  - Ejecutar regresion enfocada y suite completa.
- Resultado TM-050:
  - Endpoint medico-legal implementado y validado con casos de exito y 404.
  - Workflow trazable persistido en `agent_runs` y `agent_steps`.
  - Metricas medico-legales visibles en `/metrics`.
  - Regresion foco: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`.
  - Regresion completa: `.\venv\Scripts\python.exe -m pytest -q app/tests`.
- Plan TM-051:
  - Crear auditoria medico-legal IA vs humano (`POST/GET/summary`).
  - Persistir tabla dedicada con clasificacion `match/under_legal_risk/over_legal_risk`.
  - Exponer metricas `medicolegal_audit_*` y `medicolegal_rule_*_match_rate_percent`.
  - Ejecutar regresion enfocada y suite completa.
- Resultado TM-051:
  - Endpoints de auditoria medico-legal implementados y validados.
  - Nueva tabla `care_task_medicolegal_audit_logs` + migracion Alembic.
  - Metricas de calidad medico-legal visibles en `/metrics`.
  - Regresion foco: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`.
  - Regresion completa: `.\venv\Scripts\python.exe -m pytest -q app/tests`.
- Plan TM-052:
  - Implementar motor operativo de sepsis con qSOFA, bundle y escalado.
  - Exponer endpoint `POST /care-tasks/{id}/sepsis/recommendation`.
  - Persistir workflow `sepsis_protocol_support_v1` en `agent_runs/agent_steps`.
  - Exponer metricas `sepsis_protocol_*` en `/metrics`.
- Resultado TM-052:
  - Endpoint y servicio de sepsis implementados.
  - Workflow trazable persistido en `agent_runs`.
  - Metricas de sepsis visibles en `/metrics`.
  - Regresion foco: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`.
  - Regresion completa: `.\venv\Scripts\python.exe -m pytest -q app/tests`.
- Plan TM-053:
  - Implementar `EmergencyEpisode` con etapas y transiciones validadas.
  - Exponer endpoints de creacion/listado/detalle/transicion/KPIs.
  - Agregar pruebas de flujo completo e invalidaciones.
- Resultado TM-053:
  - Recurso `EmergencyEpisode` implementado con migracion Alembic.
  - Endpoints `/emergency-episodes/*` en API.
  - Pruebas de flujo extremo-a-extremo agregadas.
  - Regresion completa: `.\venv\Scripts\python.exe -m pytest -q app/tests`.
  - Regresion foco: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`.
  - Regresion completa: `.\venv\Scripts\python.exe -m pytest -q app/tests`.

- Plan TM-054:
  - Implementar endpoint `POST /care-tasks/{id}/scasest/recommendation`.
  - Persistir workflow `scasest_protocol_support_v1` en `agent_runs/agent_steps`.
  - Exponer metricas `scasest_protocol_*` en `/metrics`.
  - Ejecutar regresion enfocada de API y metricas.
- Resultado TM-054:
  - Endpoint y servicio SCASEST implementados.
  - Workflow trazable persistido en `agent_runs`.
  - Metricas de SCASEST visibles en `/metrics`.
  - Regresion foco: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`.
  - Resultado: `46 passed`.

- Plan TM-055:
  - Implementar auditoria SCASEST (registro/listado/resumen).
  - Persistir tabla `care_task_scasest_audit_logs` y clasificacion `match/under/over`.
  - Exponer metricas de calidad SCASEST en `/metrics`.
  - Ejecutar regresion enfocada de API y metricas.
- Resultado TM-055:
  - Endpoints de auditoria SCASEST implementados y validados.
  - Nueva tabla `care_task_scasest_audit_logs` + migracion Alembic.
  - Metricas de calidad SCASEST visibles en `/metrics`.
  - Regresion foco: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`.

- Plan TM-056:
  - Verificar que el dashboard JSON mantiene formato valido tras agregar paneles SCASEST.
  - Verificar que reglas Prometheus cargan sin errores de sintaxis.
  - Confirmar reflejo documental de runbook y alertas.
- Resultado TM-056:
  - Config dashboard validada con parseo JSON.
  - Reglas Prometheus actualizadas en `ops/prometheus/alerts.yml`.
  - Runbook operativo creado en `docs/51_runbook_alertas_scasest.md`.

- Plan TM-057:
  - Verificar que el script de simulacion SCASEST compila/arranca.
  - Validar documentacion de uso del drill.
- Resultado TM-057:
  - Script `app/scripts/simulate_scasest_alerts.py` agregado.
  - Guia `docs/52_scasest_alert_drill.md` agregada.
  - Validacion tecnica minima: `.\venv\Scripts\python.exe -m py_compile app/scripts/simulate_scasest_alerts.py`.

- Plan TM-058:
  - Validar endpoint `GET /api/v1/care-tasks/quality/scorecard` sin datos (estado inicial en cero).
  - Validar endpoint con datos de auditoria existentes (sumatorios y tasas agregadas coherentes).
  - Verificar exposicion de metricas globales de calidad IA en `/metrics`.
  - Ejecutar regresion enfocada:
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

- Resultado TM-058:
  - Endpoint agregado: `GET /api/v1/care-tasks/quality/scorecard`.
  - Metricas agregadas: `care_task_quality_audit_*`.
  - Pruebas nuevas para scorecard y metricas globales en:
    - `app/tests/test_care_tasks_api.py`
    - `app/tests/test_metrics_endpoint.py`
  - Regresion enfocada ejecutada:
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
  - Resultado: `52 passed`.

- Plan TM-059:
  - Validar sintaxis de `ops/prometheus/alerts.yml`.
  - Validar parseo JSON de `ops/grafana/dashboards/task_manager_overview.json`.
  - Validar exposicion de metricas `care_task_quality_audit_*` en `/metrics`.

- Resultado TM-059:
  - Alertas globales agregadas en `ops/prometheus/alerts.yml`.
  - Paneles globales agregados en `ops/grafana/dashboards/task_manager_overview.json`.
  - Runbook global agregado: `docs/54_runbook_alertas_calidad_global.md`.

- Plan TM-060:
  - Validar sintaxis del script de drill global.
  - Confirmar que imprime scorecard global al finalizar.
  - Documentar comandos de uso para `under`, `over`, `match-low`.

- Resultado TM-060:
  - Script agregado: `app/scripts/simulate_global_quality_alerts.py`.
  - Validacion tecnica minima:
    - `.\venv\Scripts\python.exe -m py_compile app/scripts/simulate_global_quality_alerts.py`
  - Guia agregada: `docs/55_drill_alertas_calidad_global.md`.

- Plan TM-061:
  - Ejecutar suite dedicada de evaluacion continua de calidad IA clinica.
  - Verificar escenario controlado de umbrales operativos (under <= 10, over <= 20, match >= 80).
  - Verificar escenario degradado sintetico para confirmar clasificacion `degradado`.
- Resultado TM-061:
  - Suite agregada: `app/tests/test_quality_regression_gate.py`.
  - Runner agregado: `app/scripts/run_quality_gate.py`.
  - Gate agregado en CI: `.github/workflows/ci.yml`.
  - Comando de validacion:
    - `.\venv\Scripts\python.exe app\scripts\run_quality_gate.py`

- Plan TM-062:
  - Validar recomendacion cardiovascular con traza en `agent_runs`.
  - Validar auditoria cardiovascular (`create/list/summary`).
  - Validar metricas `cardio_risk_support_*` y `cardio_risk_audit_*` en `/metrics`.
  - Validar que scorecard global incorpore dominio `cardio_risk`.
- Resultado TM-062:
  - Endpoints cardiovasculares implementados en `app/api/care_tasks.py`.
  - Modelo y migracion agregados para `care_task_cardio_risk_audit_logs`.
  - Metricas Prometheus cardiovasculares agregadas.
  - Regresion foco:
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py app/tests/test_quality_regression_gate.py`

- Plan TM-063:
  - Validar recomendacion de reanimacion con traza en `agent_runs`.
  - Validar auditoria de reanimacion (`create/list/summary`).
  - Validar metricas `resuscitation_protocol_*` y `resuscitation_audit_*` en `/metrics`.
  - Validar que scorecard global incorpore dominio `resuscitation`.
  - Validar migracion y sintaxis de reglas Prometheus.
- Resultado TM-063:
  - Endpoints de reanimacion implementados en `app/api/care_tasks.py`.
  - Modelo y migracion agregados para `care_task_resuscitation_audit_logs`.
  - Metricas Prometheus de reanimacion agregadas.
  - Regresion foco:
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py app/tests/test_quality_regression_gate.py`
    - Resultado: `66 passed`.
  - Migraciones:
    - `.\venv\Scripts\python.exe -m alembic upgrade head`
    - `.\venv\Scripts\python.exe -m alembic current`
    - Resultado: `c5e8a2f1d440 (head)`.
  - Alertas:
    - `docker compose exec prometheus promtool check rules /etc/prometheus/alerts.yml`
    - Resultado: `SUCCESS: 11 rules found`.

- Plan TM-064:
  - Validar script drill de reanimacion en modo `under/over/mixed`.
  - Validar parseo del dashboard Grafana tras agregar paneles de reanimacion.
  - Validar que reglas Prometheus sigan cargando correctamente.
- Resultado TM-064:
  - Script agregado: `app/scripts/simulate_resuscitation_alerts.py`.
  - Validacion sintaxis script:
    - `.\venv\Scripts\python.exe -m py_compile app/scripts/simulate_resuscitation_alerts.py`
  - Dashboard actualizado: `ops/grafana/dashboards/task_manager_overview.json`.
  - Validacion parseo JSON dashboard:
    - `.\venv\Scripts\python.exe -c "import json; json.load(open('ops/grafana/dashboards/task_manager_overview.json', encoding='utf-8'))"`
  - Validacion reglas Prometheus:
    - `docker compose exec prometheus promtool check rules /etc/prometheus/alerts.yml`
    - Resultado: pendiente en esta sesion (Docker Desktop apagado); revalidar con servicios levantados.

- Plan TM-065:
  - Validar extension obstetrica de `resuscitation/recommendation` con ventana critica 4-5 min.
  - Validar alertas por acceso vascular no asegurado y toxicidad por magnesio.
  - Validar que checklist de causas reversibles incluya bloque obstetrico ampliado.
  - Ejecutar regresion focalizada en API y metricas.
- Resultado TM-065:
  - Campos obstetricos opcionales agregados al schema de entrada.
  - Reglas obstetricas integradas en servicio de reanimacion sin cambios de DB.
  - Prueba agregada:
    - `test_run_resuscitation_support_obstetric_critical_window_actions`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k obstetric`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

- Plan TM-066:
  - Validar decision sincronizada/no sincronizada en taquiarritmias criticas.
  - Validar energia inicial por ritmo y checklist de seguridad pre-descarga.
  - Validar bloque de sedoanalgesia peri-procedimiento para cardioversion.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-066:
  - Bloques agregados a recomendacion de reanimacion:
    - `electrical_therapy_plan`
    - `sedoanalgesia_plan`
    - `pre_shock_safety_checklist`
  - Prueba agregada:
    - `test_run_resuscitation_support_recommends_synchronized_cardioversion`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/resuscitation_protocol.py app/services/resuscitation_protocol_service.py app/tests/test_care_tasks_api.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k cardioversion`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

- Plan TM-067:
  - Validar conflicto bioetico pediatrico en soporte medico-legal.
  - Verificar alerta de interes superior del menor y riesgo legal alto.
  - Verificar acciones/documentacion reforzada en riesgo vital.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-067:
  - Campos opcionales agregados a `MedicolegalOpsRequest` para conflicto de representacion.
  - Reglas de conflicto pediatrico integradas en `MedicolegalOpsService`.
  - Prueba agregada:
    - `test_run_medicolegal_ops_pediatric_life_saving_conflict_prioritizes_protection`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/medicolegal_ops.py app/services/medicolegal_ops_service.py app/tests/test_care_tasks_api.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k pediatric_life_saving_conflict`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

- Plan TM-068:
  - Estructurar fundamento etico-legal en salida de recomendacion medico-legal.
  - Verificar bandera de override vital y resumen de urgencia.
  - Verificar presencia de base etico-legal en conflicto pediatrico critico.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-068:
  - Campos nuevos en `MedicolegalOpsRecommendation`:
    - `life_preserving_override_recommended`
    - `ethical_legal_basis`
    - `urgency_summary`
  - Ajustes de pruebas:
    - `test_run_medicolegal_ops_returns_recommendation_and_trace`
    - `test_run_medicolegal_ops_pediatric_life_saving_conflict_prioritizes_protection`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/medicolegal_ops.py app/services/medicolegal_ops_service.py app/tests/test_care_tasks_api.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/medicolegal_ops.py app/services/medicolegal_ops_service.py app/tests/test_care_tasks_api.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k pediatric_life_saving_conflict`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

- Plan TM-069:
  - Implementar endpoint diferencial de pitiriasis sobre `care-tasks`.
  - Persistir traza de workflow dermatologico en `agent_runs/agent_steps`.
  - Exponer metricas operativas de ejecucion y red flags en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-069:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/pityriasis-differential/recommendation`
  - Workflow agregado:
    - `workflow_name=pityriasis_differential_support_v1`
  - Metricas agregadas:
    - `pityriasis_differential_runs_total`
    - `pityriasis_differential_runs_completed_total`
    - `pityriasis_differential_red_flags_total`
  - Pruebas agregadas:
    - `test_run_pityriasis_differential_returns_recommendation_and_trace`
    - `test_run_pityriasis_differential_detects_red_flags`
    - `test_run_pityriasis_differential_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_pityriasis_differential_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/pityriasis_protocol.py app/services/pityriasis_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/pityriasis_protocol.py app/services/pityriasis_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k pityriasis_differential`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k pityriasis_differential`

- Plan TM-070:
  - Implementar endpoint diferencial acne/rosacea sobre `care-tasks`.
  - Persistir traza de workflow dermatologico en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y red flags en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-070:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/acne-rosacea/recommendation`
  - Workflow agregado:
    - `workflow_name=acne_rosacea_differential_support_v1`
  - Metricas agregadas:
    - `acne_rosacea_differential_runs_total`
    - `acne_rosacea_differential_runs_completed_total`
    - `acne_rosacea_differential_red_flags_total`
  - Pruebas agregadas:
    - `test_run_acne_rosacea_differential_returns_recommendation_and_trace`
    - `test_run_acne_rosacea_differential_detects_fulminans_red_flag`
    - `test_run_acne_rosacea_differential_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_acne_rosacea_differential_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/acne_rosacea_protocol.py app/services/acne_rosacea_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/acne_rosacea_protocol.py app/services/acne_rosacea_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k acne_rosacea_differential`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k acne_rosacea_differential`

- Plan TM-070-QA-VERIF:
  - Revalidar artefactos declarados en TM-070.
  - Ejecutar regresion focalizada de acne/rosacea (API + metricas).
  - Ejecutar regresion ampliada de `care_tasks` + `metrics`.
- Resultado TM-070-QA-VERIF:
  - Artefactos declarados de TM-070 presentes y localizados en repo.
  - Comandos ejecutados:
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k acne_rosacea_differential`
      - Resultado: `3 passed, 51 deselected`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k acne_rosacea_differential`
      - Resultado: `1 passed, 20 deselected`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
      - Resultado: `75 passed`

- Plan TM-048:
  - Implementar auditoria de screening (IA vs humano) con tabla dedicada.
  - Exponer endpoints de registro/listado/resumen de auditoria screening.
  - Publicar metricas de calidad global y por regla en `/metrics`.
- Resultado TM-048:
  - Tabla `care_task_screening_audit_logs` y migracion `d2a7c9b4e110`.
  - Endpoints `POST/GET /care-tasks/{id}/screening/audit` y `GET /summary`.
  - Metricas `screening_audit_*` y `screening_rule_*_match_rate_percent`.
  - Regresion foco: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`.
  - Regresion completa: `.\venv\Scripts\python.exe -m pytest -q app/tests`.

- Plan TM-049:
  - Implementar soporte operativo de interpretacion RX torax.
  - Exponer `POST /care-tasks/{id}/chest-xray/interpretation-support`.
  - Persistir traza en `agent_runs/agent_steps` con `workflow_name=chest_xray_support_v1`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
- Resultado TM-049:
  - Endpoint y servicio de soporte RX torax implementados.
  - Workflow trazable persistido en `agent_runs`.
  - Metricas RX torax visibles en `/metrics`.
  - Regresion foco: `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`.
  - Regresion completa: `.\venv\Scripts\python.exe -m pytest -q app/tests`.

- Plan TM-071:
  - Implementar endpoint de soporte operativo de trauma sobre `care-tasks`.
  - Persistir traza de workflow de trauma en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-071:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/trauma/recommendation`
  - Workflow agregado:
    - `workflow_name=trauma_support_v1`
  - Metricas agregadas:
    - `trauma_support_runs_total`
    - `trauma_support_runs_completed_total`
    - `trauma_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_trauma_support_returns_recommendation_and_trace`
    - `test_run_trauma_support_detects_crush_risk_and_serial_ecg_requirement`
    - `test_run_trauma_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_trauma_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m ruff check app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/schemas/__init__.py app/services/__init__.py app/schemas/trauma_support_protocol.py app/services/trauma_support_protocol_service.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `$env:COVERAGE_FILE='.coverage.trauma_tmp'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py -k trauma_support`

- Plan TM-072:
  - Extender soporte de trauma con matriz de condiciones clinicas estructurada.
  - Cubrir en `condition_matrix` las patologias de politrauma, choque hemorragico, neumotorax a tension, taponamiento, TCE, sindrome compartimental y quemaduras.
  - Validar pruebas de trauma (API + metricas).
- Resultado TM-072:
  - Contrato de salida ampliado en `TraumaSupportRecommendation` con `condition_matrix[]`.
  - Se agregan campos de entrada para activar reglas toracicas, neurologicas, compartimentales y quemaduras.
  - Prueba nueva:
    - `test_run_trauma_support_detects_tension_pneumothorax_and_tamponade`
  - Pruebas actualizadas:
    - `test_run_trauma_support_returns_recommendation_and_trace` (valida `source`/matriz)
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/trauma_support_protocol.py app/services/trauma_support_protocol_service.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py`
    - `$env:COVERAGE_FILE='.coverage.trauma_matrix_tmp'; .\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py -k trauma_support`
    - Resultado: `5 passed`.

- Plan TM-073:
  - Implementar endpoint de soporte operativo critico transversal sobre `care-tasks`.
  - Persistir traza de workflow critico transversal en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-073:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/critical-ops/recommendation`
  - Workflow agregado:
    - `workflow_name=critical_ops_support_v1`
  - Metricas agregadas:
    - `critical_ops_support_runs_total`
    - `critical_ops_support_runs_completed_total`
    - `critical_ops_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_critical_ops_support_returns_recommendation_and_trace`
    - `test_run_critical_ops_support_detects_sla_breaches_and_red_flags`
    - `test_run_critical_ops_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_critical_ops_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/critical_ops_protocol.py app/services/critical_ops_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/critical_ops_protocol.py app/services/critical_ops_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k critical_ops`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k critical_ops`

- Plan TM-074:
  - Implementar endpoint de soporte operativo neurologico sobre `care-tasks`.
  - Persistir traza del workflow neurologico en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas de riesgo vascular en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-074:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/neurology/recommendation`
  - Workflow agregado:
    - `workflow_name=neurology_support_v1`
  - Metricas agregadas:
    - `neurology_support_runs_total`
    - `neurology_support_runs_completed_total`
    - `neurology_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_neurology_support_returns_recommendation_and_trace`
    - `test_run_neurology_support_detects_contraindications_and_nmda_pattern`
    - `test_run_neurology_support_prioritizes_wakeup_pathway`
    - `test_run_neurology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_neurology_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/neurology_support_protocol.py app/services/neurology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/neurology_support_protocol.py app/services/neurology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k neurology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k neurology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

- Plan TM-075:
  - Implementar endpoint de soporte operativo gastro-hepato sobre `care-tasks`.
  - Persistir traza del workflow gastro-hepato en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-075:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/gastro-hepato/recommendation`
  - Workflow agregado:
    - `workflow_name=gastro_hepato_support_v1`
  - Metricas agregadas:
    - `gastro_hepato_support_runs_total`
    - `gastro_hepato_support_runs_completed_total`
    - `gastro_hepato_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_gastro_hepato_support_returns_recommendation_and_trace`
    - `test_run_gastro_hepato_support_flags_surgery_and_pharmacology`
    - `test_run_gastro_hepato_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_gastro_hepato_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/gastro_hepato_support_protocol.py app/services/gastro_hepato_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/gastro_hepato_support_protocol.py app/services/gastro_hepato_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k gastro_hepato_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k gastro_hepato_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

- Plan TM-076:
  - Implementar endpoint de soporte operativo reuma-inmuno sobre `care-tasks`.
  - Persistir traza del workflow reuma-inmuno en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-076:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/rheum-immuno/recommendation`
  - Workflow agregado:
    - `workflow_name=rheum_immuno_support_v1`
  - Metricas agregadas:
    - `rheum_immuno_support_runs_total`
    - `rheum_immuno_support_runs_completed_total`
    - `rheum_immuno_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_rheum_immuno_support_returns_recommendation_and_trace`
    - `test_run_rheum_immuno_support_flags_safety_maternal_and_data_domains`
    - `test_run_rheum_immuno_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_rheum_immuno_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/rheum_immuno_support_protocol.py app/services/rheum_immuno_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/rheum_immuno_support_protocol.py app/services/rheum_immuno_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k rheum_immuno_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k rheum_immuno_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

- Plan TM-077:
  - Implementar endpoint de soporte operativo de psiquiatria sobre `care-tasks`.
  - Persistir traza del workflow de psiquiatria en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-077:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/psychiatry/recommendation`
  - Workflow agregado:
    - `workflow_name=psychiatry_support_v1`
  - Metricas agregadas:
    - `psychiatry_support_runs_total`
    - `psychiatry_support_runs_completed_total`
    - `psychiatry_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_psychiatry_support_returns_recommendation_and_trace`
    - `test_run_psychiatry_support_enforces_elderly_insomnia_safety_flow`
    - `test_run_psychiatry_support_flags_pregnancy_and_metabolic_risk`
    - `test_run_psychiatry_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_psychiatry_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/psychiatry_support_protocol.py app/services/psychiatry_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/psychiatry_support_protocol.py app/services/psychiatry_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k psychiatry_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k psychiatry_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

- Plan TM-078:
  - Implementar endpoint de soporte operativo de hematologia sobre `care-tasks`.
  - Persistir traza del workflow de hematologia en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-078:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/hematology/recommendation`
  - Workflow agregado:
    - `workflow_name=hematology_support_v1`
  - Metricas agregadas:
    - `hematology_support_runs_total`
    - `hematology_support_runs_completed_total`
    - `hematology_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_hematology_support_returns_recommendation_and_trace`
    - `test_run_hematology_support_flags_hemophilia_and_splenectomy_safety`
    - `test_run_hematology_support_flags_oncology_fanconi_and_transplant`
    - `test_run_hematology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_hematology_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/hematology_support_protocol.py app/services/hematology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/hematology_support_protocol.py app/services/hematology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k hematology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k hematology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

- Plan TM-079:
  - Implementar endpoint de soporte operativo de endocrinologia sobre `care-tasks`.
  - Persistir traza del workflow endocrino-metabolico en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-079:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/endocrinology/recommendation`
  - Workflow agregado:
    - `workflow_name=endocrinology_support_v1`
  - Metricas agregadas:
    - `endocrinology_support_runs_total`
    - `endocrinology_support_runs_completed_total`
    - `endocrinology_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_endocrinology_support_returns_recommendation_and_trace`
    - `test_run_endocrinology_support_flags_thyroid_and_siadh_safety`
    - `test_run_endocrinology_support_flags_diabetes_and_confounders`
    - `test_run_endocrinology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_endocrinology_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/endocrinology_support_protocol.py app/services/endocrinology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/endocrinology_support_protocol.py app/services/endocrinology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k endocrinology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k endocrinology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`112 passed`)

- Plan TM-080:
  - Implementar endpoint de soporte operativo de nefrologia sobre `care-tasks`.
  - Persistir traza del workflow nefrologico en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-080:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/nephrology/recommendation`
  - Workflow agregado:
    - `workflow_name=nephrology_support_v1`
  - Metricas agregadas:
    - `nephrology_support_runs_total`
    - `nephrology_support_runs_completed_total`
    - `nephrology_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_nephrology_support_returns_recommendation_and_trace`
    - `test_run_nephrology_support_flags_acid_base_and_aeiou`
    - `test_run_nephrology_support_flags_nephroprotection_and_interstitial_safety`
    - `test_run_nephrology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_nephrology_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/nephrology_support_protocol.py app/services/nephrology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/nephrology_support_protocol.py app/services/nephrology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k nephrology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k nephrology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`117 passed`)

- Plan TM-081:
  - Implementar endpoint de soporte operativo de neumologia sobre `care-tasks`.
  - Persistir traza del workflow neumologico en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-081:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/pneumology/recommendation`
  - Workflow agregado:
    - `workflow_name=pneumology_support_v1`
  - Metricas agregadas:
    - `pneumology_support_runs_total`
    - `pneumology_support_runs_completed_total`
    - `pneumology_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_pneumology_support_returns_recommendation_and_trace`
    - `test_run_pneumology_support_flags_safety_and_lba_context`
    - `test_run_pneumology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_pneumology_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/pneumology_support_protocol.py app/services/pneumology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/pneumology_support_protocol.py app/services/pneumology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k pneumology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k pneumology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

- Plan TM-082:
  - Implementar endpoint de soporte operativo de geriatria sobre `care-tasks`.
  - Persistir traza del workflow geriatrico en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-082:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/geriatrics/recommendation`
  - Workflow agregado:
    - `workflow_name=geriatrics_support_v1`
  - Metricas agregadas:
    - `geriatrics_support_runs_total`
    - `geriatrics_support_runs_completed_total`
    - `geriatrics_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_geriatrics_support_returns_recommendation_and_trace`
    - `test_run_geriatrics_support_flags_start_v3_and_tetanus_logic`
    - `test_run_geriatrics_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_geriatrics_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/geriatrics_support_protocol.py app/services/geriatrics_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/geriatrics_support_protocol.py app/services/geriatrics_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k geriatrics_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k geriatrics_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`

- Plan TM-083:
  - Implementar endpoint de soporte operativo de oncologia sobre `care-tasks`.
  - Persistir traza del workflow oncologico en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-083:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/oncology/recommendation`
  - Workflow agregado:
    - `workflow_name=oncology_support_v1`
  - Metricas agregadas:
    - `oncology_support_runs_total`
    - `oncology_support_runs_completed_total`
    - `oncology_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_oncology_support_returns_recommendation_and_trace`
    - `test_run_oncology_support_flags_cardio_and_sarcoma_branches`
    - `test_run_oncology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_oncology_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/oncology_support_protocol.py app/services/oncology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/oncology_support_protocol.py app/services/oncology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k oncology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k oncology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`129 passed`)

- Plan TM-084:
  - Implementar endpoint de soporte operativo de anestesiologia/reanimacion sobre `care-tasks`.
  - Persistir traza del workflow anestesiologico en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-084:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/anesthesiology/recommendation`
  - Workflow agregado:
    - `workflow_name=anesthesiology_support_v1`
  - Metricas agregadas:
    - `anesthesiology_support_runs_total`
    - `anesthesiology_support_runs_completed_total`
    - `anesthesiology_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_anesthesiology_support_returns_recommendation_and_trace`
    - `test_run_anesthesiology_support_differential_blocks_and_safety`
    - `test_run_anesthesiology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_anesthesiology_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/anesthesiology_support_protocol.py app/services/anesthesiology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/anesthesiology_support_protocol.py app/services/anesthesiology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k anesthesiology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k anesthesiology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`133 passed`)

- Plan TM-085:
  - Implementar endpoint de soporte operativo de cuidados paliativos sobre `care-tasks`.
  - Persistir traza del workflow paliativo en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-085:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/palliative/recommendation`
  - Workflow agregado:
    - `workflow_name=palliative_support_v1`
  - Metricas agregadas:
    - `palliative_support_runs_total`
    - `palliative_support_runs_completed_total`
    - `palliative_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_palliative_support_returns_recommendation_and_trace`
    - `test_run_palliative_support_flags_ethical_and_delirium_logic`
    - `test_run_palliative_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_palliative_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/palliative_support_protocol.py app/services/palliative_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/palliative_support_protocol.py app/services/palliative_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k palliative_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k palliative_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`137 passed`)

- Plan TM-086:
  - Implementar endpoint de soporte operativo de urologia sobre `care-tasks`.
  - Persistir traza del workflow urologico en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-086:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/urology/recommendation`
  - Workflow agregado:
    - `workflow_name=urology_support_v1`
  - Metricas agregadas:
    - `urology_support_runs_total`
    - `urology_support_runs_completed_total`
    - `urology_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_urology_support_returns_recommendation_and_trace`
    - `test_run_urology_support_prioritizes_diversion_and_triple_therapy_safety`
    - `test_run_urology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_urology_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/urology_support_protocol.py app/services/urology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/urology_support_protocol.py app/services/urology_support_protocol_service.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k urology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k urology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`141 passed`)

- Plan TM-087:
  - Implementar endpoint de soporte operativo de anisakis sobre `care-tasks`.
  - Persistir traza del workflow anisakis en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-087:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/anisakis/recommendation`
  - Workflow agregado:
    - `workflow_name=anisakis_support_v1`
  - Metricas agregadas:
    - `anisakis_support_runs_total`
    - `anisakis_support_runs_completed_total`
    - `anisakis_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_anisakis_support_returns_recommendation_and_trace`
    - `test_run_anisakis_support_handles_digestive_profile_without_anaphylaxis`
    - `test_run_anisakis_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_anisakis_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/anisakis_support_protocol.py app/services/anisakis_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/anisakis_support_protocol.py app/services/anisakis_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k anisakis_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k anisakis_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`145 passed`)

- Plan TM-088:
  - Implementar endpoint de soporte operativo de epidemiologia clinica sobre `care-tasks`.
  - Persistir traza del workflow epidemiologico en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-088:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/epidemiology/recommendation`
  - Workflow agregado:
    - `workflow_name=epidemiology_support_v1`
  - Metricas agregadas:
    - `epidemiology_support_runs_total`
    - `epidemiology_support_runs_completed_total`
    - `epidemiology_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_epidemiology_support_returns_recommendation_and_trace`
    - `test_run_epidemiology_support_flags_rr_and_nnt_safety_blocks`
    - `test_run_epidemiology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_epidemiology_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/epidemiology_support_protocol.py app/services/epidemiology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/epidemiology_support_protocol.py app/services/epidemiology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k epidemiology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k epidemiology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`149 passed`)

- Plan TM-089:
  - Implementar endpoint de soporte operativo de oftalmologia sobre `care-tasks`.
  - Persistir traza del workflow oftalmologico en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-089:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/ophthalmology/recommendation`
  - Workflow agregado:
    - `workflow_name=ophthalmology_support_v1`
  - Metricas agregadas:
    - `ophthalmology_support_runs_total`
    - `ophthalmology_support_runs_completed_total`
    - `ophthalmology_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_ophthalmology_support_returns_recommendation_and_trace`
    - `test_run_ophthalmology_support_flags_neuro_and_anisocoria_logic`
    - `test_run_ophthalmology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_ophthalmology_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/ophthalmology_support_protocol.py app/services/ophthalmology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/ophthalmology_support_protocol.py app/services/ophthalmology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k ophthalmology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k ophthalmology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`153 passed`)

- Plan TM-090:
  - Implementar endpoint de soporte operativo de inmunologia sobre `care-tasks`.
  - Persistir traza del workflow inmunologico en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-090:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/immunology/recommendation`
  - Workflow agregado:
    - `workflow_name=immunology_support_v1`
  - Metricas agregadas:
    - `immunology_support_runs_total`
    - `immunology_support_runs_completed_total`
    - `immunology_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_immunology_support_returns_recommendation_and_trace`
    - `test_run_immunology_support_differential_profiles_and_safety_blocks`
    - `test_run_immunology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_immunology_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/immunology_support_protocol.py app/services/immunology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/immunology_support_protocol.py app/services/immunology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/services/agent_run_service.py app/api/care_tasks.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k immunology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k immunology_support`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`157 passed`)

- Plan TM-091:
  - Implementar endpoint de soporte operativo de recurrencia genetica sobre `care-tasks`.
  - Persistir traza del workflow de recurrencia en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-091:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/genetic-recurrence/recommendation`
  - Workflow agregado:
    - `workflow_name=genetic_recurrence_support_v1`
  - Metricas agregadas:
    - `genetic_recurrence_support_runs_total`
    - `genetic_recurrence_support_runs_completed_total`
    - `genetic_recurrence_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_genetic_recurrence_support_returns_recommendation_and_trace`
    - `test_run_genetic_recurrence_support_handles_mosaicism_fraction_and_consistency`
    - `test_run_genetic_recurrence_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_genetic_recurrence_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/genetic_recurrence_support_protocol.py app/services/genetic_recurrence_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/genetic_recurrence_support_protocol.py app/services/genetic_recurrence_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k genetic_recurrence`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k genetic_recurrence`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`161 passed`)

- Plan TM-092:
  - Implementar endpoint de soporte operativo de ginecologia/obstetricia sobre `care-tasks`.
  - Persistir traza del workflow gineco-obstetrico en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-092:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/gynecology-obstetrics/recommendation`
  - Workflow agregado:
    - `workflow_name=gynecology_obstetrics_support_v1`
  - Metricas agregadas:
    - `gynecology_obstetrics_support_runs_total`
    - `gynecology_obstetrics_support_runs_completed_total`
    - `gynecology_obstetrics_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_gynecology_obstetrics_support_returns_recommendation_and_trace`
    - `test_run_gynecology_obstetrics_support_blocks_unsafe_pharmacology`
    - `test_run_gynecology_obstetrics_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_gynecology_obstetrics_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/gynecology_obstetrics_support_protocol.py app/services/gynecology_obstetrics_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/gynecology_obstetrics_support_protocol.py app/services/gynecology_obstetrics_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k gynecology_obstetrics`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k gynecology_obstetrics`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`165 passed`)

- Plan TM-093:
  - Implementar endpoint de soporte operativo de pediatria/neonatologia sobre `care-tasks`.
  - Persistir traza del workflow pediatrico-neonatal en `agent_runs/agent_steps`.
  - Exponer metricas de ejecucion y alertas criticas en `/metrics`.
  - Ejecutar regresion focalizada de API y metricas.
- Resultado TM-093:
  - Endpoint agregado:
    - `POST /api/v1/care-tasks/{id}/pediatrics-neonatology/recommendation`
  - Workflow agregado:
    - `workflow_name=pediatrics_neonatology_support_v1`
  - Metricas agregadas:
    - `pediatrics_neonatology_support_runs_total`
    - `pediatrics_neonatology_support_runs_completed_total`
    - `pediatrics_neonatology_support_critical_alerts_total`
  - Pruebas agregadas:
    - `test_run_pediatrics_neonatology_support_returns_recommendation_and_trace`
    - `test_run_pediatrics_neonatology_support_flags_critical_branches`
    - `test_run_pediatrics_neonatology_support_returns_404_when_task_not_found`
    - `test_metrics_endpoint_contains_pediatrics_neonatology_support_metrics`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/schemas/pediatrics_neonatology_support_protocol.py app/services/pediatrics_neonatology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/pediatrics_neonatology_support_protocol.py app/services/pediatrics_neonatology_support_protocol_service.py app/schemas/__init__.py app/services/__init__.py app/api/care_tasks.py app/services/agent_run_service.py app/metrics/agent_metrics.py app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k pediatrics_neonatology`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py -k pediatrics_neonatology`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py` (`169 passed`)

- Plan TM-094:
  - Implementar chat clinico-operativo persistente sobre `care-tasks`.
  - Persistir memoria conversacional por sesion en tabla dedicada.
  - Persistir trazabilidad de chat en `agent_runs/agent_steps`.
  - Ejecutar regresion focalizada de API para endpoints de chat.
- Resultado TM-094:
  - Endpoints agregados:
    - `POST /api/v1/care-tasks/{id}/chat/messages`
    - `GET /api/v1/care-tasks/{id}/chat/messages`
    - `GET /api/v1/care-tasks/{id}/chat/memory`
  - Workflow agregado:
    - `workflow_name=care_task_clinical_chat_v1`
  - Persistencia agregada:
    - tabla `care_task_chat_messages` (migracion Alembic dedicada)
  - Pruebas agregadas:
    - `test_create_care_task_chat_message_persists_message_and_trace`
    - `test_list_care_task_chat_messages_and_memory_summary`
    - `test_create_care_task_chat_message_returns_404_when_task_not_found`
  - Comandos de validacion:
    - `.\venv\Scripts\python.exe -m py_compile app/models/care_task_chat_message.py app/schemas/clinical_chat.py app/services/clinical_chat_service.py app/services/agent_run_service.py app/api/care_tasks.py app/tests/test_care_tasks_api.py alembic/versions/d4f6a9c8e221_add_care_task_chat_messages_table.py`
    - `.\venv\Scripts\python.exe -m ruff check app/models/care_task_chat_message.py app/schemas/clinical_chat.py app/services/clinical_chat_service.py app/services/agent_run_service.py app/api/care_tasks.py app/tests/test_care_tasks_api.py alembic/versions/d4f6a9c8e221_add_care_task_chat_messages_table.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat_message` (`3 passed, 126 deselected`)
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py` (`129 passed`)
    - `.\venv\Scripts\python.exe -m pytest -q` (`234 passed`)

- Plan TM-095:
  - Integrar modo de especialidad por credencial autenticada en chat.
  - Integrar continuidad longitudinal por paciente (`patient_reference`) entre episodios.
  - Integrar fuentes internas indexadas y fuentes web opcionales trazables.
  - Asegurar contrato auth/chat actualizado y regresion total en verde.
- Resultado TM-095:
  - Cobertura de pruebas agregada/ajustada:
    - `app/tests/test_auth_api.py` actualizado para `specialty`.
    - `app/tests/test_care_tasks_api.py`:
      - `test_chat_endpoints_require_authentication`
      - `test_chat_memory_aggregates_patient_history_across_tasks`
      - chat tests existentes actualizados con login y headers `Bearer`.
  - Comandos de validacion ejecutados:
    - `.\venv\Scripts\python.exe -m py_compile app/models/user.py app/models/care_task.py app/models/care_task_chat_message.py app/schemas/auth.py app/schemas/care_task.py app/schemas/clinical_chat.py app/services/auth_service.py app/services/care_task_service.py app/services/clinical_chat_service.py app/api/auth.py app/api/care_tasks.py app/tests/test_auth_api.py app/tests/test_care_tasks_api.py alembic/versions/e8a1c4b7d552_add_chat_specialty_patient_context_fields.py`
    - `.\venv\Scripts\python.exe -m ruff check app/models/user.py app/models/care_task.py app/models/care_task_chat_message.py app/schemas/auth.py app/schemas/care_task.py app/schemas/clinical_chat.py app/services/auth_service.py app/services/care_task_service.py app/services/clinical_chat_service.py app/api/auth.py app/api/care_tasks.py app/core/config.py app/tests/test_auth_api.py app/tests/test_care_tasks_api.py alembic/versions/e8a1c4b7d552_add_chat_specialty_patient_context_fields.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_auth_api.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py`
    - `.\venv\Scripts\python.exe -m pytest -q`
    - `.\venv\Scripts\python.exe -m alembic upgrade head`
    - `.\venv\Scripts\python.exe -m alembic current` (`e8a1c4b7d552 (head)`)

- Plan TM-096:
  - Crear modelo de datos para fuentes clinicas y eventos de sellado profesional.
  - Exponer API para alta/listado/sellado con control de permisos.
  - Endurecer chat para usar whitelist web estricta y fuentes internas validadas.
  - Validar regresion de chat y suite completa.
- Resultado TM-096:
  - Pruebas agregadas:
    - `app/tests/test_knowledge_sources_api.py`:
      - `test_create_knowledge_source_requires_auth`
      - `test_create_knowledge_source_rejects_non_whitelisted_domain`
      - `test_create_seal_and_list_validated_knowledge_source`
      - `test_non_admin_cannot_seal_knowledge_source`
      - `test_chat_uses_validated_knowledge_source`
  - Pruebas ajustadas:
    - `app/tests/test_care_tasks_api.py` (chat tolera ausencia de fuentes validadas al inicio).
  - Comandos de validacion ejecutados:
    - `.\venv\Scripts\python.exe -m py_compile app/models/clinical_knowledge_source.py app/models/clinical_knowledge_source_validation.py app/services/knowledge_source_service.py app/api/knowledge_sources.py app/services/clinical_chat_service.py app/core/config.py app/main.py app/api/__init__.py app/tests/test_knowledge_sources_api.py`
    - `.\venv\Scripts\python.exe -m ruff check app/models/clinical_knowledge_source.py app/models/clinical_knowledge_source_validation.py app/models/__init__.py app/core/database.py app/services/knowledge_source_service.py app/services/clinical_chat_service.py app/api/knowledge_sources.py app/api/__init__.py app/main.py app/core/config.py app/tests/test_knowledge_sources_api.py app/tests/test_care_tasks_api.py alembic/versions/c2f4a9e1b771_add_clinical_knowledge_sources_tables.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_knowledge_sources_api.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat`
    - `.\venv\Scripts\python.exe -m pytest -q`
    - `.\venv\Scripts\python.exe -m alembic upgrade head`
    - `.\venv\Scripts\python.exe -m alembic current` (`c2f4a9e1b771 (head)`)

- Plan TM-098:
  - Generar frontend MVP de chat clinico con React + Vite.
  - Validar compilacion de frontend y compatibilidad CORS local.
  - Validar regresion minima de settings backend.
- Resultado TM-098:
  - Workspace frontend agregado en `frontend/` con:
    - login profesional
    - gestion de casos
    - chat + memoria + trazabilidad
  - Comandos de validacion ejecutados:
    - `cd frontend && npm install`
    - `cd frontend && npm run build` (`vite v5.x, build OK`)
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_settings_security.py` (`4 passed`)

- Plan TM-099:
  - Redisenar frontend a UX tipo assistant con herramientas seleccionables.
  - Extender chat backend a modo hibrido (`general`/`clinical`) trazable.
  - Validar compilacion frontend y regresion de endpoints de chat.
- Resultado TM-099:
  - `POST /care-tasks/{id}/chat/messages` soporta `conversation_mode` y `tool_mode`.
  - Respuesta de chat expone `response_mode` y `tool_mode`.
  - Frontend v2 integra barra de herramientas, modo conversacional y conversacion libre.
  - Comandos de validacion ejecutados:
    - `cd frontend && npm run build`
    - `.\venv\Scripts\python.exe -m ruff check app/schemas/clinical_chat.py app/services/clinical_chat_service.py app/api/care_tasks.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat`

- Plan TM-100:
  - Integrar proveedor neuronal local para chat (Ollama) sin romper fallback actual.
  - Exponer trazabilidad de uso/latencia del LLM en `interpretability_trace`.
  - Validar build/lint/tests del flujo de chat.
- Resultado TM-100:
  - Nuevo servicio `app/services/llm_chat_provider.py` integrado en chat.
  - Configuracion de LLM agregada en settings y `.env.example`/`.env.docker`.
  - Documentacion tecnica y ADR de motor neuronal local agregadas.
  - Comandos de validacion ejecutados:
    - `cd frontend && npm run build`
    - `.\venv\Scripts\python.exe -m ruff check app/services/llm_chat_provider.py app/services/clinical_chat_service.py app/schemas/clinical_chat.py app/api/care_tasks.py app/tests/test_care_tasks_api.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat`

- Plan TM-101:
  - Verificar continuidad de hilo entre turnos de la misma sesion.
  - Evitar contaminacion de memoria con hechos de control de UI (`modo_respuesta`, `herramienta`).
  - Validar regresion de chat sin romper contratos.
- Resultado TM-101:
  - Contexto de dialogo previo integrado en prompt LLM (`recent_dialogue`).
  - Filtro aplicado para excluir hechos de control de `memory_facts_used`.
  - Nuevo test:
    - `test_chat_continuity_filters_control_facts_from_memory`
  - Comandos de validacion ejecutados:
    - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/tests/test_care_tasks_api.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k "chat_continuity_filters_control_facts_from_memory or chat_message"` (`6 passed`)

- Plan TM-102:
  - Mejorar continuidad semantica en queries de seguimiento.
  - Priorizar endpoint conversacional de Ollama (`/api/chat`) con fallback robusto.
  - Ajustar configuracion LLM local para perfil 16GB.
  - Validar regresion de chat y nuevas reglas de continuidad.
- Resultado TM-102:
  - Query expansion contextual agregada (`query_expanded`) para follow-up.
  - Proveedor LLM actualizado a estrategia `chat -> generate`.
  - Nuevos settings: `CLINICAL_CHAT_LLM_NUM_CTX`, `CLINICAL_CHAT_LLM_TOP_P`.
  - Test nuevo:
    - `test_chat_follow_up_query_reuses_previous_context_for_domain_matching`
  - Comandos de validacion ejecutados:
    - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/core/config.py app/tests/test_care_tasks_api.py`
    - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k "chat_continuity_filters_control_facts_from_memory or chat_follow_up_query_reuses_previous_context_for_domain_matching or chat_message"` (`7 passed`)

## TM-103 - Plan de validacion ejecutado

- Validar expansion de follow-up en continuidad de sesion.
- Validar preferencia de endpoint `api/chat` en proveedor Ollama.
- Validar traza operativa en e2e de 3 turnos.
- Validar build frontend tras simplificacion UI.


## TM-105 - Plan de validacion ejecutado

- Validar parseo tolerante de respuestas Ollama en formato JSONL chunked.
- Validar parseo tolerante de lineas con prefijo `data:` (SSE-like).
- Revalidar flujo e2e de continuidad con trazas de chat para evitar regresion.

Resultados:
- Nuevos tests:
  - `test_parse_ollama_payload_supports_jsonl_chunks`
  - `test_parse_ollama_payload_supports_sse_data_lines`
- Comandos ejecutados:
  - `python -m ruff check app/services/llm_chat_provider.py app/tests/test_clinical_chat_operational.py`
  - `python -m pytest -q app/tests/test_clinical_chat_operational.py`


## TM-106 - Plan de validacion ejecutado

- Verificar que saludo/consulta general no vuelca JSON crudo de recomendaciones internas.
- Verificar que recomendaciones internas sigan disponibles en modo clinico.
- Revalidar tests de parseo Ollama sin regresion.

Resultados:
- Nuevo test:
  - `test_general_answer_does_not_dump_json_snippet_for_social_query`
- Comandos ejecutados:
  - `python -m ruff check app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py`
  - `python -m pytest -q app/tests/test_clinical_chat_operational.py`


## TM-107 - Plan de validacion ejecutado

- Validar respuesta exploratoria con dominios disponibles y siguiente paso util.
- Validar no regresion en higiene de snippets para saludo general.
- Validar no regresion de parser Ollama y e2e de continuidad.

Resultados:
- Nuevo test:
  - `test_general_answer_suggests_domains_and_next_step_for_case_discovery`
- Comandos ejecutados:
  - `python -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/tests/test_clinical_chat_operational.py`
  - `python -m pytest -q app/tests/test_clinical_chat_operational.py`


## TM-108 - Plan de validacion ejecutado

- Verificar compilacion de servicios de chat tras resolver conflictos de merge.
- Validar sanitizacion anti-prompt-injection y trazabilidad asociada.
- Validar control de presupuesto de contexto/tokens en proveedor Ollama.
- Validar schema response de chat con `quality_metrics`.

Resultados:
- Nuevos tests:
  - `test_prompt_injection_detection_and_sanitization`
  - `test_llm_provider_build_chat_messages_respects_token_budget`
- Tests ajustados:
  - `app/tests/test_care_tasks_api.py` (aserciones sobre `quality_metrics` y traza de calidad)
- Comandos ejecutados:
  - `python -m py_compile app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/schemas/clinical_chat.py app/api/care_tasks.py app/tests/test_clinical_chat_operational.py app/tests/test_care_tasks_api.py`
  - `python -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/schemas/clinical_chat.py app/api/care_tasks.py app/tests/test_clinical_chat_operational.py app/tests/test_care_tasks_api.py`
  - `python -m pytest -q app/tests/test_clinical_chat_operational.py`
  - `python -m pytest -q app/tests/test_care_tasks_api.py -k chat`


## TM-109 - Plan de validacion ejecutado

- Validar sintaxis/configuracion de hooks staged (`pre-commit`).
- Validar ejecucion real del nuevo workflow `check`.
- Validar flujo focalizado `test-e2e` del nuevo workflow.
- Validar script de onboarding de hooks.

Resultados:
- Comandos ejecutados:
  - `.\venv\Scripts\python.exe -m pre_commit validate-config` (OK).
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev_workflow.ps1 -Action check` (falla por deuda previa de lint E501 fuera de TM-109; script valida correctamente el fallo).
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev_workflow.ps1 -Action test-e2e` (`18 passed, 126 deselected`).
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup_hooks.ps1` (OK; hook instalado y config validada).
- Observaciones:
  - `test-e2e` emite warnings deprecados de `datetime.utcnow()` en dependencia `python-jose`, sin romper ejecucion.


## TM-110 - Plan de validacion ejecutado

- Corregir deuda `E501` detectada por `ruff` en archivos historicos.
- Validar que lint y formato queden estables tras el saneamiento.
- Re-ejecutar `scripts/dev_workflow.ps1 -Action check` para identificar bloqueos residuales.

Resultados:
- Comandos ejecutados:
  - `.\venv\Scripts\python.exe -m ruff check app mcp_server` (OK).
  - `.\venv\Scripts\python.exe -m black app mcp_server` (aplica formato global necesario).
  - `.\venv\Scripts\python.exe -m black --check app mcp_server` (OK).
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/dev_workflow.ps1 -Action check`:
    - `ruff check` OK
    - `black --check` OK
    - `mypy` falla por deuda historica de tipado (459 errores en modulos legacy).
- Observaciones:
  - TM-110 deja saneado lint/formato, pero no cierra aun la deuda de `mypy`.


## TM-111 - Plan de validacion ejecutado

- Verificar que fallback clinico no imprima JSON crudo de recomendaciones internas.
- Verificar que continuidad clinica no se ancle a turno social.
- Validar no regresion de respuestas generales/follow-up.

Resultados:
- Tests nuevos:
  - `test_clinical_fallback_does_not_dump_json_or_internal_fact_tags`
  - `test_clinical_fallback_ignores_social_turn_for_continuity`
- Comandos ejecutados:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py` (OK).
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "clinical_fallback or general_answer or follow_up_query_expansion"` (`5 passed, 6 deselected`).

## TM-113 - Plan de validacion ejecutado

- Verificar que el endpoint de chat no rompa por desempaquetado de retorno.
- Verificar integracion RAG en `clinical_chat_service` con fallback sin regresion.
- Verificar compatibilidad de politicas de herramientas para modo clinico (`medication`).
- Verificar lint/sintaxis de modulos RAG y script de ingesta.

Resultados:
- Comandos ejecutados:
  - `.\venv\Scripts\python.exe -m ruff check app/agents/tool_policy_pipeline.py app/services/clinical_chat_service.py app/services/rag_orchestrator.py app/services/rag_retriever.py app/services/embedding_service.py app/scripts/ingest_clinical_docs.py app/tests/test_clinical_chat_operational.py app/api/care_tasks.py app/core/config.py app/models/__init__.py app/models/clinical_document.py app/models/document_chunk.py app/models/rag_query_audit.py alembic/env.py app/core/database.py app/core/chunking.py app/services/document_ingestion_service.py app/services/rag_prompt_builder.py app/services/rag_gatekeeper.py app/services/__init__.py` (OK).
  - `.\venv\Scripts\python.exe -m py_compile app/agents/tool_policy_pipeline.py app/services/clinical_chat_service.py app/services/rag_orchestrator.py app/services/rag_retriever.py app/services/embedding_service.py app/scripts/ingest_clinical_docs.py app/tests/test_clinical_chat_operational.py app/api/care_tasks.py app/core/config.py app/models/clinical_document.py app/models/document_chunk.py app/models/rag_query_audit.py app/core/database.py app/core/chunking.py app/services/document_ingestion_service.py app/services/rag_prompt_builder.py app/services/rag_gatekeeper.py` (OK).
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py` (`12 passed`).
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat` (`9 passed, 126 deselected`).
- Observaciones:
  - Persisten warnings deprecados de `python-jose` (`datetime.utcnow()`), sin afectar resultado funcional.

## TM-114 - Plan de validacion ejecutado

- Verificar validacion de nuevos flags de configuracion (retriever backend y guardrails path).
- Verificar fallback de RAG cuando backend `llamaindex` no entrega resultados.
- Verificar aplicacion de guardrails en flujo e2e de chat sin romper contrato.
- Verificar no regresion de chat API.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_settings_security.py`
    - `test_rejects_invalid_rag_retriever_backend`
    - `test_rejects_empty_guardrails_config_path`
  - `app/tests/test_nemo_guardrails_service.py`
    - `test_guardrails_service_skips_when_disabled`
    - `test_guardrails_service_fails_open_when_config_missing`
  - `app/tests/test_clinical_chat_operational.py`
    - `test_rag_orchestrator_falls_back_to_legacy_when_llamaindex_has_no_results`
    - `test_chat_e2e_applies_guardrails_when_enabled`
- Comandos ejecutados:
  - `.\venv\Scripts\python.exe -m ruff check app/core/config.py app/services/llamaindex_retriever.py app/services/nemo_guardrails_service.py app/services/rag_orchestrator.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_chat_operational.py app/tests/test_nemo_guardrails_service.py app/tests/test_settings_security.py` (OK)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_settings_security.py` (`6 passed`)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_nemo_guardrails_service.py` (`2 passed`)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py` (`14 passed`)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat` (`9 passed, 126 deselected`)

## TM-115 - Plan de validacion ejecutado

- Verificar backend `chroma` en selector de retrieval sin romper `legacy`.
- Verificar fallback a `legacy` cuando `chroma` no devuelve resultados.
- Verificar validacion de nuevo flag `CLINICAL_CHAT_RAG_CHROMA_CANDIDATE_POOL`.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_clinical_chat_operational.py`
    - `test_rag_orchestrator_uses_chroma_backend_when_configured`
    - `test_rag_orchestrator_falls_back_to_legacy_when_chroma_empty`
  - `app/tests/test_settings_security.py`
    - `test_rejects_invalid_chroma_candidate_pool`
- Comandos ejecutados:
  - `.\venv\Scripts\python.exe -m ruff check ...` (modulos tocados, OK)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_settings_security.py` (OK)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py` (OK)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat` (OK)

## TM-116 - Plan de validacion ejecutado

- Verificar compilacion frontend tras rediseno UI completo.
- Verificar responsive base y ausencia de errores TypeScript/Vite.
- Verificar continuidad de integracion con API existente (sin cambio de contrato).

Resultados:
- Comandos ejecutados:
  - `cd frontend && npm run build` (OK)
- Observaciones:
  - El streaming implementado es de presentacion (typewriter local) sobre respuesta completa.
  - No se requieren migraciones ni cambios backend para habilitar el nuevo frontend.

## TM-110 - Plan de validacion ejecutado

- Verificar que chat/messages funcione en modo automatico por intencion (sin especialidad manual).
- Verificar inferencia de especialidad por query y matching de dominio sin sesgo por perfil autenticado.
- Verificar compilacion frontend tras ajustar payload (`use_authenticated_specialty_mode=false`).

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_clinical_chat_operational.py`
    - `test_effective_specialty_is_inferred_from_query_before_user_profile`
    - `test_domain_matching_does_not_force_specialty_fallback_when_query_matches_other_domain`
- Comandos ejecutados:
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py` (`18 passed`)
  - `cd frontend && npm run build` (OK)

## TM-117 - Plan de validacion ejecutado

- Verificar que el proveedor LLM local deje de caer sistematicamente en `TimeoutError`.
- Verificar que en desarrollo no se quede sin fuentes internas cuando no hay registros validados en BD.
- Verificar no regresion de lint/tests del modulo de chat.

Resultados:
- Comandos ejecutados:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/services/llm_chat_provider.py app/tests/test_clinical_chat_operational.py` (OK)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py` (`18 passed`)
  - `.\venv\Scripts\python.exe` con llamada directa a `LLMChatProvider.generate_answer(...)`:
    - `llm_used=true`
    - `llm_endpoint=chat`
    - latencia observada ~6.8s

## TM-118 - Plan de validacion ejecutado

- Verificar que consultas clinicas en lenguaje natural entren en modo clinico automatico.
- Verificar que respuestas LLM clinicas genericas/cortas terminen en fallback estructurado.
- Verificar no regresion en integraciones RAG/guardrails del chat.

Resultados:
- Tests nuevos/actualizados:
  - `test_auto_mode_detects_clinical_signal_in_pediatric_febrile_query`
  - `test_chat_e2e_forces_structured_fallback_when_llm_answer_is_generic`
- Comandos ejecutados:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py` (OK)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py` (`22 passed`)

## TM-119 - Plan de validacion ejecutado

- Verificar filtrado de chunks por especialidad en estrategia de dominio RAG.
- Verificar ingesta progresiva clinica con mapeo por defecto y backfill de especialidad.
- Verificar no regresion del flujo de chat clinico operativo.

Resultados:
- Tests nuevos/actualizados:
  - `test_rag_orchestrator_filters_domain_chunks_by_effective_specialty`
- Comandos ejecutados:
  - `.\venv\Scripts\python.exe -m ruff check app/services/rag_orchestrator.py app/services/document_ingestion_service.py app/scripts/ingest_clinical_docs.py app/tests/test_clinical_chat_operational.py` (OK)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py` (`26 passed`)
  - `.\venv\Scripts\python.exe -m app.scripts.ingest_clinical_docs --backfill-only` (OK)

## TM-138 - Plan de validacion ejecutado

- Verificar clasificacion SVM en casos con red flags criticos.
- Verificar no regresion en flujo RAG/interrogatory.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_clinical_chat_operational.py`: `test_svm_triage_service_flags_critical_hyperkalemia_case`
- Comandos ejecutados:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_svm_triage_service.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_chat_operational.py` (OK)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "svm_triage_service_flags_critical_hyperkalemia_case or uses_rag_when_enabled"` (OK)

## TM-139 - Plan de validacion ejecutado

- Verificar calculo probabilistico y deteccion de anomalia para casos con red flags.
- Verificar no regresion en chat clinico con RAG habilitado.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_clinical_chat_operational.py`: `test_risk_pipeline_service_estimates_probability_and_anomaly`
- Comandos ejecutados:
  - `.\venv\Scripts\python.exe -m ruff check app/services/clinical_risk_pipeline_service.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_chat_operational.py` (OK)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "risk_pipeline_service_estimates_probability_and_anomaly or svm_triage_service_flags_critical_hyperkalemia_case or uses_rag_when_enabled"` (OK)

## TM-141 - Plan de validacion ejecutado

- Verificar lint en nuevos cambios de retrieval/gate/config.
- Verificar gate de fidelidad cuando la respuesta no esta soportada por evidencia recuperada.
- Verificar no regresion minima del flujo RAG operativo.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_clinical_chat_operational.py`: `test_gatekeeper_flags_low_faithfulness_as_risk`
- Comandos ejecutados:
  - `.\venv\Scripts\python.exe -m ruff check app/core/config.py app/services/rag_gatekeeper.py app/services/rag_retriever.py app/tests/test_clinical_chat_operational.py` (OK)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "gatekeeper_flags_low_faithfulness_as_risk or uses_rag_when_enabled"` (OK)

## TM-142 - Plan de validacion ejecutado

- Verificar chunking recursivo y overlap en textos sobredimensionados.
- Verificar expansion de consulta en retrieval sin dependencias externas.
- Verificar nueva validacion de relevancia de contexto en gatekeeper.
- Verificar no regresion minima del flujo RAG principal.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_chunking.py`
  - `app/tests/test_rag_retriever.py`
  - `app/tests/test_settings_security.py::test_rejects_invalid_context_min_ratio`
  - `app/tests/test_clinical_chat_operational.py::test_gatekeeper_flags_low_context_relevance_warning`
- Comandos ejecutados:
  - `.\venv\Scripts\python.exe -m ruff check app/core/chunking.py app/services/embedding_service.py app/services/rag_retriever.py app/services/rag_orchestrator.py app/services/rag_gatekeeper.py app/scripts/ingest_clinical_docs.py app/core/config.py app/tests/test_chunking.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py app/tests/test_clinical_chat_operational.py` (OK)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_chunking.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py -q` (OK)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "gatekeeper_flags_low_faithfulness_as_risk or gatekeeper_flags_low_context_relevance_warning or uses_rag_when_enabled"` (OK)

## TM-143 - Plan de validacion ejecutado

- Verificar nuevo control adaptativo de `k` y rerank MMR con trazabilidad.
- Verificar compresion de contexto antes de prompt y sus metricas.
- Verificar validaciones de settings para nuevos parametros.
- Verificar no regresion minima en flujo RAG operacional.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_rag_orchestrator_optimizations.py`
    - `test_adaptive_k_short_query_with_high_risk_marker`
    - `test_adaptive_k_disabled_uses_bounded_base`
    - `test_mmr_rerank_prioritizes_diversity`
    - `test_context_compression_keeps_overlap_sentences`
  - `app/tests/test_settings_security.py`
    - `test_rejects_invalid_adaptive_chunk_bounds`
    - `test_rejects_invalid_mmr_lambda`
    - `test_rejects_invalid_context_compression_max_chars`
- Comandos ejecutados:
  - `.\venv\Scripts\python.exe -m ruff check app/core/config.py app/services/rag_orchestrator.py app/services/rag_prompt_builder.py app/scripts/evaluate_rag_retrieval.py app/tests/test_chunking.py app/tests/test_rag_retriever.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py` (OK)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_chunking.py app/tests/test_rag_retriever.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""` (OK)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled or gatekeeper_flags_low_context_relevance_warning" -o addopts=""` (OK)

## TM-144 - Plan de validacion ejecutado

- Verificar parseo booleano y operaciones de postings (interseccion/diferencia).
- Verificar validacion de nuevos flags de candidate pool FTS.
- Verificar lint en retriever y config.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_rag_retriever.py`
    - `test_boolean_term_extraction_with_explicit_operators`
    - `test_intersect_sorted_ids_runs_in_merge_order`
    - `test_difference_sorted_ids_excludes_postings`
  - `app/tests/test_settings_security.py`
    - `test_rejects_invalid_fts_candidate_pool`
- Comandos ejecutados:
  - `.\venv\Scripts\python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py` (OK)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""` (OK)
  - `.\venv\Scripts\python.exe - <<'PY' ... HybridRetriever()._ensure_sqlite_fts_index(...) ... SELECT count(*) FROM document_chunks_fts WHERE MATCH 'oncologia' ... _fetch_candidate_chunks(...) ... PY` (OK: FTS con hits + estrategia booleana activa)

## TM-145 - Plan de validacion ejecutado

- Verificar parser booleano con precedencia/paréntesis y frases.
- Verificar nuevo setting de spell distance.
- Verificar no regresion minima de flujo RAG.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_rag_retriever.py`
    - `test_boolean_tokenizer_keeps_phrase_and_infers_implicit_and`
    - `test_boolean_rpn_respects_precedence_and_parentheses`
    - `test_levenshtein_distance_early_cutoff`
  - `app/tests/test_settings_security.py`
    - `test_rejects_invalid_spell_max_edit_distance`
- Comandos ejecutados:
  - `.\venv\Scripts\python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py` (OK)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""` (OK)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""` (OK)
  - `.\venv\Scripts\python.exe - <<'PY' ... _fetch_candidate_chunks(query='"neutropenia febril" AND oncolgia NOT pediatria') ... PY` (OK: frase + spell correction trazados)

## TM-146 - Plan de validacion ejecutado

- Verificar tokenizacion y parseo de proximidad `/k`.
- Verificar equivalencia entre interseccion lineal y con skip pointers.
- Verificar validacion de nuevo flag `CLINICAL_CHAT_RAG_SKIP_POINTERS_MIN_LIST`.
- Verificar no regresion minima del flujo RAG.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_rag_retriever.py`
    - `test_boolean_tokenizer_collapses_proximity_operator`
    - `test_intersect_with_skips_matches_linear_intersection`
  - `app/tests/test_settings_security.py`
    - `test_rejects_invalid_skip_pointers_min_list`
- Comandos ejecutados:
  - `.\venv\Scripts\python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py` (OK)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""` (OK)
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""` (OK)
  - `.\venv\Scripts\python.exe - <<'PY' ... _fetch_candidate_chunks(query='"neutropenia febril" /4 oncolgia AND NOT pediatria') ... PY` (OK: `candidate_spell_corrections=oncolgia->oncologia`, trazas skip disponibles)

## TM-147 - Plan de validacion ejecutado

- Verificar tokenizacion de wildcard (`*`) en parser booleano.
- Verificar utilidades de similitud k-gram/Jaccard y Soundex.
- Verificar validacion de nuevos settings de wildcard/spell trigger/k-gram.
- Verificar no regresion minima del flujo RAG.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_rag_retriever.py`
    - `test_boolean_tokenizer_keeps_wildcard_term`
    - `test_kgram_jaccard_similarity_is_higher_for_related_terms`
    - `test_soundex_matches_reference_shape`
  - `app/tests/test_settings_security.py`
    - `test_rejects_invalid_spell_trigger_max_postings`
    - `test_rejects_invalid_wildcard_max_expansions`
    - `test_rejects_invalid_kgram_jaccard_min`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""` (OK)

## TM-148 - Plan de validacion ejecutado

- Verificar mapeo de contexto por operandos.
- Verificar extraccion de terminos de borde en frases para contextual spell.
- Verificar validacion de nuevo setting de limite contextual.
- Verificar no regresion minima del flujo RAG.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_rag_retriever.py`
    - `test_build_operand_context_map_tracks_neighbors`
    - `test_context_term_from_neighbor_uses_phrase_edges`
  - `app/tests/test_settings_security.py`
    - `test_rejects_invalid_contextual_spell_max_candidates`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""` (OK)

## TM-149 - Plan de validacion ejecutado

- Verificar nuevas validaciones de settings para cache de vocabulario.
- Verificar helper de matching glob para wildcard.
- Verificar no regresion minima del flujo RAG.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_rag_retriever.py`
    - `test_glob_to_regex_matches_expected_pattern`
  - `app/tests/test_settings_security.py`
    - `test_rejects_invalid_vocab_cache_max_terms`
    - `test_rejects_invalid_vocab_cache_ttl_seconds`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""` (OK)

## TM-150 - Plan de validacion ejecutado

- Verificar roundtrip de codificacion de gaps (VB/Gamma).
- Verificar validacion de nuevos settings de cache de postings.
- Verificar script de estimacion Heaps/Zipf.
- Verificar no regresion minima de flujo RAG.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_rag_retriever.py`
    - `test_vb_gap_roundtrip_preserves_ids`
    - `test_gamma_gap_roundtrip_preserves_ids`
  - `app/tests/test_settings_security.py`
    - `test_rejects_invalid_postings_cache_max_entries`
    - `test_rejects_invalid_postings_cache_ttl_seconds`
    - `test_rejects_invalid_postings_cache_encoding`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/scripts/estimate_rag_index_stats.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m app.scripts.estimate_rag_index_stats --chunk-limit 200 --top 10` (OK)

## TM-151 - Plan de validacion ejecutado

- Verificar scorer lexical `tf-idf` por zonas con normalizacion pivotada.
- Verificar normalizacion de scores para mezcla hibrida.
- Verificar validaciones de settings nuevos de zona/tfidf.
- Verificar no regresion minima del flujo RAG.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_rag_retriever.py`
    - `test_normalize_candidate_scores_scales_min_max`
    - `test_build_zone_weights_normalized_sum`
    - `test_keyword_tfidf_zone_scoring_prioritizes_title_hits`
  - `app/tests/test_settings_security.py`
    - `test_rejects_invalid_tfidf_max_query_terms`
    - `test_rejects_invalid_tfidf_pivot_slope`
    - `test_rejects_invalid_tfidf_zone_blend`
    - `test_rejects_negative_zone_weight`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""` (OK)

## TM-152 - Plan de validacion ejecutado

- Verificar poda por `idf`, proximidad y calidad estatica en scorer lexical.
- Verificar validaciones de settings nuevos.
- Verificar no regresion minima en flujo RAG.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_rag_retriever.py`
    - `test_minimum_window_span_returns_smallest_window`
    - `test_estimate_static_quality_prefers_motor_operativo_document`
  - `app/tests/test_settings_security.py`
    - `test_rejects_invalid_idf_min_threshold`
    - `test_rejects_invalid_idf_min_keep_terms`
    - `test_rejects_invalid_proximity_bonus_weight`
    - `test_rejects_invalid_static_quality_weight`
    - `test_rejects_invalid_tier1_min_static_quality`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""` (OK)

## TM-153 - Plan de validacion ejecutado

- Verificar metricas IR base y ranking en evaluador offline.
- Verificar Kappa y parseo de parametros de precision@k.
- Verificar no regresion minima del stack RAG.

Resultados:
- Tests nuevos:
  - `app/tests/test_evaluate_rag_retrieval.py`
    - `test_precision_recall_and_f1_basic`
    - `test_average_precision_uses_relevant_ranks`
    - `test_dcg_prefers_early_relevance`
    - `test_kappa_from_pairs_perfect_and_none_cases`
    - `test_parse_precision_ks_with_invalid_values`
    - `test_parse_precision_ks_defaults_when_empty`
    - `test_resolve_relevance_lists_terms_fallback_caps_total_relevant`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/scripts/evaluate_rag_retrieval.py app/tests/test_evaluate_rag_retrieval.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_evaluate_rag_retrieval.py -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py app/tests/test_evaluate_rag_retrieval.py -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m app.scripts.evaluate_rag_retrieval --dataset tmp/rag_eval.jsonl --k 8 --precision-ks 1,3,5 --strategy auto` (OK)

## TM-154 - Plan de validacion ejecutado

- Verificar expansion global desde tesauro cacheado.
- Verificar derivacion de terminos PRF desde chunks pseudo-relevantes.
- Verificar validaciones de nuevos settings de tesauro/PRF.
- Verificar no regresion minima en flujo RAG.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_rag_retriever.py`
    - `test_expand_query_for_retrieval_details_uses_global_thesaurus_cache`
    - `test_derive_prf_terms_extracts_candidates_from_seed_chunks`
  - `app/tests/test_settings_security.py`
    - `test_rejects_empty_global_thesaurus_path`
    - `test_rejects_invalid_global_thesaurus_ttl`
    - `test_rejects_invalid_global_thesaurus_max_expansions`
    - `test_rejects_invalid_prf_topk`
    - `test_rejects_invalid_prf_max_terms`
    - `test_rejects_invalid_prf_min_term_len`
    - `test_rejects_invalid_prf_beta`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts=""` (OK)

## TM-155 - Plan de validacion ejecutado

- Verificar no regresion del scorer lexical con blend BM25/BIM.
- Verificar trazabilidad probabilistica en salida de scoring.
- Verificar validaciones de settings BM25/BIM.

Resultados:
- Tests nuevos/actualizados:
  - app/tests/test_rag_retriever.py
    - test_keyword_scoring_empty_chunks_keeps_probabilistic_trace
    - ajuste de test_keyword_tfidf_zone_scoring_prioritizes_title_hits
  - app/tests/test_settings_security.py
    - test_rejects_invalid_bm25_k1
    - test_rejects_invalid_bm25_b
    - test_rejects_invalid_bm25_blend
    - test_rejects_invalid_bim_binary_bonus_weight
- Comandos ejecutados:
  - ./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py (OK)
  - ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py app/tests/test_evaluate_rag_retrieval.py -o addopts="" (OK)
  - ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts="" (OK)

## TM-156 - Plan de validacion ejecutado

- Verificar formulas de suavizado (Dirichlet/JM).
- Verificar inclusion de QLM en trazas y metodo de scoring.
- Verificar validaciones de settings QLM.

Resultados:
- Tests nuevos/actualizados:
  - app/tests/test_rag_retriever.py
    - test_dirichlet_smoothed_prob_increases_with_doc_tf
    - test_jm_smoothed_prob_uses_collection_backoff
    - test_keyword_scoring_method_includes_qlm_when_enabled
    - ampliacion de trazas en test_keyword_scoring_empty_chunks_keeps_probabilistic_trace
  - app/tests/test_settings_security.py
    - test_rejects_invalid_qlm_smoothing
    - test_rejects_invalid_qlm_dirichlet_mu
    - test_rejects_invalid_qlm_jm_lambda
    - test_rejects_invalid_qlm_blend
- Comandos ejecutados:
  - ./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py (OK)
  - ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py app/tests/test_evaluate_rag_retrieval.py -o addopts="" (OK)
  - ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "uses_rag_when_enabled" -o addopts="" (OK)

## TM-157 - Plan de validacion ejecutado

- Verificar clasificador Naive Bayes (multinomial/bernoulli) con smoothing y trazas operativas.
- Verificar rerank de dominio en chat cuando la capa matematica esta incierta.
- Verificar validaciones de settings NB.

Resultados:
- Tests nuevos/actualizados:
  - app/tests/test_clinical_naive_bayes_service.py
    - test_naive_bayes_multinomial_prioritizes_oncology_query
    - test_naive_bayes_trace_contains_operational_fields
  - app/tests/test_clinical_chat_operational.py
    - test_chat_domain_rerank_uses_naive_bayes_when_math_uncertain
  - app/tests/test_settings_security.py
    - test_rejects_invalid_nb_model
    - test_rejects_invalid_nb_alpha
    - test_rejects_invalid_nb_min_confidence
    - test_rejects_invalid_nb_feature_method
    - test_rejects_invalid_nb_max_features
- Comandos ejecutados:
  - ./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/clinical_naive_bayes_service.py app/services/clinical_chat_service.py app/services/__init__.py app/tests/test_clinical_naive_bayes_service.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py (OK)
  - ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_naive_bayes_service.py -o addopts="" (OK)
  - ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "test_chat_domain_rerank_uses_naive_bayes_when_math_uncertain" -o addopts="" (OK)
  - ./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -k "nb_ or naive_bayes or invalid_nb" -o addopts="" (OK)
## TM-158 - Plan de validacion ejecutado

- Verificar metricas de clasificacion por clase y agregados macro/micro.

Resultados:
- Tests nuevos/actualizados:
  - app/tests/test_clinical_naive_bayes_service.py
    - test_naive_bayes_evaluation_supports_macro_and_micro_averaging
- Comandos ejecutados:
  - ./venv/Scripts/python.exe -m ruff check app/services/clinical_naive_bayes_service.py app/tests/test_clinical_naive_bayes_service.py (OK)
  - ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_naive_bayes_service.py -o addopts="" (OK)
## TM-159 - Plan de validacion ejecutado

- Verificar clasificacion vectorial Rocchio/kNN y trazas operativas.
- Verificar rerank de dominio en chat bajo incertidumbre matematica.
- Verificar validaciones de settings vectoriales.

Resultados:
- Tests nuevos/actualizados:
  - app/tests/test_clinical_vector_classification_service.py
    - test_vector_rocchio_prioritizes_oncology_query
    - test_vector_knn_prioritizes_nephrology_query
    - test_vector_evaluation_includes_confusion_matrix_and_macro_micro
  - app/tests/test_clinical_chat_operational.py
    - test_chat_domain_rerank_uses_vector_when_math_uncertain
  - app/tests/test_settings_security.py
    - test_rejects_invalid_vector_method
    - test_rejects_invalid_vector_k
    - test_rejects_invalid_vector_min_confidence
- Comandos ejecutados:
  - ./venv/Scripts/python.exe -m ruff check app/services/clinical_vector_classification_service.py app/services/clinical_chat_service.py app/services/__init__.py app/core/config.py app/tests/test_clinical_vector_classification_service.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py (OK)
  - ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_vector_classification_service.py -o addopts="" (OK)
  - ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "vector_when_math_uncertain" -o addopts="" (OK)
  - ./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -k "vector_" -o addopts="" (OK)
## TM-160 - Plan de validacion ejecutado

- Verificar clasificador SVM de dominio y trazas operativas.
- Verificar rerank en chat cuando la capa matematica esta incierta.
- Verificar validaciones de settings SVM de dominio.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_clinical_svm_domain_service.py`
    - `test_svm_domain_prioritizes_oncology_query`
    - `test_svm_domain_trace_contains_margin_and_hinge`
    - `test_svm_domain_evaluation_includes_confusion_matrix_and_macro_micro`
  - `app/tests/test_clinical_chat_operational.py`
    - `test_chat_domain_rerank_uses_svm_domain_when_math_uncertain`
  - `app/tests/test_settings_security.py`
    - validaciones `svm_domain_*`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/clinical_svm_domain_service.py app/tests/test_clinical_svm_domain_service.py app/tests/test_clinical_chat_operational.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_svm_domain_service.py app/tests/test_clinical_chat_operational.py -k "svm_domain" -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -k "svm_domain" -o addopts=""` (OK)

## TM-161 - Plan de validacion ejecutado

- Verificar clustering plano (k-means + EM) y trazas `cluster_*`.
- Verificar rerank por clustering bajo incertidumbre matematica.
- Verificar validaciones de nuevos settings de clustering.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_clinical_flat_clustering_service.py`
    - `test_flat_clustering_prioritizes_oncology_cluster_candidates`
    - `test_flat_clustering_trace_contains_quality_and_model_fields`
    - `test_flat_clustering_evaluation_metrics_are_computed`
  - `app/tests/test_clinical_chat_operational.py`
    - `test_chat_domain_rerank_uses_cluster_when_math_uncertain`
  - `app/tests/test_settings_security.py`
    - validaciones `cluster_*`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/clinical_flat_clustering_service.py app/services/clinical_chat_service.py app/services/__init__.py app/core/config.py app/tests/test_clinical_flat_clustering_service.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_flat_clustering_service.py app/tests/test_clinical_chat_operational.py -k "cluster" -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -k "cluster" -o addopts=""` (OK)

## TM-162 - Plan de validacion ejecutado

- Verificar servicio de clustering jerarquico (HAC/divisive/buckshot) y trazas `hcluster_*`.
- Verificar rerank por clustering jerarquico bajo incertidumbre matematica.
- Verificar validaciones de settings `hcluster_*`.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_clinical_hierarchical_clustering_service.py`
    - `test_hierarchical_clustering_prioritizes_oncology_cluster_candidates`
    - `test_hierarchical_clustering_trace_contains_quality_and_model_fields`
    - `test_hierarchical_clustering_evaluation_metrics_are_computed`
  - `app/tests/test_clinical_chat_operational.py`
    - `test_chat_domain_rerank_uses_hcluster_when_math_uncertain`
  - `app/tests/test_settings_security.py`
    - validaciones `hcluster_*`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/clinical_hierarchical_clustering_service.py app/services/clinical_chat_service.py app/services/__init__.py app/core/config.py app/tests/test_clinical_hierarchical_clustering_service.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_hierarchical_clustering_service.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py -k "hcluster or hierarchical" -o addopts=""` (OK)

## TM-163 - Plan de validacion ejecutado

- Verificar scoring LSI y trazabilidad en retriever lexical.
- Verificar validaciones de settings `CLINICAL_CHAT_RAG_LSI_*`.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_rag_retriever.py`
    - `test_keyword_scoring_method_includes_lsi_when_enabled`
  - `app/tests/test_settings_security.py`
    - validaciones `lsi_*`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/core/config.py app/tests/test_rag_retriever.py app/tests/test_settings_security.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py app/tests/test_settings_security.py -k "lsi or qlm or bm25 or tfidf" -o addopts=""` (OK)

## TM-164 - Plan de validacion ejecutado

- Verificar filtrado anti-spam en candidatos web de dominios permitidos.
- Verificar deduplicacion por URL canonica y near-duplicate por MinHash.
- Verificar traza de error en fallo de request web.
- Verificar no regresion del flujo e2e de chat.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_clinical_chat_operational.py`
    - `test_web_source_quality_filter_removes_spam_and_near_duplicates`
    - `test_fetch_web_sources_returns_error_trace_when_request_fails`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "web_source_quality_filter or fetch_web_sources_returns_error_trace_when_request_fails" -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "test_chat_e2e_uses_rag_when_enabled" -o addopts=""` (OK)

## TM-165 - Plan de validacion ejecutado

- Verificar normalizacion de URL y limpieza de tracking params.
- Verificar extraccion HTML y filtrado de enlaces por dominio permitido.
- Verificar deteccion near-duplicate por MinHash.
- Verificar roundtrip de checkpoint (save/load).
- Verificar no regresion rapida en chat.

Resultados:
- Tests nuevos:
  - `app/tests/test_web_crawler_service.py`
    - `test_canonicalize_url_strips_tracking_and_fragment`
    - `test_extract_html_payload_keeps_allowed_domain_links`
    - `test_near_duplicate_detection_uses_signature_threshold`
    - `test_checkpoint_roundtrip_restores_frontier_and_stats`
    - `test_priority_prefers_authoritative_domains`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/web_crawler_service.py app/scripts/crawl_clinical_web.py app/tests/test_web_crawler_service.py app/services/__init__.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_web_crawler_service.py -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "test_chat_e2e_uses_rag_when_enabled" -o addopts=""` (OK)

## TM-166 - Plan de validacion ejecutado

- Verificar construccion de snapshot con PageRank global, Topic-PageRank y HITS.
- Verificar scoring runtime de candidatos web usando señales de grafo + anchor text.
- Verificar enriquecimiento del manifiesto de crawler con enlaces/anchors.
- Verificar integracion del blend de link-analysis en ranking final de `web_sources`.
- Verificar validaciones de settings `CLINICAL_CHAT_WEB_LINK_ANALYSIS_*`.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_web_link_analysis_service.py`
    - `test_build_snapshot_computes_topic_pagerank_bias`
    - `test_score_candidates_uses_anchor_relevance_and_hits`
  - `app/tests/test_web_crawler_service.py`
    - ajuste de `test_extract_html_payload_keeps_allowed_domain_links`
    - `test_persist_page_writes_outgoing_edges_and_anchor_text`
  - `app/tests/test_clinical_chat_operational.py`
    - `test_web_source_quality_blends_link_analysis_signal`
  - `app/tests/test_settings_security.py`
    - validaciones `CLINICAL_CHAT_WEB_LINK_ANALYSIS_*`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/web_link_analysis_service.py app/services/web_crawler_service.py app/services/clinical_chat_service.py app/scripts/build_web_link_analysis.py app/tests/test_web_link_analysis_service.py app/tests/test_web_crawler_service.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py app/core/config.py app/services/__init__.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_web_link_analysis_service.py -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_web_crawler_service.py -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "web_source_quality" -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -k "web_link_analysis" -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m app.scripts.build_web_link_analysis --help` (OK)

## TM-167 - Plan de validacion ejecutado

- Verificar que no se haga doble invocacion LLM tras `rag_status=failed_generation`.
- Verificar que RAG conserva `rag_sources` en failed_generation para fallback con evidencia.
- Verificar no regresion del flujo RAG e2e.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_clinical_chat_operational.py`
    - `test_chat_e2e_skips_second_llm_when_rag_failed_generation`
    - `test_rag_orchestrator_keeps_sources_when_generation_fails`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/llm_chat_provider.py app/services/rag_orchestrator.py app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "rag_orchestrator_keeps_sources_when_generation_fails or chat_e2e_skips_second_llm_when_rag_failed_generation" -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "test_chat_e2e_uses_rag_when_enabled" -o addopts=""` (OK)

## TM-168 - Plan de validacion ejecutado

- Verificar que el proveedor LLM prioriza `/api/generate`.
- Verificar no regresion de fallback RAG/LLM en fallo de generacion.
- Verificar no regresion de flujo RAG e2e.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_clinical_chat_operational.py`
    - `test_llm_provider_prefers_ollama_generate_endpoint`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/llm_chat_provider.py app/tests/test_clinical_chat_operational.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "test_llm_provider_prefers_ollama_generate_endpoint or rag_orchestrator_keeps_sources_when_generation_fails or chat_e2e_skips_second_llm_when_rag_failed_generation" -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "test_chat_e2e_uses_rag_when_enabled" -o addopts=""` (OK)

## TM-169 - Plan de validacion ejecutado

- Verificar preferencia de endpoint principal (`generate`).
- Verificar recovery exitoso cuando el intento principal falla por timeout.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_clinical_chat_operational.py`
    - `test_llm_provider_recovers_after_primary_timeout`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/llm_chat_provider.py app/tests/test_clinical_chat_operational.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "test_llm_provider_prefers_ollama_generate_endpoint or test_llm_provider_recovers_after_primary_timeout" -o addopts=""` (OK)

## TM-170 - Plan de validacion operativo

- Comprobar que `phi3:mini` este disponible en Ollama.
- Reiniciar API y validar trazas `llm_enabled/llm_used`.
- Ejecutar benchmark y comparar latencia vs perfil anterior.

Comandos:
- `ollama pull phi3:mini`
- `./venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010`
- `./venv/Scripts/python.exe tmp/run_chat_benchmark.py`
- `./venv/Scripts/python.exe tmp/summarize_chat_benchmark.py`


## TM-171 - Plan de validacion ejecutado

- Verificar fallback extractivo en RAG cuando LLM falla.
- Verificar circuit breaker LLM para evitar timeouts en cadena.
- Verificar no regresion de retrieval tras filtrar chunks sin specialty.
- Verificar ingesta PDF masiva sin caidas por Unicode en consola.

Resultados:
- Tests nuevos/actualizados:
  - `app/tests/test_clinical_chat_operational.py`
    - `test_rag_orchestrator_uses_extractive_fallback_when_generation_fails`
    - `test_llm_provider_circuit_breaker_short_circuits_after_failures`
  - `app/tests/test_rag_orchestrator_optimizations.py`
    - `test_extractive_answer_filters_non_clinical_noise`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/llm_chat_provider.py app/services/rag_orchestrator.py app/services/rag_retriever.py app/services/clinical_chat_service.py app/scripts/ingest_clinical_docs.py app/tests/test_clinical_chat_operational.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_rag_retriever.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "rag_orchestrator_uses_extractive_fallback_when_generation_fails or llm_provider_circuit_breaker_short_circuits_after_failures" -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m app.scripts.ingest_clinical_docs --paths docs/pdf_raw --backfill-specialty --skip-ollama-embeddings` (OK)

## TM-172 - Plan de validacion ejecutado

- Verificar lint del script de ingesta.
- Verificar que la ingesta incremental omite rutas existentes y termina rapido.

Resultados:
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/scripts/ingest_clinical_docs.py` (OK)
  - `./venv/Scripts/python.exe -m app.scripts.ingest_clinical_docs --paths docs/pdf_raw --backfill-specialty` (OK)

## TM-173 - Plan de validacion ejecutado

- Verificar lint de archivos tocados.
- Verificar budget de latencia en RAG y fallback extractivo cuando no hay margen para LLM.
- Verificar no regresion en provider LLM (preferencia endpoint/fallback/circuit breaker).
- Verificar validaciones de settings.

Resultados:
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/llm_chat_provider.py app/services/rag_orchestrator.py app/schemas/clinical_chat.py app/tests/test_rag_orchestrator_optimizations.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "llm_provider_build_chat_messages_respects_token_budget or llm_provider_prefers_ollama_generate_endpoint or llm_provider_recovers_after_primary_timeout or llm_provider_circuit_breaker_short_circuits_after_failures" -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -o addopts=""` (OK)

## TM-174 - Plan de validacion ejecutado

- Verificar lint de config/orchestrator.
- Verificar tests de optimizacion RAG y no-regresion de provider/settings.
- Verificar evaluacion retrieval baseline sin degradacion material.

Resultados:
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/rag_orchestrator.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "llm_provider_build_chat_messages_respects_token_budget or llm_provider_prefers_ollama_generate_endpoint or llm_provider_recovers_after_primary_timeout or llm_provider_circuit_breaker_short_circuits_after_failures" -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m app.scripts.evaluate_rag_retrieval --dataset tmp/rag_eval.jsonl --k 8` (OK)

## TM-175 - Plan de validacion ejecutado

- Verificar lint en config/orchestrator/tests.
- Verificar tests de optimizaci?n RAG.
- Verificar validaci?n global de settings.
- Verificar retrieval eval de control.

Resultados:
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/rag_orchestrator.py app/tests/test_rag_orchestrator_optimizations.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m app.scripts.evaluate_rag_retrieval --dataset tmp/rag_eval.jsonl --k 8` (OK)


## TM-176 - Plan de validacion ejecutado

- Verificar lint de archivos tocados.
- Verificar que no se invoque segundo pase LLM en `failed_retrieval`.
- Verificar no-regresion de tests de optimizacion RAG/settings.

Resultados:
- Comandos ejecutados:
  - pendiente
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/clinical_chat_service.py app/core/config.py app/tests/test_clinical_chat_operational.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "failed_retrieval or failed_generation" -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""` (OK)

## TM-177 - Plan de validacion ejecutado

- Verificar lint de archivos tocados.
- Verificar reparacion evidence-first cuando calidad final es degraded.
- Verificar no-regresion de settings y optimizaciones RAG.

Resultados:
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/clinical_chat_service.py app/tests/test_clinical_chat_operational.py app/core/config.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py::test_chat_e2e_repairs_degraded_answer_with_evidence_first -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "failed_retrieval or failed_generation" -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py app/tests/test_rag_orchestrator_optimizations.py -o addopts=""` (OK)

## TM-178 - Plan de validacion ejecutado

- Verificar lint y compilacion de cambios.
- Verificar priorizacion de fuentes por score en RAG.
- Verificar fallback quality/evidence no roto.
- Verificar benchmark summary con p95 correcto y gate automatico de aceptacion.

Resultados:
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_orchestrator.py app/services/clinical_chat_service.py app/tests/test_rag_orchestrator_optimizations.py tmp/summarize_chat_benchmark.py tmp/check_acceptance.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py::test_build_rag_sources_prioritizes_high_score_before_source_type -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "quality_repair or failed_retrieval" -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m py_compile app/services/clinical_chat_service.py app/services/rag_orchestrator.py tmp/summarize_chat_benchmark.py tmp/check_acceptance.py` (OK)
  - `./venv/Scripts/python.exe tmp/summarize_chat_benchmark.py` (OK)
  - `./venv/Scripts/python.exe tmp/check_acceptance.py` (FALLA esperada por no cumplir umbrales de calidad/p95 actuales)

## TM-179 - Plan de validacion ejecutado

- Verificar lint de config y scripts benchmark.
- Verificar no-regresion de settings y optimizaciones RAG.

Resultados:
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/core/config.py tmp/summarize_chat_benchmark.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py app/tests/test_rag_orchestrator_optimizations.py -o addopts=""` (OK)

## TM-180 - Plan de validacion ejecutado

- Verificar lint de provider/config/tests.
- Verificar tests de provider alternativo y parseo respuesta.

Resultados:
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/llm_chat_provider.py app/tests/test_settings_security.py app/tests/test_clinical_chat_operational.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py app/tests/test_clinical_chat_operational.py -k "llama_cpp or parse_ollama_payload_supports_sse_data_lines or llm_provider_prefers_ollama_generate_endpoint" -o addopts=""` (OK)

## TM-181 (validacion minima)

- Verificar parseo de payload OpenAI-compatible de `llama.cpp`:
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py::test_extract_llama_cpp_answer_openai_compatible_payload -o addopts=""`
- Verificar settings para proveedor `llama_cpp`:
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py::test_allows_llama_cpp_provider -o addopts=""`

## TM-183 (pruebas)

- API async enqueue:
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_care_tasks_api.py::test_create_care_task_chat_message_async_enqueues_job -o addopts=""`
- API async status completed:
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_care_tasks_api.py::test_get_care_task_chat_message_async_status_returns_completed_payload -o addopts=""`
- API async status not-found:
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_care_tasks_api.py::test_get_care_task_chat_message_async_status_returns_404_for_unknown_job -o addopts=""`

- Resultado TM-138:

  - Objetivo: reducir variabilidad de latencia y reforzar fallback seguro sin romper endpoints.

  - Validacion prevista:

    - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/llm_chat_provider.py app/services/rag_gatekeeper.py app/services/rag_orchestrator.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_clinical_chat_operational.py app/tests/test_settings_security.py`

    - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""`

    - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "llm_provider_build_chat_messages_respects_token_budget" -o addopts=""`

    - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -k "invalid_llm_context_utilization_ratio or invalid_simple_route_max_chunks_vs_hard_limit" -o addopts=""`

  - Resultado ejecutado:

    - `ruff`: OK (sin errores).
    - `pytest app/tests/test_rag_orchestrator_optimizations.py`: 10 passed.
    - `pytest app/tests/test_clinical_chat_operational.py -k llm_provider_build_chat_messages_respects_token_budget`: 1 passed.
    - `pytest app/tests/test_settings_security.py -k "invalid_llm_context_utilization_ratio or invalid_simple_route_max_chunks_vs_hard_limit"`: 2 passed.
    - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -o addopts=""` (77 passed)
    - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "llm_provider" -o addopts=""` (4 passed)

## TM-184 - Plan de validacion ejecutado

- Verificar lint de archivos tocados.
- Verificar modo extractivo forzado (sin invocacion LLM) y traza de skip explicita.
- Verificar reintento de retrieval sin filtro de especialidad cuando el primer intento queda vacio.
- Verificar no-regresion en skip de segundo pase LLM en casos `failed_retrieval/failed_generation`.

Resultados:
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/rag_orchestrator.py app/services/clinical_chat_service.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_clinical_chat_operational.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "force_extractive_only or rag_failed_retrieval or rag_failed_generation" -o addopts=""` (OK)

## TM-185 - Plan de validacion ejecutado

- Validar lint de retriever y tests.
- Validar fallback relajado en consulta natural.
- Validar no regresion en consulta booleana explicita.

Resultados:
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_retriever.py app/tests/test_rag_retriever.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_retriever.py -k "fetch_candidate_chunks_relaxes_non_explicit_boolean_when_intersection_is_empty or fetch_candidate_chunks_keeps_strict_no_match_for_explicit_boolean" -o addopts=""` (2 passed)
  - Verificacion manual local de retrieval:
    - query 1/2/5 del benchmark devuelven chunks con `candidate_strategy=fts_boolean_relaxed_union`.

## TM-186 - Plan de validacion ejecutado

- Validar lint de config/orchestrator/tests.
- Validar tests de no-regresion de orquestador.
- Validar reglas nuevas de settings para QA shortcut.
- Smoke local de matching QA en BD real.

Resultados:
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/rag_orchestrator.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""` (14 passed)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -k "qa_shortcut" -o addopts=""` (2 passed)
  - Smoke local `_match_precomputed_qa_chunks(...)` sobre 3 queries operativas (hit parcial observado, sin errores).

## TM-187 - Plan de validacion ejecutado

- Verificar no-regresion de orchestrator RAG (QA shortcut, ruido, fallback de dominio).
- Verificar validaciones de settings para parser PDF `pypdf|mineru`.
- Verificar chunking y regeneracion de preguntas no-placeholder.
- Verificar parser PDF configurable y fallback fail-open/fail-closed.

Resultados:
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""` (16 passed)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -o addopts=""` (81 passed)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_ingest_clinical_docs_script.py app/tests/test_chunking.py app/tests/test_pdf_parser_service.py app/tests/test_document_ingestion_service.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""` (108 passed)
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_orchestrator.py app/scripts/ingest_clinical_docs.py app/tests/test_ingest_clinical_docs_script.py app/services/pdf_parser_service.py app/services/document_ingestion_service.py app/tests/test_pdf_parser_service.py app/tests/test_chunking.py -q` (OK)

## TM-188 - Plan de validacion ejecutado

- Verificar lint en parser/ingesta/chunking/config/tests.
- Verificar parser MinerU fail-open y filtrado de artefactos repetidos.
- Verificar chunking tipado para bloques preparseados.
- Verificar validaciones de settings PDF nuevos.

Resultados:
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/pdf_parser_service.py app/services/document_ingestion_service.py app/core/chunking.py app/core/config.py app/scripts/ingest_clinical_docs.py app/tests/test_pdf_parser_service.py app/tests/test_document_ingestion_service.py app/tests/test_chunking.py app/tests/test_settings_security.py -q` (OK)
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_pdf_parser_service.py app/tests/test_document_ingestion_service.py app/tests/test_chunking.py app/tests/test_settings_security.py app/tests/test_ingest_clinical_docs_script.py -o addopts=""` (97 passed)

## TM-189 - Plan de validacion ejecutado

- Alcance validado:
  - `app/scripts/ingest_clinical_docs.py`
  - `app/scripts/evaluate_rag_retrieval.py`
  - `app/tests/test_ingest_clinical_docs_script.py`
  - `app/tests/test_evaluate_rag_retrieval.py`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/scripts/ingest_clinical_docs.py app/scripts/evaluate_rag_retrieval.py app/tests/test_ingest_clinical_docs_script.py app/tests/test_evaluate_rag_retrieval.py -q`
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_ingest_clinical_docs_script.py app/tests/test_evaluate_rag_retrieval.py -o addopts=""`
- Resultado:
  - `15 passed`.

## TM-190 - Plan de validacion ejecutado

- Lint:
  - `./venv/Scripts/python.exe -m ruff check app/services/clinical_chat_service.py app/services/rag_orchestrator.py app/services/rag_retriever.py -q`
- Tests:
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""`
- Benchmark:
  - `./venv/Scripts/python.exe tmp/run_chat_benchmark.py`
  - `./venv/Scripts/python.exe tmp/summarize_chat_benchmark.py`
  - `./venv/Scripts/python.exe tmp/check_acceptance.py`
  - Resultado final: `BENCHMARK OK - criterios cumplidos.`

## TM-191 - Plan de validacion ejecutado

- `./venv/Scripts/python.exe -m ruff check app/services/rag_orchestrator.py app/services/rag_retriever.py app/services/clinical_chat_service.py -q`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py -o addopts=""`
- Benchmark E2E:
  - `./venv/Scripts/python.exe tmp/run_chat_benchmark.py`
  - `./venv/Scripts/python.exe tmp/summarize_chat_benchmark.py`
  - `./venv/Scripts/python.exe tmp/check_acceptance.py`
  - Resultado: `BENCHMARK OK` y p95 por debajo del umbral.

- Resultado TM-192:
  - Respuestas de chat no exponen endpoints internos ni comandos de backend.
  - Validacion: .
    venv\Scripts\python.exe -m ruff check app/services/clinical_chat_service.py app/services/rag_orchestrator.py

## TM-193 - Plan de validacion ejecutado

- `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/elastic_retriever.py app/services/rag_orchestrator.py app/tests/test_settings_security.py app/tests/test_clinical_chat_operational.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_settings_security.py -o addopts=""`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py -k "elastic_backend or falls_back_to_legacy_when_elastic_empty" -o addopts=""`
- `./venv/Scripts/python.exe -m ruff check app/scripts/sync_chunks_to_elastic.py app/tests/test_sync_chunks_to_elastic_script.py`
- `./venv/Scripts/python.exe -m pytest -q app/tests/test_sync_chunks_to_elastic_script.py -o addopts=""`

## TM-199 - Plan de validacion ejecutado

- Alcance validado:
  - `app/core/config.py`
  - `app/services/rag_orchestrator.py`
  - `app/services/clinical_chat_service.py`
  - `app/tests/test_rag_orchestrator_optimizations.py`
  - `app/tests/test_settings_security.py`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/clinical_chat_service.py app/services/rag_orchestrator.py app/core/config.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py`
  - `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
- Resultado:
  - `ruff`: OK.
  - `pytest`: `113 passed`.

## TM-200 - Plan de validacion ejecutado

- Alcance validado:
  - `app/core/config.py`
  - `app/services/rag_orchestrator.py`
  - `app/services/rag_prompt_builder.py`
  - `app/tests/test_rag_orchestrator_optimizations.py`
  - `app/tests/test_settings_security.py`
- Comandos ejecutados:
  - `./venv/Scripts/python.exe -m ruff check app/services/rag_orchestrator.py app/services/rag_prompt_builder.py app/core/config.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py`
  - `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
- Resultado:
  - `ruff`: OK.
  - `pytest`: `122 passed`.


- Resultado TM-201:

  - Backend RAG optimizado para portatil/local:
    - modo fact-only (sin segundo pase LLM en chat),
    - early-goal test en orquestador RAG para salida extractiva directa,
    - cache de consultas con TTL + poda por subset para evitar recalculo.
  - Validacion:
    - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/rag_orchestrator.py app/services/clinical_chat_service.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py`
    - `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
    - `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`

- Resultado TM-202:

  - RAG con capa de coherencia discursiva local:
    - clasificacion heuristica `nucleus/satellite` (RST-like),
    - enfoque de entidad saliente (centering theory),
    - cohesión lexical + LCD local con discriminacion de orden de oraciones,
    - reranking y filtrado de chunks con trazas `rag_discourse_*`.
  - Validacion:
    - `./venv/Scripts/python.exe -m ruff check app/core/config.py app/services/rag_orchestrator.py app/services/clinical_chat_service.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py`
    - `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`

- Resultado TM-203:

  - Algoritmos explicitamente implementados y usados en runtime del chat:
    - `EDU segmentation`,
    - `TextTiling` (similitud coseno entre ventanas vecinas),
    - `Lexical chaining`,
    - `LCD` con operaciones vectoriales (`concat`, `diff`, `|diff|`, `prod`),
    - `Entity Grid` para continuidad/shift de entidades.
  - Integracion:
    - reranking discursivo de chunks en `RAGOrchestrator` antes de ensamblado final.
    - trazabilidad en `rag_discourse_top_texttiling`, `rag_discourse_top_lexical_chain`, `rag_discourse_top_lsa`, `rag_discourse_top_entity_grid`.
  - Validacion:
    - `./venv/Scripts/python.exe -m ruff check app/services/rag_orchestrator.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py`
    - `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`
    - `$env:DEBUG='false'; ./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_chat_operational.py app/tests/test_rag_orchestrator_optimizations.py app/tests/test_settings_security.py -o addopts=""`

