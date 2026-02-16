# Motor de Sepsis en Urgencias

## Objetivo

Agregar soporte operativo temprano para sepsis en `CareTask` para:

- detectar riesgo alto con qSOFA,
- no perder la ventana del bundle de 1 hora,
- escalar shock septico de forma trazable.

## Endpoint

- `POST /api/v1/care-tasks/{task_id}/sepsis/recommendation`

## Entrada (`SepsisProtocolRequest`)

- `suspected_infection`
- `respiratory_rate_rpm`
- `systolic_bp`
- `altered_mental_status`
- `lactate_mmol_l`
- `map_mmhg`
- estado de acciones clave: hemocultivos, antibiotico, fluidos, vasopresor
- `time_since_detection_minutes`

## Salida (`SepsisProtocolRecommendation`)

- `qsofa_score`
- `high_sepsis_risk`
- `septic_shock_suspected`
- `one_hour_bundle_actions`
- `escalation_actions`
- `alerts`
- `human_validation_required`

## Reglas implementadas

- qSOFA:
  - FR >=22
  - TAS <=100
  - alteracion del estado mental
- Riesgo alto si infeccion sospechada + `qSOFA >=2`.
- Sospecha de shock septico si:
  - lactato >=4, o
  - PAM <65 con vasopresor.
- Bundle operativo:
  - hemocultivos
  - antibiotico <1h
  - fluidos 30 ml/kg
  - lactato y control seriado

## Trazabilidad y observabilidad

- Workflow: `sepsis_protocol_support_v1`
- Step: `sepsis_operational_assessment`
- Metricas en `/metrics`:
  - `sepsis_protocol_runs_total`
  - `sepsis_protocol_runs_completed_total`
  - `sepsis_protocol_critical_alerts_total`

## Limites

- No realiza diagnostico definitivo.
- No sustituye validacion clinica humana ni protocolos institucionales.
