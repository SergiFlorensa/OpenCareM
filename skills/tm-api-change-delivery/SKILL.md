---
name: tm-api-change-delivery
description: "Entrega cambios de FastAPI en este repositorio con ejecucion orientada a contratos: schemas, servicios, endpoints, pruebas, migraciones y documentacion alineados en un unico cambio. Usar cuando haya endpoints nuevos, cambios en auth, actualizaciones de modelo/schema, migraciones Alembic o correcciones API."
---

# TM Entrega de Cambios API

## Vision general

Usa esta skill cuando toques el comportamiento de la API.
Mantiene una entrega determinista y auditable.

## Flujo de entrega

1. Carga `references/api-delivery-checklist.md`.
2. Actualiza el contrato API y el plan de pruebas antes o durante la implementacion.
3. Implementa por capas:
   - schema,
   - servicio,
   - endpoint/router,
   - pruebas de integracion.
4. Si cambia el schema, carga `references/migration-playbook.md`.
5. Valida con `references/validation-matrix.md`.
6. Alinea documentacion y ADR cuando haya cambios estructurales.

## Regla de migraciones

Cuando cambien modelos:

- agrega migracion Alembic,
- confirma que `alembic/env.py` importa modelos actualizados si aplica,
- ejecuta comandos de migracion y guarda evidencia.

## Estandar de salida

Entrega un unico conjunto coherente donde codigo, pruebas y docs coinciden.

