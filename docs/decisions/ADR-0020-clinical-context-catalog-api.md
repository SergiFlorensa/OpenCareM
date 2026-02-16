# ADR-0020: Catalogo clinico-operativo versionado en API

- Estado: aceptado
- Fecha: 2026-02-11

## Contexto

Se dispone de informacion realista de operaciones de urgencias:

- areas fisicas y capacidades,
- circuitos operativos,
- roles diferenciados,
- checklists de procedimientos,
- estandares de seguimiento.

Este conocimiento era necesario para que agentes y frontend no trabajen con datos ficticios.

## Decision

Crear catalogo versionado en codigo (`clinical_context_service`) y exponerlo por API
en `GET /api/v1/clinical-context/*`.

No se crea tabla de base de datos en esta iteracion.

## Motivo

- Entrega rapida y didactica.
- Reutilizacion inmediata en prompts/tests/frontend.
- Menor complejidad de migracion en fase temprana.

## Consecuencias

Positivas:

- Contexto consistente y auditable.
- Base clara para evolucionar agentes por reglas reales.
- Facil de consumir desde UI y QA.

Riesgos:

- Mantenimiento manual del catalogo en codigo.
- Puede divergir de protocolos oficiales si no se revisa periodicamente.

Mitigacion:

- Versionar contexto.
- Documentar fuente y limites de uso.
- Planificar migracion a catalogos en DB/FHIR en fases posteriores.
