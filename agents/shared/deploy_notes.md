# Notas de Despliegue

## Estado actual

- Ejecucion local con `uvicorn`.
- MCP local en `stdio`.
- Migraciones controladas por Alembic (`alembic upgrade head`).
- Pipeline CI base activo en GitHub Actions (`.github/workflows/ci.yml`).
- Entorno Docker Compose operativo (`docker-compose.yml` + `docker/Dockerfile`).
- Config por entorno base definida (`.env.example` y `.env.docker`).
- Endpoint de metricas Prometheus disponible en `/metrics`.
- Prometheus local integrado en Compose (`http://localhost:9090`).
- Grafana local integrado en Compose (`http://localhost:3000`).
- Login con proteccion anti brute force activo en API.
- Metricas operativas de agentes exportadas en `/metrics` y paneles en dashboard Grafana.
- Reglas de alerta baseline para agentes cargadas en Prometheus (`ops/prometheus/alerts.yml`).
- Alertmanager integrado en Compose para ruteo de alertas (`http://localhost:9093`).
- Triaje directo de `CareTask` activo en `POST /api/v1/care-tasks/{id}/triage` con trazabilidad en `agent_runs/agent_steps`.
- Aprobacion humana de triaje activa en `POST /api/v1/care-tasks/{id}/triage/approve` con persistencia en `care_task_triage_reviews`.
- Contexto clinico-operativo disponible en `GET /api/v1/clinical-context/*` para prompts, frontend y pruebas.
- Catalogo Manchester de niveles/SLA disponible en `GET /api/v1/clinical-context/triage-levels/manchester`.
- Auditoria de desviacion de triaje disponible en `POST/GET /api/v1/care-tasks/{id}/triage/audit`.
- Metricas de auditoria expuestas en `/metrics`: `triage_audit_*`.
- Chat clinico-operativo disponible en:
  - `POST /api/v1/care-tasks/{id}/chat/messages`
  - `GET /api/v1/care-tasks/{id}/chat/messages`
  - `GET /api/v1/care-tasks/{id}/chat/memory`
- Chat clinico-operativo reforzado con:
  - modo por especialidad autenticada (`users.specialty`),
  - continuidad longitudinal por paciente (`care_tasks.patient_reference`),
  - trazabilidad de fuentes internas y web por mensaje.
- Interrogatorio clinico activo opcional (TM-126):
  - activacion por request en `POST /care-tasks/{id}/chat/messages`:
    - `enable_active_interrogation=true`
    - `interrogation_max_turns`
    - `interrogation_confidence_threshold`
  - en incertidumbre alta (dominios soportados), el primer turno puede ser pregunta de aclaracion.
- Psicologia de decision en chat (TM-127):
  - capa local sin dependencias externas de pago.
  - agrega trazas de riesgo perceptual/decision en `interpretability_trace`:
    - `prospect_*` y `fechner_*`.
  - puede reforzar texto de cierre operativo en fallback clinico con marco de riesgo.
- Evidencia local adjunta en chat (TM-128):
  - request `POST /care-tasks/{id}/chat/messages` acepta `local_evidence` (max 5).
  - soporte de modalidad: `note|report|pdf|image|ehr_structured|lab_panel`.
  - la evidencia se integra como `knowledge_sources` (`type=local_evidence`) y trazas:
    - `local_evidence_items`
    - `local_evidence_modalities`.
- Ingesta documental PDF (TM-129):
  - `app.scripts.ingest_clinical_docs` ahora procesa `.pdf` multipagina.
  - dependencia local requerida: `pypdf`.
  - flujo: depositar PDFs en `docs/pdf_raw/` y ejecutar ingesta con `--paths docs/pdf_raw`.
- Motor logico clinico determinista (TM-130):
  - servicio: `app/services/clinical_logic_engine_service.py`.
  - integrado en `ClinicalChatService.create_message` antes de respuesta final.
  - nuevas trazas: `logic_*` en `interpretability_trace`.
  - nuevas salidas fallback: bloque "logico formal" con reglas activadas y alertas de consistencia.
- Logica formal extendida (TM-131):
  - firma estructural del plan con codificacion tipo Godel y verificacion de roundtrip.
  - estado de consistencia formal (`consistent|inconsistent|insufficient_evidence`).
  - abstencion automatica por evidencia insuficiente/inconsistente, con fallback estructurado seguro.
  - trazas nuevas: `logic_consistency_status`, `logic_abstention_*`, `logic_godel_*`, `logic_beta_signature`.
- Contratos operativos por dominio (TM-132):
  - nuevo servicio `app/services/clinical_protocol_contracts_service.py`.
  - cobertura inicial: `nephrology` y `gynecology_obstetrics`.
  - añade trazas `contract_*` y bloque de contrato en fallback clinico.
  - puede forzar fallback estructurado si faltan datos criticos del contrato.
- Capa matematica local para inferencia de similitud (TM-133):
  - nuevo servicio `app/services/clinical_math_inference_service.py`.
  - combina coseno + L2 + posterior Bayes sobre dominios ya enrutados.
  - añade trazas `math_*` y bloque matematico en fallback clinico.
  - sin migraciones ni dependencias de pago.
- Extension de enrutado matematico (TM-134):
  - permite reordenar `matched_domains` con `math_top_domain` cuando la confianza es suficiente.
  - expone incertidumbre matematica (`math_margin_top2`, `math_entropy`, `math_uncertainty_level`) para auditoria.
- Curacion de fuentes oficiales para RAG:
  - documento base: `docs/86_fuentes_oficiales_sarampion_tosferina.md`
  - ingesta puntual: `.\venv\Scripts\python.exe -m app.scripts.ingest_clinical_docs --paths docs/86_fuentes_oficiales_sarampion_tosferina.md`
- Endpoints de chat ahora requieren autenticacion `Bearer`.
- Workflow de chat trazable en `agent_runs/agent_steps`:
  - `workflow_name=care_task_clinical_chat_v1`
- Persistencia de memoria conversacional:
  - tabla `care_task_chat_messages` (requiere `alembic upgrade head`).
- Migracion requerida para TM-095:
  - `e8a1c4b7d552_add_chat_specialty_patient_context_fields.py`
  - agrega columnas en `users`, `care_tasks` y `care_task_chat_messages`.
- Migracion requerida para TM-096:
  - `c2f4a9e1b771_add_clinical_knowledge_sources_tables.py`
  - crea tablas `clinical_knowledge_sources` y `clinical_knowledge_source_validations`.
- Settings operativos nuevos:
  - `CLINICAL_CHAT_WEB_ENABLED` (default `true`)
  - `CLINICAL_CHAT_WEB_TIMEOUT_SECONDS` (default `6`)
  - `CLINICAL_CHAT_WEB_STRICT_WHITELIST` (default `true`)
  - `CLINICAL_CHAT_WEB_ALLOWED_DOMAINS` (CSV)
  - `CLINICAL_CHAT_REQUIRE_VALIDATED_INTERNAL_SOURCES` (default `true`)
- API de curacion de conocimiento disponible en:
  - `POST /api/v1/knowledge-sources/`
  - `GET /api/v1/knowledge-sources/`
  - `POST /api/v1/knowledge-sources/{id}/seal`
  - `GET /api/v1/knowledge-sources/{id}/validations`
  - `GET /api/v1/knowledge-sources/trusted-domains`
- Playbook operativo para uso en hospital:
  - `docs/90_playbook_curacion_fuentes_clinicas.md`
- Frontend MVP para chat clinico disponible en `frontend/`:
  - `npm install`
  - `npm run dev` (Vite en `http://127.0.0.1:5173`)
- Frontend v2 incorpora:
  - selector de herramientas (`chat`, `medication`, `cases`, `treatment`, `deep_search`, `images`)
  - selector de modo de conversacion (`auto`, `general`, `clinical`)
  - soporte de conversacion libre con creacion automatica de `CareTask`
- Motor neuronal local opcional de chat:
  - proveedor: `ollama` (`app/services/llm_chat_provider.py`)
  - activar en `.env`: `CLINICAL_CHAT_LLM_ENABLED=true`
  - configurar endpoint/modelo:
    - `CLINICAL_CHAT_LLM_BASE_URL=http://127.0.0.1:11434`
    - `CLINICAL_CHAT_LLM_MODEL=phi3:mini`
  - si el proveedor no responde, el sistema cae a fallback rule-based.
- Hardening de calidad conversacional (TM-123):
  - ciclo de reparacion `draft->verify->rewrite` en respuestas clinicas con fuentes internas.
  - rechazo automatico de salidas LLM genericas tipo "no puedo proporcionar asesoramiento".
  - rechazo automatico de salidas truncadas antes de entregar respuesta final.
- Hardening adicional ruta RAG (TM-124):
  - la respuesta producida por RAG hereda `llm_trace` y pasa por los mismos quality gates.
  - evita que salidas RAG cortadas/genericas se entreguen sin fallback estructurado.
- Hardening adicional de salida (TM-125):
  - bloqueo de placeholders genericos (`[Informacion ...]`) y parentesis no balanceados en respuesta clinica.
  - fallback forzado cuando `rag_validation_status=warning`.
- CORS base actualizado para frontend local:
  - `http://localhost:5173` y `http://127.0.0.1:5173` incluidos por defecto en settings y `.env.example`/`.env.docker`.
- Protocolo respiratorio operativo disponible en `POST /api/v1/care-tasks/{id}/respiratory-protocol/recommendation`.
- Metricas respiratorias expuestas en `/metrics`: `respiratory_protocol_runs_total` y `respiratory_protocol_runs_completed_total`.
- Humanizacion pediatrica operativa disponible en `POST /api/v1/care-tasks/{id}/humanization/recommendation`.
- Metricas de humanizacion expuestas en `/metrics`: `pediatric_humanization_runs_total` y `pediatric_humanization_runs_completed_total`.
- Screening avanzado operativo disponible en `POST /api/v1/care-tasks/{id}/screening/recommendation`.
- Metricas de screening en `/metrics`: `advanced_screening_runs_total`, `advanced_screening_runs_completed_total`, `advanced_screening_alerts_generated_total`, `advanced_screening_alerts_suppressed_total`.
- Auditoria de screening disponible en `POST/GET /api/v1/care-tasks/{id}/screening/audit`.
- Resumen de auditoria screening en `GET /api/v1/care-tasks/{id}/screening/audit/summary`.
- Metricas de calidad de screening en `/metrics`: `screening_audit_*` y `screening_rule_*_match_rate_percent`.
- Soporte RX torax operativo disponible en `POST /api/v1/care-tasks/{id}/chest-xray/interpretation-support`.
- Metricas RX torax en `/metrics`: `chest_xray_support_runs_total`, `chest_xray_support_runs_completed_total`, `chest_xray_support_critical_alerts_total`.
- Soporte diferencial de pitiriasis disponible en `POST /api/v1/care-tasks/{id}/pityriasis-differential/recommendation`.
- Metricas pitiriasis en `/metrics`: `pityriasis_differential_runs_total`, `pityriasis_differential_runs_completed_total`, `pityriasis_differential_red_flags_total`.
- Soporte diferencial acne/rosacea disponible en `POST /api/v1/care-tasks/{id}/acne-rosacea/recommendation`.
- Metricas acne/rosacea en `/metrics`: `acne_rosacea_differential_runs_total`, `acne_rosacea_differential_runs_completed_total`, `acne_rosacea_differential_red_flags_total`.
- Soporte operativo de trauma disponible en `POST /api/v1/care-tasks/{id}/trauma/recommendation`.
- Metricas trauma en `/metrics`: `trauma_support_runs_total`, `trauma_support_runs_completed_total`, `trauma_support_critical_alerts_total`.
- Soporte operativo critico transversal disponible en `POST /api/v1/care-tasks/{id}/critical-ops/recommendation`.
- Metricas critical-ops en `/metrics`: `critical_ops_support_runs_total`, `critical_ops_support_runs_completed_total`, `critical_ops_support_critical_alerts_total`.
- Soporte operativo neurologico disponible en `POST /api/v1/care-tasks/{id}/neurology/recommendation`.
- Metricas neurologia en `/metrics`: `neurology_support_runs_total`, `neurology_support_runs_completed_total`, `neurology_support_critical_alerts_total`.
- Soporte operativo gastro-hepato disponible en `POST /api/v1/care-tasks/{id}/gastro-hepato/recommendation`.
- Metricas gastro-hepato en `/metrics`: `gastro_hepato_support_runs_total`, `gastro_hepato_support_runs_completed_total`, `gastro_hepato_support_critical_alerts_total`.
- Soporte operativo reuma-inmuno disponible en `POST /api/v1/care-tasks/{id}/rheum-immuno/recommendation`.
- Metricas reuma-inmuno en `/metrics`: `rheum_immuno_support_runs_total`, `rheum_immuno_support_runs_completed_total`, `rheum_immuno_support_critical_alerts_total`.
- Soporte operativo de psiquiatria disponible en `POST /api/v1/care-tasks/{id}/psychiatry/recommendation`.
- Metricas de psiquiatria en `/metrics`: `psychiatry_support_runs_total`, `psychiatry_support_runs_completed_total`, `psychiatry_support_critical_alerts_total`.
- Soporte operativo de hematologia disponible en `POST /api/v1/care-tasks/{id}/hematology/recommendation`.
- Metricas de hematologia en `/metrics`: `hematology_support_runs_total`, `hematology_support_runs_completed_total`, `hematology_support_critical_alerts_total`.
- Soporte operativo de endocrinologia disponible en `POST /api/v1/care-tasks/{id}/endocrinology/recommendation`.
- Metricas de endocrinologia en `/metrics`: `endocrinology_support_runs_total`, `endocrinology_support_runs_completed_total`, `endocrinology_support_critical_alerts_total`.
- Soporte operativo de nefrologia disponible en `POST /api/v1/care-tasks/{id}/nephrology/recommendation`.
- Metricas de nefrologia en `/metrics`: `nephrology_support_runs_total`, `nephrology_support_runs_completed_total`, `nephrology_support_critical_alerts_total`.
- Soporte operativo de neumologia disponible en `POST /api/v1/care-tasks/{id}/pneumology/recommendation`.
- Metricas de neumologia en `/metrics`: `pneumology_support_runs_total`, `pneumology_support_runs_completed_total`, `pneumology_support_critical_alerts_total`.
- Soporte operativo de geriatria disponible en `POST /api/v1/care-tasks/{id}/geriatrics/recommendation`.
- Metricas de geriatria en `/metrics`: `geriatrics_support_runs_total`, `geriatrics_support_runs_completed_total`, `geriatrics_support_critical_alerts_total`.
- Soporte operativo de oncologia disponible en `POST /api/v1/care-tasks/{id}/oncology/recommendation`.
- Metricas de oncologia en `/metrics`: `oncology_support_runs_total`, `oncology_support_runs_completed_total`, `oncology_support_critical_alerts_total`.
- Soporte operativo de anestesiologia/reanimacion disponible en `POST /api/v1/care-tasks/{id}/anesthesiology/recommendation`.
- Metricas de anestesiologia/reanimacion en `/metrics`: `anesthesiology_support_runs_total`, `anesthesiology_support_runs_completed_total`, `anesthesiology_support_critical_alerts_total`.
- Soporte operativo de cuidados paliativos disponible en `POST /api/v1/care-tasks/{id}/palliative/recommendation`.
- Metricas de cuidados paliativos en `/metrics`: `palliative_support_runs_total`, `palliative_support_runs_completed_total`, `palliative_support_critical_alerts_total`.
- Soporte operativo de urologia disponible en `POST /api/v1/care-tasks/{id}/urology/recommendation`.
- Metricas de urologia en `/metrics`: `urology_support_runs_total`, `urology_support_runs_completed_total`, `urology_support_critical_alerts_total`.
- Soporte operativo de oftalmologia disponible en `POST /api/v1/care-tasks/{id}/ophthalmology/recommendation`.
- Metricas de oftalmologia en `/metrics`: `ophthalmology_support_runs_total`, `ophthalmology_support_runs_completed_total`, `ophthalmology_support_critical_alerts_total`.
- Soporte operativo de inmunologia disponible en `POST /api/v1/care-tasks/{id}/immunology/recommendation`.
- Metricas de inmunologia en `/metrics`: `immunology_support_runs_total`, `immunology_support_runs_completed_total`, `immunology_support_critical_alerts_total`.
- Soporte operativo de recurrencia genetica disponible en `POST /api/v1/care-tasks/{id}/genetic-recurrence/recommendation`.
- Metricas de recurrencia genetica en `/metrics`: `genetic_recurrence_support_runs_total`, `genetic_recurrence_support_runs_completed_total`, `genetic_recurrence_support_critical_alerts_total`.
- Soporte operativo de ginecologia y obstetricia disponible en `POST /api/v1/care-tasks/{id}/gynecology-obstetrics/recommendation`.
- Metricas de ginecologia y obstetricia en `/metrics`: `gynecology_obstetrics_support_runs_total`, `gynecology_obstetrics_support_runs_completed_total`, `gynecology_obstetrics_support_critical_alerts_total`.
- Soporte operativo de pediatria y neonatologia disponible en `POST /api/v1/care-tasks/{id}/pediatrics-neonatology/recommendation`.
- Metricas de pediatria y neonatologia en `/metrics`: `pediatrics_neonatology_support_runs_total`, `pediatrics_neonatology_support_runs_completed_total`, `pediatrics_neonatology_support_critical_alerts_total`.
- Soporte operativo de epidemiologia clinica disponible en `POST /api/v1/care-tasks/{id}/epidemiology/recommendation`.
- Metricas de epidemiologia clinica en `/metrics`: `epidemiology_support_runs_total`, `epidemiology_support_runs_completed_total`, `epidemiology_support_critical_alerts_total`.
- Soporte operativo de anisakis disponible en `POST /api/v1/care-tasks/{id}/anisakis/recommendation`.
- Metricas de anisakis en `/metrics`: `anisakis_support_runs_total`, `anisakis_support_runs_completed_total`, `anisakis_support_critical_alerts_total`.
- La salida de trauma incluye `condition_matrix[]` (matriz estructurada por condicion, diagnostico, tratamiento y fuente) para consumo de frontend/auditoria.
- Soporte medico-legal operativo disponible en `POST /api/v1/care-tasks/{id}/medicolegal/recommendation`.
- Extension bioetica pediatrica en medico-legal:
  - conflicto de representacion en menor con riesgo vital
  - alertas de interes superior del menor y deber de proteccion
  - trazabilidad reforzada de estado de necesidad terapeutica
- Salida medico-legal ampliada para frontend/auditoria:
  - `life_preserving_override_recommended`
  - `ethical_legal_basis`
  - `urgency_summary`
- Metricas medico-legales en `/metrics`: `medicolegal_ops_runs_total`, `medicolegal_ops_runs_completed_total`, `medicolegal_ops_critical_alerts_total`.
- Auditoria medico-legal disponible en `POST/GET /api/v1/care-tasks/{id}/medicolegal/audit`.
- Resumen de auditoria medico-legal en `GET /api/v1/care-tasks/{id}/medicolegal/audit/summary`.
- Metricas de calidad medico-legal en `/metrics`: `medicolegal_audit_*`, `medicolegal_rule_*_match_rate_percent`.
- Soporte sepsis operativo disponible en `POST /api/v1/care-tasks/{id}/sepsis/recommendation`.
- Metricas sepsis en `/metrics`: `sepsis_protocol_runs_total`, `sepsis_protocol_runs_completed_total`, `sepsis_protocol_critical_alerts_total`.
- Soporte SCASEST operativo disponible en `POST /api/v1/care-tasks/{id}/scasest/recommendation`.
- Metricas SCASEST en `/metrics`: `scasest_protocol_runs_total`, `scasest_protocol_runs_completed_total`, `scasest_protocol_critical_alerts_total`.
- Auditoria SCASEST disponible en `POST/GET /api/v1/care-tasks/{id}/scasest/audit`.
- Resumen auditoria SCASEST en `GET /api/v1/care-tasks/{id}/scasest/audit/summary`.
- Metricas de calidad SCASEST en `/metrics`: `scasest_audit_*`, `scasest_rule_*_match_rate_percent`.
- Scorecard global de calidad IA disponible en `GET /api/v1/care-tasks/quality/scorecard`.
- Metricas globales de scorecard en `/metrics`: `care_task_quality_audit_*`.
- Alertas SCASEST en Prometheus: `ScasestAuditUnderRateHigh`, `ScasestAuditOverRateHigh`.
- Alertas globales de calidad IA en Prometheus:
  - `CareTaskQualityUnderRateHigh`
  - `CareTaskQualityOverRateHigh`
  - `CareTaskQualityMatchRateLow`
- Script de drill SCASEST para generar escenarios `under/over`: `app/scripts/simulate_scasest_alerts.py`.
- Script de drill global para generar escenarios de calidad IA:
  - `app/scripts/simulate_global_quality_alerts.py`
- Gate de evaluacion continua de calidad IA disponible en:
  - Test suite: `app/tests/test_quality_regression_gate.py`
  - Runner: `app/scripts/run_quality_gate.py`
- Flujo de episodio extremo-a-extremo disponible en `POST/GET /api/v1/emergency-episodes/*`.
- KPI por episodio disponible en `GET /api/v1/emergency-episodes/{id}/kpis`.
- Soporte de riesgo cardiovascular disponible en `POST /api/v1/care-tasks/{id}/cardio-risk/recommendation`.
- Auditoria cardiovascular disponible en `POST/GET /api/v1/care-tasks/{id}/cardio-risk/audit`.
- Resumen auditoria cardiovascular en `GET /api/v1/care-tasks/{id}/cardio-risk/audit/summary`.
- Metricas cardiovasculares en `/metrics`: `cardio_risk_support_*`, `cardio_risk_audit_*`.
- Soporte de reanimacion disponible en `POST /api/v1/care-tasks/{id}/resuscitation/recommendation`.
- Extension obstetrica critica integrada en reanimacion:
  - codigo obstetrico multidisciplinar
  - ventana 4-5 min para histerotomia resucitativa
  - control de compresion aortocava y toxicidad por magnesio
- Terapia electrica integrada en reanimacion:
  - bloque `electrical_therapy_plan` con energia por ritmo
  - bloque `sedoanalgesia_plan` para cardioversion sincronizada
  - bloque `pre_shock_safety_checklist` para seguridad pre-descarga
- Auditoria de reanimacion disponible en `POST/GET /api/v1/care-tasks/{id}/resuscitation/audit`.
- Resumen auditoria de reanimacion en `GET /api/v1/care-tasks/{id}/resuscitation/audit/summary`.
- Metricas de reanimacion en `/metrics`: `resuscitation_protocol_*`, `resuscitation_audit_*`.
- Alertas de reanimacion en Prometheus: `ResuscitationAuditUnderRateHigh`, `ResuscitationAuditOverRateHigh`.
- Drill de reanimacion disponible: `app/scripts/simulate_resuscitation_alerts.py`.
- Runbook de alertas de reanimacion: `docs/59_runbook_alertas_reanimacion.md`.
- Dashboard Grafana actualizado con bloque de reanimacion:
  - `Reanimacion Runs Total`
  - `Reanimacion Under Rate %`
  - `Reanimacion Over Rate %`
  - `Reanimacion Shock Match %`

## Proximo paso recomendado

- Incluir paso de migraciones en arranque de entorno (`alembic upgrade head`).
- Incluir gates de calidad en CI: `ruff`, `black --check`, `mypy`, `pytest`.
- Definir imagen runtime endurecida (usuario no root y reduccion de dependencias build-time).
- Ejecutar TM-038: pivot de dominio a Clinical Ops de forma incremental, sin downtime ni ruptura de API actual.
- Continuar TM-039: castellanizacion por lotes de nombres internos sin romper contratos externos.
- Ejecutar gate de evaluacion continua antes de cada despliegue:
  - `.\venv\Scripts\python.exe app\scripts\run_quality_gate.py`
- Recargar Prometheus tras cambios de alertas:
  - `docker compose restart prometheus`

## Riesgos

- Falta pipeline CI.
- Falta separacion formal por entorno.
- Riesgo de deriva de dominio si se mezcla terminologia `Task` y `CareTask` sin versionado de contrato.

## TM-058 (completado)

- Se agregara endpoint de lectura para scorecard global:
  - `GET /api/v1/care-tasks/quality/scorecard`
- Objetivo operativo:
  - Consultar calidad IA global sin recorrer cuatro summaries por separado.

## TM-059 (completado)

- Objetivo operativo:
  - Monitorizar degradacion de calidad global en Grafana y Prometheus.

## TM-102 (completado)

- Mejora del runtime conversacional local sin pago:
  - proveedor LLM intenta `Ollama /api/chat` con historial corto y fallback a `/api/generate`.
  - continuidad de follow-up por expansion contextual (`query_expanded`) en backend.
- Nuevas variables recomendadas para perfil 16GB:
  - `CLINICAL_CHAT_LLM_NUM_CTX=4096`
  - `CLINICAL_CHAT_LLM_TOP_P=0.9`
- Perfil recomendado (latencia/calidad en 16GB):
  - `CLINICAL_CHAT_LLM_MODEL=phi3:mini` (estable)
  - opcional `qwen2.5:14b` si el equipo mantiene latencia aceptable.



## TM-103 - Notas de despliegue

- Configurar variables LLM en `.env` de runtime con `CLINICAL_CHAT_LLM_ENABLED=true`.
- Verificar proceso `ollama serve` y modelo `phi3:mini` presente (`ollama list`).
- Mantener whitelist web estricta activa para `deep_search`.


## TM-105 - Notas de despliegue

- No requiere migraciones DB ni cambios de endpoints.
- Recomendacion operativa:
  - validar `CLINICAL_CHAT_LLM_BASE_URL` contra instancia Ollama real (`/api/chat`).
  - si existe proxy intermedio, confirmar que no rompe payload JSON y timeout.
- Smoke sugerido post-deploy:
  - enviar un turno de chat y verificar `interpretability_trace` con `llm_used=true` y `llm_endpoint=chat|generate`.


## TM-106 - Notas de despliegue

- No requiere migraciones ni cambios de configuracion.
- Validacion funcional sugerida:
  - enviar `hola, tienes informacion de algunos casos?` y confirmar respuesta conversacional sin blob JSON.
  - enviar consulta clinica concreta y confirmar que mantiene contexto/recomendaciones clinicas.


## TM-107 - Notas de despliegue

- Sin migraciones ni flags nuevos.
- Smoke funcional recomendado:
  - Input: `hola, tienes informacion de algunos casos?`
  - Esperado: respuesta humana con dominios disponibles y repregunta de caso, sin JSON crudo.
  - Verificar traza: `reasoning_threads=intent>context>sources>actions`.


## TM-108 - Notas de despliegue

- Sin migraciones DB.
- Nuevas variables recomendadas en runtime:
  - `CLINICAL_CHAT_LLM_MAX_INPUT_TOKENS=3200`
  - `CLINICAL_CHAT_LLM_PROMPT_MARGIN_TOKENS=256`
- Validaciones post-deploy:
  - enviar consulta con texto largo y verificar trazas:
    - `llm_input_tokens_budget`
    - `llm_input_tokens_estimated`
    - `llm_prompt_truncated`
  - enviar intento de inyeccion (`ignora instrucciones...`) y verificar trazas:
    - `prompt_injection_detected=1`
    - `prompt_injection_signals=...`
  - verificar presencia de `quality_metrics` en response de chat.


## TM-109 - Notas de despliegue

- Sin cambios de runtime productivo, endpoints ni migraciones.
- Cambios orientados a productividad del equipo:
  - `.pre-commit-config.yaml` para staged files.
  - `scripts/dev_workflow.ps1` como entrada unica de comandos locales.
  - `scripts/setup_hooks.ps1` para onboarding reproducible.
- Onboarding recomendado por clon local:
  - `powershell -ExecutionPolicy Bypass -File scripts/setup_hooks.ps1`
- Smoke recomendado:
  - `powershell -ExecutionPolicy Bypass -File scripts/dev_workflow.ps1 -Action test-e2e`

## TM-113 - Notas de despliegue

- Migraciones requeridas:
  - `alembic upgrade head`
- Variables nuevas de runtime para chat RAG:
  - `CLINICAL_CHAT_RAG_ENABLED`
  - `CLINICAL_CHAT_RAG_MAX_CHUNKS`
  - `CLINICAL_CHAT_RAG_VECTOR_WEIGHT`
  - `CLINICAL_CHAT_RAG_KEYWORD_WEIGHT`
  - `CLINICAL_CHAT_RAG_EMBEDDING_MODEL`
  - `CLINICAL_CHAT_RAG_ENABLE_GATEKEEPER`
- Carga inicial recomendada de corpus interno:
  - `python -m app.scripts.ingest_clinical_docs --paths docs agents/shared`
- Smoke funcional recomendado:
  - enviar consulta clinica a `POST /api/v1/care-tasks/{id}/chat/messages`.
  - verificar en `interpretability_trace`:
    - `rag_status=success` cuando hay corpus cargado.
    - `rag_status=failed_retrieval` + fallback cuando no hay chunks.

## TM-114 - Notas de despliegue

- Sin migraciones DB.
- Dependencias opcionales (solo si se activa backend extendido):
  - `pip install -r requirements.optional-rag-guardrails.txt`
- Variables nuevas de runtime:
  - `CLINICAL_CHAT_RAG_RETRIEVER_BACKEND=legacy|llamaindex`
  - `CLINICAL_CHAT_RAG_LLAMAINDEX_CANDIDATE_POOL=120`
  - `CLINICAL_CHAT_GUARDRAILS_ENABLED=true|false`
  - `CLINICAL_CHAT_GUARDRAILS_CONFIG_PATH=app/guardrails`
  - `CLINICAL_CHAT_GUARDRAILS_FAIL_OPEN=true|false`
- Config guardrails incluida por defecto:
  - `app/guardrails/config.yml` (modelo Ollama local).
- Smoke funcional recomendado:
  - con `CLINICAL_CHAT_RAG_RETRIEVER_BACKEND=llamaindex`, enviar consulta clinica y validar traza:
    - `rag_retriever_backend=llamaindex`
    - `llamaindex_available=1` (si dependencias instaladas)
  - si faltan extras/config, validar fallback:
    - `rag_retriever_fallback=legacy_hybrid` o `guardrails_status=fallback_unavailable`
  - con guardrails activo, validar presencia de:
    - `guardrails_status=applied_passthrough|applied_rewrite`

## TM-115 - Notas de despliegue

- Sin migraciones DB.
- Dependencia opcional para backend Chroma:
  - `pip install -r requirements.optional-rag-guardrails.txt`
- Variable nueva:
  - `CLINICAL_CHAT_RAG_CHROMA_CANDIDATE_POOL=200`
- Activacion de backend:
  - `CLINICAL_CHAT_RAG_RETRIEVER_BACKEND=chroma`
- Smoke recomendado:
  - enviar consulta clinica y validar en traza:
    - `rag_retriever_backend=chroma`
    - `chroma_available=1`
  - en ausencia de dependencia o resultado:
    - `rag_retriever_fallback=legacy_hybrid`

## TM-116 - Notas de despliegue

- Sin migraciones DB ni cambios de API.
- Requiere rebuild frontend:
  - `cd frontend && npm run build`
- Smoke UX recomendado:
  - login correcto y carga de historial de casos.
  - envio de consulta y visualizacion de typing + respuesta render progresiva.
  - expansion de `Fuentes y referencias` en una respuesta con RAG.
  - validacion de footer fijo con disclaimer medico.
  - validacion responsive en tablet/desktop.

## TM-118 - Notas de despliegue

- Sin migraciones DB ni flags nuevas obligatorias.
- Impacto operativo:
  - mejor deteccion automatica de consultas clinicas en modo `auto`.
  - mayor robustez contra respuestas clinicas genericas cuando guardrails esta desactivado.
- Smoke recomendado:
  - enviar: `Paciente pediatrico con sospecha de sarampion y triada febril, pasos iniciales`.
  - verificar:
    - respuesta con estructura operativa (pasos + fuentes), no bloque generico.
    - traza incluye `response_mode=clinical`.

## TM-119 - Notas de despliegue

- Sin migraciones DB.
- Recomendacion operativa para curacion progresiva:
  - `python -m app.scripts.ingest_clinical_docs --backfill-specialty`
- Si necesitas incorporar material no clinico para auditoria interna:
  - `python -m app.scripts.ingest_clinical_docs --include-shared --backfill-specialty`
- Smoke recomendado:
  - consulta clinica de dominio (ej. pediatria/oncologia) y validar:
    - `rag_status=success`
    - `domain_search_filtered_out` presente solo cuando se descartaron chunks por especialidad
    - menor presencia de fuentes no clinicas en respuesta.


## TM-138 - Notas de despliegue

- Sin migraciones DB ni cambios de API.
- Capa SVM activa por defecto en runtime del chat clinico (trazabilidad interna).
- Smoke recomendado:
  - enviar consulta con red flags (ej: `oliguria + K 6.2 + QRS ancho`).
  - verificar en `interpretability_trace`:
    - `svm_enabled=1`
    - `svm_class=critical`
    - `svm_priority_score=medium|high`

## TM-139 - Notas de despliegue

- Sin migraciones DB ni cambios de API.
- Capa de riesgo probabilistica activa en runtime del chat clinico.
- Smoke recomendado:
  - consulta: `TA 82/50 + K 6.2 + creatinina 2.1 + oliguria`.
  - validar en `interpretability_trace`:
    - `risk_pipeline_enabled=1`
    - `risk_model_probability` (0..1)
    - `risk_model_priority=medium|high`
    - `risk_model_anomaly_flag=0|1`

## TM-141 - Notas de despliegue

- Sin migraciones DB ni cambios de API.
- Variables nuevas/ajustadas:
  - `CLINICAL_CHAT_RAG_PARALLEL_HYBRID_ENABLED=true|false`
  - `CLINICAL_CHAT_RAG_FAITHFULNESS_MIN_RATIO=0.20` (rango esperado 0..1)
  - preset local recomendado:
    - `CLINICAL_CHAT_LLM_NUM_CTX=3072`
    - `CLINICAL_CHAT_LLM_TIMEOUT_SECONDS=75`
    - `CLINICAL_CHAT_LLM_MAX_INPUT_TOKENS=1200`
    - `CLINICAL_CHAT_LLM_MAX_OUTPUT_TOKENS=320`
- Reinicio requerido tras cambios de `.env`.
- Smoke recomendado:
  - consulta con evidencia recuperable y verificar `hybrid_parallelized=1`.
  - consulta con respuesta fuera de evidencia y verificar riesgo por fidelidad baja en `rag_validation_issues`.

## TM-142 - Notas de despliegue

- Sin migraciones DB ni cambios de API.
- Variables nuevas/ajustadas:
  - `CLINICAL_CHAT_RAG_CONTEXT_MIN_RATIO=0.08` (rango esperado 0..1)
- Cambios operativos:
  - chunking recursivo y overlap real durante ingesta.
  - embeddings largos procesados por ventanas locales (evita caida por contexto en Ollama `/api/embed`).
  - expansion de consulta en retrieval hibrido para mejorar recall sin coste.
  - `ingest_clinical_docs` reconoce por defecto rutas `docs/pdf_raw/<especialidad>/`.
- Reinicio recomendado tras cambios de `.env`.
- Smoke recomendado:
  - reingestar un PDF largo y validar progreso sin errores de contexto en embeddings.
  - enviar consulta clinica ambigua y verificar trazas:
    - `retrieval_query_expanded=1`
    - `retrieval_query_expansion_terms` con terminos medicos
    - `rag_validation_issues` con warning de `context_relevance` solo cuando aplica.

## TM-143 - Notas de despliegue

- Sin migraciones DB ni cambios de API.
- Variables nuevas/ajustadas:
  - `CLINICAL_CHAT_RAG_ADAPTIVE_K_ENABLED=true|false`
  - `CLINICAL_CHAT_RAG_MIN_CHUNKS=3`
  - `CLINICAL_CHAT_RAG_MAX_CHUNKS_HARD=12`
  - `CLINICAL_CHAT_RAG_MMR_ENABLED=true|false`
  - `CLINICAL_CHAT_RAG_MMR_LAMBDA=0.70`
  - `CLINICAL_CHAT_RAG_COMPRESS_CONTEXT_ENABLED=true|false`
  - `CLINICAL_CHAT_RAG_COMPRESS_MAX_CHARS=420`
- Reinicio recomendado tras cambios de `.env`.
- Smoke recomendado:
  - consulta corta de alto riesgo (ej. `K 6.2 con oliguria`) y verificar:
    - `rag_adaptive_k_enabled=1`
    - `rag_adaptive_k_reason=short_query+high_risk`
  - consulta amplia (>18 tokens) y verificar aumento de `rag_adaptive_k_value`.
  - validar compresion:
    - `rag_context_compressed=1`
    - `rag_context_compression_ratio` < `1.0`.
  - validar rerank:
    - `rag_mmr_enabled=1`
    - `rag_mmr_selected` coherente con `rag_chunks_retrieved`.

## TM-144 - Notas de despliegue

- Sin migraciones Alembic en esta fase.
- Variables nuevas:
  - `CLINICAL_CHAT_RAG_FTS_CANDIDATE_ENABLED=true|false`
  - `CLINICAL_CHAT_RAG_FTS_CANDIDATE_POOL=160`
- Comportamiento:
  - primer uso en SQLite intenta bootstrap lazy de FTS5 (`document_chunks_fts` + triggers).
  - bootstrap usa `rebuild` para garantizar indexacion inicial consistente del contenido existente.
  - si FTS5 no esta disponible, fallback automatico a `full_scan`.
- Reinicio recomendado tras cambios en `.env`.
- Smoke recomendado:
  - ejecutar consulta clinica y verificar trazas:
    - `candidate_strategy=fts_postings_boolean` (esperado)
    - o `candidate_strategy=full_scan_fallback` si entorno sin FTS5
    - `candidate_chunks_pool` menor que total de chunks (cuando FTS activo).

## TM-145 - Notas de despliegue

- Sin migraciones Alembic en esta fase.
- Variables nuevas:
  - `CLINICAL_CHAT_RAG_SPELL_CORRECTION_ENABLED=true|false`
  - `CLINICAL_CHAT_RAG_SPELL_MAX_EDIT_DISTANCE=1..3`
- Comportamiento:
  - parser booleano con precedencia y parentesis activo en candidate retrieval.
  - frases entre comillas pasan a FTS como phrase query.
  - spell correction se aplica solo cuando un termino no devuelve postings.
  - `NOT` opera sobre universo acotado por candidate stage para mantener latencia controlada.
- Reinicio recomendado tras cambios en `.env`.
- Smoke recomendado:
  - consulta: `"neutropenia febril" AND oncologia NOT pediatria`
  - verificar trazas:
    - `candidate_boolean_parser=precedence_v1`
    - `candidate_phrase_terms>=1`
    - `candidate_spell_applied>=0`

## TM-146 - Notas de despliegue

- Sin migraciones Alembic en esta fase.
- Variables nuevas:
  - `CLINICAL_CHAT_RAG_SKIP_POINTERS_ENABLED=true|false`
  - `CLINICAL_CHAT_RAG_SKIP_POINTERS_MIN_LIST=16..4096`
- Comportamiento:
  - operador `/k` se interpreta en candidate retrieval como `NEAR(...)`.
  - intersecciones `AND` usan skip pointers cuando ambas listas superan el umbral configurado.
  - expresiones booleanas validas sin match retornan `candidate_strategy=fts_boolean_no_match`.
- Reinicio recomendado tras cambios en `.env`.
- Smoke recomendado:
  - consulta: `"neutropenia febril" /4 oncologia AND NOT pediatria`
  - verificar trazas:
    - `candidate_skip_enabled=1`
    - `candidate_skip_intersections>=0`
    - `candidate_skip_shortcuts>=0`

## TM-147 - Notas de despliegue

- Sin migraciones Alembic en esta fase.
- Variables nuevas:
  - `CLINICAL_CHAT_RAG_SPELL_TRIGGER_MAX_POSTINGS=1..50`
  - `CLINICAL_CHAT_RAG_WILDCARD_ENABLED=true|false`
  - `CLINICAL_CHAT_RAG_WILDCARD_MAX_EXPANSIONS=8..256`
  - `CLINICAL_CHAT_RAG_KGRAM_SIZE=2..4`
  - `CLINICAL_CHAT_RAG_KGRAM_JACCARD_MIN=0.05..0.95`
  - `CLINICAL_CHAT_RAG_SOUNDEX_ENABLED=true|false`
- Comportamiento:
  - wildcard `*` se expande sobre vocabulario FTS y se filtra con k-gram/Jaccard.
  - spell correction se activa cuando postings de termino <= umbral configurado.
  - Soundex actua como fallback cuando Levenshtein no encuentra candidato adecuado.
- Reinicio recomendado tras cambios en `.env`.
- Smoke recomendado:
  - consulta: `psicot* AND urgencias`
  - consulta con typo: `oncolgia neutropenia`
  - verificar trazas:
    - `candidate_wildcard_attempted>=0`
    - `candidate_wildcard_expanded_terms>=0`
    - `candidate_did_you_mean` (si hubo correccion)
    - `candidate_spell_trigger_max_postings=<valor>`
    - `candidate_soundex_enabled=1`

## TM-148 - Notas de despliegue

- Sin migraciones Alembic en esta fase.
- Variables nuevas:
  - `CLINICAL_CHAT_RAG_CONTEXTUAL_SPELL_ENABLED=true|false`
  - `CLINICAL_CHAT_RAG_CONTEXTUAL_SPELL_MAX_CANDIDATES=8..128`
- Comportamiento:
  - cuando hay contexto vecino de termino en query, la sugerencia ortografica se reranquea por soporte de bigramas en corpus local.
  - el numero de candidatos con evaluacion contextual se limita para no penalizar latencia.
- Reinicio recomendado tras cambios en `.env`.
- Smoke recomendado:
  - consulta con typo contextual: `oncolgia neutropenia febril`
  - verificar trazas:
    - `candidate_contextual_spell_enabled=1`
    - `candidate_contextual_spell_max_candidates=<valor>`
    - `candidate_did_you_mean` con sugerencia esperada (ej. `oncologia`).

## TM-149 - Notas de despliegue

- Sin migraciones Alembic en esta fase.
- Variables nuevas:
  - `CLINICAL_CHAT_RAG_VOCAB_CACHE_ENABLED=true|false`
  - `CLINICAL_CHAT_RAG_VOCAB_CACHE_MAX_TERMS=1000..2000000`
  - `CLINICAL_CHAT_RAG_VOCAB_CACHE_TTL_SECONDS=30..86400`
- Comportamiento:
  - wildcard/spell priorizan lookup en cache de vocabulario en memoria y hacen fallback a DB.
  - recarga de cache por TTL para equilibrar frescura y latencia.
- Reinicio recomendado tras cambios en `.env`.
- Smoke recomendado:
  - ejecutar dos consultas consecutivas con typo/wildcard y verificar en trazas:
    - primera consulta: `candidate_vocab_lookup_db_hits>=1` (si cache frio)
    - siguientes: `candidate_vocab_lookup_cache_hits>=1`.

## TM-150 - Notas de despliegue

- Sin migraciones Alembic en esta fase.
- Variables nuevas:
  - `CLINICAL_CHAT_RAG_POSTINGS_CACHE_ENABLED=true|false`
  - `CLINICAL_CHAT_RAG_POSTINGS_CACHE_MAX_ENTRIES=100..200000`
  - `CLINICAL_CHAT_RAG_POSTINGS_CACHE_TTL_SECONDS=30..86400`
  - `CLINICAL_CHAT_RAG_POSTINGS_CACHE_ENCODING=vb|gamma`
- Comportamiento:
  - postings se almacenan en cache comprimida por gaps para reducir huella y lecturas repetidas.
  - `vb` recomendado para produccion por velocidad de decodificacion.
- Reinicio recomendado tras cambios en `.env`.
- Smoke recomendado:
  - repetir la misma consulta 2-3 veces y verificar:
    - `candidate_postings_cache_hits` creciente
    - `candidate_postings_cache_misses` decreciente
    - `candidate_postings_cache_encoding=vb` (recomendado)
  - dimensionamiento de corpus:
    - `./venv/Scripts/python.exe -m app.scripts.estimate_rag_index_stats --specialty oncology --top 20`

## TM-151 - Notas de despliegue

- Sin migraciones Alembic en esta fase.
- Variables nuevas:
  - `CLINICAL_CHAT_RAG_ZONE_WEIGHT_TITLE`
  - `CLINICAL_CHAT_RAG_ZONE_WEIGHT_SECTION`
  - `CLINICAL_CHAT_RAG_ZONE_WEIGHT_BODY`
  - `CLINICAL_CHAT_RAG_ZONE_WEIGHT_KEYWORDS`
  - `CLINICAL_CHAT_RAG_ZONE_WEIGHT_CUSTOM_QUESTIONS`
  - `CLINICAL_CHAT_RAG_TFIDF_MAX_QUERY_TERMS=4..64`
  - `CLINICAL_CHAT_RAG_TFIDF_PIVOT_SLOPE=0..1`
  - `CLINICAL_CHAT_RAG_TFIDF_ZONE_BLEND=0..1`
- Comportamiento:
  - scoring keyword pasa a `tf-idf` por zonas + coseno + normalizacion pivotada.
  - mezcla hibrida usa score normalizado real de ambos canales.
- Reinicio recomendado tras cambios en `.env`.
- Smoke recomendado:
  - repetir una consulta clinica con terminos de alta especificidad y verificar en trazas:
    - `keyword_search_method=tfidf_zone_cosine_pivoted`
    - `keyword_search_query_terms` > 0
    - `keyword_search_avg_doc_length` informado.

## TM-152 - Notas de despliegue

- Sin migraciones Alembic en esta fase.
- Variables nuevas:
  - `CLINICAL_CHAT_RAG_IDF_TERM_PRUNING_ENABLED`
  - `CLINICAL_CHAT_RAG_IDF_MIN_THRESHOLD=1.0..4.0`
  - `CLINICAL_CHAT_RAG_IDF_MIN_KEEP_TERMS=1..16`
  - `CLINICAL_CHAT_RAG_PROXIMITY_BONUS_ENABLED`
  - `CLINICAL_CHAT_RAG_PROXIMITY_BONUS_WEIGHT=0..1`
  - `CLINICAL_CHAT_RAG_STATIC_QUALITY_ENABLED`
  - `CLINICAL_CHAT_RAG_STATIC_QUALITY_WEIGHT=0..1`
  - `CLINICAL_CHAT_RAG_TIERED_RANKING_ENABLED`
  - `CLINICAL_CHAT_RAG_TIER1_MIN_STATIC_QUALITY=0..1`
- Comportamiento:
  - keyword ranking aplica poda de terminos por `idf` para acelerar scoring.
  - se suma bonus de proximidad y calidad estatica en net-score.
  - se prioriza tier1 (alta calidad) y se completa con tier2 si hace falta.
- Reinicio recomendado tras cambios en `.env`.
- Smoke recomendado:
  - consulta clinica con terminos especificos y verificar trazas:
    - `keyword_search_idf_pruned_terms` >= 0
    - `keyword_search_proximity_enabled=1`
    - `keyword_search_static_quality_enabled=1`
    - `keyword_search_tiered_enabled=1`.

## TM-153 - Notas de despliegue

- Sin migraciones ni cambios de runtime API.
- Script operativo:
  - Basico:
    - `./venv/Scripts/python.exe -m app.scripts.evaluate_rag_retrieval --dataset tmp/rag_eval.jsonl --k 8 --precision-ks 1,3,5 --strategy auto`
  - A/B offline:
    - `./venv/Scripts/python.exe -m app.scripts.evaluate_rag_retrieval --dataset tmp/rag_eval.jsonl --k 8 --strategy hybrid --ab-strategy domain`
  - Reporte detallado:
    - `./venv/Scripts/python.exe -m app.scripts.evaluate_rag_retrieval --dataset tmp/rag_eval.jsonl --k 8 --report-out tmp/rag_eval_report.json`
- Recomendacion operativa:
  - usar `expected_doc_ids` o `graded_relevance` para gold robusto.
  - reservar `expected_terms` para validaciones rapidas de smoke.

## TM-154 - Notas de despliegue

- Sin migraciones Alembic.
- Variables nuevas:
  - `CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_ENABLED=true|false`
  - `CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_PATH=docs/clinical_thesaurus_es_en.json`
  - `CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_TTL_SECONDS=30..86400`
  - `CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_MAX_EXPANSIONS_PER_TERM=1..32`
  - `CLINICAL_CHAT_RAG_PRF_ENABLED=true|false`
  - `CLINICAL_CHAT_RAG_PRF_TOPK=1..12`
  - `CLINICAL_CHAT_RAG_PRF_MAX_TERMS=1..24`
  - `CLINICAL_CHAT_RAG_PRF_MIN_TERM_LEN=3..12`
  - `CLINICAL_CHAT_RAG_PRF_ALPHA/BETA/GAMMA=0..2`
- Comportamiento:
  - expansion semantica previa al retrieval con tesauro local + hints de especialidad.
  - segunda pasada opcional PRF para expansion automatica de consulta.
- Reinicio recomendado tras cambios de `.env` o del tesauro.
- Smoke recomendado:
  - consulta con sinonimos (`leucemia`) y revisar trazas:
    - `retrieval_query_expansion_global_terms` no vacio.
    - `retrieval_query_prf_enabled=1`.

## TM-155 - Notas de despliegue

- Sin migraciones Alembic.
- Variables relevantes:
  - CLINICAL_CHAT_RAG_BM25_ENABLED=true|false
  - CLINICAL_CHAT_RAG_BM25_K1=0..3
  - CLINICAL_CHAT_RAG_BM25_B=0..1
  - CLINICAL_CHAT_RAG_BM25_BLEND=0..1
  - CLINICAL_CHAT_RAG_BIM_BINARY_BONUS_ENABLED=true|false
  - CLINICAL_CHAT_RAG_BIM_BINARY_BONUS_WEIGHT=0..1
- Comportamiento:
  - scoring lexical base tf-idf por zonas + normalizacion pivotada.
  - blend probabilistico BM25 para frecuencia/longitud.
  - bonus BIM opcional para reforzar terminos discriminativos.
  - trazas probabilisticas disponibles tambien en casos sin candidatos, para diagnostico.
- Reinicio recomendado tras cambios de .env.
- Smoke recomendado:
  - consulta con terminos clinicos concretos y validar trazas:
    - keyword_search_bm25_enabled=1
    - keyword_search_bm25_top_avg presente
    - keyword_search_bim_top_avg presente

## TM-156 - Notas de despliegue

- Sin migraciones Alembic.
- Variables nuevas:
  - CLINICAL_CHAT_RAG_QLM_ENABLED=true|false
  - CLINICAL_CHAT_RAG_QLM_SMOOTHING=dirichlet|jm
  - CLINICAL_CHAT_RAG_QLM_DIRICHLET_MU=100..5000
  - CLINICAL_CHAT_RAG_QLM_JM_LAMBDA=0..1
  - CLINICAL_CHAT_RAG_QLM_BLEND=0..1
- Comportamiento:
  - scoring lexical incorpora probabilidad P(q|d) por modelo unigrama.
  - smoothing evita probabilidad cero para terminos ausentes.
  - blend QLM permite calibrar precision/recall sin cambiar arquitectura.
- Reinicio recomendado tras cambios de .env.
- Smoke recomendado:
  - ejecutar una consulta clinica y verificar trazas:
    - keyword_search_qlm_enabled=1
    - keyword_search_qlm_smoothing=dirichlet|jm
    - keyword_search_qlm_top_avg presente

## TM-157 - Notas de despliegue

- Sin migraciones Alembic.
- Variables nuevas/relevantes:
  - CLINICAL_CHAT_NB_ENABLED=true|false
  - CLINICAL_CHAT_NB_MODEL=multinomial|bernoulli
  - CLINICAL_CHAT_NB_ALPHA=0.01..5
  - CLINICAL_CHAT_NB_MIN_CONFIDENCE=0..1 (calibrado a 0.25 por defecto)
  - CLINICAL_CHAT_NB_FEATURE_METHOD=chi2|mi|none
  - CLINICAL_CHAT_NB_MAX_FEATURES=32..2000
  - CLINICAL_CHAT_NB_RERANK_WHEN_MATH_UNCERTAIN_ONLY=true|false
- Comportamiento:
  - clasificador NB estima dominio top de consulta y puede reordenar dominios candidatos.
  - el rerank se aplica solo si supera umbral y, por defecto, cuando la inferencia matematica esta incierta.
  - se exponen trazas `nb_*` para auditoria operativa.
- Reinicio recomendado tras cambios de .env.
- Smoke recomendado:
  - consulta: "neutropenia febril oncologica pasos 0-10"
  - verificar en `interpretability_trace`:
    - `nb_enabled=1`
    - `nb_top_domain=oncology`
    - `nb_rerank_recommended=1`
## TM-158 - Notas de despliegue

- Sin migraciones Alembic.
- Sin nuevas variables de entorno.
- Comportamiento:
  - se habilita evaluacion explicita macro/micro en utilitario de clasificacion NB.
- Smoke recomendado:
  - `./venv/Scripts/python.exe -m pytest -q app/tests/test_clinical_naive_bayes_service.py -o addopts=""`
## TM-159 - Notas de despliegue

- Sin migraciones Alembic.
- Variables nuevas/relevantes:
  - CLINICAL_CHAT_VECTOR_ENABLED=true|false
  - CLINICAL_CHAT_VECTOR_METHOD=rocchio|knn|hybrid
  - CLINICAL_CHAT_VECTOR_K=1..25
  - CLINICAL_CHAT_VECTOR_MIN_CONFIDENCE=0..1 (default 0.05)
  - CLINICAL_CHAT_VECTOR_RERANK_WHEN_MATH_UNCERTAIN_ONLY=true|false
- Comportamiento:
  - clasificacion semantica tf-idf en espacio vectorial para priorizar dominio clinico.
  - Rocchio actua como baseline de baja varianza/latencia.
  - kNN habilita frontera no lineal a coste computacional mayor.
  - `hybrid` balancea ambos metodos.
- Reinicio recomendado tras cambios de .env.
- Smoke recomendado:
  - consulta: "neutropenia febril oncologica tras quimioterapia"
  - verificar en `interpretability_trace`:
    - `vector_enabled=1`
    - `vector_top_domain=oncology`
    - `vector_rerank_recommended=1`
## TM-160 - Notas de despliegue

- Sin migraciones Alembic.
- Variables nuevas/relevantes:
  - `CLINICAL_CHAT_SVM_DOMAIN_ENABLED=true|false`
  - `CLINICAL_CHAT_SVM_DOMAIN_C=0.05..20`
  - `CLINICAL_CHAT_SVM_DOMAIN_L2=0.0001..1.0`
  - `CLINICAL_CHAT_SVM_DOMAIN_EPOCHS=1..100`
  - `CLINICAL_CHAT_SVM_DOMAIN_MIN_CONFIDENCE=0..1`
  - `CLINICAL_CHAT_SVM_DOMAIN_RERANK_WHEN_MATH_UNCERTAIN_ONLY=true|false`
- Comportamiento:
  - SVM lineal OVA estima dominio top de la consulta y puede reordenar dominios candidatos.
  - inferencia calibrada para priorizar la señal discriminativa semantica y reducir sesgo por bias en clases desbalanceadas.
- Reinicio recomendado tras cambios de `.env`.
- Smoke recomendado:
  - consulta: `"Paciente con neutropenia febril oncologica y quimioterapia"`
  - verificar en `interpretability_trace`:
    - `svm_domain_enabled=1`
    - `svm_domain_top_domain=oncology`
    - `svm_domain_rerank_recommended=1`

## TM-161 - Notas de despliegue

- Sin migraciones Alembic.
- Variables nuevas/relevantes:
  - `CLINICAL_CHAT_CLUSTER_ENABLED=true|false`
  - `CLINICAL_CHAT_CLUSTER_METHOD=kmeans|kmeans_em`
  - `CLINICAL_CHAT_CLUSTER_K_MIN=1..20`
  - `CLINICAL_CHAT_CLUSTER_K_MAX=1..30`
  - `CLINICAL_CHAT_CLUSTER_MAX_ITERATIONS=5..100`
  - `CLINICAL_CHAT_CLUSTER_EM_ITERATIONS=1..50`
  - `CLINICAL_CHAT_CLUSTER_MIN_CONFIDENCE=0..1`
  - `CLINICAL_CHAT_CLUSTER_RERANK_WHEN_MATH_UNCERTAIN_ONLY=true|false`
  - `CLINICAL_CHAT_CLUSTER_F_BETA=0.5..3.0`
- Comportamiento:
  - agrupa muestras de dominio en clusters semanticos y prioriza dominios del cluster top para rerank.
  - reporta metricas operativas de calidad de clustering en trazas (`purity`, `nmi`, `rand`, `f_measure`).
- Reinicio recomendado tras cambios de `.env`.
- Smoke recomendado:
  - consulta: `"Paciente con neutropenia febril oncologica y quimioterapia"`
  - verificar en `interpretability_trace`:
    - `cluster_enabled=1`
    - `cluster_candidate_domains` contiene `oncology`
    - `cluster_rerank_recommended=1`

## TM-162 - Notas de despliegue

- Sin migraciones Alembic.
- Variables nuevas/relevantes:
  - `CLINICAL_CHAT_HCLUSTER_ENABLED=true|false`
  - `CLINICAL_CHAT_HCLUSTER_METHOD=hac_single|hac_complete|hac_average|divisive|buckshot`
  - `CLINICAL_CHAT_HCLUSTER_K_MIN=1..20`
  - `CLINICAL_CHAT_HCLUSTER_K_MAX=1..30`
  - `CLINICAL_CHAT_HCLUSTER_MIN_CONFIDENCE=0..1`
  - `CLINICAL_CHAT_HCLUSTER_RERANK_WHEN_MATH_UNCERTAIN_ONLY=true|false`
  - `CLINICAL_CHAT_HCLUSTER_F_BETA=0.5..3.0`
  - `CLINICAL_CHAT_HCLUSTER_BUCKSHOT_SAMPLE_SCALE=0.5..3.0`
  - `CLINICAL_CHAT_HCLUSTER_MAX_CANDIDATE_DOMAINS=1..12`
- Comportamiento:
  - agrega capa jerarquica de agrupamiento para priorizar dominios candidatos del chat.
  - emite trazas `hcluster_*` para auditoria de metodo, calidad y recomendacion de rerank.
- Reinicio recomendado tras cambios de `.env`.
- Smoke recomendado:
  - consulta: `"Paciente con neutropenia febril oncologica y quimioterapia"`
  - verificar en `interpretability_trace`:
    - `hcluster_enabled=1`
    - `hcluster_candidate_domains` contiene `oncology`
    - `hcluster_rerank_recommended=1`

## TM-163 - Notas de despliegue

- Sin migraciones Alembic.
- Variables nuevas/relevantes:
  - `CLINICAL_CHAT_RAG_LSI_ENABLED=true|false`
  - `CLINICAL_CHAT_RAG_LSI_K=2..512`
  - `CLINICAL_CHAT_RAG_LSI_BLEND=0..1`
  - `CLINICAL_CHAT_RAG_LSI_MAX_VOCAB_TERMS=64..4000`
  - `CLINICAL_CHAT_RAG_LSI_MIN_DOCS=2..200`
- Comportamiento:
  - agrega señal semantica LSI sobre retrieval lexical (candidate pool) y la mezcla con score actual.
  - añade trazas `keyword_search_lsi_*` y posible sufijo `+lsi` en `keyword_search_method`.
- Reinicio recomendado tras cambios de `.env`.
- Smoke recomendado:
  - lanzar consulta clinica ambigua con sinonimia y verificar en trazas:
    - `keyword_search_lsi_enabled=1`
    - `keyword_search_lsi_components>0`
    - `keyword_search_method` incluye `+lsi`.

## TM-164 - Notas de despliegue

- Sin migraciones Alembic.
- Sin nuevas variables obligatorias de entorno.
- Comportamiento:
  - mejora del pipeline `web_sources` con deduplicacion de URL canonica y near-duplicate por MinHash.
  - filtro heuristico anti-spam/clickbait previo a exponer fuentes web.
  - ordenacion por score combinado de autoridad de dominio + relevancia lexical.
  - trazas nuevas `web_search_*` para auditoria operativa.
- Reinicio recomendado tras despliegue de backend para activar nuevo codigo.
- Smoke recomendado:
  - consulta con `use_web_sources=true` y verificar en `interpretability_trace`:
    - `web_search_quality_sorted=1`
    - `web_search_results` > 0 (si hay fuentes)
    - contadores de `web_search_*_filtered_out` coherentes.

## TM-165 - Notas de despliegue

- Sin migraciones Alembic.
- Sin cambios en endpoints API.
- Nuevo componente operativo:
  - `python -m app.scripts.crawl_clinical_web`
- Ejemplo de ejecucion:
  - `./venv/Scripts/python.exe -m app.scripts.crawl_clinical_web --max-pages 80 --workers 6 --resume`
- Salidas:
  - markdowns: `docs/web_raw/<host>/*.md`
  - manifiesto: `docs/web_raw/crawl_manifest.jsonl`
  - checkpoint: `tmp/web_crawl_checkpoint.json`
- Recomendaciones:
  - mantener `--politeness-multiplier` >= 10 para no saturar hosts.
  - no usar `--disable-robots` salvo pruebas controladas.

## TM-166 - Notas de despliegue

- Sin migraciones Alembic.
- Variables nuevas/relevantes:
  - `CLINICAL_CHAT_WEB_LINK_ANALYSIS_ENABLED=true|false`
  - `CLINICAL_CHAT_WEB_LINK_ANALYSIS_PATH=docs/web_raw/link_analysis_snapshot.json`
  - `CLINICAL_CHAT_WEB_LINK_ANALYSIS_BLEND=0..1`
  - `CLINICAL_CHAT_WEB_LINK_ANALYSIS_MAX_HITS_BASE=20..2000`
- Nuevos componentes operativos:
  - `python -m app.scripts.build_web_link_analysis`
  - `app/services/web_link_analysis_service.py`
- Flujo recomendado:
  1. Ejecutar crawler (`crawl_clinical_web`) para actualizar `crawl_manifest.jsonl`.
  2. Ejecutar build de snapshot (`build_web_link_analysis`).
  3. Reiniciar backend para recargar snapshot cacheado.
- Smoke recomendado:
  - consulta con `use_web_sources=true` y revisar trazas:
    - `web_search_link_analysis_loaded=1`
    - `web_search_link_analysis_avg_score` presente
    - `web_search_link_analysis_blend` presente

## TM-167 - Notas de despliegue

- Sin migraciones Alembic.
- Sin nuevos endpoints.
- Cambios de comportamiento:
  - evita doble pase LLM cuando RAG ya reporta `failed_generation` por error de LLM.
  - prioriza fallback con evidencia interna cuando hay `rag_sources` disponibles.
  - LLM opera con presupuesto temporal total por request (`CLINICAL_CHAT_LLM_TIMEOUT_SECONDS`).
- Recomendaciones:
  - revisar `CLINICAL_CHAT_LLM_TIMEOUT_SECONDS` acorde al hardware local (p.ej. 30-60s).
  - reiniciar backend tras cambios de `.env`.
- Smoke recomendado:
  - lanzar 5 consultas clinicas del benchmark y verificar que no haya timeout de cliente y aparezca `llm_second_pass_skipped=rag_failed_generation` solo cuando aplique.

## TM-168 - Notas de despliegue

- Sin migraciones Alembic.
- Sin cambios en API publica.
- Cambios de comportamiento:
  - intento principal LLM via `Ollama /api/generate`.
  - fallback a `/api/chat` y luego `generate_quick_recovery` dentro de presupuesto temporal.
  - trazabilidad `llm_enabled` y `llm_primary_error` para diagnostico rapido.
- Recomendaciones:
  - mantener `CLINICAL_CHAT_LLM_TIMEOUT_SECONDS` entre 10 y 25 en hardware CPU local.
  - reiniciar uvicorn tras cualquier cambio de `.env`.
- Smoke recomendado:
  - 1 consulta corta (`test rapido`) y validar `llm_enabled=true` en traza.
  - benchmark de 5 consultas y comparar latencia/`llm_used`.

## TM-170 - Notas de despliegue

- Perfil recomendado para CPU local sin pago:
  - `phi3:mini` + contexto/tokens reducidos + timeout 10s.
- Requisitos:
  - ejecutar `ollama pull phi3:mini`.
  - reiniciar backend tras cambios de `.env`.
- Objetivo:
  - reducir `rag_status=failed_generation` por timeout de inferencia.


## TM-171 - Notas de despliegue

- Sin migraciones Alembic.
- Variables nuevas/relevantes:
  - `CLINICAL_CHAT_LLM_CIRCUIT_BREAKER_ENABLED=true`
  - `CLINICAL_CHAT_LLM_CIRCUIT_BREAKER_FAILURE_THRESHOLD=2`
  - `CLINICAL_CHAT_LLM_CIRCUIT_BREAKER_OPEN_SECONDS=90`
  - `CLINICAL_CHAT_RAG_EXTRACTIVE_FALLBACK_ENABLED=true`
  - `CLINICAL_CHAT_RAG_EXTRACTIVE_FALLBACK_MAX_ITEMS=5`
  - `DATABASE_ECHO=false` (recomendado para latencia y logs limpios)
- Cambios de comportamiento:
  - ante fallo/timeout LLM, RAG entrega respuesta extractiva con fuentes en vez de quedar en `failed_generation`.
  - si hay fallos consecutivos LLM, el circuit breaker corta llamadas temporariamente.
  - retrieval clinico excluye chunks sin `specialty` para reducir ruido.
- Requisito operativo:
  - reiniciar uvicorn para aplicar cambios de codigo y `.env`.

## TM-172 - Notas de despliegue

- Sin migraciones Alembic.
- Sin cambios en API publica.
- Cambio operativo:
  - ingesta incremental evita reprocesado por ruta existente (`source_file`) y reduce latencia de mantenimiento del corpus.
- Nuevo flag CLI:
  - `--force-reprocess-existing-paths` para reingestar todo aun cuando la ruta ya exista en BD.

## TM-173 - Notas de despliegue

- Sin migraciones Alembic.
- Variables nuevas/relevantes:
  - `CLINICAL_CHAT_LLM_MAX_DIALOGUE_TURNS`
  - `CLINICAL_CHAT_RAG_MAX_TOTAL_LATENCY_MS`
  - `CLINICAL_CHAT_RAG_LLM_MIN_REMAINING_BUDGET_MS`
- Perfil recomendado aplicado:
  - `LLM timeout/context/input/output` mas bajos
  - `RAG adaptive_k + context compression` activos
  - `PRF/LSI` desactivados para reducir latencia por defecto
- Requisito operativo:
  - reiniciar uvicorn tras cambios de `.env`.

## TM-174 - Notas de despliegue

- Sin migraciones Alembic.
- Tuning aplicado en runtime:
  - `CLINICAL_CHAT_RAG_MAX_CHUNKS=2`
  - `CLINICAL_CHAT_RAG_MAX_CHUNKS_HARD=6`
  - `CLINICAL_CHAT_RAG_FTS_CANDIDATE_POOL=96`
  - `CLINICAL_CHAT_RAG_COMPRESS_MAX_CHARS=280`
  - `CLINICAL_CHAT_RAG_CONTEXTUAL_SPELL_MAX_CANDIDATES=12`
- Cambio de logica:
  - `adaptive_k` mas conservador con soft-cap `base_k + 1`.
- Requisito operativo:
  - reiniciar uvicorn para cargar nuevos settings.

## TM-175 - Notas de despliegue

- Sin migraciones Alembic.
- Nuevas variables/tuning activos:
  - `CLINICAL_CHAT_RAG_SKIP_DOMAIN_SEARCH_TOKENS_OVER=10`
  - `CLINICAL_CHAT_RAG_FTS_CANDIDATE_POOL=80`
  - `CLINICAL_CHAT_RAG_WILDCARD_MAX_EXPANSIONS=16`
  - `CLINICAL_CHAT_RAG_CONTEXTUAL_SPELL_MAX_CANDIDATES=10`
  - `CLINICAL_CHAT_RAG_GLOBAL_THESAURUS_MAX_EXPANSIONS_PER_TERM=4`
  - `CLINICAL_CHAT_RAG_MAX_TOTAL_LATENCY_MS=3200`
  - `CLINICAL_CHAT_RAG_LLM_MIN_REMAINING_BUDGET_MS=1100`
- Requisito operativo:
  - reiniciar uvicorn para aplicar cambios de `.env` y c?digo.


## TM-176 - Notas de despliegue

- Sin migraciones Alembic.
- Tuning aplicado:
  - `CLINICAL_CHAT_RAG_FTS_CANDIDATE_POOL=96`
  - `CLINICAL_CHAT_RAG_SKIP_DOMAIN_SEARCH_TOKENS_OVER=18`
- Cambio de logica:
  - fail-fast cuando `rag_status` es `failed_retrieval`/`failed_exception` para evitar cascada de latencia por segundo pase LLM.
- Requisito operativo:
  - reiniciar uvicorn para aplicar cambios de `.env` y codigo.

## TM-177 - Notas de despliegue

- Sin migraciones Alembic.
- Ajustes de calidad por defecto:
  - `CLINICAL_CHAT_RAG_ENABLE_GATEKEEPER=true`
  - `CLINICAL_CHAT_RAG_CONTEXT_MIN_RATIO=0.12`
  - `CLINICAL_CHAT_LLM_REWRITE_ENABLED=true`
- Requisito operativo:
  - reiniciar uvicorn para aplicar cambios de `.env` y codigo.

## TM-178 - Notas de despliegue

- Sin migraciones Alembic.
- Cambios de runtime de calidad:
  - priorizacion de fuentes RAG por score de retrieval.
  - salida evidence-first incluye `Consulta objetivo`.
- Cambios de observabilidad local:
  - `tmp/summarize_chat_benchmark.py` genera `tmp/chat_benchmark_results_summary.json`.
  - `tmp/check_acceptance.py` devuelve exit code 1 cuando no se cumplen umbrales.
- Requisito operativo:
  - reiniciar uvicorn para cambios de servicios antes de benchmark.

## TM-179 - Notas de despliegue

- Sin migraciones Alembic.
- Ajustes aplicados:
  - `CLINICAL_CHAT_RAG_MAX_TOTAL_LATENCY_MS=3000`
  - `CLINICAL_CHAT_RAG_LLM_MIN_REMAINING_BUDGET_MS=700`
  - `CLINICAL_CHAT_RAG_FTS_CANDIDATE_POOL=88`
  - `CLINICAL_CHAT_RAG_SKIP_DOMAIN_SEARCH_TOKENS_OVER=12`
- Bench summary ahora imprime por query:
  - `llm_enabled=`
  - `llm_used=`
  - `llm_error=`
- Requisito operativo:
  - reiniciar uvicorn para aplicar `.env`.

## TM-180 - Notas de despliegue

- Sin migraciones Alembic.
- Configuracion nueva opcional:
  - `CLINICAL_CHAT_LLM_PROVIDER=llama_cpp`
  - `CLINICAL_CHAT_LLM_BASE_URL=http://127.0.0.1:8080`
  - `CLINICAL_CHAT_LLM_API_KEY=` (opcional; vacio por defecto)
- Requisito operativo:
  - levantar servidor `llama.cpp` con endpoint OpenAI-compatible `/v1/chat/completions`.
  - reiniciar uvicorn tras cambios de `.env`.

## TM-181 (runtime local llama.cpp)

- Ajustes base aplicados en `.env`/`.env.example`:
  - `CLINICAL_CHAT_LLM_PROVIDER=llama_cpp`
  - `CLINICAL_CHAT_LLM_BASE_URL=http://127.0.0.1:8080`
  - `CLINICAL_CHAT_LLM_MODEL=Phi-3-mini-4k-instruct-q4.gguf`
  - `CLINICAL_CHAT_LLM_TIMEOUT_SECONDS=18`
  - `CLINICAL_CHAT_LLM_CIRCUIT_BREAKER_FAILURE_THRESHOLD=4`
  - `CLINICAL_CHAT_LLM_CIRCUIT_BREAKER_OPEN_SECONDS=20`
  - `CLINICAL_CHAT_RAG_LLM_MIN_REMAINING_BUDGET_MS=400`
- Requiere reinicio de API para aplicar settings en memoria.

## TM-182 (tuning latencia llama.cpp)

- Se reduce complejidad de retrieval para priorizar entrada a LLM en hardware CPU local.
- Ajustes clave: menor `FTS_CANDIDATE_POOL`, desactivar wildcard/soundex/contextual spell, menor ventana de prompt y salida.

## TM-183 (deploy/runtime)

- El worker asincrono es local, en memoria del proceso API.
- No requiere migraciones de BD.
- Escala objetivo: baja (single-process/local).
- Requiere polling desde cliente para consultar estado por `job_id`.

- Plan B v2 (TM-138) activo por configuracion:

  - `CLINICAL_CHAT_LLM_MAX_CONTEXT_UTILIZATION_RATIO=0.40`
  - `CLINICAL_CHAT_RAG_DETERMINISTIC_ROUTING_ENABLED=true`
  - `CLINICAL_CHAT_RAG_DETERMINISTIC_COMPLEX_MIN_TOKENS=10`
  - `CLINICAL_CHAT_RAG_SIMPLE_ROUTE_MAX_CHUNKS=2`
  - `CLINICAL_CHAT_RAG_COMPLEX_ROUTE_FORCE_SKIP_DOMAIN_SEARCH=true`
  - `CLINICAL_CHAT_RAG_SAFE_WRAPPER_ENABLED=true`
  - `CLINICAL_CHAT_RAG_SAFE_WRAPPER_MIN_CONTEXT_RATIO=0.10`

- Operativamente, tras cambiar `.env`, reiniciar API (`uvicorn`) para aplicar settings en memoria.

## TM-184 - Notas de despliegue

- Sin migraciones Alembic.
- Variables nuevas/relevantes:
  - `CLINICAL_CHAT_RAG_FORCE_EXTRACTIVE_ONLY=true|false`
  - perfil aplicado para esta alternativa local: `CLINICAL_CHAT_LLM_ENABLED=false` + `CLINICAL_CHAT_RAG_FORCE_EXTRACTIVE_ONLY=true`.
- Cambios de comportamiento:
  - RAG responde en modo extractivo estable sin depender de inferencia LLM sincrona.
  - si retrieval por especialidad falla, hay reintento automatico sin filtro de especialidad.
- Requisito operativo:
  - reiniciar uvicorn tras cambios de `.env`.
- Smoke recomendado:
  - ejecutar benchmark y validar descenso de `llm_error=*` y de `failed_retrieval_rate`.

## TM-185 - Notas de despliegue

- Sin migraciones Alembic.
- Cambio runtime:
  - fallback de retrieval para lenguaje natural cuando la evaluacion booleana implicita queda vacia.
  - mantiene modo estricto para booleano explicito.
- Requisito operativo:
  - reiniciar `uvicorn` para aplicar el cambio antes de benchmark HTTP.
- Smoke recomendado:
  - ejecutar benchmark y revisar descenso de `failed_retrieval_rate`.

## TM-186 - Notas de despliegue

- Sin migraciones Alembic.
- Config nueva:
  - `CLINICAL_CHAT_RAG_QA_SHORTCUT_ENABLED=true`
  - `CLINICAL_CHAT_RAG_QA_SHORTCUT_MIN_SCORE=0.24`
  - `CLINICAL_CHAT_RAG_QA_SHORTCUT_TOP_K=2`
  - `CLINICAL_CHAT_RAG_QA_SHORTCUT_MAX_CANDIDATES=80`
- Requisito operativo:
  - reiniciar `uvicorn` para aplicar el cambio en memoria.
- Smoke recomendado post-restart:
  - ejecutar benchmark y monitorizar `failed_retrieval_rate`, `rag_retrieval_strategy=qa_shortcut` y p95.

## TM-187 - Notas de despliegue

- Sin migraciones Alembic.
- Variables nuevas/relevantes:
  - `CLINICAL_CHAT_PDF_PARSER_BACKEND=pypdf|mineru`
  - `CLINICAL_CHAT_PDF_MINERU_BASE_URL`
  - `CLINICAL_CHAT_PDF_MINERU_TIMEOUT_SECONDS`
  - `CLINICAL_CHAT_PDF_MINERU_FAIL_OPEN`
- Requisito operativo:
  - reiniciar `uvicorn` tras cambios de `.env`.
- Backfill recomendado post-deploy para cobertura de especialidades:
  - `./venv/Scripts/python.exe -m app.scripts.ingest_clinical_docs --paths docs --backfill-specialty --backfill-only`
- Rebuild recomendado de preguntas hipoteticas en corpus existente:
  - `./venv/Scripts/python.exe -m app.scripts.ingest_clinical_docs --paths docs --rebuild-custom-questions --backfill-only`
- Activacion MinerU (si hay servicio disponible):
  - `CLINICAL_CHAT_PDF_PARSER_BACKEND=mineru`
  - `CLINICAL_CHAT_PDF_MINERU_BASE_URL=http://127.0.0.1:8091`
  - mantener `CLINICAL_CHAT_PDF_MINERU_FAIL_OPEN=true` para no bloquear ingesta.

## TM-188 - Notas de despliegue

- Sin migraciones Alembic.
- Variables nuevas/relevantes:
  - `CLINICAL_CHAT_PDF_OCR_MODE=region_selective|page_full`
  - `CLINICAL_CHAT_PDF_LAYOUT_READING_ORDER_ENABLED=true|false`
  - `CLINICAL_CHAT_PDF_FILTER_REPEATED_EDGE_TEXT_ENABLED=true|false`
  - `CLINICAL_CHAT_PDF_FILTER_REPEATED_EDGE_TEXT_MIN_PAGES` (>=2)
  - `CLINICAL_CHAT_PDF_TELEMETRY_ENABLED=true|false`
- Requisito operativo:
  - reiniciar `uvicorn` tras cambios de `.env`.
- Recomendada reingesta para aprovechar chunking tipado y limpieza estructural:
  - `./venv/Scripts/python.exe -m app.scripts.ingest_clinical_docs --paths docs/pdf_raw --force-reprocess-existing-paths --skip-ollama-embeddings`

## TM-189 - Notas de despliegue

- No requiere migraciones ni reinicializacion de DB.
- Nuevos controles en ingesta CLI:
  - quality gates activos por defecto (desactivables con `--disable-quality-gates`).
  - ajustar umbrales segun corpus antes de ingestas masivas.
- Nuevo gate offline de retrieval:
  - `evaluate_rag_retrieval.py` puede cortar pipeline con `--fail-on-acceptance` cuando no se cumplen umbrales.
- Smoke recomendado:
  - correr evaluacion con dataset representativo por especialidad y revisar `by_specialty.*.acceptance_passed`.

## TM-190 - Notas de despliegue

- Reiniciar `uvicorn` es obligatorio para que entren en vigor ajustes de scoring y fast-path retrieval.
- En modo extractivo forzado, consultas complejas usan `keyword_only` para reducir p95.
- Verificacion post-deploy recomendada:
  - ejecutar benchmark de 5 queries y confirmar `latency_ok_p95_ms <= 3000` y `BENCHMARK OK`.

## TM-191 - Notas de despliegue

- Requiere reinicio de API para activar enrutado adaptativo nuevo.
- Se recomienda mantener `CLINICAL_CHAT_RAG_LLM_MIN_REMAINING_BUDGET_MS` alto cuando el objetivo principal sea SLA de latencia.
- Para respuestas mas naturales en frontend, usar consultas simples/domain-focused; en complejas prevalece politica de presupuesto.

## TM-193 - Notas de despliegue

- Variables nuevas en `.env`:
  - `CLINICAL_CHAT_RAG_RETRIEVER_BACKEND=elastic`
  - `CLINICAL_CHAT_RAG_ELASTIC_URL=http://127.0.0.1:9200`
  - `CLINICAL_CHAT_RAG_ELASTIC_INDEX=clinical_chunks`
  - `CLINICAL_CHAT_RAG_ELASTIC_TIMEOUT_SECONDS=2`
  - `CLINICAL_CHAT_RAG_ELASTIC_CANDIDATE_POOL=160`
  - `CLINICAL_CHAT_RAG_ELASTIC_TEXT_FIELDS=chunk_text^3,section_path^2,keywords_text^2,custom_questions_text^2,source_file`
  - `CLINICAL_CHAT_RAG_ELASTIC_SEMANTIC_FIELD=semantic_content`
  - `CLINICAL_CHAT_RAG_ELASTIC_VERIFY_TLS=true|false`
- Requisito operativo:
  - reiniciar `uvicorn` tras cambios de `.env`.
- Inicializacion de indice recomendada:
  - `./venv/Scripts/python.exe -m app.scripts.sync_chunks_to_elastic --recreate-index`
- Seguridad y resiliencia:
  - si Elastic falla/no responde, el backend cae automaticamente a `legacy` sin romper el chat.

## TM-199 - Notas de despliegue

- Sin migraciones Alembic.
- Variables nuevas/relevantes:
  - `CLINICAL_CHAT_RAG_MULTI_INTENT_ENABLED=true|false`
  - `CLINICAL_CHAT_RAG_MULTI_INTENT_MAX_SEGMENTS=1..8`
  - `CLINICAL_CHAT_RAG_MULTI_INTENT_MIN_SEGMENT_CHARS=8..120`
  - `CLINICAL_CHAT_RAG_MULTI_INTENT_MIN_DOMAIN_PROBABILITY=0..1`
  - `CLINICAL_CHAT_RAG_ACTION_FOCUS_ENABLED=true|false`
  - `CLINICAL_CHAT_RAG_ACTION_MIN_SCORE=0..1`
  - `CLINICAL_CHAT_RAG_ACTION_MAX_AUX_RATIO=0..1`
- Requisito operativo:
  - reiniciar `uvicorn` tras cambios de `.env`.
- Recomendacion post-deploy:
  - monitorizar en trazas `rag_multi_intent_plan_size`, `rag_multi_intent_chunks` y `quality_threshold_attention_*` para calibracion por subdominio.

## TM-200 - Notas de despliegue

- Sin migraciones Alembic.
- Variables nuevas/relevantes:
  - `CLINICAL_CHAT_RAG_HYDE_ENABLED=true|false`
  - `CLINICAL_CHAT_RAG_VERIFIER_ENABLED=true|false`
  - `CLINICAL_CHAT_RAG_VERIFIER_MIN_SCORE=0..1`
  - `CLINICAL_CHAT_RAG_VERIFIER_MIN_CHUNKS=1..12`
  - `CLINICAL_CHAT_RAG_VERIFIER_BM25_FALLBACK_ENABLED=true|false`
  - `CLINICAL_CHAT_RAG_ECORAG_ENABLED=true|false`
  - `CLINICAL_CHAT_RAG_ECORAG_MIN_EVIDENTIALITY=0..1`
  - `CLINICAL_CHAT_RAG_ECORAG_MIN_CHUNKS=1..12`
- Requisito operativo:
  - reiniciar `uvicorn` tras cambios de `.env`.
- Recomendacion post-deploy:
  - revisar `rag_verifier_passed`, `rag_verifier_reason`, `rag_ecorag_evidentiality_score` y `rag_safe_wrapper_reason` en trazas para calibrar precision/recall por subdominio.

- TM-201 (RAG latencia/fact-only):

  - Nuevas flags de configuracion:
    - `CLINICAL_CHAT_RAG_FACT_ONLY_MODE_ENABLED` (default `false`)
    - `CLINICAL_CHAT_RAG_EARLY_GOAL_TEST_ENABLED` y umbrales `CLINICAL_CHAT_RAG_EARLY_GOAL_*`
    - `CLINICAL_CHAT_RAG_QUERY_CACHE_ENABLED`, `CLINICAL_CHAT_RAG_QUERY_CACHE_TTL_SECONDS`, `CLINICAL_CHAT_RAG_QUERY_CACHE_MAX_ENTRIES`
  - Recomendacion para portatil local: activar `FACT_ONLY_MODE`, mantener `QUERY_CACHE_ENABLED=true` y ajustar TTL/size segun memoria disponible.
  - Sin migraciones DB ni cambios de infraestructura obligatorios.

- TM-202 (coherencia discursiva RAG):

  - Nuevas flags de configuracion:
    - `CLINICAL_CHAT_RAG_DISCOURSE_COHERENCE_ENABLED`
    - `CLINICAL_CHAT_RAG_DISCOURSE_MIN_SCORE`
    - `CLINICAL_CHAT_RAG_DISCOURSE_MAX_SATELLITE_RATIO`
    - `CLINICAL_CHAT_RAG_DISCOURSE_LCD_MIN_SCORE`
  - Recomendacion inicial de despliegue local:
    - mantener `DISCOURSE_COHERENCE_ENABLED=true`,
    - empezar con umbrales por defecto y revisar trazas `rag_discourse_*` por subdominio.
  - Sin migraciones DB ni cambios de infraestructura obligatorios.

- TM-203 (algoritmos discursivos explicitos en runtime):

  - Se activa en la misma capa `CLINICAL_CHAT_RAG_DISCOURSE_COHERENCE_ENABLED=true`.
  - Algoritmos aplicados por chunk recuperado:
    - `EDU segmentation`,
    - `TextTiling`,
    - `Lexical chaining`,
    - `LSA-like coherence`,
    - `LCD local` con operaciones vectoriales,
    - `Entity Grid`.
  - Verificacion operativa sugerida:
    - revisar en trazas `rag_discourse_top_texttiling`, `rag_discourse_top_lexical_chain`, `rag_discourse_top_lsa`, `rag_discourse_top_entity_grid`.

