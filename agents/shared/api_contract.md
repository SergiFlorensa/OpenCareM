# Notas de Contrato API

## Endpoint base

- Prefijo: `/api/v1`

## Recursos

- `tasks`
  - Crear: `POST /tasks/`
  - Listar: `GET /tasks/`
  - Obtener: `GET /tasks/{task_id}`
  - Actualizar: `PUT /tasks/{task_id}`
  - Eliminar: `DELETE /tasks/{task_id}`
  - Estadisticas: `GET /tasks/stats/count`
- `auth`
  - Login: `POST /auth/login`
  - Usuario actual: `GET /auth/me`
  - Registro: `POST /auth/register`
  - Rotacion de refresh token: `POST /auth/refresh`
  - Logout (revocacion refresh): `POST /auth/logout`
  - Lista de usuarios admin: `GET /auth/admin/users` (requiere rol admin)
- `ai`
  - Triaje de tarea: `POST /ai/triage-task`
  - La respuesta incluye `source` (`rules` | `llm` | `rules_fallback`)
- `agents`
  - Ejecutar workflow: `POST /agents/run`
  - Listar ejecuciones: `GET /agents/runs` (soporta `status`, `workflow_name`, `created_from`, `created_to`, `limit`)
  - Detalle de ejecucion: `GET /agents/runs/{run_id}`
  - Resumen operativo: `GET /agents/ops/summary` (soporta `workflow_name`)
- `care-tasks`
  - Crear: `POST /care-tasks/`
  - Listar: `GET /care-tasks/` (soporta `completed`, `clinical_priority`, `skip`, `limit`)
  - Obtener: `GET /care-tasks/{task_id}`
  - Actualizar: `PUT /care-tasks/{task_id}`
  - Eliminar: `DELETE /care-tasks/{task_id}`
  - Estadisticas: `GET /care-tasks/stats/count`
  - Scorecard global de calidad IA: `GET /care-tasks/quality/scorecard`
  - Triaje agente por recurso: `POST /care-tasks/{task_id}/triage`
  - Aprobacion humana de triaje: `POST /care-tasks/{task_id}/triage/approve`
  - Auditoria de triaje (IA vs humano): `POST /care-tasks/{task_id}/triage/audit`
  - Historial de auditoria: `GET /care-tasks/{task_id}/triage/audit`
  - Resumen de auditoria: `GET /care-tasks/{task_id}/triage/audit/summary`
  - Chat clinico-operativo (crear turno): `POST /care-tasks/{task_id}/chat/messages`
  - Historial de chat clinico: `GET /care-tasks/{task_id}/chat/messages`
  - Memoria agregada de chat clinico: `GET /care-tasks/{task_id}/chat/memory`
  - Recomendacion respiratoria operativa: `POST /care-tasks/{task_id}/respiratory-protocol/recommendation`
  - Recomendacion operativa de humanizacion pediatrica: `POST /care-tasks/{task_id}/humanization/recommendation`
  - Recomendacion de screening operativo avanzado: `POST /care-tasks/{task_id}/screening/recommendation`
  - Auditoria de screening avanzado: `POST /care-tasks/{task_id}/screening/audit`
  - Historial de auditoria screening: `GET /care-tasks/{task_id}/screening/audit`
  - Resumen de auditoria screening: `GET /care-tasks/{task_id}/screening/audit/summary`
  - Soporte de interpretacion RX torax: `POST /care-tasks/{task_id}/chest-xray/interpretation-support`
  - Soporte diferencial de pitiriasis: `POST /care-tasks/{task_id}/pityriasis-differential/recommendation`
  - Soporte diferencial acne/rosacea: `POST /care-tasks/{task_id}/acne-rosacea/recommendation`
  - Soporte operativo de trauma: `POST /care-tasks/{task_id}/trauma/recommendation`
  - Soporte operativo critico transversal: `POST /care-tasks/{task_id}/critical-ops/recommendation`
  - Soporte operativo neurologico: `POST /care-tasks/{task_id}/neurology/recommendation`
  - Soporte operativo gastro-hepato: `POST /care-tasks/{task_id}/gastro-hepato/recommendation`
  - Soporte operativo reuma-inmuno: `POST /care-tasks/{task_id}/rheum-immuno/recommendation`
  - Soporte operativo de psiquiatria: `POST /care-tasks/{task_id}/psychiatry/recommendation`
  - Soporte operativo de hematologia: `POST /care-tasks/{task_id}/hematology/recommendation`
  - Soporte operativo de endocrinologia: `POST /care-tasks/{task_id}/endocrinology/recommendation`
  - Soporte operativo de nefrologia: `POST /care-tasks/{task_id}/nephrology/recommendation`
  - Soporte operativo de oncologia: `POST /care-tasks/{task_id}/oncology/recommendation`
  - Soporte operativo de anestesiologia/reanimacion: `POST /care-tasks/{task_id}/anesthesiology/recommendation`
  - Soporte operativo de cuidados paliativos: `POST /care-tasks/{task_id}/palliative/recommendation`
  - Soporte operativo de urologia: `POST /care-tasks/{task_id}/urology/recommendation`
  - Soporte operativo de oftalmologia: `POST /care-tasks/{task_id}/ophthalmology/recommendation`
  - Soporte operativo de inmunologia: `POST /care-tasks/{task_id}/immunology/recommendation`
  - Soporte operativo de recurrencia genetica: `POST /care-tasks/{task_id}/genetic-recurrence/recommendation`
  - Soporte operativo de ginecologia/obstetricia: `POST /care-tasks/{task_id}/gynecology-obstetrics/recommendation`
  - Soporte operativo de pediatria/neonatologia: `POST /care-tasks/{task_id}/pediatrics-neonatology/recommendation`
  - Soporte operativo de epidemiologia clinica: `POST /care-tasks/{task_id}/epidemiology/recommendation`
  - Soporte operativo de anisakis: `POST /care-tasks/{task_id}/anisakis/recommendation`
  - Soporte operativo medico-legal: `POST /care-tasks/{task_id}/medicolegal/recommendation`
  - Auditoria medico-legal (IA vs humano): `POST /care-tasks/{task_id}/medicolegal/audit`
  - Historial auditoria medico-legal: `GET /care-tasks/{task_id}/medicolegal/audit`
  - Resumen auditoria medico-legal: `GET /care-tasks/{task_id}/medicolegal/audit/summary`
  - Recomendacion operativa sepsis: `POST /care-tasks/{task_id}/sepsis/recommendation`
  - Recomendacion operativa SCASEST: `POST /care-tasks/{task_id}/scasest/recommendation`
  - Auditoria SCASEST (IA vs humano): `POST /care-tasks/{task_id}/scasest/audit`
  - Historial auditoria SCASEST: `GET /care-tasks/{task_id}/scasest/audit`
  - Resumen auditoria SCASEST: `GET /care-tasks/{task_id}/scasest/audit/summary`
  - Recomendacion operativa riesgo cardiovascular: `POST /care-tasks/{task_id}/cardio-risk/recommendation`
  - Auditoria cardiovascular (IA vs humano): `POST /care-tasks/{task_id}/cardio-risk/audit`
  - Historial auditoria cardiovascular: `GET /care-tasks/{task_id}/cardio-risk/audit`
  - Resumen auditoria cardiovascular: `GET /care-tasks/{task_id}/cardio-risk/audit/summary`
  - Recomendacion operativa de reanimacion: `POST /care-tasks/{task_id}/resuscitation/recommendation`
  - Auditoria de reanimacion (IA vs humano): `POST /care-tasks/{task_id}/resuscitation/audit`
  - Historial auditoria de reanimacion: `GET /care-tasks/{task_id}/resuscitation/audit`
  - Resumen auditoria de reanimacion: `GET /care-tasks/{task_id}/resuscitation/audit/summary`
- `clinical-context`
  - Resumen de contexto: `GET /clinical-context/resumen`
  - Areas de urgencias: `GET /clinical-context/areas`
  - Circuitos de triaje operativo: `GET /clinical-context/circuitos`
  - Roles operativos: `GET /clinical-context/roles`
  - Checklists de procedimientos: `GET /clinical-context/procedimientos`
  - Detalle de procedimiento: `GET /clinical-context/procedimientos/{clave}`
  - Estandares operativos: `GET /clinical-context/estandares`
  - Niveles de triaje Manchester: `GET /clinical-context/triage-levels/manchester`
- `emergency-episodes`
  - Crear episodio: `POST /emergency-episodes/`
  - Listar episodios: `GET /emergency-episodes/`
  - Obtener episodio: `GET /emergency-episodes/{episode_id}`
  - Transicionar etapa: `POST /emergency-episodes/{episode_id}/transition`
  - Resumen KPI del episodio: `GET /emergency-episodes/{episode_id}/kpis`

## Campos principales de tarea

- `id: int`
- `title: str`
- `description: str | null`
- `completed: bool`
- `created_at: datetime`
- `updated_at: datetime`

## Riesgos de contrato

- Si cambia el prefijo API, actualizar MCP y docs.

## TM-128 (Evidencia local adjunta en chat clinico, sin cambio de endpoint)

- Endpoint afectado:
  - `POST /api/v1/care-tasks/{task_id}/chat/messages`
- Request extendido:
  - Nuevo campo opcional `local_evidence` (max 5 items).
  - Item:
    - `title: str` (obligatorio)
    - `modality: note|report|pdf|image|ehr_structured|lab_panel`
    - `source: str | null`
    - `content: str | null`
    - `metadata: dict[str, str]`
- Response:
  - Sin cambio de shape.
  - Efecto observable en:
    - `knowledge_sources` (entrada `type=local_evidence`)
    - `extracted_facts` (`evidencia_local:*`)
    - `interpretability_trace` (`local_evidence_items`, `local_evidence_modalities`).

## TM-130 (Motor logico clinico determinista, sin cambio de endpoint)

- Endpoint afectado:
  - `POST /api/v1/care-tasks/{task_id}/chat/messages`
- Request:
  - Sin cambios.
- Response:
  - Sin cambios de shape.
  - Trazas nuevas en `interpretability_trace`:
    - `logic_enabled`
    - `logic_rules_fired`
    - `logic_contradictions`
    - `logic_epistemic_facts`
    - `logic_rule_ids`

## TM-131 (Logica formal extendida, sin cambio de endpoint)

- Endpoint afectado:
  - `POST /api/v1/care-tasks/{task_id}/chat/messages`
- Request:
  - Sin cambios.
- Response:
  - Sin cambios de shape.
  - Trazas extendidas en `interpretability_trace`:
    - `logic_consistency_status`
    - `logic_abstention_required`
    - `logic_abstention_reason`
    - `logic_evidence_items`
    - `logic_structural_steps`
    - `logic_godel_code`
    - `logic_godel_roundtrip`
    - `logic_beta_signature`
    - `logic_first_escalation_step`
  - Fallback clinico puede incluir:
    - firma estructural del plan (Godel)
    - estado de consistencia formal
    - motivo de abstencion (cuando aplica)

## TM-132 (Contratos operativos por dominio, sin cambio de endpoint)

- Endpoint afectado:
  - `POST /api/v1/care-tasks/{task_id}/chat/messages`
- Request:
  - Sin cambios.
- Response:
  - Sin cambios de shape.
  - Trazas nuevas en `interpretability_trace`:
    - `contract_enabled`
    - `contract_domain`
    - `contract_id`
    - `contract_state`
    - `contract_has_trigger`
    - `contract_missing_data_count`
    - `contract_force_fallback`
  - Fallback clinico puede incluir bloque "Contrato operativo" con:
    - pasos 0-10 / 10-60
    - datos criticos faltantes
    - criterios de escalado contractuales

## TM-133 (Capa matematica de similitud + Bayes, sin cambio de endpoint)

- Endpoint afectado:
  - `POST /api/v1/care-tasks/{task_id}/chat/messages`
- Request:
  - Sin cambios.
- Response:
  - Sin cambios de shape.
  - Trazas nuevas en `interpretability_trace`:
    - `math_enabled`
    - `math_top_domain`
    - `math_top_probability`
    - `math_margin_top2`
    - `math_entropy`
    - `math_uncertainty_level`
    - `math_abstention_recommended`
    - `math_priority_score`
    - `math_domains_evaluated`
    - `math_model`
  - Fallback clinico puede incluir bloque "Bloque matematico de similitud" con:
    - dominio top por posterior
    - probabilidad posterior top
    - score de prioridad operativo
    - incertidumbre matematica (margen/entropia)
  - Efecto de comportamiento:
    - el dominio top matematico puede reordenar `matched_domains` cuando la confianza es suficiente.
- Si cambia la forma del token JWT (`sub`) ajustar dependencias de auth.
- Si cambia `CurrentUserResponse`, actualizar consumidores de `/auth/me`.
- Si cambian `workflow_name` o estructura de trazas de `/agents/run`, actualizar tests de agentes.
- Si cambia `TaskTriageResponse.source`, actualizar consumidores de `/ai/triage-task` y `AgentRun`.
- Si cambia la vista resumen/detalle de `/agents/runs`, actualizar dashboards y playbooks operativos.
- Si cambia el payload de `/care-tasks/{task_id}/triage`, actualizar integraciones de panel operacional.
- Si cambia el payload de `/care-tasks/{task_id}/triage/approve`, actualizar automatizaciones de cierre operacional.
- Si cambia el payload de `/care-tasks/{task_id}/triage/audit`, revisar comparadores under/over-triage y alertas.
- Si cambia el payload de `/care-tasks/{task_id}/chat/messages`, revisar integraciones de chat, memoria por sesion y trazabilidad de `care_task_clinical_chat_v1`.
- Si cambia el payload de `/care-tasks/{task_id}/chat/memory`, revisar paneles que reutilizan `top_domains` y `top_extracted_facts`.
- Si cambia el payload de `/care-tasks/{task_id}/respiratory-protocol/recommendation`, revisar flujos operativos de infecciones viricas y paneles de agentes.
- Si cambia el payload de `/care-tasks/{task_id}/humanization/recommendation`, revisar playbooks de comunicacion familiar y coordinacion multidisciplinar.
- Si cambia el payload de `/care-tasks/{task_id}/screening/recommendation`, revisar reglas de cribado temprano, umbrales geriatricos y control de fatiga de alertas.
- Si cambia el payload de `/care-tasks/{task_id}/screening/audit`, revisar calculo de under/over-screening y precision por regla.
- Si cambia el payload de `/care-tasks/{task_id}/chest-xray/interpretation-support`, revisar reglas de patrones/signos y red flags urgentes.
- Si cambia el payload de `/care-tasks/{task_id}/pityriasis-differential/recommendation`, revisar logica de clasificacion versicolor/rosada/alba y red flags dermatologicas.
- Si cambia el payload de `/care-tasks/{task_id}/acne-rosacea/recommendation`, revisar logica de diferencial acne/rosacea, escalado terapeutico y checklist de isotretinoina.
- Si cambia el payload de `/care-tasks/{task_id}/trauma/recommendation`, revisar reglas de curva trimodal, triada laringea, sindromes medulares, aplastamiento renal, hipotermia y Gustilo-Anderson.
  - La salida incluye `condition_matrix[]` con estructura:
    - `condition`
    - `classification_category`
    - `key_signs_symptoms`
    - `diagnostic_method`
    - `initial_immediate_treatment`
    - `definitive_surgical_treatment`
    - `technical_observations`
    - `source`
- Si cambia el payload de `/care-tasks/{task_id}/critical-ops/recommendation`, revisar reglas de SLA (ECG/Sepsis/Triage rojo), seleccion de oxigenoterapia, ruta de TEP por Wells, anafilaxia, perfil de shock, antidotos y red flags quirurgicas.
- Si cambia el payload de `/care-tasks/{task_id}/neurology/recommendation`, revisar reglas de HSA/ictus (incluyendo perfusion y ASPECTS), diferenciales neurologicos, alertas de contraindicacion en SGB y soporte de biomarcadores.
- Si cambia el payload de `/care-tasks/{task_id}/gastro-hepato/recommendation`, revisar reglas de trombosis portal, HDA en cirrosis, red flags de gas portal/neumatosis, Courvoisier, criterios quirurgicos y alertas de seguridad farmacologica.
- Si cambia el payload de `/care-tasks/{task_id}/rheum-immuno/recommendation`, revisar reglas de TEP en LES, isquemia digital en esclerosis, Behcet, anti-MDA5, seguridad materno-fetal y dominios IgG4/SAF.
- Si cambia el payload de `/care-tasks/{task_id}/psychiatry/recommendation`, revisar reglas temporales de estres/TEPT, riesgo suicida adolescente, seguridad en bipolaridad durante embarazo e insomnio geriatrico.
- Si cambia el payload de `/care-tasks/{task_id}/hematology/recommendation`, revisar reglas de MAT/SHU/TIH, seguridad de hemofilia con inhibidores, criterios de muestra en linfoma y checklist de esplenectomia.
- Si cambia el payload de `/care-tasks/{task_id}/endocrinology/recommendation`, revisar reglas de hipoglucemia hipocetosica, SIADH, incidentaloma suprarrenal, estadiaje DM1 y seguridad farmacologica en obesidad/riesgo CV.
- Si cambia el payload de `/care-tasks/{task_id}/nephrology/recommendation`, revisar reglas de FRA (prerrenal/parenquimatoso/obstructivo), sindrome renopulmonar, AEIOU, compensacion acido-base y seguridad de bloqueo RAAS.
- Si cambia el payload de `/care-tasks/{task_id}/pneumology/recommendation`, revisar diferenciales por imagen (NOC/bronquiolitis/NII), reglas de ventilacion (CPAP/BiPAP), escalado GOLD/asma biologica y seguridad por VO2 max.
- Si cambia el payload de `/care-tasks/{task_id}/geriatrics/recommendation`, revisar reglas de envejecimiento fisiologico, inmovilidad con balance nitrogenado negativo, bloqueo de benzodiacepinas en delirium y criterios START v3.
- Si cambia el payload de `/care-tasks/{task_id}/oncology/recommendation`, revisar reglas de checkpoint inhibitors, dMMR/MSI-high, hepatotoxicidad inmune grado >=3, FEVI pre-tratamiento, neutropenia febril y necrosis post-neoadyuvancia.
- Si cambia el payload de `/care-tasks/{task_id}/anesthesiology/recommendation`, revisar activacion ISR por estomago lleno, ventanas de preoxigenacion/intubacion, bloqueos de seguridad en via aerea y seleccion anatomica de bloqueos simpaticos.
- Si cambia el payload de `/care-tasks/{task_id}/palliative/recommendation`, revisar distincion etico-legal (rechazo/adecuacion/LO 3-2021), seguridad opioide en insuficiencia renal, decisiones de confort en demencia avanzada y manejo de delirium.
- Si cambia el payload de `/care-tasks/{task_id}/urology/recommendation`, revisar reglas de PFE, prioridad de derivacion en FRA obstructivo, bloqueo de sondaje en trauma genital y estrategia sistemica en prostata metastasica de alto volumen.
- Si cambia el payload de `/care-tasks/{task_id}/ophthalmology/recommendation`, revisar reglas de triaje OVCR/OACR por fondo de ojo, localizacion pupilar aferente/eferente, diferencial de superficie ocular, riesgo IFIS por tamsulosina y clasificacion DMAE seca/humeda.
- Si cambia el payload de `/care-tasks/{task_id}/immunology/recommendation`, revisar reglas de Bruton/BTK, perfil CD19/CD20 e inmunoglobulinas, ventana de IgG materna, defensa innata pulmonar y diferenciales humorales (IgA/Hiper-IgM/CVID).
- Si cambia el payload de `/care-tasks/{task_id}/genetic-recurrence/recommendation`, revisar regla de alerta de mosaicismo en recurrencia dominante con padres sanos, descarte de de novo aislado, diferencial recesivo/penetrancia y consistencia de riesgo por fraccion germinal mutada.
- Si cambia el payload de `/care-tasks/{task_id}/gynecology-obstetrics/recommendation`, revisar reglas de Lynch/Amsterdam II, triaje de ectopico/rotura, datacion CRL-CIR-STFF, varicela gestacional, preeclampsia grave y bloqueos de seguridad terapeutica (diureticos en linfedema, neuroproteccion y ACO).
- Si cambia el payload de `/care-tasks/{task_id}/pediatrics-neonatology/recommendation`, revisar reglas de sarampion (triada+Koplik+aislamiento), objetivos SatO2 y CPAP neonatal, profilaxis de contactos de tosferina, alertas de invaginacion y estigmas de sifilis congenita.
- Si cambia el payload de `/care-tasks/{task_id}/epidemiology/recommendation`, revisar calculos de incidencia/prevalencia/densidad, formula de NNT, semantica condicional de RR causal y clasificacion coste-utilidad por AVAC/QALY.
- Si cambia el payload de `/care-tasks/{task_id}/anisakis/recommendation`, revisar reglas de latencia post-ingesta, disparo alergico (urticaria/anafilaxia), solicitud de IgE especifica y recomendaciones de congelacion/coccion al alta.
- Si cambia el payload de `/care-tasks/{task_id}/medicolegal/recommendation`, revisar checklist legal, reglas de custodia y alertas de riesgo juridico.
- Extension bioetica pediatrica en `/care-tasks/{task_id}/medicolegal/recommendation`:
  - Campos opcionales: `legal_representatives_deceased`, `parental_religious_refusal_life_saving_treatment`, `life_threatening_condition`, `blood_transfusion_indicated`, `immediate_judicial_authorization_available`.
  - La salida puede reforzar `critical_legal_alerts`, `required_documents`, `operational_actions` y `compliance_checklist` cuando existe conflicto de representacion en menor con riesgo vital.
- Salida estructurada adicional en medico-legal:
  - `life_preserving_override_recommended`
  - `ethical_legal_basis`
  - `urgency_summary`
- Si cambia el payload de `/care-tasks/{task_id}/medicolegal/audit`, revisar clasificacion under/over legal y tasas de match por regla.
- Si cambia el payload de `/care-tasks/{task_id}/sepsis/recommendation`, revisar qSOFA, bundle de 1 hora y reglas de escalado.
- Si cambia el payload de `/care-tasks/{task_id}/scasest/recommendation`, revisar reglas de sospecha/riesgo alto, acciones iniciales y escalado cardiologico.
- Si cambia el payload de `/care-tasks/{task_id}/scasest/audit`, revisar clasificacion under/over SCASEST y tasas de match por regla.
- Si cambia el payload de `/care-tasks/{task_id}/cardio-risk/recommendation`, revisar estratificacion de riesgo, objetivos lipidemicos y criterios de escalado.
- Si cambia el payload de `/care-tasks/{task_id}/cardio-risk/audit`, revisar clasificacion under/over cardiovascular y precision por regla.
- Si cambia el payload de `/care-tasks/{task_id}/resuscitation/recommendation`, revisar reglas de RCP, ritmo/choque, ventilacion y alertas SLA.
- Extension obstetrica de `/care-tasks/{task_id}/resuscitation/recommendation`:
  - Campos opcionales: `gestational_weeks`, `uterine_fundus_at_or_above_umbilicus`, `minutes_since_arrest`, `access_above_diaphragm_secured`, `fetal_monitor_connected`, `magnesium_infusion_active`, `magnesium_toxicity_suspected`.
  - Salida mantiene contrato base y amplia `special_situation_actions`, `reversible_causes_checklist` y `alerts` en escenarios de gestacion critica.
- Extension de terapia electrica en `/care-tasks/{task_id}/resuscitation/recommendation`:
  - Campos opcionales: `systolic_bp_mm_hg`, `diastolic_bp_mm_hg`.
  - Nuevos bloques de salida:
    - `electrical_therapy_plan`
    - `sedoanalgesia_plan`
    - `pre_shock_safety_checklist`
- Si cambia el payload de `/care-tasks/{task_id}/resuscitation/audit`, revisar clasificacion under/over de reanimacion y precision por regla.
- Si cambia el payload de `/care-tasks/quality/scorecard`, revisar paneles y runbooks que consumen calidad global.
- Si cambia el contexto de `/clinical-context/*`, actualizar prompts de agentes y escenarios de pruebas.
- Si cambia el catalogo Manchester, revisar reglas de priorizacion y paneles de SLA.
- Si cambia el flujo de `/emergency-episodes/*`, revisar reglas de transicion, KPIs y paneles de operacion.

## Politica de errores actual

- `400`: reglas de negocio invalidadas (ej. registro).
- `401`: autenticacion/token invalido.
- `429`: limite de intentos de login superado temporalmente.
- `403`: autenticado sin permisos suficientes.
- `404`: recurso inexistente.
- `422`: validacion de payload/params por FastAPI.

## TM-038 Clinical Ops Pivot (Fase 1)

- Objetivo de contrato:
  - Mantener compatibilidad con `tasks` mientras se introduce vocabulario clinico-operativo.
- No cambia en Fase 1:
  - Endpoints actuales de `tasks`, `agents`, `auth`, `ai`.
- Cambios previstos por etapas (sin ejecutar aun):
  - `CareTask` como recurso paralelo a `Task` (sin eliminar `Task` en esta fase).
  - Campos operativos: `clinical_priority`, `specialty`, `sla_target_minutes`, `human_review_required`.
  - Endpoint de triage agente adaptado a contexto clinico-operativo no diagnostico.
- Barreras de dominio:
  - El sistema no debe dar diagnostico medico.
  - El sistema solo clasifica y prioriza operaciones.

## TM-058 Scorecard global de calidad IA clinica

- Cambio de contrato planificado:
  - Nuevo endpoint agregado:
    - `GET /care-tasks/quality/scorecard`
- Proposito:
  - Entregar un resumen unico de calidad de auditorias para triaje, screening, medico-legal y SCASEST.
- Compatibilidad:
  - No rompe endpoints existentes.
  - Solo agrega una vista de lectura orientada a observabilidad.

## TM-061 Evaluacion continua y gate CI

- Cambio de contrato:
  - Sin nuevos endpoints.
  - Se introduce validacion de regresion funcional sobre endpoint existente:
    - `GET /care-tasks/quality/scorecard`
- Objetivo:
  - Bloquear cambios que degraden tasas globales (under/over/match) fuera de umbral operativo.
- Riesgo de contrato:
  - Si cambia la semantica de `quality_status` o de tasas (`under_rate_percent`, `over_rate_percent`, `match_rate_percent`), actualizar tests del gate y umbrales de CI.

## TM-095 Chat por especialidad y contexto longitudinal

- Cambios de contrato en `auth`:
  - `POST /auth/register` acepta `specialty` (opcional, default `general`).
  - `GET /auth/me` agrega `specialty` en respuesta.
  - `GET /auth/admin/users` agrega `specialty` por usuario.
- Cambios de contrato en `care-tasks`:
  - `CareTask` agrega `patient_reference` (nullable).
  - `GET /care-tasks/` acepta filtro opcional `patient_reference`.
  - `GET /care-tasks/stats/count` acepta filtro opcional `patient_reference`.
- Cambios de contrato en chat de `care-tasks`:
  - `POST /care-tasks/{task_id}/chat/messages`, `GET /chat/messages` y `GET /chat/memory` requieren autenticacion (`Bearer`).
  - Request de `POST /chat/messages` agrega:
    - `use_authenticated_specialty_mode`
    - `use_patient_history`
    - `max_patient_history_messages`
    - `use_web_sources`

## TM-110 Chat automatico por intencion (sin especialidad manual)

- Cambio de contrato (compatibilidad mantenida):
  - `POST /care-tasks/{task_id}/chat/messages` mantiene el campo `use_authenticated_specialty_mode`, pero el valor por defecto ahora es `false`.
  - El backend infiere dominio/especialidad efectiva desde la propia consulta (`query`) antes de usar perfil autenticado o especialidad del caso.
- Impacto esperado:
  - El medico puede entrar y preguntar en lenguaje natural sin seleccionar especialidad de consulta.
  - Mayor probabilidad de recuperar fuentes internas de dominios como pediatria/oncologia aunque el usuario este en perfil `emergency`.
- Riesgo de contrato:
  - Consumidores que asumian sesgo fijo por especialidad autenticada deben revisar trazas `effective_specialty` y `matched_domains`.

## TM-117 Estabilidad de respuesta local y fuentes internas en desarrollo

- Cambios sin ruptura de contrato:
  - Sin nuevos endpoints ni cambios de payload obligatorios.
  - En `ENVIRONMENT=development`, si no hay fuentes validadas en BD, el chat puede usar fallback al catalogo interno documental para evitar respuestas vacias de evidencia.
  - Estrategia LLM local con `keep_alive` y ruta de recuperacion rapida ante timeout para reducir casos `llm_used=false`.
- Impacto esperado:
  - Menos respuestas degradadas por ausencia de fuentes validadas en entornos de practica local.
  - Menos timeouts acumulados (chat + generate) en CPU local.
    - `max_web_sources`
    - `max_internal_sources`
  - Response de `POST /chat/messages` agrega:
    - `effective_specialty`
    - `knowledge_sources[]`
    - `web_sources[]`
    - `patient_history_facts_used[]`
  - Historial `GET /chat/messages` agrega por item:
    - `effective_specialty`
    - `knowledge_sources[]`
    - `web_sources[]`
    - `patient_history_facts_used[]`
  - Memoria `GET /chat/memory` agrega:
    - `patient_reference`
    - `patient_interactions_count`
    - `patient_top_domains[]`
    - `patient_top_extracted_facts[]`
- Riesgos de contrato:
  - Si se elimina `specialty` de `auth`, se rompe modo especialidad por credencial.
  - Si se elimina `patient_reference` de `care_tasks`, se degrada memoria longitudinal entre episodios.
  - Si se cambian campos de fuentes (`knowledge_sources`, `web_sources`), se afectan consumers de frontend/auditoria.

## TM-096 Fuentes confiables y whitelist estricta

- Nuevos endpoints:
  - `POST /api/v1/knowledge-sources/` (auth): registra fuente en `pending_review`.
  - `GET /api/v1/knowledge-sources/` (auth): lista fuentes (por defecto `validated_only=true`).
  - `POST /api/v1/knowledge-sources/{source_id}/seal` (solo admin): `approve|reject|expire`.
  - `GET /api/v1/knowledge-sources/{source_id}/validations` (auth): historial de sellado.
  - `GET /api/v1/knowledge-sources/trusted-domains` (auth): whitelist activa.
- Cambios de comportamiento en chat:
  - `POST /care-tasks/{task_id}/chat/messages`:
    - fuentes web solo se incluyen si el dominio pertenece a whitelist.
    - fuentes internas priorizan registro validado (`clinical_knowledge_sources`).
    - si no hay evidencia validada, la respuesta lo explicita.
- Riesgos de contrato:
  - Si frontend asume que `knowledge_sources` siempre contiene items, debe adaptarse al caso vacio.
  - Si se cambia whitelist sin control de version, puede alterarse trazabilidad de respuestas entre despliegues.

## TM-098 Frontend MVP chat clinico (sin cambios de contrato)

- No se agregan endpoints nuevos ni se modifican payloads de API.
- El frontend consume:
  - `POST /auth/login`
  - `GET /auth/me`
  - `POST/GET /care-tasks`
  - `POST /care-tasks/{task_id}/chat/messages`
  - `GET /care-tasks/{task_id}/chat/messages`
  - `GET /care-tasks/{task_id}/chat/memory`
- Riesgos de integracion:
  - Si cambia el esquema de `chat/messages` o `chat/memory`, se impacta panel de trazabilidad del frontend.
  - Si CORS no incluye origen de Vite (`5173`), el frontend no podra consumir API en navegador.

## TM-099 Chat hibrido con herramientas (cambio de contrato)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Request agrega campos opcionales:
  - `conversation_mode`: `auto | general | clinical` (default `auto`)
  - `tool_mode`: `chat | medication | cases | treatment | deep_search | images` (default `chat`)
- Response agrega:
  - `response_mode`: `general | clinical`
  - `tool_mode`: replica herramienta aplicada por el motor
- Compatibilidad:
  - Clientes antiguos siguen funcionando sin enviar los nuevos campos.
- Comportamiento:
  - `deep_search` fuerza consulta web (whitelist) y aumenta `max_web_sources`.
  - `response_mode` pasa a trazabilidad para frontend y auditoria.
- Riesgos:
  - Frontend que no contemple `response_mode/tool_mode` perdera contexto de UX.
  - Seleccion de `general` no desactiva medidas de seguridad web/whitelist.

## TM-100 Motor neuronal local (sin cambio de payload)

- No se agregan endpoints ni campos nuevos.
- Cambia el comportamiento interno de `POST /care-tasks/{task_id}/chat/messages`:
  - si `CLINICAL_CHAT_LLM_ENABLED=true`, intenta generacion con Ollama.
  - si falla, retorna respuesta de fallback rule-based.
- `interpretability_trace` puede incluir:
  - `llm_used=...`
  - `llm_provider=...`
  - `llm_model=...`
  - `llm_latency_ms=...`
- Riesgos:
  - Si el entorno no expone Ollama en `CLINICAL_CHAT_LLM_BASE_URL`, se activara fallback.

## TM-101 Continuidad conversacional (sin cambio de payload)

- No se agregan endpoints ni campos nuevos.
- Se ajusta el comportamiento interno de `POST /care-tasks/{task_id}/chat/messages`:
  - La memoria reutilizable excluye hechos de control (`modo_respuesta:*`, `herramienta:*`).
  - El motor LLM recibe resumen de dialogo previo de la sesion (`recent_dialogue`) para mantener hilo.
  - El fallback rule-based incorpora referencia al turno previo cuando existe historial.
- Compatibilidad:
  - Contrato externo inalterado.
  - Mejora de coherencia en `answer` y `memory_facts_used`.
- Riesgos:
  - Cambiar de `session_id` invalida continuidad (comportamiento esperado).

## TM-102 Calidad conversacional local avanzada (sin cambio de payload)

- No se agregan endpoints ni campos nuevos.
- Cambios internos en `POST /care-tasks/{task_id}/chat/messages`:
  - consultas de seguimiento cortas se expanden con el ultimo turno (`query_expanded`) para mejorar matching y recuperacion.
  - proveedor Ollama intenta primero `POST /api/chat` con historial reciente, y si falla usa `POST /api/generate`.
  - el fallback clinico cambia a formato accionable por pasos (priorizacion, contexto, evidencia, cierre).
- Cambios de trazabilidad:
  - `interpretability_trace` agrega `query_expanded=0|1`.
  - `interpretability_trace` puede incluir `llm_endpoint=chat|generate`.
- Compatibilidad:
  - contrato externo estable; clientes existentes no requieren cambios.
- Riesgos:
  - rendimiento y naturalidad dependen del modelo local/hardware.



## TM-103 (chat clinico operativo avanzado)

- Se mantiene contrato existente de `POST /api/v1/care-tasks/{task_id}/chat/messages` sin romper rutas.
- Cambios backward compatible:
  - se amplian trazas internas (`interpretability_trace`) con llaves: `matched_endpoints`, `endpoint_recommendations`, `llm_model` en escenarios sin LLM.
  - no se elimina ningun campo existente de request/response.
- Compatibilidad:
  - clientes actuales siguen funcionando aunque ignoren nuevas entradas de traza.


## TM-105 (robustez parseo Ollama, sin cambio de payload)

- No se agregan endpoints ni campos nuevos en request/response de chat.
- Cambia comportamiento interno del proveedor LLM:
  - parseo tolerante de respuesta Ollama para formatos JSON unico, JSONL chunked y lineas prefijadas con `data:`.
  - extraccion robusta de contenido en `message.content`, `response` o `content`.
- Compatibilidad:
  - contrato externo estable y backward compatible.
- Riesgos:
  - integraciones via proxy que alteren framing HTTP pueden requerir cabeceras adicionales en runtime.


## TM-106 (higiene de respuesta general, sin cambio de payload)

- Sin cambios de rutas ni esquema request/response.
- Cambios internos:
  - en `response_mode=general` se evita imprimir snippets tecnicos crudos (JSON) en salida de fallback.
  - recomendaciones de endpoints se incorporan al contexto solo en `response_mode=clinical`.
- Compatibilidad:
  - contrato externo se mantiene backward compatible.


## TM-107 (hilos conversacionales y politica de fuentes, sin cambio de payload)

- No se agregan endpoints ni campos nuevos de request/response.
- Cambios internos:
  - fallback/response general mas humano: muestra dominios disponibles y solicita datos minimos del caso.
  - trazabilidad ampliada en `interpretability_trace` con:
    - `reasoning_threads=intent>context>sources>actions`
    - `source_policy=internal_first_web_whitelist`
- Compatibilidad: contrato publico estable.

## TM-108 (chat local endurecido, cambio de contrato)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Cambio de response (backward compatible para consumidores tolerantes a campos nuevos):
  - nuevo bloque obligatorio `quality_metrics`:
    - `answer_relevance` (`0..1`)
    - `context_relevance` (`0..1`)
    - `groundedness` (`0..1`)
    - `quality_status` (`ok | attention | degraded`)
- Cambios internos de comportamiento:
  - sanitizacion anti-prompt-injection sobre consulta de usuario antes de construir prompt.
  - control de presupuesto de contexto/tokens para mensajes enviados a Ollama.
  - nuevas trazas en `interpretability_trace`:
    - `prompt_injection_detected`
    - `prompt_injection_signals`
    - `query_sanitized`
    - `quality_status`
    - `answer_relevance`, `context_relevance`, `groundedness`
    - `llm_input_tokens_budget`, `llm_input_tokens_estimated`, `llm_prompt_truncated`
- Riesgos de contrato:
  - clientes con deserializacion estricta del schema anterior deben aceptar `quality_metrics`.

## TM-109 (adaptacion blueprint OSS interno)

- No se agregan endpoints nuevos ni se eliminan endpoints existentes.
- No se cambian schemas de request/response de recursos API.
- Impacto acotado a estandarizacion operativa de desarrollo:
  - scripts de flujo local (`scripts/dev_workflow.ps1`)
  - hooks staged (`.pre-commit-config.yaml`)
  - guia de adopcion (`docs/96_adaptacion_blueprint_agentes_oss_interno.md`)
- Compatibilidad:
  - contrato publico de API se mantiene estable y backward compatible.

## TM-113 (RAG hibrido integrado en chat, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios de request/response.
  - se mantiene compatibilidad con clientes existentes.
- Cambios internos:
  - el chat clinico puede ejecutar pipeline RAG cuando `CLINICAL_CHAT_RAG_ENABLED=true`.
  - trazabilidad ampliada en `interpretability_trace` con llaves `rag_*`:
    - `rag_status`
    - `rag_chunks_retrieved`
    - `rag_retrieval_strategy`
    - `rag_validation_status`
    - `rag_total_latency_ms`
  - si RAG no recupera contexto o falla, se mantiene fallback seguro al flujo actual.
- Riesgos de contrato:
  - clientes que parsean `interpretability_trace` con reglas estrictas deben tolerar entradas nuevas `rag_*`.

## TM-114 (LlamaIndex + NeMo Guardrails opcionales, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios de request/response.
  - no se agregan endpoints.
- Cambios internos:
  - retrieval RAG configurable por backend:
    - `legacy` (actual)
    - `llamaindex` (opcional, con fallback automatico a `legacy` si falla/no disponible)
  - capa de validacion de salida con NeMo Guardrails (opcional, fail-open por defecto).
  - trazabilidad ampliada en `interpretability_trace`:
    - `rag_retriever_backend`
    - `rag_retriever_fallback`
    - `llamaindex_*`
    - `guardrails_status`
    - `guardrails_loaded`
    - `guardrails_fail_mode`
- Riesgos de contrato:
  - clientes que parsean `interpretability_trace` de forma estricta deben tolerar nuevas claves.

## TM-115 (Chroma opcional, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios de request/response.
  - no se agregan endpoints.
- Cambios internos:
  - backend retrieval `chroma` disponible por flag:
    - `CLINICAL_CHAT_RAG_RETRIEVER_BACKEND=chroma`
  - fallback automatico a retriever `legacy` cuando:
    - no esta instalada dependencia `chromadb`,
    - no hay resultados,
    - ocurre error en runtime.
  - trazabilidad ampliada:
    - `chroma_available`
    - `chroma_candidates`
    - `chroma_chunks_found`
    - `chroma_latency_ms`
    - `chroma_error` (si aplica)
- Riesgos de contrato:
  - consumidores que parsean trazas con whitelist estricta deben aceptar nuevas claves `chroma_*`.

## TM-116 (rediseno frontend chat, sin cambio de payload)

- Endpoints afectados:
  - `POST /care-tasks/{task_id}/chat/messages`
  - `GET /care-tasks/{task_id}/chat/messages`
  - `GET /care-tasks/{task_id}/chat/memory`
- Contrato externo:
  - sin cambios en rutas, request ni response.
  - no se agregan campos API.
- Cambios de cliente:
  - el frontend consume y presenta trazabilidad existente (`interpretability_trace`) para:
    - estado de typing/render progresivo,
    - nivel de confianza (derivado de `groundedness`),
    - panel expandible de fuentes exactas por turno.
- Riesgos de contrato:
  - ninguno nuevo; compatibilidad completa con API actual.

## TM-118 (quality gate clinico final y deteccion clinica robusta, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios de request/response.
  - no se agregan endpoints.
- Cambios internos:
  - deteccion clinica mas robusta en `conversation_mode=auto` para lenguaje de caso:
    - terminos adicionales como `pediatrico`, `paciente`, `sospecha`, `febril`, `disnea`, etc.
  - compuerta final de calidad para respuesta clinica cuando guardrails esta desactivado:
    - si el texto final queda generico/no accionable, se fuerza fallback estructurado.
  - trazabilidad ampliada:
    - `clinical_answer_quality_gate=final_structured_fallback` (cuando aplica).
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar la nueva clave.

## TM-119 (reestructuracion RAG clinico + ingesta progresiva por especialidad, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan rutas nuevas.
- Cambios internos:
  - `RAGOrchestrator` filtra resultados de busqueda por especialidad efectiva cuando la estrategia es por dominio.
  - `ingest_clinical_docs` pasa a orientarse a corpus clinico:
    - default `--paths docs`
    - mapeo de especialidad por defecto para `docs/45_*` a `docs/86_*`
    - `--backfill-specialty` y `--backfill-only` para rellenar `specialty` en registros existentes.
  - `DocumentIngestionService` normaliza paths para matching estable en Windows/Linux.
- Riesgos de contrato:
  - clientes que parsean trazas de retrieval deben tolerar nueva clave opcional:
    - `domain_search_filtered_out`.

## TM-126 (interrogatorio clinico activo Bayes+DEIG, cambio menor de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Cambios de request:
  - nuevos campos opcionales:
    - `enable_active_interrogation: bool` (default `false`)
    - `interrogation_max_turns: int` (default `3`, rango `1..10`)
    - `interrogation_confidence_threshold: float` (default `0.93`, rango `0.5..0.99`)
- Comportamiento nuevo:
  - cuando `enable_active_interrogation=true` y el dominio soportado tiene incertidumbre alta,
    el chat devuelve primero una pregunta de aclaracion en lugar de cerrar plan final.
  - trazabilidad ampliada con:
    - `interrogatory_enabled`
    - `interrogatory_active`
    - `interrogatory_reason`
    - `interrogatory_domain` (si aplica)
    - `deig_score` (si aplica)
    - `interrogatory_entropy` (si aplica)
    - `interrogatory_top_probability` (si aplica)
- Riesgos de contrato:
  - clientes que asumen respuesta final en todos los turnos deben soportar turnos de aclaracion.

## TM-127 (Fechner + Prospect framing en chat clinico, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response estructural.
- Cambios internos:
  - trazabilidad ampliada en `interpretability_trace` con:
    - `psychology_enabled`
    - `prospect_risk_level`
    - `prospect_frame`
    - `prospect_risk_score`
    - `prospect_signals`
    - `fechner_intensity`
    - `fechner_change`
  - en fallback clinico puede incluir bloque de comunicacion de riesgo
    (sin diagnostico, orientado a decision operativa).
- Riesgos de contrato:
  - consumidores con parseo estricto de `interpretability_trace` deben tolerar nuevas claves.

## TM-138 (capa SVM de triaje, sin cambio de payload)

- Endpoint afectado:
  - POST /care-tasks/{task_id}/chat/messages`r
- Contrato externo:
  - sin cambios en request/response.
- Cambios internos:
  - nueva traza en interpretability_trace: svm_enabled, svm_score, svm_margin, svm_hinge_loss, svm_class, svm_priority_score, svm_support_signals.
- Riesgos de contrato:
  - consumidores con parseo estricto de interpretability_trace deben tolerar nuevas claves.


## TM-139 (pipeline de riesgo clinico probabilistico, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
- Cambios internos:
  - nuevas claves en `interpretability_trace`:
    - `risk_pipeline_enabled`
    - `risk_model_linear_score`
    - `risk_model_probability`
    - `risk_model_priority`
    - `risk_model_features_missing`
    - `risk_model_anomaly_score`
    - `risk_model_anomaly_flag`
- Riesgos de contrato:
  - parseadores estrictos de `interpretability_trace` deben tolerar claves nuevas.

## TM-141 (RAG paralelo + gate de fidelidad, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - retrieval hibrido ahora puede ejecutarse en paralelo (vector + keyword) y anota:
    - `hybrid_parallelized=1|0`
  - quality gate incorpora control de fidelidad minima contra chunks recuperados.
- Riesgos de contrato:
  - consumidores con parseo estricto de `interpretability_trace` deben tolerar claves nuevas.

## TM-142 (chunking+query-expansion+context-relevance, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - trazabilidad ampliada de retrieval:
    - `retrieval_query_expanded`
    - `retrieval_query_expansion_terms`
  - validacion RAG incorpora chequeo de `context_relevance` en `rag_validation_issues`.
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves.

## TM-143 (adaptive-k+MMR+compresion contexto, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - nuevas trazas opcionales de retrieval:
    - `rag_adaptive_k_enabled`
    - `rag_adaptive_k_value`
    - `rag_adaptive_k_reason`
    - `rag_adaptive_k_tokens`
    - `rag_mmr_enabled`
    - `rag_mmr_lambda`
    - `rag_mmr_selected`
    - `rag_mmr_candidates`
    - `rag_context_compressed`
    - `rag_context_original_chars`
    - `rag_context_compressed_chars`
    - `rag_context_compression_ratio`
- Riesgos de contrato:
  - clientes que parsean `interpretability_trace` de forma estricta deben tolerar nuevas claves opcionales.

## TM-144 (indice invertido FTS + postings booleanos, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - retrieval hibrido usa candidate generation con indice invertido local (FTS5) y postings booleanos.
  - nuevas trazas opcionales:
    - `fts_candidate_enabled`
    - `fts_candidate_ready`
    - `fts_candidate_reason`
    - `candidate_strategy`
    - `candidate_boolean_explicit`
    - `candidate_terms_included`
    - `candidate_terms_optional`
    - `candidate_terms_excluded`
    - `candidate_postings_terms`
    - `candidate_chunks_pool`
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves.

## TM-145 (parser booleano avanzado + frases + spell local, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - candidate retrieval aplica parser booleano con precedencia (`NOT > AND > OR`) y parentesis.
  - soporte de frases con comillas (`"..."`) en consulta FTS.
  - correccion ortografica local opcional sobre vocabulario FTS para terminos sin postings.
  - nuevas trazas opcionales:
    - `candidate_boolean_parser`
    - `candidate_boolean_tokens`
    - `candidate_boolean_rpn`
    - `candidate_postings_operands`
    - `candidate_phrase_terms`
    - `candidate_spell_attempted`
    - `candidate_spell_applied`
    - `candidate_spell_corrections`
    - `candidate_boolean_parse_error`
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves opcionales.

## TM-146 (proximidad /k + skip pointers, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - operador de proximidad `/k` en consulta booleana mapeado a `NEAR(...)`.
  - interseccion `AND` puede usar skip pointers en listas largas.
  - nuevas trazas opcionales:
    - `candidate_skip_enabled`
    - `candidate_skip_threshold`
    - `candidate_skip_intersections`
    - `candidate_skip_shortcuts`
    - `candidate_strategy=fts_boolean_no_match` en expresiones booleanas validas sin coincidencias.
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves opcionales.

## TM-147 (comodines + k-gram/Jaccard + Soundex, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - candidate retrieval acepta terminos wildcard `*` en expresiones booleanas.
  - expansion wildcard sobre vocabulario FTS con limite configurable.
  - spell correction usa pre-filtro de similitud k-gram/Jaccard y fallback fonetico Soundex.
  - nuevas trazas opcionales:
    - `candidate_did_you_mean`
    - `candidate_spell_trigger_max_postings`
    - `candidate_wildcard_enabled`
    - `candidate_wildcard_attempted`
    - `candidate_wildcard_expanded_terms`
    - `candidate_soundex_enabled`
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves opcionales.

## TM-148 (spell contextual por bigramas, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - spell correction prioriza candidatos por distancia y soporte contextual (`left_term candidate`, `candidate right_term`).
  - limite configurable de candidatos para contextual spell.
  - nuevas trazas opcionales:
    - `candidate_contextual_spell_enabled`
    - `candidate_contextual_spell_max_candidates`
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves opcionales.

## TM-149 (cache de vocabulario FTS en memoria, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - candidate retrieval usa cache de diccionario FTS en memoria para wildcard/spell.
  - lookup de prefijos sobre estructura ordenada en memoria (`bisect`) + fallback a DB.
  - nuevas trazas opcionales:
    - `candidate_vocab_cache_enabled`
    - `candidate_vocab_cache_ready`
    - `candidate_vocab_cache_terms`
    - `candidate_vocab_lookup_cache_hits`
    - `candidate_vocab_lookup_db_hits`
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves opcionales.

## TM-150 (cache de postings comprimida + script Heaps/Zipf, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - cache de postings por query/specialty con codificacion por gaps (`vb` o `gamma`).
  - nuevas trazas opcionales:
    - `candidate_postings_cache_enabled`
    - `candidate_postings_cache_encoding`
    - `candidate_postings_cache_hits`
    - `candidate_postings_cache_misses`
    - `candidate_postings_cache_evictions`
    - `candidate_postings_cache_size`
  - nuevo script operativo (no API): `python -m app.scripts.estimate_rag_index_stats`.
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves opcionales.

## TM-151 (tf-idf por zonas + coseno pivotado, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - keyword retrieval usa `tf-idf` por zonas (`title`, `section`, `body`, `keywords`, `custom_questions`).
  - normalizacion de coseno + penalizacion pivotada por longitud de chunk.
  - mezcla hibrida vector+keyword pasa a score normalizado real por canal.
  - nuevas trazas opcionales:
    - `keyword_search_method=tfidf_zone_cosine_pivoted`
    - `keyword_search_query_terms`
    - `keyword_search_zone_blend`
    - `keyword_search_pivot_slope`
    - `keyword_search_avg_doc_length`
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves opcionales.

## TM-152 (idf pruning + proximidad + calidad estatica + tiered ranking, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - scorer lexical aplica poda por `idf` para reducir terminos de bajo impacto.
  - se agrega bonus de proximidad por ventana minima (`keyword proximity`).
  - se agrega calidad estatica `g(d)` para net-score lexical.
  - se agrega ranking por niveles (`tier1` por calidad minima y `tier2` como respaldo).
  - nuevas trazas opcionales:
    - `keyword_search_active_terms`
    - `keyword_search_idf_pruned_terms`
    - `keyword_search_proximity_enabled`
    - `keyword_search_static_quality_enabled`
    - `keyword_search_tiered_enabled`
    - `keyword_search_tier1_selected`
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves opcionales.

## TM-153 (evaluacion IR offline ampliada, sin cambio de payload API)

- Endpoint afectado:
  - ninguno (script offline).
- Contrato externo API:
  - sin cambios en request/response de endpoints existentes.
- Cambios internos:
  - script `app.scripts.evaluate_rag_retrieval` ampliado con metricas:
    - `precision_at_k`, `recall_at_k`, `f1_at_k`
    - `p@1,p@3,p@5` (configurable)
    - `map`, `mrr`, `ndcg`, `context_relevance`
    - `kappa` opcional.
  - soporte de comparativa A/B offline: `--ab-strategy`.
  - reporte detallado opcional por consulta (`--report-out`) con `kwic_top1`.
- Riesgos de contrato:
  - no aplica a contrato HTTP.

## TM-154 (expansion global + PRF, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - expansion global por tesauro local configurable (`docs/clinical_thesaurus_es_en.json`).
  - pseudo-relevance feedback (blind RF) con termino expansion derivada de top-k pseudo-relevante.
  - nuevas trazas opcionales:
    - `retrieval_query_expansion_local_terms`
    - `retrieval_query_expansion_global_terms`
    - `retrieval_query_expansion_specialty_terms`
    - `retrieval_query_prf_enabled`
    - `retrieval_query_prf_terms`
    - `retrieval_query_prf_topk`
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves opcionales.

## TM-155 (scoring probabilistico BM25/BIM, sin cambio de payload)

- Endpoint afectado:
  - POST /care-tasks/{task_id}/chat/messages
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - scorer lexical mezcla tf-idf por zonas con BM25 configurable (k1, b, blend).
  - bonus BIM opcional para coincidencia binaria discriminativa.
  - trazas nuevas opcionales:
    - keyword_search_bm25_top_avg
    - keyword_search_bim_top_avg
  - se mantienen trazas de config BM25/BIM aun cuando no hay candidatos.
- Riesgos de contrato:
  - clientes con parseo estricto de interpretability_trace deben tolerar nuevas claves opcionales.

## TM-156 (query likelihood model con smoothing, sin cambio de payload)

- Endpoint afectado:
  - POST /care-tasks/{task_id}/chat/messages
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - scorer lexical incorpora Query Likelihood Model (unigrama multinomial) sobre terminos de consulta.
  - suavizado configurable:
    - dirichlet (mu)
    - jm (lambda)
  - blend configurable de score QLM con score lexical existente.
  - nuevas trazas opcionales:
    - keyword_search_qlm_enabled
    - keyword_search_qlm_smoothing
    - keyword_search_qlm_mu
    - keyword_search_qlm_jm_lambda
    - keyword_search_qlm_blend
    - keyword_search_qlm_top_avg
- Riesgos de contrato:
  - clientes con parseo estricto de interpretability_trace deben tolerar nuevas claves opcionales.

## TM-157 (Naive Bayes supervisado para rerank de dominio, sin cambio de payload)

- Endpoint afectado:
  - POST /care-tasks/{task_id}/chat/messages
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - clasificacion Naive Bayes en capa de chat para estimar dominio top desde texto de consulta.
  - rerank de dominio cuando NB supera umbral de confianza y la capa matematica no es concluyente.
  - nuevas trazas opcionales:
    - nb_enabled
    - nb_model
    - nb_alpha
    - nb_top_domain
    - nb_top_probability
    - nb_margin_top2
    - nb_entropy
    - nb_tokens
    - nb_vocab_size
    - nb_classes
    - nb_features_selected
    - nb_rerank_recommended
- Riesgos de contrato:
  - clientes con parseo estricto de interpretability_trace deben tolerar nuevas claves opcionales.
## TM-158 (metricas macro/micro de clasificacion NB, sin cambio de payload)

- Endpoint afectado:
  - ninguno.
- Contrato externo:
  - sin cambios en request/response.
- Cambios internos:
  - utilitario de evaluacion offline/servicio NB incorpora macropromediado y micropromediado.
- Riesgos de contrato:
  - no aplica.
## TM-159 (vector space classification Rocchio+kNN, sin cambio de payload)

- Endpoint afectado:
  - POST /care-tasks/{task_id}/chat/messages
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - clasificador vectorial para estimar dominio top de consulta (`rocchio|knn|hybrid`).
  - rerank de dominios candidatos en fase pre-respuesta.
  - nuevas trazas opcionales:
    - vector_enabled
    - vector_method
    - vector_k
    - vector_top_domain
    - vector_top_probability
    - vector_margin_top2
    - vector_entropy
    - vector_tokens
    - vector_vocab_size
    - vector_classes
    - vector_training_docs
    - vector_rerank_recommended
- Riesgos de contrato:
  - clientes con parseo estricto de interpretability_trace deben tolerar nuevas claves opcionales.
## TM-160 (SVM lineal OVA para rerank de dominio, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - clasificador SVM de dominio (`ClinicalSVMDomainService`) para estimar dominio top desde texto.
  - rerank de dominios candidatos cuando supera umbral de confianza y la capa matematica esta incierta.
  - nuevas trazas opcionales:
    - `svm_domain_enabled`
    - `svm_domain_method`
    - `svm_domain_c`
    - `svm_domain_l2`
    - `svm_domain_epochs`
    - `svm_domain_top_domain`
    - `svm_domain_top_probability`
    - `svm_domain_margin_top2`
    - `svm_domain_entropy`
    - `svm_domain_support_vectors`
    - `svm_domain_avg_hinge_loss`
    - `svm_domain_vocab_size`
    - `svm_domain_classes`
    - `svm_domain_training_docs`
    - `svm_domain_rerank_recommended`
    - `svm_domain_support_terms`
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves opcionales.

## TM-161 (clustering plano para rerank de dominio, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - capa de clustering no supervisado para seleccionar dominios candidatos.
  - nuevas trazas opcionales:
    - `cluster_enabled`
    - `cluster_method`
    - `cluster_k_selected`
    - `cluster_k_min`
    - `cluster_k_max`
    - `cluster_top_id`
    - `cluster_top_confidence`
    - `cluster_margin_top2`
    - `cluster_entropy`
    - `cluster_candidate_domains`
    - `cluster_singletons`
    - `cluster_rss`
    - `cluster_aic`
    - `cluster_purity`
    - `cluster_nmi`
    - `cluster_rand_index`
    - `cluster_f_measure`
    - `cluster_vocab_size`
    - `cluster_training_docs`
    - `cluster_rerank_recommended`
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves opcionales.

## TM-162 (clustering jerarquico para rerank de dominio, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - capa de clustering jerarquico no supervisado (`HAC/divisive/buckshot`) para priorizar dominios candidatos.
  - nuevas trazas opcionales:
    - `hcluster_enabled`
    - `hcluster_method`
    - `hcluster_strategy`
    - `hcluster_linkage`
    - `hcluster_k_selected`
    - `hcluster_k_min`
    - `hcluster_k_max`
    - `hcluster_top_id`
    - `hcluster_top_confidence`
    - `hcluster_margin_top2`
    - `hcluster_entropy`
    - `hcluster_candidate_domains`
    - `hcluster_singletons`
    - `hcluster_merge_steps`
    - `hcluster_sample_size`
    - `hcluster_purity`
    - `hcluster_nmi`
    - `hcluster_rand_index`
    - `hcluster_f_measure`
    - `hcluster_vocab_size`
    - `hcluster_training_docs`
    - `hcluster_rerank_recommended`
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves opcionales.

## TM-163 (LSI por SVD truncada en retrieval, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - nueva señal semantica LSI sobre retrieval lexical (`keyword`), con proyeccion latente de consulta y documentos.
  - nuevas trazas opcionales:
    - `keyword_search_lsi_enabled`
    - `keyword_search_lsi_k`
    - `keyword_search_lsi_blend`
    - `keyword_search_lsi_max_vocab_terms`
    - `keyword_search_lsi_min_docs`
    - `keyword_search_lsi_vocab_size`
    - `keyword_search_lsi_components`
    - `keyword_search_lsi_doc_count`
    - `keyword_search_lsi_top_avg`
    - `keyword_search_lsi_error` (solo en fallback/error)
  - `keyword_search_method` puede incluir sufijo `+lsi`.
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves opcionales.

## TM-164 (quality pipeline de web sources, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - `web_sources` ahora se depura por calidad antes de exponerse:
    - deduplicacion por URL canonica.
    - filtro near-duplicate por shingles + MinHash.
    - filtro heuristico anti-spam.
    - ranking por autoridad de dominio + relevancia de consulta.
  - nuevas trazas opcionales en `interpretability_trace`:
    - `web_search_enabled`
    - `web_search_candidates_total`
    - `web_search_whitelist_filtered_out`
    - `web_search_spam_filtered_out`
    - `web_search_duplicate_filtered_out`
    - `web_search_quality_sorted`
    - `web_search_near_duplicate_threshold`
    - `web_search_avg_quality_top`
    - `web_search_results`
    - `web_search_error` (solo en fallo).
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves opcionales.

## TM-165 (crawler web clinico local, sin cambio de payload API)

- Endpoint afectado:
  - ninguno (script/servicio interno).
- Contrato externo:
  - sin cambios en request/response de API HTTP.
  - no se agregan endpoints.
- Cambios internos:
  - nuevo servicio `WebCrawlerService` para rastreo web polite con:
    - frontier priorizada por autoridad/profundidad,
    - colas por host y delay de cortesia,
    - robots.txt + cache,
    - dedupe URL + near-duplicate por contenido,
    - checkpoint de estado para resume.
  - nuevo script operativo: `python -m app.scripts.crawl_clinical_web`.
- Riesgos de contrato:
  - no aplica a contrato HTTP.

## TM-166 (link analysis para web sources, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - `web_sources` ahora puede incorporar senal de autoridad por grafo:
    - `PageRank` global.
    - `Topic-Specific PageRank`.
    - `HITS` (authority/hub).
    - relevancia por `anchor_text` entrante.
  - nuevas trazas opcionales en `interpretability_trace`:
    - `web_search_link_analysis_loaded`
    - `web_search_link_analysis_error`
    - `web_search_link_analysis_candidates`
    - `web_search_link_analysis_nodes`
    - `web_search_link_analysis_edges`
    - `web_search_link_analysis_topic_seed_nodes`
    - `web_search_link_analysis_hits_base`
    - `web_search_link_analysis_avg_score`
    - `web_search_link_analysis_blend`
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves opcionales.

## TM-167 (hardening timeout/fallback chat)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - se evita segundo pase LLM cuando RAG ya falló en generacion por error LLM (`rag_status=failed_generation` + `llm_error`).
  - `RAGOrchestrator` ahora conserva `rag_sources` y `rag_chunks_retrieved` tambien en `failed_generation`.
  - fallback `evidence_first` se habilita cuando hay chunks/fuentes RAG aunque no haya respuesta LLM.
  - `LLMChatProvider` usa presupuesto temporal total por request (evita multiplicar timeout por cada fallback interno).
  - nueva traza opcional: `llm_second_pass_skipped=rag_failed_generation`.
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nueva clave opcional.

## TM-168 (estabilidad LLM local en chat)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - `LLMChatProvider` ahora prioriza `Ollama /api/generate` sobre `/api/chat` para reducir fallos 500 en entorno local.
  - trazas LLM incluyen `llm_enabled=true` en flujos con LLM habilitado (exito y error), para observabilidad consistente.
  - nueva traza opcional `llm_primary_error` cuando falla el intento principal y se usa fallback.
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves opcionales (`llm_primary_error`).

## TM-169 (timeout budgeting LLM)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
- Cambios internos:
  - presupuesto de timeout particionado por etapas en `LLMChatProvider.generate_answer`:
    - intento principal ~55%
    - fallback secundario ~30%
    - quick-recovery ~15%
  - evita consumir 100% del budget en el primer intento, permitiendo recuperacion en la misma request.
- Riesgos de contrato:
  - no aplica (sin cambios estructurales de payload).

## TM-170 (perfil LLM local CPU estable)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios de request/response.
- Cambios internos de despliegue/config:
  - `CLINICAL_CHAT_LLM_MODEL=phi3:mini`
  - `CLINICAL_CHAT_LLM_TIMEOUT_SECONDS=10`
  - `CLINICAL_CHAT_LLM_NUM_CTX=1024`
  - `CLINICAL_CHAT_LLM_MAX_INPUT_TOKENS=420`
  - `CLINICAL_CHAT_LLM_MAX_OUTPUT_TOKENS=96`
  - `CLINICAL_CHAT_LLM_PROMPT_MARGIN_TOKENS=96`
  - `CLINICAL_CHAT_LLM_TEMPERATURE=0.1`
  - `CLINICAL_CHAT_LLM_QUALITY_GATES_ENABLED=true`
- Riesgos de contrato:
  - no aplica (solo tuning runtime).


## TM-171 (RAG extractivo resiliente + latencia estable)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios de request/response.
  - no se agregan endpoints.
- Cambios internos:
  - `RAGOrchestrator` ya no degrada por `failed_generation` cuando hay evidencia recuperada y LLM no responde: aplica fallback extractivo con fuentes.
  - nuevo `rag_generation_mode` en trazas (`llm`, `extractive_no_llm`, `extractive_fallback_llm_error`).
  - `LLMChatProvider` incorpora circuit breaker para cortar cascadas de timeout (`llm_error=CircuitOpen`).
  - salida evidence-first limpia snippets no clinicos en fallback.
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves opcionales (`rag_generation_mode`, `llm_circuit_*`).

## TM-172 (ingesta incremental rapida por source_file)

- Endpoint afectado:
  - ninguno (sin cambios de API publica).
- Contrato externo:
  - sin cambios de request/response.
  - no se agregan endpoints.
- Cambios internos:
  - `ingest_clinical_docs` filtra en pre-scan archivos con `source_file` ya existente en BD.
  - nuevo flag CLI: `--force-reprocess-existing-paths` para reingesta total cuando se necesite.
- Riesgos de contrato:
  - no aplica.

## TM-173 (latency-budget + contexto denso)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios de request/response.
  - no se agregan endpoints.
- Cambios internos:
  - presupuesto de latencia RAG antes de fase LLM; si no hay margen, se omite llamada LLM y se aplica fallback extractivo.
  - nuevas trazas opcionales: `rag_latency_budget_total_ms`, `rag_latency_budget_remaining_pre_llm_ms`, `rag_llm_skipped_reason`, `rag_llm_timeout_override_seconds`.
  - compaccion adicional del prompt (historial no duplicado y payload de resultados mas corto).
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar claves opcionales nuevas.

## TM-174 (latency stabilization retrieval)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios de request/response.
  - no se agregan endpoints.
- Cambios internos:
  - `adaptive_k` conservador para evitar saltos de fan-out en consultas de riesgo.
  - tuning de defaults RAG para reducir latencia (chunks/pool/context compaction).
- Riesgos de contrato:
  - no aplica.

## TM-175 (retrieval fast-path para p95)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios de request/response.
- Cambios internos:
  - se omite b?squeda por dominio en consultas largas (`rag_domain_search_skipped=1`) para evitar doble costo de retrieval.
  - tuning de par?metros de expansi?n/candidate pool para latencia.
- Riesgos de contrato:
  - parseadores estrictos de traza deben aceptar nueva clave opcional `rag_domain_search_skipped`.


## TM-176 (fail-fast retrieval y estabilidad de recall)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios de request/response.
- Cambios internos:
  - se evita segundo pase LLM cuando `rag_status` es `failed_retrieval` o `failed_exception`.
  - nueva traza: `llm_second_pass_skipped=rag_failed_retrieval`.
- Riesgos de contrato:
  - clientes con parseo estricto de trazas deben tolerar nueva clave opcional.

## TM-177 (quality-first en respuesta final)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios de request/response.
- Cambios internos:
  - reparacion de respuesta final cuando `quality_status=degraded` y hay evidencia RAG disponible.
  - nueva traza: `quality_repair_applied=evidence_first_from_degraded`.
- Riesgos de contrato:
  - parseadores estrictos de traza deben tolerar nueva clave opcional.

## TM-178 (mejora calidad + observabilidad benchmark)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios de request/response.
- Cambios internos:
  - priorizacion de fuentes RAG por score de retrieval (relevancia) antes de tipo de fuente.
  - fallback evidence-first ahora incluye `Consulta objetivo` para mejorar trazabilidad/alineacion.
  - scripts de benchmark: p95 corregido (nearest-rank), resumen JSON y gate de aceptacion automatizado.
- Riesgos de contrato:
  - no aplica a contrato HTTP; nuevas salidas en scripts locales de benchmark.

## TM-179 (tuning latencia/calidad operativo)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios de request/response.
- Cambios internos:
  - tuning de presupuesto RAG->LLM para permitir mas llamadas LLM util cuando hay margen.
  - tuning de retrieval para recortar p95 en queries largas.
  - benchmark summary amplía trazas `llm_enabled/llm_used/llm_error` por query.
- Riesgos de contrato:
  - no aplica; solo trazas y config runtime.

## TM-180 (provider LLM alternativo local)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios de request/response.
- Cambios internos:
  - `CLINICAL_CHAT_LLM_PROVIDER` ahora admite `llama_cpp`.
  - soporte de llamada a endpoint OpenAI-compatible: `POST /v1/chat/completions`.
  - parseo de respuesta `choices[0].message.content`.
- Riesgos de contrato:
  - no aplica a API externa; requiere configuracion correcta de base URL del servidor local.

## TM-181 (runtime LLM local)

- Se estandariza proveedor local `llama_cpp` en configuracion base.
- Endpoint efectivo del proveedor: `POST /v1/chat/completions` contra `CLINICAL_CHAT_LLM_BASE_URL`.
- Contrato externo del API clinico no cambia (`POST /api/v1/care-tasks/{id}/chat/messages`).

## TM-183 (chat asincrono)

- Nuevos endpoints:
  - `POST /api/v1/care-tasks/{task_id}/chat/messages/async`
  - `GET /api/v1/care-tasks/{task_id}/chat/messages/async/{job_id}`
- Contrato:
  - El endpoint sincrono existente no cambia.
  - El endpoint asincrono devuelve `job_id` y estado (`queued|running|completed|failed`).

## Resultado TM-138

- Sin cambios de endpoints HTTP.
- Se extiende el contrato de trazabilidad en `interpretability_trace` con:
  - `llm_context_utilization_target_ratio`
  - `llm_context_utilization_estimated_ratio`
  - `rag_query_complexity`
  - `rag_query_complexity_reason`
  - `rag_domain_search_skip_reason`
  - `rag_safe_wrapper_triggered`
  - `rag_safe_wrapper_reason`
  - `rag_context_relevance_pre` / `rag_context_relevance_post`
  - `rag_faithfulness_post`

## TM-184 (modo extractivo forzado + relajacion de specialty filter, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios de request/response.
  - no se agregan endpoints.
- Cambios internos:
  - nuevo setting `CLINICAL_CHAT_RAG_FORCE_EXTRACTIVE_ONLY`.
  - en ruta RAG, se omite llamada LLM cuando el modo forzado esta activo.
  - si retrieval con `specialty_filter` devuelve vacio, se reintenta una vez sin filtro para recuperar evidencia.
  - nuevas trazas opcionales:
    - `rag_force_extractive_only`
    - `rag_llm_skipped_reason=force_extractive_only`
    - `rag_retriever_specialty_relaxation`
    - `rag_retriever_specialty_relaxation_reason`
    - `rag_retriever_specialty_original`
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves opcionales.

## TM-185 (boolean relaxed union para consultas naturales)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios de request/response.
- Cambios internos:
  - cuando la consulta no usa booleano explicito y el parser booleano deja candidatos en cero,
    se aplica union relajada de terminos relevantes (`candidate_strategy=fts_boolean_relaxed_union`).
  - se mantiene comportamiento estricto para consultas booleanas explicitas (`AND/OR/NOT`).
- Riesgos de contrato:
  - clientes con parseo estricto de trazas deben tolerar nuevas claves de traza:
    - `candidate_boolean_relaxed_union`
    - `candidate_boolean_relaxed_union_terms`

## TM-186 (HybridRAG QA shortcut, sin cambio de payload)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
- Cambios internos:
  - nueva etapa de `QA shortcut` antes del retrieval dominio/hibrido.
  - nuevas trazas opcionales:
    - `rag_qa_shortcut_enabled`
    - `rag_qa_shortcut_hit`
    - `rag_qa_shortcut_hits`
    - `rag_qa_shortcut_top_score`
    - `rag_qa_shortcut_reason`
    - `rag_qa_shortcut_candidates`
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar nuevas claves opcionales.

## TM-187 (multi-specialty coverage + parser PDF configurable)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
  - no se agregan endpoints.
- Cambios internos:
  - bypass del dominio fallback generico (`critical_ops`) en consultas generales para evitar sesgo de retrieval.
  - filtrado de chunks ruidosos no clinicos antes de ensamblar contexto.
  - QA shortcut ampliado para incluir chunks sin `specialty` y con relajacion de filtro.
  - nuevas trazas opcionales:
    - `rag_domain_search_skip_reason=generic_domain_fallback_bypass`
    - `rag_chunks_noise_filtered`
    - `rag_chunks_noise_filter_fallback`
    - `rag_qa_shortcut_noise_filtered`
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar claves nuevas opcionales.

## TM-188 (ingesta PDF estructurada + telemetria)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages` (impacto indirecto via corpus RAG)
- Contrato externo:
  - sin cambios de request/response.
  - no se agregan endpoints HTTP.
- Cambios internos:
  - parser PDF configurable `pypdf|mineru` con salida estructurada (`blocks`) y trazas.
  - soporte de orden de lectura y limpieza de artefactos repetidos por pagina.
  - chunking admite bloques preparseados con `type` (`text/table/formula`) y conserva `content_type`.
  - telemetria de ingesta agregada al resumen del script (`pdf_pages_total`, `pdf_blocks_total`, etc.).
- Riesgos de contrato:
  - no aplica a contrato HTTP; solo aumentan trazas internas y salida de script CLI.

## TM-189 (quality gates ingesta + acceptance offline retrieval)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages` (impacto indirecto via mejora del corpus RAG)
- Contrato externo:
  - sin cambios en request/response HTTP.
  - no se agregan endpoints.
- Cambios internos:
  - script de ingesta agrega quality gates deterministas para descartar documentos de baja señal antes de indexacion.
  - script de evaluacion offline añade `by_specialty` en el resumen y bloque de aceptacion por umbrales (`acceptance_passed`, `acceptance_failures`).
  - CLI de evaluacion soporta `--acceptance-thresholds` y `--fail-on-acceptance` para uso como quality gate en CI/local.
- Riesgos de contrato:
  - consumers que parsean la salida JSON de `evaluate_rag_retrieval.py` deben tolerar nuevas claves de resumen.

## TM-190 (benchmark acceptance pass en modo extractivo local)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios de request/response.
- Cambios internos:
  - `quality_metrics` cambia a scoring por cobertura + bonus de citas para respuestas extractivas.
  - `rag_orchestrator` compacta query en ruta compleja y habilita fast-path `keyword_only` en retrieval cuando hay `force_extractive_only`.
  - `rag_retriever.search_hybrid` soporta `keyword_only` para desactivar vector scoring en ese fast-path.
- Riesgos de contrato:
  - consumidores de `interpretability_trace` veran nuevas claves (`rag_retrieval_query_*`, `rag_retrieval_keyword_only`, `hybrid_vector_disabled`).

## TM-191 (adaptive routing por complejidad y presupuesto)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios request/response.
- Cambios internos:
  - RAG activa `keyword_only` en consultas complejas cuando el presupuesto reservado para LLM es alto.
  - presupuesto minimo de llamada LLM pasa a ser dinamico (`simple/medium/complex` + `pre_context_relevance`).
  - nuevas trazas: `rag_llm_min_remaining_budget_config_ms`, `rag_llm_min_remaining_budget_dynamic_ms`.
- Riesgos de contrato:
  - parseadores estrictos de `interpretability_trace` deben tolerar nuevas claves opcionales.

## TM-193 (Elastic RAG backend)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en request/response.
- Cambios internos:
  - nuevo backend retrieval `elastic` seleccionable por `CLINICAL_CHAT_RAG_RETRIEVER_BACKEND`.
  - fallback automatico a `legacy_hybrid` cuando Elastic no devuelve resultados.
- Riesgos de contrato:
  - `interpretability_trace` incorpora claves `elastic_*` opcionales.

## TM-194 (CIR ambiguedad + NQP-lite)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios en schema request/response.
- Cambios internos:
  - nuevo gate determinista de ambiguedad para consultas clinicas poco informativas.
  - cuando se activa, el turno responde con pregunta de clarificacion y sugerencias de siguiente consulta util.
  - `answer` puede incluir bloque textual de sugerencias, sin campos nuevos en payload.
- Riesgos de contrato:
  - consumidores de `interpretability_trace` veran claves nuevas opcionales:
    - `clarification_gate_triggered`
    - `clarification_gate_score`
    - `clarification_gate_reason`
    - `clarification_suggestions`

## TM-199 (segmentacion multi-intento + actionability rerank)

- Endpoint afectado:
  - `POST /care-tasks/{task_id}/chat/messages`
- Contrato externo:
  - sin cambios de schema request/response.
  - no se agregan endpoints.
- Cambios internos:
  - nueva estrategia de retrieval `multi_intent_hybrid` cuando la consulta compuesta se segmenta por dominios.
  - nuevos settings de control:
    - `CLINICAL_CHAT_RAG_MULTI_INTENT_*`
    - `CLINICAL_CHAT_RAG_ACTION_*`
  - nuevas trazas opcionales para auditoria:
    - `rag_multi_intent_*`
    - umbrales de calidad por subdominio (`quality_threshold_attention_*`)
  - composicion extractiva prioriza frases accionables y ancla fuentes con `section + source leaf`.
- Riesgos de contrato:
  - clientes con parseo estricto de `interpretability_trace` deben tolerar claves opcionales nuevas.

