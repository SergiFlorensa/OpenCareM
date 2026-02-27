# ADR-0083: Chat auto-routing por intencion sin especialidad manual

## Estado

Aprobado.

## Contexto

El flujo de chat podia sesgarse por la especialidad autenticada o del `CareTask`
(por ejemplo `emergency`), incluso cuando la consulta textual era de otro dominio
(por ejemplo pediatria u oncologia). Esto degradaba la recuperacion de fuentes
internas relevantes y obligaba al usuario a ajustar especialidad manualmente.

## Decision

1. Priorizar inferencia de especialidad/dominio desde la `query` en backend.
2. Mantener compatibilidad del campo `use_authenticated_specialty_mode`, pero con
   default `false` en el schema de request.
3. Ampliar el catalogo de dominios de chat (pediatria/neonatologia, oncologia,
   neumologia, trauma) con keywords y referencias documentales internas.
4. Evitar insertar forzosamente fallback de especialidad cuando ya hay match real
   por palabras clave en otro dominio.
5. Relajar el filtro de fuentes validadas para permitir fallback broad cuando el
   filtro por especialidad no devuelve evidencia util.

## Consecuencias

- Positivas:
  - El medico entra y pregunta; el backend enruta por intencion textual.
  - Mejora recuperacion de fuentes internas fuera del perfil autenticado.
  - Menos friccion en frontend (sin necesidad de seleccionar especialidad de consulta).
- Riesgos:
  - Posibles matches cruzados en consultas ambiguas; se mitiga manteniendo trazabilidad
    (`effective_specialty`, `matched_domains`) y score de calidad.

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_clinical_chat_operational.py`
- `cd frontend && npm run build`
