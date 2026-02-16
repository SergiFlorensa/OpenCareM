# ADR-0001: Alembic como fuente unica del esquema

## Contexto

El proyecto creaba tablas en runtime mediante `Base.metadata.create_all()` en el arranque de la API.
Ese enfoque es util al inicio, pero no da control de versionado ni trazabilidad de cambios de esquema
entre entornos.

## Decision

- Adoptar Alembic como mecanismo oficial para evolucion de esquema.
- Mantener migraciones versionadas en `alembic/versions/`.
- No crear tablas automaticamente en el startup de la API.

## Consecuencias

### Positivas

- Esquema reproducible en cualquier entorno.
- Historial de cambios y posibilidad de rollback (`downgrade`).
- Flujo de despliegue mas profesional y predecible.

### Costes

- Requiere disciplina para generar/aplicar migraciones en cada cambio de modelo.
- Se aÃ±ade una fase operativa (`alembic upgrade head`) al ciclo de despliegue.

## Validacion

- Migracion inicial generada y aplicada:
  - `alembic revision --autogenerate -m "init tasks table"`
  - `alembic upgrade head`
  - `alembic current`
- Estado esperado: `f1b3f75c533d (head)`.




