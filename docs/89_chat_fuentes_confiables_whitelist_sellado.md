# Chat Clinico v3: Fuentes Confiables, Whitelist Estricta y Sellado Profesional

## Objetivo

Blindar la calidad de informacion del chat clinico para que solo use:

- fuentes internas selladas por profesionales,
- y fuentes web dentro de dominios explicitamente permitidos.

## Cambios implementados

- Politica de confianza:
  - whitelist estricta de dominios web en settings.
  - rechazo de fuentes nuevas fuera de whitelist.
- Repositorio de conocimiento en BD:
  - tabla `clinical_knowledge_sources` para registrar fuentes por especialidad.
  - tabla `clinical_knowledge_source_validations` para historial de sellado.
- API de conocimiento:
  - `POST /api/v1/knowledge-sources/` (alta en estado `pending_review`).
  - `POST /api/v1/knowledge-sources/{id}/seal` (sellado admin: approve/reject/expire).
  - `GET /api/v1/knowledge-sources/` (por defecto solo validadas).
  - `GET /api/v1/knowledge-sources/{id}/validations`.
  - `GET /api/v1/knowledge-sources/trusted-domains`.
- Integracion chat:
  - prioriza `clinical_knowledge_sources` con `status=validated`.
  - si no hay fuente validada, informa explicitamente la carencia.
  - filtra resultados web por dominio permitido antes de incluirlos en respuesta.
- Estructura backend para curacion progresiva:
  - `app/knowledge/README.md`
  - `app/knowledge/specialties/`

## Settings relevantes

- `CLINICAL_CHAT_WEB_STRICT_WHITELIST=true`
- `CLINICAL_CHAT_WEB_ALLOWED_DOMAINS=...`
- `CLINICAL_CHAT_REQUIRE_VALIDATED_INTERNAL_SOURCES=true`

## Validacion ejecutada

- `.\venv\Scripts\python.exe -m ruff check ...`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_knowledge_sources_api.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat`
- `.\venv\Scripts\python.exe -m pytest -q`
- `.\venv\Scripts\python.exe -m alembic upgrade head`
- `.\venv\Scripts\python.exe -m alembic current`

## Riesgos pendientes

- La whitelist requiere gobierno continuo (nuevos dominios y retirada de obsoletos).
- El matching de fuentes internas sigue siendo lexical; pendiente evolucion a retrieval semantico validado.
- El sellado inicial depende de disponibilidad de revisores (flujo operativo humano).
