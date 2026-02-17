# Flujo de Calidad

Guia operativa para ejecutar checks de calidad de forma reproducible.

## Prerrequisito

Activar entorno virtual del proyecto.

- PowerShell:
  - `.\venv\Scripts\Activate.ps1`
- Git Bash:
  - `source venv/Scripts/activate`

## Comando unificado recomendado

Para evitar variaciones entre desarrolladores:

- `powershell -ExecutionPolicy Bypass -File scripts/dev_workflow.ps1 -Action check`
- `powershell -ExecutionPolicy Bypass -File scripts/dev_workflow.ps1 -Action test`
- `powershell -ExecutionPolicy Bypass -File scripts/dev_workflow.ps1 -Action test-e2e`

## Orden recomendado de ejecucion

1. Lint:
   - `ruff check app mcp_server`
2. Formato:
   - `black --check app mcp_server`
3. Tipado:
   - `mypy app mcp_server`
4. Tests:
   - `pytest -q`

## Modo correccion automatica

Si `ruff` o `black` fallan:

1. `ruff check app mcp_server --fix`
2. `black app mcp_server`
3. Repetir validacion completa.

## Configuracion fuente

- `pyproject.toml`:
  - `tool.ruff`
  - `tool.black`
  - `tool.mypy`
- `.pre-commit-config.yaml`:
  - hooks staged de `ruff --fix`, `black`, `ruff`.
- `pytest.ini`:
  - paths de tests y coverage local.

## Hooks pre-commit (staged files)

Instalacion recomendada:

- `powershell -ExecutionPolicy Bypass -File scripts/setup_hooks.ps1`

Validacion manual:

- `python -m pre_commit validate-config`

## Criterio de merge local

No cerrar una tarea tecnica sin:

- `ruff` en verde.
- `black --check` en verde.
- `mypy` en verde.
- `pytest` en verde.

## CI automatizado

El workflow de CI vive en:

- `.github/workflows/ci.yml`

Se ejecuta en `push` (branches `main`/`master`) y en `pull_request`.

Orden de checks en CI:

1. `ruff check app mcp_server`
2. `black --check app mcp_server`
3. `mypy app mcp_server`
4. `alembic upgrade head`
5. `alembic current`
6. `pytest -q`

## Como depurar cuando CI falla

1. Reproducir localmente los comandos en el mismo orden.
2. Corregir primero lint/format (son los fallos mas rapidos de resolver).
3. Validar tipado (`mypy`) antes de correr tests.
4. Confirmar migraciones Alembic en `head`.


