# ADR-0068: Chat Clinico-Operativo con Memoria por CareTask

- Fecha: 2026-02-15
- Estado: Aprobado

## Contexto

El sistema cubria multiples motores operativos por endpoint especializado, pero
faltaba una interfaz conversacional para que el profesional:

- consultara en lenguaje natural sobre un caso concreto,
- guardara el hilo de interacciones por sesion,
- y reutilizara hechos ya aportados en consultas posteriores.

Ademas era necesario mantener:

- trazabilidad completa en `agent_runs/agent_steps`,
- enfoque no diagnostico,
- y persistencia estructurada de memoria conversacional.

## Decision

Implementar chat clinico-operativo asociado a `CareTask` con:

- Nueva tabla: `care_task_chat_messages`.
- Nuevos endpoints:
  - `POST /api/v1/care-tasks/{task_id}/chat/messages`
  - `GET /api/v1/care-tasks/{task_id}/chat/messages`
  - `GET /api/v1/care-tasks/{task_id}/chat/memory`
- Nuevo workflow de trazabilidad:
  - `workflow_name=care_task_clinical_chat_v1`
  - `step_name=clinical_chat_assessment`

La logica de respuesta se mantiene rules-first:

- matching de dominios por keywords,
- sugerencia de rutas API existentes,
- extraccion de hechos (umbrales/comparadores/terminos),
- memoria por sesion usando hechos previos frecuentes.

## Consecuencias

### Positivas

- Aporta canal conversacional persistente dentro del mismo software.
- Mejora continuidad de consulta mediante memoria reutilizable por caso/sesion.
- Mantiene auditabilidad completa con persistencia en DB y `AgentRun`.

### Riesgos

- Matching semantico limitado por estrategia de keywords.
- Memoria sensible a ruido en consultas ambiguas.
- Riesgo de sobreconfianza si se interpreta como diagnostico.

## Mitigaciones

- Advertencia explicita de soporte no diagnostico en cada respuesta.
- Validacion humana/protocolo local como requisito operacional.
- Estructura trazable (`matched_domains`, `matched_endpoints`, `extracted_facts`)
  para auditar y ajustar reglas.
