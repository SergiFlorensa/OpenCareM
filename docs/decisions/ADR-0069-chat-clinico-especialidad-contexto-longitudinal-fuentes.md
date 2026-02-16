# ADR-0069: Chat Clinico por Especialidad con Contexto Longitudinal y Fuentes Trazables

- Fecha: 2026-02-15
- Estado: Aprobado

## Contexto

El chat clinico inicial (ADR-0068) resolvia memoria por `CareTask`, pero en uso
operativo de urgencias seguian faltando capacidades para decision rapida:

- ajustar automaticamente el chat a la especialidad del profesional autenticado,
- recuperar continuidad entre episodios recurrentes de un mismo paciente,
- trazar fuentes internas y web usadas en cada respuesta para auditoria.

Ademas se necesitaba mantener:

- enfoque no diagnostico y soporte operativo,
- auditabilidad completa por mensaje,
- y compatibilidad con API/DB ya desplegada.

## Decision

Evolucionar el chat clinico-operativo con un contrato v2:

- Datos y modelo:
  - agregar `users.specialty` para modo por credencial.
  - agregar `care_tasks.patient_reference` para continuidad entre episodios.
  - agregar en `care_task_chat_messages`:
    - `effective_specialty`
    - `knowledge_sources[]`
    - `web_sources[]`
    - `patient_history_facts_used[]`
- API:
  - `POST /auth/register`, `GET /auth/me`, `GET /auth/admin/users` exponen `specialty`.
  - `GET /care-tasks/` y `GET /care-tasks/stats/count` admiten filtro `patient_reference`.
  - endpoints de chat requieren autenticacion `Bearer`.
  - request/response de chat se amplian con controles y trazas de especialidad,
    fuentes y contexto longitudinal.
- Servicio:
  - resolver `effective_specialty` desde credencial autenticada por defecto.
  - agregar memoria longitudinal por `patient_reference`.
  - indexar fuentes internas de `docs/` y habilitar consulta web opcional.

## Consecuencias

### Positivas

- Reduce latencia cognitiva del profesional al responder por contexto de especialidad.
- Mejora continuidad asistencial con resumen de interacciones previas del paciente.
- Refuerza auditabilidad mediante trazas de fuentes y hechos usados en cada turno.

### Riesgos

- Calidad de memoria longitudinal depende de consistencia de `patient_reference`.
- El ranking interno es lexical (rules-first), no semantico avanzado.
- La consulta web puede introducir ruido si no se gobiernan dominios permitidos.

## Mitigaciones

- Campos de trazabilidad persistidos por mensaje para revision clinica y QA.
- Configuracion explicita de web (`CLINICAL_CHAT_WEB_ENABLED`, timeout controlado).
- Mantener validacion humana/protocolo local como control final de decision.

## Validacion

- `.\venv\Scripts\python.exe -m alembic upgrade head`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_auth_api.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat`
- `.\venv\Scripts\python.exe -m pytest -q`
