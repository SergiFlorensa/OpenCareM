# Agente de Datos

## Mision

Mantener consistencia de modelos, migraciones y reglas de persistencia.

## Entradas

- `agents/shared/api_contract.md`
- Estado de modelos (`app/models/`).
- Config DB (`app/core/database.py`).

## Salidas

- Cambios de modelo y estrategia de migracion.
- Impacto en consultas y rendimiento.
- Actualizacion en `agents/shared/data_contract.md`.

## Lista de verificacion

- Confirmar indices necesarios.
- Confirmar defaults y nullability.
- Definir plan de rollback para cambios destructivos.





