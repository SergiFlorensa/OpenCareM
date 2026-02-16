# Auditoria de Calidad Medico-Legal

## Objetivo

Medir si la recomendacion del motor medico-legal coincide con la validacion humana en:

- nivel de riesgo legal global,
- necesidad de consentimiento,
- necesidad de notificacion judicial,
- necesidad de cadena de custodia.

## Endpoints

- `POST /api/v1/care-tasks/{task_id}/medicolegal/audit`
- `GET /api/v1/care-tasks/{task_id}/medicolegal/audit`
- `GET /api/v1/care-tasks/{task_id}/medicolegal/audit/summary`

## Modelo de auditoria

Tabla: `care_task_medicolegal_audit_logs`

Campos clave:

- `ai_legal_risk_level` vs `human_validated_legal_risk_level`
- `classification`: `match | under_legal_risk | over_legal_risk`
- flags IA/humano para consentimiento, notificacion judicial y cadena de custodia

## Regla de clasificacion

- `match`: IA y humano con mismo riesgo legal.
- `under_legal_risk`: IA menos severa que humano.
- `over_legal_risk`: IA mas severa que humano.

## Resumen agregado

`GET /summary` devuelve:

- volumen total y distribucion `match/under/over`,
- tasas de under/over,
- tasas de coincidencia por regla:
  - `consent_required_match_rate_percent`
  - `judicial_notification_match_rate_percent`
  - `chain_of_custody_match_rate_percent`

## Metricas Prometheus

Disponibles en `/metrics`:

- `medicolegal_audit_total`
- `medicolegal_audit_match_total`
- `medicolegal_audit_under_total`
- `medicolegal_audit_over_total`
- `medicolegal_audit_under_rate_percent`
- `medicolegal_audit_over_rate_percent`
- `medicolegal_rule_consent_match_rate_percent`
- `medicolegal_rule_judicial_notification_match_rate_percent`
- `medicolegal_rule_chain_of_custody_match_rate_percent`

## Uso practico

Permite revisar de forma objetiva:

- si el motor se queda corto en riesgo legal (under),
- si sobrerreacciona (over),
- en que reglas concretas falla mas y necesita ajuste.
