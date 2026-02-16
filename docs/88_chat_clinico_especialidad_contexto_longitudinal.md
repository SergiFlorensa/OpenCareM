# Chat Clinico v2: Especialidad, Contexto Longitudinal y Fuentes

## Problema

El chat inicial (TM-094) resolvia persistencia y memoria por sesion, pero faltaban
tres capacidades clave para uso real en urgencias:

- modo automatico por especialidad del profesional autenticado,
- continuidad entre episodios de un mismo paciente,
- trazabilidad de fuentes internas y consulta web opcional bajo demanda.

## Cambios implementados

- Credenciales y especialidad:
  - `users.specialty` agregado en BD y modelos.
  - `/auth/register`, `/auth/me` y `/auth/admin/users` exponen `specialty`.
- Continuidad por paciente:
  - `care_tasks.patient_reference` agregado para vincular episodios recurrentes.
  - `GET /care-tasks/` y `GET /care-tasks/stats/count` admiten filtro `patient_reference`.
- Chat reforzado:
  - endpoints de chat ahora requieren `Bearer`.
  - el modo de especialidad usa `users.specialty` por defecto (`use_authenticated_specialty_mode=true`).
  - memoria longitudinal agrega hechos de consultas previas del mismo `patient_reference`.
  - se registran fuentes internas (`knowledge_sources`) y web (`web_sources`) por turno.

## Contrato de chat (nuevo)

Request `POST /care-tasks/{id}/chat/messages`:

- `use_authenticated_specialty_mode`
- `use_patient_history`
- `max_patient_history_messages`
- `use_web_sources`
- `max_web_sources`
- `max_internal_sources`

Response:

- `effective_specialty`
- `knowledge_sources[]`
- `web_sources[]`
- `patient_history_facts_used[]`

`GET /chat/memory` agrega:

- `patient_reference`
- `patient_interactions_count`
- `patient_top_domains[]`
- `patient_top_extracted_facts[]`

## Validacion

- `.\venv\Scripts\python.exe -m ruff check ...` (archivos modificados)
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_auth_api.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py`
- `.\venv\Scripts\python.exe -m pytest -q`
- `.\venv\Scripts\python.exe -m alembic upgrade head`

## Riesgos pendientes

- El ranking de fuentes internas es lexical (rules-first), no embedding semantico.
- La busqueda web requiere gobernanza de fuentes para evitar ruido no clinico.
- La continuidad depende de calidad de `patient_reference` en admision.
