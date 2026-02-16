# Guia de Migraciones

Usa esta referencia cuando cambien modelos SQLAlchemy.

1. Generar migracion:
   - `alembic revision --autogenerate -m "<mensaje>"`
2. Revisar el archivo de migracion manualmente.
3. Aplicar migracion:
   - `alembic upgrade head`
4. Verificar estado:
   - `alembic current`
5. Anadir evidencia en `agents/shared/TASK_BOARD.md` y `agents/shared/test_plan.md`.

