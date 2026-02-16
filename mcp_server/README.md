# Servidor MCP (API de Gestion de Tareas)

Este directorio contiene un servidor **MCP** que expone herramientas (tools) para gestionar tareas,
pero **no toca la BD directamente**: llama a la API FastAPI por HTTP.

## Requisitos

1) Tener la API corriendo (por defecto en `http://localhost:8000`).
2) Crear un venv para el MCP server e instalar dependencias:

```powershell
python -m venv mcp_server\.venv
mcp_server\.venv\Scripts\python.exe -m pip install -r mcp_server\requirements.txt
```

## Ejecutar

```powershell
$env:TASK_API_BASE_URL="http://localhost:8000/api/v1"
mcp_server\.venv\Scripts\python.exe mcp_server\server.py
```

Por defecto corre en `stdio` (lo tipico para Claude Desktop / clientes MCP locales).

## Variables de entorno

- `TASK_API_BASE_URL` (por defecto: `http://localhost:8000/api/v1`)
- `TASK_API_ROOT_URL` (opcional; si lo pones, se usa para `openapi_schema`)




