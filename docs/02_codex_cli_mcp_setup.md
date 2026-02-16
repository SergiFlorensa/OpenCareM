# Configuracion MCP de Codex CLI

Esta guia explica como probar MCP en Codex CLI con este proyecto.

## Aclaracion clave

- Codex CLI es una herramienta de OpenAI (ecosistema ChatGPT).
- MCP es un protocolo abierto para conectar herramientas a asistentes.
- En este proyecto, Codex CLI actua como cliente MCP y `mcp_server/server.py` como servidor MCP.

## Prerrequisitos

1. Python instalado.
2. Dependencias del API instaladas en `venv/`.
3. Dependencias del MCP instaladas en `mcp_server/.venv/`.
4. `codex` disponible en terminal.

## Paso 1: levantar la API

Desde la raiz del repo:

```powershell
.\venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

Validar salud:

```powershell
curl http://127.0.0.1:8000/health
```

## Paso 2: (opcional) probar MCP server standalone

En otra terminal:

```powershell
$env:TASK_API_BASE_URL="http://127.0.0.1:8000/api/v1"
.\mcp_server\.venv\Scripts\python.exe .\mcp_server\server.py
```

Nota: por defecto corre en `stdio`, que es lo normal para clientes MCP locales.

## Paso 3: registrar servidor MCP en Codex CLI

```powershell
$py = (Resolve-Path ".\mcp_server\.venv\Scripts\python.exe").Path
$srv = (Resolve-Path ".\mcp_server\server.py").Path
codex mcp add task-manager-api --env TASK_API_BASE_URL=http://127.0.0.1:8000/api/v1 -- $py $srv
```

## Paso 4: verificar configuracion

```powershell
codex mcp list
codex mcp get task-manager-api --json
```

Si esta bien, veras:

- `transport.type = "stdio"`
- `command = ...\mcp_server\.venv\Scripts\python.exe`
- `args = [...\mcp_server\server.py]`
- `env.TASK_API_BASE_URL = "http://127.0.0.1:8000/api/v1"`

## Paso 5: usarlo en sesion Codex

Inicia Codex en la carpeta del proyecto:

```powershell
codex
```

Ejemplos de prompts para forzar uso del MCP:

1. "Usa el MCP task-manager-api y crea una tarea llamada 'Probar MCP'."
2. "Lista tareas por MCP y dame solo id, title y completed."
3. "Marca como completada la tarea con id 1 usando MCP."

## Paso 6: mantenimiento

- Ver lista: `codex mcp list`
- Ver config: `codex mcp get task-manager-api --json`
- Eliminar: `codex mcp remove task-manager-api`

## Resolucion de Problemas rapido

- Error de conexion HTTP:
  - Verifica API activa en `http://127.0.0.1:8000`.
  - Revisa `TASK_API_BASE_URL`.
- Tool no aparece:
  - Confirma que el server MCP arranca sin error: `python mcp_server/server.py`.
- Conflicto de entorno virtual:
  - Reinstala deps MCP: `python -m pip install -r mcp_server/requirements.txt`.



