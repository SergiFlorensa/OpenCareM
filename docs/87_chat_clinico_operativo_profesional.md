# Chat Clinico-Operativo Profesional en CareTask

## Problema

El sistema no tenia un canal conversacional persistente para que el profesional
medico:

- hiciera consultas en lenguaje natural sobre el caso,
- reutilizara contexto de preguntas previas,
- y dejara trazabilidad estructurada para futuras consultas.

Faltaba ademas una forma de registrar hechos operativos extraidos de cada
consulta para mejorar precision contextual sin romper el enfoque no diagnostico.

## Cambios implementados

- Nuevo modelo persistente:
  - `app/models/care_task_chat_message.py`
  - tabla `care_task_chat_messages` (nueva migracion Alembic).
- Nueva migracion:
  - `alembic/versions/d4f6a9c8e221_add_care_task_chat_messages_table.py`
- Nuevos schemas:
  - `app/schemas/clinical_chat.py`
- Nuevo servicio:
  - `app/services/clinical_chat_service.py`
  - matching de dominios por keywords,
  - memoria por sesion (`top_extracted_facts`),
  - extraccion de hechos operativos (umbrales/comparadores/terminos),
  - respuesta interpretables con rutas sugeridas.
- Trazabilidad de agente:
  - `AgentRunService.run_care_task_clinical_chat_workflow`
  - `workflow_name=care_task_clinical_chat_v1`
  - `step_name=clinical_chat_assessment`
- Nuevos endpoints:
  - `POST /api/v1/care-tasks/{task_id}/chat/messages`
  - `GET /api/v1/care-tasks/{task_id}/chat/messages`
  - `GET /api/v1/care-tasks/{task_id}/chat/memory`

## Logica operativa cubierta

1. Consulta conversacional por caso:
- recibe `query` libre y opcionalmente `session_id`.
- si no hay sesion, genera una nueva (`chat-xxxxxxxxxxxx`).

2. Contexto incremental:
- usa historial reciente de la sesion para extraer hechos frecuentes,
- aplica esos hechos como memoria en la siguiente respuesta.

3. Relacion con capacidades existentes:
- mapea la consulta a dominios operativos (sepsis, SCASEST, reanimacion,
  medico-legal, neurologia, etc.),
- responde con endpoints recomendados ya existentes en la API.

4. Persistencia reutilizable:
- guarda por mensaje:
  - pregunta,
  - respuesta,
  - dominios y endpoints detectados,
  - hechos usados de memoria,
  - hechos extraidos de la consulta actual.

5. Seguridad de uso:
- siempre devuelve advertencia explicita de soporte no diagnostico,
- exige validacion humana/protocolo local.

## Validacion

- `.\venv\Scripts\python.exe -m py_compile app/models/care_task_chat_message.py app/schemas/clinical_chat.py app/services/clinical_chat_service.py app/services/agent_run_service.py app/api/care_tasks.py app/tests/test_care_tasks_api.py alembic/versions/d4f6a9c8e221_add_care_task_chat_messages_table.py`
- `.\venv\Scripts\python.exe -m ruff check app/models/care_task_chat_message.py app/schemas/clinical_chat.py app/services/clinical_chat_service.py app/services/agent_run_service.py app/api/care_tasks.py app/tests/test_care_tasks_api.py alembic/versions/d4f6a9c8e221_add_care_task_chat_messages_table.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat_message`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py`

## Riesgos pendientes

- El matching semantico es rules-first por keywords; no sustituye RAG clinico
  con ontologias o embeddings.
- La memoria por sesion puede contener ruido si el input es ambiguo.
- No se aplica aprendizaje automatico online; la "mejora" actual es
  contextual/memoristica, no reentrenamiento del modelo.
