# ADR-0057: Soporte Operativo de Oncologia para Urgencias

- Fecha: 2026-02-13
- Estado: Aprobado

## Contexto

Faltaba una capa oncologica dedicada para resolver de forma trazable:

- uso operativo de mecanismos checkpoint (PD-1/PD-L1-L2/CTLA-4),
- priorizacion por biomarcadores dMMR/MSI-high en CCR metastasico irresecable,
- gestion inicial de toxicidades inmunomediadas hepaticas,
- seguridad cardio-oncologica previa a trastuzumab/antraciclinas,
- activacion temprana de ruta de neutropenia febril,
- soporte pronostico por necrosis post-neoadyuvancia en sarcomas.

## Decision

Crear el workflow `oncology_support_v1` y exponerlo mediante:

- `POST /api/v1/care-tasks/{task_id}/oncology/recommendation`

Persistir trazas en `agent_runs/agent_steps` con `run_output.oncology_support`.

Agregar metricas Prometheus:

- `oncology_support_runs_total`
- `oncology_support_runs_completed_total`
- `oncology_support_critical_alerts_total`

## Consecuencias

### Positivas

- Estandariza decisiones operativas oncologicas criticas en urgencias.
- Mejora seguridad en irAEs, cardio-oncologia y neutropenia febril.
- Aumenta observabilidad con trazas y metricas sin cambios de esquema de DB.

### Riesgos

- Riesgo de uso como diagnostico definitivo sin validacion humana.
- Dependencia de calidad de datos clinicos/laboratorio de entrada.
- Variabilidad local en protocolos de escalado inmunosupresor y onco-cardiologia.

## Mitigaciones

- Advertencia explicita de no diagnostico en salida.
- Validacion humana obligatoria.
- Ajuste protocolizado por oncologia, urgencias y cardio-oncologia locales.
