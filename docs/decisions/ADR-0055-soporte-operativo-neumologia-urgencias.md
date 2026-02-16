# ADR-0055: Soporte Operativo de Neumologia para Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

Faltaba una capa neumologica dedicada para resolver de forma trazable:

- diferenciales radiologicos/tomograficos respiratorios en urgencias,
- decisiones iniciales de soporte ventilatorio en hipoxemia vs hipercapnia,
- escalado terapeutico EPOC/asma grave por fenotipo,
- seguridad de decision quirurgica en nodulo pulmonar con funcion limite.

## Decision

Crear el workflow `pneumology_support_v1` y exponerlo mediante:

- `POST /api/v1/care-tasks/{task_id}/pneumology/recommendation`

Persistir trazas en `agent_runs/agent_steps` con `run_output.pneumology_support`.

Agregar metricas Prometheus:

- `pneumology_support_runs_total`
- `pneumology_support_runs_completed_total`
- `pneumology_support_critical_alerts_total`

## Consecuencias

### Positivas

- Estandariza reglas operativas de neumologia en urgencias.
- Refuerza seguridad en seleccion de terapia ventilatoria y decision intervencionista.
- Mejora observabilidad sin nuevas tablas ni migraciones.

### Riesgos

- Riesgo de uso como diagnostico definitivo fuera de contexto clinico.
- Dependencia de disponibilidad local de TAC, LBA, PET y pruebas funcionales.
- Necesidad de calibracion local de umbrales de escalado y alertas.

## Mitigaciones

- Advertencia explicita de no diagnostico en salida.
- Validacion humana obligatoria.
- Revision periodica por equipo clinico local y comite de vias respiratorias.
