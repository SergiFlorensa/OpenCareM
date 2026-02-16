# Motor de Reanimacion y Soporte Vital Operativo

## Objetivo

Agregar soporte operativo para escenarios de reanimacion y soporte vital en urgencias, con validacion humana obligatoria, auditoria IA vs humano y observabilidad completa.

No es un diagnostico medico autonomo ni sustituye protocolos ACLS/BLS institucionales.

## Endpoint de recomendacion

- `POST /api/v1/care-tasks/{task_id}/resuscitation/recommendation`

### Entrada principal

- contexto: `cardiac_arrest|tachyarrhythmia_with_pulse|bradyarrhythmia_with_pulse|post_rosc`
- ritmo: `vf|pulseless_vt|asystole|pea|svt_flutter|af|vt_monomorphic|vt_polymorphic|brady_advanced`
- calidad RCP opcional: profundidad, frecuencia, interrupciones y EtCO2
- criterios de inestabilidad con pulso
- soporte post-ROSC (PAM, SpO2, coma)
- situaciones especiales: embarazo, sospecha de opiaceos
- extension obstetrica:
  - `gestational_weeks`
  - `uterine_fundus_at_or_above_umbilicus`
  - `minutes_since_arrest`
  - `access_above_diaphragm_secured`
  - `fetal_monitor_connected`
  - `magnesium_infusion_active`
  - `magnesium_toxicity_suspected`
- SLA operativos: `door_ecg_minutes`, `symptom_onset_minutes`

### Salida principal

- `severity_level`: `medium|high|critical`
- `rhythm_classification`
- `shock_recommended`
- `cpr_quality_ok` (si aplica)
- bloques operativos:
  - `primary_actions`
  - `medication_actions`
  - `electrical_therapy_plan`
  - `sedoanalgesia_plan`
  - `pre_shock_safety_checklist`
  - `ventilation_actions`
  - `reversible_causes_checklist`
  - `special_situation_actions`
  - `sla_alerts`
  - `alerts`
- `human_validation_required=true`

### Extension obstetrica critica

Cuando `pregnant=true`, el motor agrega acciones especificas:

- activacion de codigo obstetrico multidisciplinar
- desplazamiento uterino lateral manual 15-30 grados
- recomendacion de acceso vascular por encima del diafragma
- desconexion de monitor fetal durante RCP (si aplica)
- regla 4-5 minutos para histerotomia resucitativa en paro sin ROSC
- antidoto de toxicidad por magnesio (calcio 1 g IV) si hay sospecha
- checklist etiologico ampliado (A-B-C-D-E-F-G-H obstetrico)

### Extension de terapia electrica en arritmias criticas

El motor incorpora recomendaciones explicables para diferenciar:

- cardioversion sincronizada (ritmos organizados con pulso e inestabilidad)
- desfibrilacion no sincronizada (FV/TV sin pulso y TV polimorfica)

Incluye energia inicial orientativa por ritmo:

- TSV/Flutter: 50-100 J sincronizado
- FA: 120-200 J bifasico sincronizado
- TV monomorfica con pulso: 100 J sincronizado
- TV polimorfica / ritmos de paro desfibrilables: descarga no sincronizada

Tambien agrega:

- plan de sedoanalgesia peri-procedimiento (fentanilo + etomidato como referencia)
- checklist de seguridad pre-descarga (sync, oxigeno, avisos de seguridad)
- alerta por presion de pulso estrecha cuando se reporta PAS/PAD

## Auditoria de calidad de reanimacion

- `POST /api/v1/care-tasks/{task_id}/resuscitation/audit`
- `GET /api/v1/care-tasks/{task_id}/resuscitation/audit`
- `GET /api/v1/care-tasks/{task_id}/resuscitation/audit/summary`

Clasificacion:

- `match`
- `under_resuscitation_risk`
- `over_resuscitation_risk`

Resumen agrega precision por reglas:

- `shock_recommended_match_rate_percent`
- `reversible_causes_match_rate_percent`
- `airway_plan_match_rate_percent`

## Trazabilidad de agente

- Workflow: `resuscitation_protocol_support_v1`
- Paso: `resuscitation_operational_assessment`
- Persistencia en:
  - `agent_runs`
  - `agent_steps`

## Metricas Prometheus

Workflow:

- `resuscitation_protocol_runs_total`
- `resuscitation_protocol_runs_completed_total`
- `resuscitation_protocol_alerts_total`

Calidad:

- `resuscitation_audit_total`
- `resuscitation_audit_match_total`
- `resuscitation_audit_under_total`
- `resuscitation_audit_over_total`
- `resuscitation_audit_under_rate_percent`
- `resuscitation_audit_over_rate_percent`
- `resuscitation_rule_shock_match_rate_percent`
- `resuscitation_rule_reversible_causes_match_rate_percent`
- `resuscitation_rule_airway_plan_match_rate_percent`

## Alertas Prometheus

- `ResuscitationAuditUnderRateHigh` (`>10%`, 2m)
- `ResuscitationAuditOverRateHigh` (`>20%`, 2m)

## Validacion recomendada

```powershell
.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py app/tests/test_metrics_endpoint.py app/tests/test_quality_regression_gate.py
```
