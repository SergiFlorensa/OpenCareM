# ADR-0064: Soporte Operativo de Inmunologia para Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

Faltaba una capa operativa trazable para escenarios inmunologicos de urgencias:

- sospecha de Bruton/XLA con foco en BTK y ausencia de B perifericos,
- interpretacion estructurada de IgG/IgA/IgM en diferenciales humorales,
- señalizacion del cambio de riesgo tras perdida de IgG materna,
- evaluacion de primera linea de defensa pulmonar innata.

## Decision

Crear el workflow `immunology_support_v1` y exponerlo mediante:

- `POST /api/v1/care-tasks/{task_id}/immunology/recommendation`

Persistir trazas en `agent_runs/agent_steps` con `run_output.immunology_support`.

Agregar metricas Prometheus:

- `immunology_support_runs_total`
- `immunology_support_runs_completed_total`
- `immunology_support_critical_alerts_total`

## Consecuencias

### Positivas

- Estandariza el soporte operativo para inmunodeficiencias humorales en urgencias.
- Aporta bloques de seguridad para inconsistencias analiticas en IgM/perfiles
  superpuestos.
- Integra contexto de defensa pulmonar innata sin cambios de esquema en DB.

### Riesgos

- Riesgo de sobreinterpretacion si los datos inmunologicos de entrada son incompletos.
- Variabilidad institucional en umbrales y estrategia terapeutica final.
- Requiere validacion clinica especializada para cerrar decision asistencial.

## Mitigaciones

- Salida marcada como no diagnostica.
- Validacion humana obligatoria.
- Trazabilidad completa por `AgentRun`/`AgentStep` para auditoria y ajuste.
