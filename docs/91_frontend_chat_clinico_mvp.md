# Frontend MVP: Chat Clinico Operativo

## Objetivo

Disponer de una interfaz moderna y minimalista para simular el flujo real de uso
profesional del chat clinico:

- login del profesional,
- seleccion/creacion de caso,
- conversacion por sesion,
- visualizacion de memoria, trazas y fuentes.

## Stack elegido

- `Vite + React + TypeScript` en `frontend/`.

Motivo: menor complejidad operativa, arranque rapido y buen rendimiento para
un MVP de interfaz conversacional.

## Estructura

- `frontend/src/App.tsx`: shell principal, estado y llamadas API.
- `frontend/src/styles.css`: UI dark/minimal estilo chat moderno.
- `frontend/vite.config.ts`: servidor local en `127.0.0.1:5173`.

## Flujo funcional implementado

1. Login (`POST /api/v1/auth/login`).
2. Consulta de perfil (`GET /api/v1/auth/me`).
3. Creacion y listado de casos (`POST/GET /api/v1/care-tasks/`).
4. Conversacion (`POST /api/v1/care-tasks/{id}/chat/messages`).
5. Historial y memoria (`GET /chat/messages`, `GET /chat/memory`).
6. Panel de trazabilidad:
   - `effective_specialty`
   - `knowledge_sources`
   - `web_sources`
   - `interpretability_trace`
   - `non_diagnostic_warning`

## Ejecucion local

Desde raiz del repo:

1. API backend:
   - `.\venv\Scripts\python.exe -m uvicorn app.main:app --reload`
2. Frontend:
   - `cd frontend`
   - `npm install`
   - `npm run dev`
3. Abrir:
   - `http://127.0.0.1:5173`

## Requisito de CORS

La configuracion por defecto incluye `http://localhost:5173` y
`http://127.0.0.1:5173` en CORS.

Si tu `.env` local define `BACKEND_CORS_ORIGINS`, asegura incluir ambos
origenes (`localhost` y `127.0.0.1`) segun tu navegador.

## Limitaciones actuales del MVP

- No incluye streaming token a token.
- No incluye UI de sellado de fuentes (`knowledge-sources`), solo consumo chat.
- No incluye tablero clinico completo (fase posterior).
