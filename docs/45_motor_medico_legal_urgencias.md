# Motor Medico-Legal de Urgencias

## Objetivo

Agregar un soporte operativo medico-legal para `CareTask` que ayude a:

- Detectar alertas juridicas criticas tempranas.
- Recordar documentacion obligatoria segun contexto.
- Estandarizar checklist de cumplimiento en guardia.
- Dejar trazabilidad completa en `agent_runs`/`agent_steps`.

## Endpoint

- `POST /api/v1/care-tasks/{task_id}/medicolegal/recommendation`

## Entrada principal (`MedicolegalOpsRequest`)

- Tiempos operativos: `triage_wait_minutes`, `first_medical_contact_minutes`.
- Capacidad/autonomia: `patient_has_decision_capacity`, `refuses_care`.
- Consentimiento y tecnica: `invasive_procedure_planned`, `informed_consent_documented`.
- Escenarios judiciales: `suspected_crime_injuries`, `non_natural_death_suspected`.
- Cadena de custodia: `intoxication_forensic_context`, `chain_of_custody_started`.
- Riesgos extra: `public_health_risk`, `involuntary_psychiatric_admission`, `patient_escape_risk`.
- Extension bioetica pediatrica:
  - `legal_representatives_deceased`
  - `parental_religious_refusal_life_saving_treatment`
  - `life_threatening_condition`
  - `blood_transfusion_indicated`
  - `immediate_judicial_authorization_available`

## Salida principal (`MedicolegalOpsRecommendation`)

- `legal_risk_level`: nivel agregado (`low|medium|high`).
- `life_preserving_override_recommended`: activa override vital en conflicto pediatrico critico.
- `ethical_legal_basis`: fundamentos estructurados de la decision etico-legal.
- `urgency_summary`: resumen ejecutivo de urgencia para toma de decisiones en tiempo real.
- `critical_legal_alerts`: alertas de alto impacto legal.
- `required_documents`: documentos que no deben omitirse.
- `operational_actions`: acciones inmediatas sugeridas.
- `compliance_checklist`: lista de control para guardia.
- `human_validation_required`: siempre `true`.

## Reglas clave implementadas

- Triaje > 5 min genera alerta operativa.
- Valoracion medica > 30 min genera alerta operativa.
- Procedimiento invasivo sin consentimiento documentado (si hay capacidad) genera alerta critica.
- Contexto forense sin cadena de custodia genera alerta critica.
- Sospecha de muerte no natural genera alerta critica de judicializacion.
- En menor con riesgo vital + tratamiento potencialmente salvador indicado + rechazo
  representado, se prioriza interes superior del menor y deber de proteccion.
- Si no hay representante disponible o hay desamparo legal inmediato, se emite alerta
  de asuncion de deber de garante por el equipo clinico.
- Se exige trazabilidad reforzada de proporcionalidad, estado de necesidad terapeutica
  y comunicacion judicial post-estabilizacion.

## Trazabilidad y observabilidad

- Workflow persistido: `medicolegal_ops_support_v1`.
- Paso persistido: `medicolegal_operational_assessment`.
- Metricas nuevas en `/metrics`:
  - `medicolegal_ops_runs_total`
  - `medicolegal_ops_runs_completed_total`
  - `medicolegal_ops_critical_alerts_total`

## Validacion sugerida

1. Crear `CareTask`.
2. Ejecutar `POST /medicolegal/recommendation` con un caso normal.
3. Ejecutar otro caso critico (ej. `non_natural_death_suspected=true`).
4. Consultar `/metrics` y verificar series `medicolegal_ops_*`.

## Limites del modulo

- No sustituye criterio medico, juridico ni forense.
- No emite diagnostico ni dictamen legal definitivo.
- Es soporte operativo para reducir omisiones en entorno de alta presion.
