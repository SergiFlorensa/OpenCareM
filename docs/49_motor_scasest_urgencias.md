# Motor de SCASEST en Urgencias

## Objetivo

Agregar soporte operativo temprano para sospecha de SCASEST en `CareTask` para:

- estructurar la sospecha inicial con datos clinicos y ECG/troponina,
- detectar casos de alto riesgo para escalado rapido,
- dejar trazabilidad operativa de pruebas, acciones y alertas.

## Endpoint

- `POST /api/v1/care-tasks/{task_id}/scasest/recommendation`

## Entrada (`ScasestProtocolRequest`)

- sintomas de presentacion: `chest_pain_typical`, `dyspnea`, `syncope`
- hallazgos de soporte: `ecg_st_depression`, `ecg_t_inversion`, `troponin_positive`
- gravedad/escala: `hemodynamic_instability`, `ventricular_arrhythmias`, `refractory_angina`, `grace_score`
- contraindicaciones operativas: `contraindication_antiplatelet`, `contraindication_anticoagulation`
- constantes opcionales: `heart_rate_bpm`, `systolic_bp`, `oxygen_saturation_percent`

## Salida (`ScasestProtocolRecommendation`)

- `scasest_suspected`
- `high_risk_scasest`
- `diagnostic_actions`
- `initial_treatment_actions`
- `escalation_actions`
- `alerts`
- `human_validation_required`

## Reglas implementadas

- Sospecha SCASEST si coexisten:
  - sintoma compatible (`dolor toracico tipico`/`disnea`/`sincope`), y
  - soporte objetivo (ECG con cambios o troponina positiva).
- Alto riesgo si hay sospecha y ademas:
  - inestabilidad hemodinamica, o
  - arritmias ventriculares, o
  - angina refractaria, o
  - `GRACE > 140`.
- Salida siempre no diagnostica y con validacion humana obligatoria.

## Trazabilidad y observabilidad

- Workflow: `scasest_protocol_support_v1`
- Step: `scasest_operational_assessment`
- Metricas en `/metrics`:
  - `scasest_protocol_runs_total`
  - `scasest_protocol_runs_completed_total`
  - `scasest_protocol_critical_alerts_total`

## Limites

- No sustituye diagnostico cardiologico ni protocolo institucional.
- No reemplaza juicio clinico humano.
- Organiza acciones operativas iniciales y prioridad de escalado.
