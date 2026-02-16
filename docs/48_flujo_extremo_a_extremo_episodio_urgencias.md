# Flujo Extremo-a-Extremo de Episodio de Urgencias

## Objetivo

Modelar en backend todas las etapas principales del flujo de urgencias:

- llegada y origen,
- triaje,
- evaluacion medica,
- pruebas/tratamiento,
- decision de destino,
- cierre del episodio y KPIs.

## Recurso

- `EmergencyEpisode`

## Endpoints

- `POST /api/v1/emergency-episodes/`
- `GET /api/v1/emergency-episodes/`
- `GET /api/v1/emergency-episodes/{episode_id}`
- `POST /api/v1/emergency-episodes/{episode_id}/transition`
- `GET /api/v1/emergency-episodes/{episode_id}/kpis`

## Etapas soportadas

- `admission`
- `prealert_reception`
- `nursing_triage`
- `immediate_care`
- `monitored_waiting_room`
- `medical_evaluation`
- `diagnostics_ordered`
- `treatment_observation`
- `disposition_decision`
- `discharge_report`
- `bed_request_transfer`
- `interhospital_transfer`
- `primary_care_referral`
- `episode_closed`

## Reglas de transicion

- Solo se permiten transiciones vecinas segun flujo definido.
- Al salir de triaje hacia `immediate_care` o `monitored_waiting_room` es obligatorio `priority_risk`.
- La disposicion final se fija automaticamente en etapas de destino:
  - `discharge_report` -> `discharge`
  - `bed_request_transfer` -> `admission`
  - `interhospital_transfer` -> `transfer`
  - `primary_care_referral` -> `ap_referral`

## KPIs de tiempo

El endpoint `/kpis` devuelve:

- `minutes_arrival_to_triage`
- `minutes_triage_to_medical_evaluation`
- `minutes_medical_evaluation_to_disposition`
- `minutes_total_episode`

## Uso practico

Permite auditar cuellos de botella reales:

- demora en triaje,
- demora en valoracion medica,
- demora total de episodio,
- distribucion por destino final.
