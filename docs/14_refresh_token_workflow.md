# Flujo de Token de Refresco

Este documento explica el flujo de refresh token con rotacion y logout.

## Objetivo

- Evitar sesiones largas con solo access token.
- Poder invalidar sesiones de refresh al cerrar sesion.
- Bloquear reuso de refresh antiguos (rotacion).

## Componentes

- `app/models/auth_session.py`: tabla de sesiones de refresh.
- `app/services/auth_service.py`: logica de emision, rotacion y revocacion.
- `app/api/auth.py`: endpoints `/auth/refresh` y `/auth/logout`.
- `app/core/security.py`: utilidades JWT para refresh token.

## Flujo paso a paso

1. Login correcto (`/auth/login`).
2. API devuelve `access_token` + `refresh_token`.
3. Se guarda una fila en `auth_sessions` con `jti` y expiracion.
4. Cliente llama `/auth/refresh` con refresh vigente.
5. API revoca sesion anterior y crea nueva sesion (rotacion).
6. Cliente recibe nuevo par de tokens.
7. Si cliente llama `/auth/logout`, esa sesion queda revocada.

## Reglas principales

- Un refresh revocado no se puede reutilizar.
- Un refresh expirado no se acepta.
- Un refresh con `type` incorrecto no se acepta.
- Solo refresh token rota tokens; access token no.

## Endpoints

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

## Validacion

Comando:

`.\venv\Scripts\python.exe -m pytest -q app/tests/test_auth_api.py`

Casos cubiertos:

- Login entrega refresh token.
- Refresh rota correctamente.
- Reuso de refresh viejo devuelve `401`.
- Logout revoca y bloquea refresh posterior.

## Riesgos pendientes

- No hay lista de sesiones por usuario para cerrar todas desde perfil.
- No hay deteccion avanzada de robo de token (reuse detection global).
- No se usa almacenamiento distribuido (Redis) para sesiones en esta fase.


