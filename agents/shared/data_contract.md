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
