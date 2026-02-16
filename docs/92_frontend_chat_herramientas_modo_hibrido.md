# Frontend v2: Herramientas y modo conversacional hibrido

## Objetivo

Evolucionar el frontend MVP para una experiencia mas cercana a asistentes
conversacionales modernos, manteniendo control clinico y trazabilidad.

## Cambios principales

- UI redisenada estilo copilot:
  - barra lateral de casos y sesiones,
  - area central de conversacion con timeline limpio,
  - panel de inspeccion (memoria y trazas).
- Selector de herramientas en el composer:
  - `chat`, `medication`, `cases`, `treatment`, `deep_search`, `images`.
- Selector de modo de conversacion:
  - `auto`, `general`, `clinical`.
- Soporte de conversacion libre:
  - si no hay caso seleccionado, el frontend crea un `CareTask` de conversacion.

## Backend de chat actualizado

- Request de `POST /care-tasks/{id}/chat/messages` amplía:
  - `conversation_mode`
  - `tool_mode`
- Response amplía:
  - `response_mode`
  - `tool_mode`
- El motor decide automaticamente:
  - modo `clinical` cuando detecta señales clinicas o herramientas clinicas,
  - modo `general` en consultas no clinicas o en `deep_search`.
- `deep_search` fuerza consulta web dentro de whitelist y aumenta `max_web_sources`.

## Seguridad y trazabilidad

- Se mantiene la politica de whitelist de dominios.
- Se conserva `non_diagnostic_warning` para respuestas clinicas.
- Se incorporan trazas extra:
  - `conversation_mode`
  - `response_mode`
  - `tool_mode`
  - `keyword_hits`

## Validacion

- `cd frontend && npm run build`
- `.\venv\Scripts\python.exe -m ruff check app/schemas/clinical_chat.py app/services/clinical_chat_service.py app/api/care_tasks.py frontend/src/App.tsx`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat`
