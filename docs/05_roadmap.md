# Hoja de Ruta

Hoja de Ruta incremental para profesionalizar el proyecto sin saltos grandes.

## Fase 1: estabilizacion base

- [x] Crear tests unitarios de `TaskService`.
- Crear tests de integracion para endpoints de `tasks`.
- [x] Agregar script de smoke test MCP.
- [x] Documentar flujo de error handling.

## Fase 2: calidad y observabilidad

- [x] Eliminar deprecaciones de FastAPI startup/shutdown migrando a lifespan.
- [x] Aislar configuracion local de pytest/coverage para evitar dependencia de config global externa.
- [x] Migrar settings de Pydantic a configuracion v2 (`SettingsConfigDict`).
- [x] Definir y validar flujo local de `ruff`, `black`, `mypy`.
- [x] Integrar `ruff`, `black`, `mypy` en pipeline automatizado (GitHub Actions).
- [x] Activar hooks `pre-commit` sobre staged files (`ruff --fix`, `black`, verificacion `ruff`).
- [x] Agregar logging estructurado por request.
- [x] Exponer metricas Prometheus en endpoint dedicado.
- [x] Integrar Prometheus en Docker Compose para scraping local.
- [x] Integrar Grafana con dashboard base para metricas API.
- [x] Integrar metricas operativas de agentes en Prometheus/Grafana.
- [x] Activar alertas baseline para salud de agentes.
- [x] Integrar Alertmanager para ruteo de alertas.
- Definir politicas de manejo de secretos para local/prod.

## Fase 3: datos y seguridad

- [x] Migrar de `create_all` a migraciones Alembic versionadas.
- [x] Separar config base por entorno local y Docker (`.env.example`, `.env.docker`).
- [x] Aplicar baseline de seguridad en settings (secret key y CORS por entorno).
- Extender estrategia de config a `staging` y `prod`.
- [x] Crear fundacion tecnica para auth JWT (utilidades core + tests).
- [x] Exponer auth JWT minima en endpoints (`/auth/login`, `/auth/me`).
- [x] Pasar auth de usuario demo a usuarios persistentes en DB.
- [x] AÃ±adir registro de usuario (`/auth/register`) con politica basica de password.
- [x] AÃ±adir bootstrap seguro de primer admin por CLI.
- [x] Endurecer auth JWT con refresh tokens y rotacion.
- [x] Agregar control de permisos por usuario.
- [x] Mitigar brute force en login con rate limit temporal.

## Fase 5: AI aplicada al producto

- [x] AÃ±adir triage inteligente de tareas (rules-first, explicable).
- [x] Crear fundacion de ejecucion agente con trazas por paso (`AgentRun` + `AgentStep`).
- [x] Evolucionar a modo configurable (`rules`/`hybrid`) con fallback seguro.
- [x] Exponer historial de corridas de agentes en API.
- [x] Agregar filtros operativos en historial de corridas.
- [x] Agregar resumen operativo de corridas para monitoreo.
- [x] Agregar scorecard global de calidad IA clinica para auditorias operativas.
- [x] Activar gate de evaluacion continua de calidad IA en CI.
- Evolucionar a provider LLM real con dataset y evaluacion offline/online.

## Fase 6: Productividad de agentes

- [x] Crear libreria de skills de proyecto para orquestacion/API/observabilidad.
- [x] Estandarizar scripts operativos internos (`dev`, `build`, `check`, `test`, `test-e2e`) para ejecucion local consistente.

## Fase 7: Clinical Ops Copilot (nuevo foco)

- [ ] Fase 1 (2-4 semanas): pivot de dominio `Task` -> `CareTask` (operacional, no diagnostico).
- [x] Integrar `CareTask` con triaje agente y trazabilidad (`POST /care-tasks/{id}/triage`).
- [x] Integrar aprobacion humana de triaje (`POST /care-tasks/{id}/triage/approve`).
- [x] Integrar contexto operativo realista de urgencias (`/clinical-context/*`).
- [x] Integrar catalogo Manchester de niveles y SLA (`/clinical-context/triage-levels/manchester`).
- [x] Integrar auditoria de over/under-triage (`/care-tasks/{id}/triage/audit`).
- [x] Integrar motor de protocolo respiratorio operativo (`/care-tasks/{id}/respiratory-protocol/recommendation`).
- [x] Integrar motor de humanizacion pediatrica (`/care-tasks/{id}/humanization/recommendation`).
- [x] Integrar motor de screening operativo avanzado (`/care-tasks/{id}/screening/recommendation`).
- [x] Integrar auditoria de calidad de screening (`/care-tasks/{id}/screening/audit`).
- [x] Integrar soporte operativo de RX torax (`/care-tasks/{id}/chest-xray/interpretation-support`).
- [x] Integrar soporte operativo medico-legal (`/care-tasks/{id}/medicolegal/recommendation`).
- [x] Integrar auditoria de calidad medico-legal (`/care-tasks/{id}/medicolegal/audit`).
- [x] Integrar motor operativo de sepsis (`/care-tasks/{id}/sepsis/recommendation`).
- [x] Integrar motor operativo de SCASEST (`/care-tasks/{id}/scasest/recommendation`).
- [x] Integrar auditoria de calidad SCASEST (`/care-tasks/{id}/scasest/audit`).
- [x] Integrar soporte operativo de riesgo cardiovascular (`/care-tasks/{id}/cardio-risk/recommendation`).
- [x] Integrar soporte operativo de reanimacion y soporte vital (`/care-tasks/{id}/resuscitation/recommendation`).
- [x] Integrar soporte operativo de neumologia (`/care-tasks/{id}/pneumology/recommendation`).
- [x] Integrar soporte operativo de geriatria y fragilidad (`/care-tasks/{id}/geriatrics/recommendation`).
- [x] Integrar soporte operativo de oncologia (`/care-tasks/{id}/oncology/recommendation`).
- [x] Integrar soporte operativo de anestesiologia/reanimacion (`/care-tasks/{id}/anesthesiology/recommendation`).
- [x] Integrar soporte operativo de cuidados paliativos (`/care-tasks/{id}/palliative/recommendation`).
- [x] Integrar soporte operativo de urologia (`/care-tasks/{id}/urology/recommendation`).
- [x] Integrar soporte operativo de oftalmologia (`/care-tasks/{id}/ophthalmology/recommendation`).
- [x] Integrar soporte operativo de inmunologia (`/care-tasks/{id}/immunology/recommendation`).
- [x] Integrar soporte operativo de recurrencia genetica (`/care-tasks/{id}/genetic-recurrence/recommendation`).
- [x] Integrar soporte operativo de ginecologia y obstetricia (`/care-tasks/{id}/gynecology-obstetrics/recommendation`).
- [x] Integrar soporte operativo de pediatria y neonatologia (`/care-tasks/{id}/pediatrics-neonatology/recommendation`).
- [x] Integrar chat clinico-operativo con memoria por caso (`/care-tasks/{id}/chat/*`).
- [x] Evolucionar chat clinico con especialidad autenticada, contexto longitudinal y fuentes trazables.
- [x] Endurecer chat con whitelist web estricta y repositorio de fuentes selladas por profesionales.
- [x] Integrar soporte operativo de anisakis (`/care-tasks/{id}/anisakis/recommendation`).
- [x] Integrar soporte operativo de epidemiologia clinica (`/care-tasks/{id}/epidemiology/recommendation`).
- [x] Integrar flujo completo de episodio de urgencias (`/emergency-episodes/*`).
- [ ] Fase 2 (4-6 semanas): campos clinico-operativos (riesgo, SLA, revision humana, especialidad).
- [x] Entregar MVP frontend de chat clinico para validacion de UX con profesionales (`frontend/`).
- [x] Evolucionar frontend a UX tipo assistant con herramientas y modo hibrido general/clinico.
- [x] Integrar motor neuronal local opcional (Ollama) con fallback rule-based en chat.
- [ ] Fase 3 (4-8 semanas): frontend (Next.js) con tablero de casos y trazas de agente.
- [ ] Fase 4 (6-10 semanas): integracion FHIR/SMART on FHIR en sandbox.
- [x] Fase 5 (iteracion inicial): gate CI de calidad global (`run_quality_gate.py`).
- [ ] Fase 5 (continuo): ampliar evaluacion de agentes (calidad, fallback, latencia, coste) con dataset real versionado.
- [ ] Fase 6 (continuo): seguridad/compliance (RBAC fuerte, auditoria, retencion y threat modeling).

## Fase 4: entrega continua

- [x] Crear Dockerfile y `docker-compose` funcionales.
- [x] Endurecer runtime de contenedor (multi-stage + non-root user).
- Pipeline CI con pruebas y lint por pull request.
- Pipeline CD opcional para entorno de staging.

## Criterio de avance

No avanzar de fase hasta tener:

- Documentacion actualizada.
- Validaciones reproducibles.
- Riesgos conocidos registrados en `docs/decisions/`.


