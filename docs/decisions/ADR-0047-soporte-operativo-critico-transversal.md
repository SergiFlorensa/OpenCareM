# ADR-0047: Soporte Operativo Critico Transversal en Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

El sistema disponia de motores por subdominio (sepsis, reanimacion, trauma, SCASEST), pero no de una capa unica para reglas transversales de guardia centradas en:

- cumplimiento de SLAs clinicos tiempo-dependientes,
- eleccion de soporte respiratorio por perfil fisiologico,
- rutas de decision rapida (TEP, anafilaxia),
- identificacion de shock por patron hemodinamico,
- protocolos de antidotos/reversion y banderas rojas criticas.

Esta dispersion aumentaba el riesgo de aplicar reglas de forma inconsistente y reducia la trazabilidad operativa.

## Decision

Crear un nuevo workflow independiente `critical_ops_support_v1` expuesto por:

- `POST /api/v1/care-tasks/{task_id}/critical-ops/recommendation`

Con contrato estructurado en `critical_ops_protocol` y traza persistida en `agent_runs/agent_steps`.

Agregar metricas Prometheus especificas:

- `critical_ops_support_runs_total`
- `critical_ops_support_runs_completed_total`
- `critical_ops_support_critical_alerts_total`

## Consecuencias

### Positivas

- Unifica en un solo motor reglas transversales de alto impacto operativo.
- Mejora interpretabilidad mediante `interpretability_trace`.
- Facilita observabilidad y drill operacional con metricas dedicadas.
- No requiere migraciones de base de datos (reutiliza `agent_runs/agent_steps`).

### Riesgos

- Riesgo de sobre-alerta si los umbrales no se calibran por centro.
- Riesgo de uso fuera de alcance si se interpreta como diagnostico.
- Toxicologia y hemodinamica requieren siempre validacion clinica humana local.

## Mitigaciones

- Mantener aviso explicito de no diagnostico en contrato de salida.
- Revisar umbrales de SLA/alerta con comite clinico local antes de despliegue real.
- Auditar periodicamente `critical_alerts` y ajustar reglas de disparo.
