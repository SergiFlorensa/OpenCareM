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
