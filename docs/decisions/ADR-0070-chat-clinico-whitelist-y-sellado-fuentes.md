# ADR-0070: Chat Clinico con Whitelist Estricta y Sellado Profesional de Fuentes

- Fecha: 2026-02-15
- Estado: Aprobado

## Contexto

El chat clinico ya disponia de especialidad autenticada y memoria longitudinal
(ADR-0069), pero faltaba cerrar el control de confianza de contenido:

- el uso web podia mezclar dominios no clinicos,
- no existia un flujo formal para sellar fuentes internas como fiables,
- y no habia trazabilidad explicita de validacion profesional en conocimiento.

## Decision

Implementar un marco de confianza obligatorio en backend:

- Web:
  - whitelist estricta por dominio (`CLINICAL_CHAT_WEB_STRICT_WHITELIST`).
  - solo se aceptan resultados web de dominios permitidos.
- Conocimiento interno:
  - nuevas tablas:
    - `clinical_knowledge_sources`
    - `clinical_knowledge_source_validations`
  - flujo de sellado admin/profesional:
    - alta (`pending_review`)
    - sellado (`approve/reject/expire`) con historial auditable.
- API:
  - `POST/GET /api/v1/knowledge-sources/*` para alta, listado, sellado e historial.
- Chat:
  - prioriza fuentes con `status=validated`.
  - cuando no hay evidencia validada, lo declara explicitamente.

## Consecuencias

### Positivas

- Aumenta seguridad informacional y reduce ruido de internet generalista.
- Permite gobierno de evidencia por especialidad con trazabilidad completa.
- Facilita auditoria medico-legal de por que fuente se sugirio cada respuesta.

### Riesgos

- Carga operativa inicial de curacion/sellado de contenido.
- Dependencia de mantenimiento de whitelist y expiracion de fuentes.
- El ranking interno sigue siendo lexical en esta iteracion.

## Mitigaciones

- Endpoint de dominios confiables para verificacion operativa (`/trusted-domains`).
- Historial de validacion por fuente para control de calidad.
- Parametro de expiracion para forzar revision periodica.

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_knowledge_sources_api.py`
- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_care_tasks_api.py -k chat`
- `.\venv\Scripts\python.exe -m pytest -q`
- `.\venv\Scripts\python.exe -m alembic upgrade head`
