# Notas de Contrato de Datos

## Modelo actual

- Tabla: `tasks`
- PK: `id`
- Indices: `id`, `title`, `completed`
- Tabla: `users`
- PK: `id`
- Indices: `id`, `username`
- Tabla: `auth_sessions`
- PK: `id`
- Indices: `id`, `user_id`, `jti` (unico)
- Tabla: `login_attempts`
- PK: `id`
- Indices: `id`, `username`, `ip_address`
- Tabla: `agent_runs`
- PK: `id`
- Indices: `id`, `workflow_name`, `status`
- Tabla: `agent_steps`
- PK: `id`
- Indices: `id`, `run_id`, `status`
- Tabla: `care_tasks`
- PK: `id`
- Indices: `id`, `title`, `clinical_priority`, `specialty`, `completed`
- Tabla: `care_task_chat_messages`
- PK: `id`
- Indices: `id`, `care_task_id`, `session_id`, `care_task_id+session_id`
- Tabla: `care_task_triage_reviews`
- PK: `id`
- Indices: `id`, `care_task_id`, `agent_run_id` (unico)
- Tabla: `care_task_triage_audit_logs`
- PK: `id`
- Indices: `id`, `care_task_id`, `agent_run_id` (unico), `classification`
- Tabla: `care_task_screening_audit_logs`
- PK: `id`
- Indices: `id`, `care_task_id`, `agent_run_id` (unico), `classification`
- Tabla: `care_task_medicolegal_audit_logs`
- PK: `id`
- Indices: `id`, `care_task_id`, `agent_run_id` (unico), `classification`
- Tabla: `care_task_scasest_audit_logs`
- PK: `id`
- Indices: `id`, `care_task_id`, `agent_run_id` (unico), `classification`
- Tabla: `care_task_cardio_risk_audit_logs`
- PK: `id`
- Indices: `id`, `care_task_id`, `agent_run_id` (unico), `classification`
- Tabla: `care_task_resuscitation_audit_logs`
- PK: `id`
- Indices: `id`, `care_task_id`, `agent_run_id` (unico), `classification`
- Tabla: `emergency_episodes`
- PK: `id`
- Indices: `id`, `care_task_id`, `origin`, `current_stage`, `priority_risk`, `disposition`
- Catalogo en codigo: `clinical_context` (areas, circuitos, roles, procedimientos, estandares)
- Catalogo en codigo: `triage_levels_manchester` (nivel, color, SLA objetivo)
- DB local actual: SQLite
- Fuente de verdad del esquema: Alembic (`alembic/versions`)

## Reglas actuales

- `title` obligatorio.
- `description` opcional.
- `completed` por defecto `False`.
- `username` obligatorio y unico.
- `hashed_password` obligatorio.
- `is_active` por defecto `True`.
- `is_superuser` por defecto `False`.
- `auth_sessions.jti` identifica cada refresh token emitido.
- `auth_sessions.is_revoked` invalida una sesion de refresh.
- `login_attempts` guarda contador de fallos y ventana de bloqueo.
- `agent_runs` guarda estado/coste/latencia global por ejecucion agente.
- `agent_steps` guarda traza detallada por paso (entrada/salida/decision/fallback/error).
- `care_tasks` representa trabajo clinico-operativo con SLA y revision humana.
- `care_task_chat_messages` guarda turnos de chat clinico por caso/sesion
  (consulta, respuesta, dominios sugeridos, hechos extraidos y memoria usada).
- El triaje de `care_tasks` reutiliza `agent_runs` y `agent_steps` con `workflow_name=care_task_triage_v1`.
- El chat clinico de `care_tasks` reutiliza `agent_runs` y `agent_steps` con `workflow_name=care_task_clinical_chat_v1`.
- El protocolo respiratorio reutiliza `agent_runs` y `agent_steps` con `workflow_name=respiratory_protocol_v1`.
- La humanizacion pediatrica reutiliza `agent_runs` y `agent_steps` con `workflow_name=pediatric_neuro_onco_support_v1`.
- El screening avanzado reutiliza `agent_runs` y `agent_steps` con `workflow_name=advanced_screening_support_v1`.
- El soporte RX torax reutiliza `agent_runs` y `agent_steps` con `workflow_name=chest_xray_support_v1`.
- El soporte diferencial de pitiriasis reutiliza `agent_runs` y `agent_steps` con `workflow_name=pityriasis_differential_support_v1`.
- El soporte diferencial acne/rosacea reutiliza `agent_runs` y `agent_steps` con `workflow_name=acne_rosacea_differential_support_v1`.
- El soporte operativo de trauma reutiliza `agent_runs` y `agent_steps` con `workflow_name=trauma_support_v1`.
- El soporte operativo critico transversal reutiliza `agent_runs` y `agent_steps` con `workflow_name=critical_ops_support_v1`.
- El soporte operativo neurologico reutiliza `agent_runs` y `agent_steps` con `workflow_name=neurology_support_v1`.
- El soporte operativo gastro-hepato reutiliza `agent_runs` y `agent_steps` con `workflow_name=gastro_hepato_support_v1`.
- El soporte operativo reuma-inmuno reutiliza `agent_runs` y `agent_steps` con `workflow_name=rheum_immuno_support_v1`.
- El soporte operativo de psiquiatria reutiliza `agent_runs` y `agent_steps` con `workflow_name=psychiatry_support_v1`.
- El soporte operativo de hematologia reutiliza `agent_runs` y `agent_steps` con `workflow_name=hematology_support_v1`.
- El soporte operativo de endocrinologia reutiliza `agent_runs` y `agent_steps` con `workflow_name=endocrinology_support_v1`.
- El soporte operativo de nefrologia reutiliza `agent_runs` y `agent_steps` con `workflow_name=nephrology_support_v1`.
- El soporte operativo de urologia reutiliza `agent_runs` y `agent_steps` con `workflow_name=urology_support_v1`.
- El soporte operativo de oftalmologia reutiliza `agent_runs` y `agent_steps` con `workflow_name=ophthalmology_support_v1`.
- El soporte operativo de inmunologia reutiliza `agent_runs` y `agent_steps` con `workflow_name=immunology_support_v1`.
- El soporte operativo de recurrencia genetica reutiliza `agent_runs` y `agent_steps` con `workflow_name=genetic_recurrence_support_v1`.
- El soporte operativo de ginecologia/obstetricia reutiliza `agent_runs` y `agent_steps` con `workflow_name=gynecology_obstetrics_support_v1`.
- El soporte operativo de pediatria/neonatologia reutiliza `agent_runs` y `agent_steps` con `workflow_name=pediatrics_neonatology_support_v1`.
- El soporte operativo de epidemiologia clinica reutiliza `agent_runs` y `agent_steps` con `workflow_name=epidemiology_support_v1`.
- El soporte operativo de anisakis reutiliza `agent_runs` y `agent_steps` con `workflow_name=anisakis_support_v1`.
- El soporte medico-legal reutiliza `agent_runs` y `agent_steps` con `workflow_name=medicolegal_ops_support_v1`.
- `care_task_triage_reviews` guarda decision humana (approved/rejected) por corrida de triaje.
- `care_task_triage_audit_logs` compara nivel IA vs nivel humano y clasifica `match/under/over`.
- `clinical_context` se mantiene versionado en codigo para consistencia de prompts y tests.
- `triage_levels_manchester` define prioridad base para estandarizar tiempos de atencion.
- El payload de protocolo respiratorio se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de humanizacion pediatrica se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de screening avanzado se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa y metricas de alertas.
- `care_task_screening_audit_logs` compara nivel global IA vs humano y coincidencia por reglas clave.
- El payload de soporte RX torax se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte diferencial de pitiriasis se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte diferencial acne/rosacea se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte de trauma se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte critico transversal se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte neurologico se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte gastro-hepato se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte reuma-inmuno se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte de psiquiatria se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte de hematologia se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte de endocrinologia se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte de nefrologia se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.

## TM-128

- Sin cambios de esquema ni migraciones.
- Persistencia/traabilidad ampliada en artefactos existentes:
  - `agent_runs.run_input.chat_input.local_evidence_items`
  - `care_task_chat_messages.knowledge_sources` incluye items `type=local_evidence`
  - `care_task_chat_messages.extracted_facts` puede incluir `evidencia_local:<modalidad>`.

## TM-129

- Sin cambios de esquema ni migraciones.
- Ingesta documental RAG ahora soporta extensiones `.pdf` ademas de `.md/.txt`.
- Los chunks de PDF se persisten en las mismas tablas:
  - `clinical_documents`
  - `document_chunks`

## TM-130

- Sin cambios de esquema ni migraciones.
- Persistencia/traabilidad ampliada en artefactos existentes:
  - `care_task_chat_messages.extracted_facts` puede incluir:
    - `logic_rule:<rule_id>`
    - `logic_contradictions:<n>`
  - `agent_runs.run_output.chat_output.logic_assessment` con reglas, acciones y contradicciones.

## TM-131

- Sin cambios de esquema ni migraciones.
- Persistencia/trazabilidad extendida en artefactos existentes:
  - `agent_runs.run_output.chat_output.logic_assessment` ahora puede incluir:
    - `protocol_sequence_ids`
    - `protocol_sequence_code`
    - `protocol_sequence_roundtrip_ok`
    - `protocol_beta_signature`
    - `consistency_status`
    - `abstention_required`
    - `abstention_reason`
  - `care_task_chat_messages.extracted_facts` puede incluir:
    - `logic_consistency:<status>`
    - `logic_abstention:1`

## TM-132

- Sin cambios de esquema ni migraciones.
- Persistencia/trazabilidad extendida en artefactos existentes:
  - `agent_runs.run_output.chat_output.contract_assessment` con:
    - `contract_id`, `contract_domain`, `contract_state`
    - `missing_data`, `steps_0_10`, `steps_10_60`
    - `escalation_criteria`, `force_structured_fallback`
  - `care_task_chat_messages.extracted_facts` puede incluir:
    - `contract_domain:<domain>`
    - `contract_state:<state>`
    - `contract_id:<id>`

## TM-133

- Sin cambios de esquema ni migraciones.
- Persistencia/trazabilidad extendida en artefactos existentes:
  - `agent_runs.run_output.chat_output.math_assessment` con:
    - `enabled`, `top_domain`, `top_probability`, `priority_score`
    - `margin_top2`, `normalized_entropy`, `uncertainty_level`, `abstention_recommended`
    - `posterior_topk`, `similarity_details`
  - `care_task_chat_messages.extracted_facts` puede incluir:
    - `math_top_domain:<domain>`
    - `math_priority_score:<score>`
- El payload de soporte de neumologia se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte geriatrico se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte oncologico se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte anestesiologico se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte paliativo se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte de urologia se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte de oftalmologia se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte de inmunologia se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte de recurrencia genetica se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte de ginecologia/obstetricia se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte de pediatria/neonatologia se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte de epidemiologia clinica se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El payload de soporte de anisakis se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- La salida persistida en `run_output.trauma_support` incluye `condition_matrix[]` para trazabilidad medico-operativa por patologia.
- El payload medico-legal se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- Extension bioetica pediatrica (TM-067) en payload medico-legal persistido en `run_input`:
  `legal_representatives_deceased`, `parental_religious_refusal_life_saving_treatment`,
  `life_threatening_condition`, `blood_transfusion_indicated`,
  `immediate_judicial_authorization_available`.
- TM-068 agrega en `run_output` medico-legal:
  `life_preserving_override_recommended`, `ethical_legal_basis`, `urgency_summary`.
- `care_task_medicolegal_audit_logs` compara riesgo legal IA vs humano y coincidencia en reglas de consentimiento, judicializacion y custodia.
- El soporte sepsis reutiliza `agent_runs` y `agent_steps` con `workflow_name=sepsis_protocol_support_v1`.
- El payload de sepsis se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- El soporte SCASEST reutiliza `agent_runs` y `agent_steps` con `workflow_name=scasest_protocol_support_v1`.
- El payload de SCASEST se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- `care_task_scasest_audit_logs` compara riesgo global SCASEST IA vs humano y coincidencia en escalado/estrategia antiisquemica.
- `care_task_cardio_risk_audit_logs` compara riesgo cardiovascular IA vs humano y coincidencia en objetivo no-HDL, estrategia farmacologica e intensidad de estilo de vida.
- El soporte de reanimacion reutiliza `agent_runs` y `agent_steps` con `workflow_name=resuscitation_protocol_support_v1`.
- El payload de reanimacion se persiste en trazas de `agent_runs` (`run_input`/`run_output`) para auditoria operativa.
- Extension obstetrica de reanimacion (TM-065) se persiste tambien en `run_input`:
  `gestational_weeks`, `uterine_fundus_at_or_above_umbilicus`, `minutes_since_arrest`,
  `access_above_diaphragm_secured`, `fetal_monitor_connected`,
  `magnesium_infusion_active`, `magnesium_toxicity_suspected`.
- Extension de terapia electrica (TM-066) se persiste tambien en `run_input`:
  `systolic_bp_mm_hg`, `diastolic_bp_mm_hg`.
- `care_task_resuscitation_audit_logs` compara severidad de reanimacion IA vs humano y coincidencia en choque, causas reversibles y plan de via aerea.
- `emergency_episodes` modela estado extremo-a-extremo del proceso de urgencias y timestamps para KPIs.
- El scorecard global de calidad IA se calcula en lectura agregando auditorias de triaje, screening, medico-legal y SCASEST (sin tabla nueva).
- El scorecard global de calidad IA incluye tambien auditorias cardiovasculares.
- TM-061 no agrega tablas ni migraciones; reutiliza auditorias existentes para evaluacion continua en CI.
- TM-065 no agrega tablas ni migraciones; extiende solo payload y logica del workflow de reanimacion.
- TM-066 no agrega tablas ni migraciones; extiende salida operativa de reanimacion con
  bloques de terapia electrica y sedoanalgesia.
- TM-067 no agrega tablas ni migraciones; extiende reglas del workflow medico-legal para
  conflicto bioetico pediatrico en riesgo vital.
- TM-068 no agrega tablas ni migraciones; extiende estructura de salida y explicabilidad
  del workflow medico-legal.
- TM-069 no agrega tablas ni migraciones; agrega nuevo workflow dermatologico en trazas
  (`pityriasis_differential_support_v1`) y metricas derivadas de `run_output`.
- TM-070 no agrega tablas ni migraciones; agrega workflow dermatologico
  (`acne_rosacea_differential_support_v1`) y metricas derivadas de `run_output`.
- TM-071 no agrega tablas ni migraciones; agrega workflow de trauma
  (`trauma_support_v1`) y metricas derivadas de `run_output`.
- TM-073 no agrega tablas ni migraciones; agrega workflow critico transversal
  (`critical_ops_support_v1`) y metricas derivadas de `run_output`.
- TM-074 no agrega tablas ni migraciones; agrega workflow neurologico
  (`neurology_support_v1`) y metricas derivadas de `run_output`.
- TM-075 no agrega tablas ni migraciones; agrega workflow gastro-hepato
  (`gastro_hepato_support_v1`) y metricas derivadas de `run_output`.
- TM-076 no agrega tablas ni migraciones; agrega workflow reuma-inmuno
  (`rheum_immuno_support_v1`) y metricas derivadas de `run_output`.
- TM-077 no agrega tablas ni migraciones; agrega workflow de psiquiatria
  (`psychiatry_support_v1`) y metricas derivadas de `run_output`.
- TM-078 no agrega tablas ni migraciones; agrega workflow de hematologia
  (`hematology_support_v1`) y metricas derivadas de `run_output`.
- TM-079 no agrega tablas ni migraciones; agrega workflow de endocrinologia
  (`endocrinology_support_v1`) y metricas derivadas de `run_output`.
- TM-080 no agrega tablas ni migraciones; agrega workflow de nefrologia
  (`nephrology_support_v1`) y metricas derivadas de `run_output`.
- TM-081 no agrega tablas ni migraciones; agrega workflow de neumologia
  (`pneumology_support_v1`) y metricas derivadas de `run_output`.
- TM-082 no agrega tablas ni migraciones; agrega workflow de geriatria
  (`geriatrics_support_v1`) y metricas derivadas de `run_output`.
- TM-083 no agrega tablas ni migraciones; agrega workflow de oncologia
  (`oncology_support_v1`) y metricas derivadas de `run_output`.
- TM-084 no agrega tablas ni migraciones; agrega workflow de anestesiologia/reanimacion
  (`anesthesiology_support_v1`) y metricas derivadas de `run_output`.
- TM-085 no agrega tablas ni migraciones; agrega workflow de cuidados paliativos
  (`palliative_support_v1`) y metricas derivadas de `run_output`.
- TM-086 no agrega tablas ni migraciones; agrega workflow de urologia
  (`urology_support_v1`) y metricas derivadas de `run_output`.
- TM-087 no agrega tablas ni migraciones; agrega workflow de anisakis
  (`anisakis_support_v1`) y metricas derivadas de `run_output`.
- TM-088 no agrega tablas ni migraciones; agrega workflow de epidemiologia clinica
  (`epidemiology_support_v1`) y metricas derivadas de `run_output`.
- TM-089 no agrega tablas ni migraciones; agrega workflow de oftalmologia
  (`ophthalmology_support_v1`) y metricas derivadas de `run_output`.
- TM-090 no agrega tablas ni migraciones; agrega workflow de inmunologia
  (`immunology_support_v1`) y metricas derivadas de `run_output`.
- TM-091 no agrega tablas ni migraciones; agrega workflow de recurrencia genetica
  (`genetic_recurrence_support_v1`) y metricas derivadas de `run_output`.
- TM-092 no agrega tablas ni migraciones; agrega workflow de ginecologia/obstetricia
  (`gynecology_obstetrics_support_v1`) y metricas derivadas de `run_output`.
- TM-093 no agrega tablas ni migraciones; agrega workflow de pediatria/neonatologia
  (`pediatrics_neonatology_support_v1`) y metricas derivadas de `run_output`.
- TM-094 agrega tabla `care_task_chat_messages` por migracion Alembic
  y workflow de chat `care_task_clinical_chat_v1` para trazabilidad conversacional.

## TM-095 Datos de especialidad autenticada y continuidad de paciente

- Migracion:
  - `alembic/versions/e8a1c4b7d552_add_chat_specialty_patient_context_fields.py`
- Cambios de esquema:
  - Tabla `users`:
    - Nuevo campo `specialty` (`String(80)`, no nulo, default `general`, indexado).
  - Tabla `care_tasks`:
    - Nuevo campo `patient_reference` (`String(120)`, nullable, indexado).
  - Tabla `care_task_chat_messages`:
    - Nuevo campo `effective_specialty` (`String(80)`, no nulo, default `general`, indexado).
    - Nuevo campo `knowledge_sources` (`JSON`, no nulo, default `[]`).
    - Nuevo campo `web_sources` (`JSON`, no nulo, default `[]`).
    - Nuevo campo `patient_history_facts_used` (`JSON`, no nulo, default `[]`).
- Reglas operativas nuevas:
  - `users.specialty` se usa como modo por defecto del chat autenticado.
  - `care_tasks.patient_reference` habilita agregacion longitudinal de memoria entre episodios.
  - Fuentes internas/web y hechos longitudinales quedan persistidos por turno para auditoria.
- Riesgos pendientes:
  - Si `patient_reference` no se normaliza, puede fragmentarse la historia longitudinal.

## TM-096 Datos de conocimiento clinico sellado

- Nuevas tablas:
  - `clinical_knowledge_sources`:
    - `specialty`, `title`, `summary`, `content`, `source_type`,
    - `source_url`, `source_domain`, `source_path`, `tags`,
    - `status` (`pending_review|validated|rejected|expired`),
    - `created_by_user_id`, `validated_by_user_id`, `validated_at`, `expires_at`.
  - `clinical_knowledge_source_validations`:
    - `source_id`, `reviewer_user_id`, `decision`, `note`, `created_at`.
- Restricciones operativas:
  - Fuentes con URL fuera de whitelist no se aceptan en alta ni sellado.
  - Chat prioriza `status=validated` y descarta expiradas (`expires_at`).
- Riesgos de datos:
  - Sin gobernanza de `expires_at` puede quedar evidencia obsoleta marcada como valida.
  - Sin normalizacion de `specialty`, puede fragmentarse el retrieval por especialidad.
  - JSON de fuentes puede crecer rapido en volumen alto y requerir politicas de retencion.

## Pendientes

- Definir ruta a PostgreSQL para entorno no local.
- AÃ±adir verificacion automatica de migraciones en CI.

## TM-038 Clinical Ops Pivot (Fase 1)

- Estrategia de datos:
  - No se migra ni elimina `tasks` en esta fase.
  - Se prepara transicion incremental hacia entidad paralela `care_tasks`.
- Nuevos campos planificados (fase posterior):
  - `clinical_priority` (low|medium|high|critical)
  - `specialty` (valor controlado)
  - `sla_target_minutes` (entero positivo)
  - `human_review_required` (bool)
  - `risk_flags` (json/lista)
- Criterio de seguridad:
  - Datos de entrenamiento/demo sin PHI real.
  - Cuando se usen datos sensibles: desidentificacion previa.



## TM-103

- Sin cambios de esquema DB ni migraciones.
- Persistencia existente de `care_task_chat_messages` se mantiene compatible.


## TM-105

- Sin cambios en modelos de datos, migraciones ni esquemas persistentes.
- Riesgo: nulo en capa de datos (cambio confinado a integracion HTTP con Ollama).


## TM-106

- Sin cambios de persistencia, modelos ni migraciones.


## TM-107

- Sin cambios en esquema de datos ni migraciones.

## TM-108

- Sin cambios de esquema ni nuevas migraciones.
- Cambio de payload solo en capa API de respuesta (`quality_metrics`), sin persistencia adicional.

## TM-109

- Sin cambios en modelos de datos, tablas, indices o migraciones Alembic.
- Sin cambios en politicas de retencion o persistencia.
- Impacto confinado a documentacion operativa y tooling de calidad en desarrollo.

## TM-113

- Migracion nueva:
  - `alembic/versions/d8c3f2e1a445_add_rag_tables.py`
- Tablas nuevas:
  - `clinical_documents`
    - metadata de documentos fuente (`title`, `source_file`, `specialty`, `content_hash`)
  - `document_chunks`
    - fragmentos enriquecidos (`chunk_text`, `section_path`, `keywords`, `custom_questions`)
    - embedding persistido en binario (`chunk_embedding`)
  - `rag_queries_audit`
    - auditoria por consulta RAG (`search_method`, `chunks_retrieved`, latencias)
- Reglas operativas:
  - `clinical_documents.content_hash` evita duplicados de fuente.
  - `document_chunks` referencia `clinical_documents.id` con `ON DELETE CASCADE`.
  - el chat no depende de estas tablas si RAG esta desactivado o vacio (fallback).
- Riesgos de datos:
  - en SQLite el retrieval vectorial es lineal y puede degradar con corpus grande.
  - embeddings fallback (hash local) priorizan continuidad operativa, no precision semantica alta.

## TM-114

- Sin cambios de esquema DB ni migraciones.
- Sin nuevas tablas, columnas o indices.
- Cambios operativos:
  - backend de retrieval puede usar `llamaindex` de forma opcional sobre el corpus ya persistido.
  - guardrails actua en capa de respuesta y no persiste datos adicionales estructurales.
- Riesgos de datos:
  - sin impacto de integridad relacional; riesgo principal es latencia por procesamiento adicional en runtime.

## TM-115

- Sin cambios de esquema DB ni migraciones.
- Sin nuevas tablas/columnas para Chroma en esta fase.
- Comportamiento de datos:
  - Chroma se usa como indice en memoria por consulta con embeddings ya persistidos en `document_chunks`.
  - no altera ni duplica persistencia principal del repositorio.
- Riesgos de datos:
  - reconstruccion de indice por consulta puede incrementar latencia con alto volumen de chunks.

## TM-126

- Sin cambios de esquema DB ni migraciones.
- Persistencia reutilizada:
  - `care_task_chat_messages.extracted_facts` puede incluir nuevos hechos:
    - `clarify_question:<feature>`
    - `clarify_turn:<n>`
- Riesgos de datos:
  - crecimiento leve de cardinalidad en `extracted_facts` por turnos de aclaracion.

## TM-127

- Sin cambios de esquema DB ni migraciones.
- Persistencia reutilizada:
  - `care_task_chat_messages.extracted_facts` puede incluir:
    - `risk_level:<low|medium|high>`
    - `risk_frame:<prospect_frame>`
    - `fechner_intensity:<valor>`
    - `fechner_change:<valor>`
- Riesgos de datos:
  - crecimiento leve de cardinalidad en hechos extraidos; sin impacto estructural.

## TM-141

- Sin cambios de esquema DB ni migraciones.
- Persistencia:
  - sin nuevas tablas, columnas ni indices.
- cambios confinados a recuperacion en memoria y validacion de respuesta.
- Riesgos de datos:
  - ningun riesgo estructural nuevo en almacenamiento.

## TM-142

- Sin cambios de esquema DB ni migraciones.
- Persistencia:
  - sin nuevas tablas/columnas.
  - mejora de pipeline de ingesta y retrieval sobre estructuras existentes.
- Riesgos de datos:
  - chunking mas fino puede aumentar numero total de `document_chunks` por documento largo.
  - requiere monitorizar crecimiento de storage y latencia de indexacion local.

## TM-143

- Sin cambios de esquema DB ni migraciones.
- Persistencia:
  - sin nuevas tablas/columnas/indices.
  - cambios confinados a scoring, ordenado y compresion en memoria durante retrieval.
- Riesgos de datos:
  - al usar compresion de contexto se reduce texto enviado al LLM; puede ocultar detalles si el chunk original es muy denso.

## TM-144

- Sin cambios en modelos ORM ni migraciones Alembic en esta fase.
- Persistencia:
  - se crea indice invertido FTS5 de forma lazy/best-effort en SQLite:
    - `document_chunks_fts` (virtual table)
    - triggers `document_chunks_fts_ai`, `document_chunks_fts_au`, `document_chunks_fts_ad`
  - origen de verdad de datos permanece en `document_chunks`.
- Riesgos de datos:
  - si SQLite local no soporta FTS5, se aplica fallback `full_scan` sin perder funcionalidad.
  - bootstrap FTS inicial puede añadir coste puntual en primera consulta tras despliegue.

## TM-145

- Sin cambios en modelos ORM ni migraciones Alembic en esta fase.
- Persistencia:
  - se reutiliza `document_chunks_fts_vocab` (vista virtual FTS5) para sugerencias ortograficas locales.
  - origen de verdad de documentos permanece en `document_chunks`.
- Riesgos de datos:
  - sugerencias ortograficas sobre vocabulario global pueden proponer terminos de otro dominio.
  - consultas con uso intensivo de operadores booleanos pueden aumentar CPU en etapa de candidatos.

## TM-146

- Sin cambios en modelos ORM ni migraciones Alembic en esta fase.
- Persistencia:
  - sin nuevas tablas/columnas; reutiliza `document_chunks`, `document_chunks_fts` y `document_chunks_fts_vocab`.
- Riesgos de datos:
  - `NOT` opera sobre universo acotado por candidate pool para mantener latencia.
  - `NEAR(...)` en FTS puede variar segun tokenizacion local de SQLite.

## TM-147

- Sin cambios en modelos ORM ni migraciones Alembic en esta fase.
- Persistencia:
  - sin nuevas tablas/columnas; reutiliza `document_chunks_fts_vocab` para expansion wildcard y sugerencias.
- Riesgos de datos:
  - wildcard con `*` puede expandir a terminos no deseados en vocabulario amplio si la consulta es demasiado corta.
  - Soundex aporta recall para terminos foneticos, con riesgo de colisiones semanticas en vocabularios clinicos tecnicos.

## TM-148

- Sin cambios en modelos ORM ni migraciones Alembic en esta fase.
- Persistencia:
  - sin nuevas tablas/columnas; reutiliza `document_chunks_fts` para conteo de bigramas contextuales.
- Riesgos de datos:
  - el ranking contextual depende de distribucion estadistica del corpus local, no de una verdad clinica externa.

## TM-149

- Sin cambios en modelos ORM ni migraciones Alembic en esta fase.
- Persistencia:
  - sin nuevas tablas/columnas; reutiliza `document_chunks_fts_vocab` para poblar cache en memoria.
- Riesgos de datos:
  - cache temporalmente stale hasta TTL en entornos con ingesta continua de documentos.

## TM-150

- Sin cambios en modelos ORM ni migraciones Alembic en esta fase.
- Persistencia:
  - sin nuevas tablas/columnas; la cache de postings es solo en memoria de proceso.
  - nuevo script de analitica lee `document_chunks` para estimaciones Heaps/Zipf.
- Riesgos de datos:
  - el script de estimacion depende de calidad de tokenizacion y puede requerir filtros por especialidad para resultados accionables.

## TM-151

- Sin cambios en modelos ORM ni migraciones Alembic en esta fase.
- Persistencia:
  - sin nuevas tablas/columnas; cambios confinados a scoring en memoria durante retrieval.
  - se aprovechan zonas ya existentes (`chunk_text`, `section_path`, `keywords`, `custom_questions`) y metadata del documento asociado (`title`, `source_file`).
- Riesgos de datos:
  - al ponderar zonas, cambios extremos en pesos pueden alterar ranking y coverage por especialidad.
  - `idf` calculado por pool candidato prioriza latencia sobre estabilidad global de la estadistica.

## TM-152

- Sin cambios en modelos ORM ni migraciones Alembic en esta fase.
- Persistencia:
  - sin nuevas tablas/columnas; scoring y tiering calculados en memoria durante retrieval.
  - se usan campos ya existentes (`chunk_text`, `section_path`, `keywords`, `custom_questions`, metadata de documento).
- Riesgos de datos:
  - heuristicas de calidad/proximidad pueden reordenar resultados en dominios con corpus pequeno o ruido lexical.

## TM-153

- Sin cambios en modelos ORM ni migraciones Alembic.
- Persistencia:
  - no altera datos de produccion.
  - opcion de reporte JSON (`--report-out`) genera artefacto local para auditoria offline.
- Riesgos de datos:
  - uso de `expected_terms` como gold de emergencia no sustituye juicios por doc_id/grade.

## TM-154

- Sin cambios en modelos ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - tesauro global en archivo local JSON (`docs/clinical_thesaurus_es_en.json`) cargado en memoria con cache TTL.
- Riesgos de datos:
  - sinonimos globales no curados pueden introducir expansion semantica no deseada.

## TM-155

- Sin cambios en modelos ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - scoring probabilistico BM25/BIM calculado en memoria sobre el candidate pool.
- Riesgos de datos:
  - al depender del candidate pool, el score probabilistico es relativo a la consulta y no global del corpus.

## TM-156

- Sin cambios en modelos ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - probabilidades de consulta/documento (QLM) calculadas en memoria durante scoring.
- Riesgos de datos:
  - QLM usa distribucion de terminos del candidate pool, por lo que su estimacion depende del set recuperado en primera fase.

## TM-157

- Sin cambios en modelos ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - clasificacion NB y rerank se calculan en memoria por consulta.
- Riesgos de datos:
  - el entrenamiento pseudo-supervisado se basa en catalogo local de dominios; la calidad depende de mantenimiento de keywords y descripciones.
## TM-158

- Sin cambios en modelos ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas; calculo de metricas en memoria.
- Riesgos de datos:
  - la interpretacion de macro/micro depende del balance de clases en el dataset de evaluacion.
## TM-159

- Sin cambios en modelos ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - entrenamiento/inferencia vectorial y evaluacion se ejecutan en memoria.
- Riesgos de datos:
  - la calidad de centroides y vecinos depende de la representatividad del catalogo pseudo-etiquetado.
## TM-160

- Sin cambios en modelos ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - entrenamiento/inferencia SVM de dominio y metricas de evaluacion se ejecutan en memoria.
- Riesgos de datos:
  - el entrenamiento pseudo-supervisado depende del catalogo de dominios y su curacion de keywords.
  - cambios fuertes en catalogo pueden requerir recalibrar umbral de confianza y escala de logits.

## TM-161

- Sin cambios en modelos ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - clustering y metricas se calculan en memoria por consulta.
- Riesgos de datos:
  - la calidad del clustering depende de la representatividad del catalogo y de la tokenizacion.
  - singleton clusters pueden aumentar en catálogos muy fragmentados y deben monitorizarse como señal de drift.

## TM-162

- Sin cambios en modelos ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - clustering jerarquico, etiquetado diferencial y metricas se calculan en memoria por consulta.
- Riesgos de datos:
  - la calidad del clustering depende de la representatividad del catalogo pseudo-etiquetado.
  - el etiquetado diferencial puede derivar en terminos poco estables cuando cambie el corpus de dominios.

## TM-163

- Sin cambios en modelos ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - la matriz termino-documento LSI se construye en memoria por consulta sobre el pool candidato.
- Riesgos de datos:
  - al operar sobre candidate pool (no corpus completo), la geometria latente es local a la consulta.
  - requerira recalibracion de blend/k si crece significativamente el tamano medio de pool.

## TM-164

- Sin cambios en modelos ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - el filtrado/ranking de fuentes web ocurre en memoria en runtime antes de persistir `web_sources` del turno.
- Riesgos de datos:
  - heuristicas de spam/duplicados pueden ocultar alguna fuente valida en consultas muy cortas; requiere ajuste por telemetria.
  - no existe verificacion fuerte de cloaking sin fetch/render de destino final.

## TM-165

- Sin cambios en modelos ORM ni migraciones Alembic.
- Persistencia:
  - salida documental del crawler en filesystem (`docs/web_raw/<host>/*.md`).
  - manifiesto en `docs/web_raw/crawl_manifest.jsonl`.
  - checkpoint de runtime en `tmp/web_crawl_checkpoint.json` (ajustable por CLI).
- Riesgos de datos:
  - el volumen de archivos en `docs/web_raw/` puede crecer rapido sin politica de retencion.
  - el checkpoint contiene estado operativo del frontier; limpiar si se cambia estrategia de rastreo.

## TM-166

- Sin cambios en modelos ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas en DB.
  - enriquecimiento del manifiesto de crawler en filesystem:
    - `outgoing_links`
    - `outgoing_anchor_texts`
    - `outgoing_edges`
  - nuevo snapshot de analisis de enlaces en filesystem:
    - `docs/web_raw/link_analysis_snapshot.json`.
- Riesgos de datos:
  - el snapshot puede quedar obsoleto si no se recompone tras nuevos crawls.
  - si el manifiesto crece mucho, el snapshot puede aumentar memoria en runtime.


## TM-171

- Sin cambios de esquema ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - ingesta masiva ejecutada sobre `docs/pdf_raw/*` con deduplicacion por `content_hash`.
- Volumen actualizado (entorno local de desarrollo):
  - `clinical_documents`: 256
  - `document_chunks`: 23907
  - documentos PDF ingeridos: 50
- Riesgos de datos:
  - crecimiento fuerte del corpus puede impactar cache/memoria si no se monitorea.
  - quedan chunks legacy con `specialty=NULL` de documentos no clinicos antiguos; retrieval clinico ahora los excluye.

## TM-172

- Sin cambios de esquema ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - optimizacion de pipeline de ingesta: pre-skip por `source_file` existente para reducir tiempo de ejecucion.
- Riesgos de datos:
  - cambios de contenido en archivo con misma ruta requieren `--force-reprocess-existing-paths`.

## TM-173

- Sin cambios de esquema ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - solo ajuste de logica runtime y configuracion de latencia/contexto.
- Riesgos de datos:
  - menor contexto por defecto puede omitir detalle historico si el cliente no ajusta limites en request.

## TM-174

- Sin cambios de esquema ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - ajuste de politica runtime de retrieval/contexto.
- Riesgos de datos:
  - menor fan-out puede omitir contexto marginal en consultas ambiguas; se mitiga con overrides por request.

## TM-175

- Sin cambios de esquema ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - cambios solo en pol?tica runtime de recuperaci?n.
- Riesgos de datos:
  - menor expansi?n l?xica por defecto puede perder alg?n candidato marginal en consultas ambiguas.


## TM-176

- Sin cambios de esquema ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - cambios solo de flujo runtime de respuesta/fallback.
- Riesgos de datos:
  - no aplica.

## TM-177

- Sin cambios de esquema ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - cambios solo en logica runtime de composicion de respuesta.
- Riesgos de datos:
  - no aplica.

## TM-178

- Sin cambios de esquema ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - cambios en ranking runtime y scripts de evaluacion local.
- Riesgos de datos:
  - no aplica.

## TM-179

- Sin cambios de esquema ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - cambios solo de configuracion runtime y scripts de benchmark.
- Riesgos de datos:
  - no aplica.

## TM-180

- Sin cambios de esquema ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - cambios solo en capa de inferencia LLM.
- Riesgos de datos:
  - no aplica.

## TM-187

- Sin cambios de esquema ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - ampliado mapeo de especialidades en `app.scripts.ingest_clinical_docs` para cobertura de `docs/40_*` a `docs/86_*` y `docs/pdf_raw/*`.
  - soporte de reconstruccion de `custom_questions` en chunks existentes (`--rebuild-custom-questions`).
- Riesgos de datos:
  - chunks legacy con texto tecnico/operativo pueden seguir presentes; se mitiga en runtime con filtro anti-ruido.
  - la reconstruccion masiva de `custom_questions` puede tardar en corpus grandes.

## TM-188

- Sin cambios de esquema ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - se aprovecha `document_chunks.content_type` existente para chunking tipado desde parser estructurado.
- Riesgos de datos:
  - documentos legacy siguen con chunking previo; para homogeneizar se recomienda reingesta incremental por rutas PDF criticas.
  - limpieza de artefactos puede eliminar algun encabezado util si coincide en todas las paginas.

## TM-189

- Cambios de datos persistidos:
  - no hay migraciones DB.
  - no se agregan tablas ni columnas.
- Cambios de calidad en pipeline:
  - durante ingesta se descartan documentos por reglas de calidad (`min_chunks`, `min_total_chars`, `min_avg_chunk_chars`, y reglas PDF por pagina/bloques).
  - se agregan contadores de rechazo en salida de script (`documents_rejected_quality`, `quality_rejection_reason_counts`).
- Riesgos de datos:
  - umbrales no calibrados pueden reducir recall del corpus si filtran contenido corto valido.

## TM-190

- Persistencia:
  - sin migraciones ni cambios de esquema.
- Datos derivados:
  - mejora de latencia via ruta keyword-only en retrieval hibrido para ciertos casos complejos.
  - mejora de scoring de calidad sin cambiar payload persistido.

## TM-191

- Persistencia:
  - sin migraciones DB.
- Politica de datos en runtime:
  - mayor peso lexical en consultas complejas para reducir costo de vector scoring.
  - decision de uso LLM condicionada por complejidad y relevancia de contexto.

## TM-193

- Persistencia:
  - sin migraciones DB ni cambios de esquema.
- Datos derivados en runtime:
  - retrieval remoto opcional contra indice Elastic (clinical_chunks) con filtros por especialidad.
  - sincronizacion de chunks al indice via `app.scripts.sync_chunks_to_elastic`.
- Riesgos de datos:
  - mapeos de indice no alineados pueden reducir recall y disparar fallback a legacy.

## TM-195 (Regression Set de chat y evaluacion continua offline)

- Impacto en datos persistidos:
  - sin cambios de schema en DB (sin migraciones).
- Nuevos artefactos de datos:
  - `tmp/chat_regression_set.jsonl` (export de pares `query`/`expected_answer` + constraints).
  - `tmp/chat_regression_eval_summary.json` (metricas agregadas de evaluacion).
- Formato base del item en regression set:
  - `id`, `care_task_id`, `session_id`, `query`, `expected_answer`,
    `expected_domains`, `must_include_terms`, `forbidden_terms`.
- Riesgos de datos:
  - posible sesgo por seleccionar historico reciente; el set debe regenerarse periodicamente.
  - no incluir PHI adicional fuera de lo ya registrado en `care_task_chat_messages`.

## TM-199

- Sin cambios de esquema ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - cambios solo de logica runtime de retrieval, scoring y composicion de respuesta.
- Riesgos de datos:
  - umbrales estrictos de actionability pueden reducir recall de snippets validos si no se calibran por subdominio.
  - la segmentacion multi-intento depende de marcadores lexicales; consultas muy cortas pueden no segmentar.

## TM-200

- Sin cambios de esquema ORM ni migraciones Alembic.
- Persistencia:
  - sin nuevas tablas/columnas.
  - enriquecimiento de contexto en runtime con metadatos derivados (`source_title`, `source_page`).
- Riesgos de datos:
  - umbral de verificacion alto puede reducir recall en consultas cortas o terminologia variable.
  - parseo de pagina por regex puede no detectar numeracion en todos los formatos de seccion.

## TM-201

- Sin cambios de modelo persistente ni migraciones.
- Cache de RAG y poda de estado implementadas en memoria de proceso (no persistente).
- Riesgo operativo: cache se reinicia al reiniciar proceso; comportamiento esperado para entorno local.

## TM-202

- Sin cambios de esquema ORM ni migraciones Alembic.
- Los puntajes de coherencia discursiva se calculan en runtime y se guardan en atributos efimeros del chunk (`_rag_discourse_score`, `_rag_rst_role`, `_rag_argument_zone`, `_rag_lcd_score`).
- Riesgo operativo: al ser heuristico, requiere ajuste por subdominio para equilibrar precision/recall.

## TM-203

- Sin cambios de esquema ORM ni migraciones Alembic.
- Nuevos puntajes efimeros por chunk en runtime:
  - `_rag_texttiling_score`
  - `_rag_lexical_chain_score`
  - `_rag_lsa_score`
  - `_rag_entity_grid_score`
- Riesgo operativo: aumento marginal de CPU por chunk; mitigado al ejecutarse sobre `top-k` ya recuperado.

