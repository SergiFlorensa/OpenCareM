# ADR-0003: Token de refresco con rotacion y revocacion basica

## Contexto

El access token solo ya no es suficiente para sesiones seguras y controlables.
Necesitamos renovar acceso sin pedir login continuo y, a la vez, poder invalidar sesiones.

## Decision

Implementar refresh token con estas reglas:

- Cada refresh emitido se registra en `auth_sessions` con `jti`.
- En `POST /auth/refresh`, el refresh actual se revoca y se emite uno nuevo (rotacion).
- En `POST /auth/logout`, se revoca explicitamente la sesion refresh recibida.

## Consecuencias

Beneficios:

- Reduce ventana de uso de access token.
- Permite invalidar sesiones concretas.
- Evita reuso de refresh ya usado/revocado.

Costo:

- Mas complejidad de estado en base de datos.
- Necesidad de limpiar sesiones expiradas en el futuro.

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_auth_api.py`
- `.\venv\Scripts\python.exe -m pytest -q`
- Casos clave: rotacion correcta, reuso bloqueado, logout revoca.



