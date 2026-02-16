# RBAC Admin v1

Este documento explica el primer control de permisos por rol (`admin`) en la API.

## Objetivo

- Proteger endpoints operativos para que solo los admins puedan usarlos.
- Mantener una implementacion simple y legible para evolucionar despues.

## Que se implemento

1. Dependencias reutilizables de auth en `app/api/deps.py`.
2. Endpoint admin en `app/api/auth.py`:
   - `GET /api/v1/auth/admin/users`
3. Respuesta de `/auth/me` extendida con flag `is_superuser`.
4. Pruebas de permisos en `app/tests/test_auth_api.py`.

## Flujo paso a paso

1. Cliente envia `Bearer token`.
2. `get_current_subject` valida JWT y extrae `sub` (username).
3. `get_current_user` busca ese usuario en DB.
4. `require_superuser` valida `is_superuser == True`.
5. Si pasa, el endpoint admin responde.

## Respuestas esperadas

- Sin token: `401`.
- Con token valido pero sin rol admin: `403`.
- Con token admin: `200` y listado de usuarios.

## Contrato de respuesta

`GET /api/v1/auth/admin/users`

```json
[
  {
    "id": 1,
    "username": "rootadmin",
    "is_active": true,
    "is_superuser": true
  }
]
```

## Validacion

Comando ejecutado:

`.\venv\Scripts\python.exe -m pytest -q app/tests/test_auth_api.py`

Resultado esperado:

- Tests de auth en verde.
- Casos de permiso (`401`, `403`, `200`) cubiertos.

## Riesgos pendientes

- Falta separar permisos mas finos (por ejemplo, admin de solo lectura vs escritura).
- Falta estandarizar auditoria de acciones admin.
- Falta refresh token y revocacion de sesiones.


