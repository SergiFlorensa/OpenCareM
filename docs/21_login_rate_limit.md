# Login Rate Limit and Brute Force Protection

Este documento explica la proteccion de login contra intentos masivos de fuerza bruta.

## Objetivo

- Limitar intentos fallidos de autenticacion por `username + IP`.
- Aplicar bloqueo temporal automatico al superar umbral.
- Reducir riesgo de ataque por prueba de contrasenas.

## Reglas implementadas

Configurables desde settings:

- `LOGIN_MAX_ATTEMPTS` (default: `5`)
- `LOGIN_WINDOW_MINUTES` (default: `5`)
- `LOGIN_BLOCK_MINUTES` (default: `10`)

Comportamiento:

1. Se acumulan fallos de login en la ventana definida.
2. Si alcanza el maximo, se bloquea temporalmente.
3. Durante bloqueo, `POST /auth/login` responde `429`.
4. Login correcto limpia contador y bloqueo.

## Componentes

- Modelo: `app/models/login_attempt.py`
- Servicio: `app/services/login_throttle_service.py`
- Integracion endpoint: `app/api/auth.py`
- Migracion: `alembic/versions/e7f1c2a4b990_add_login_attempts_table.py`

## Respuestas esperadas

- Credenciales incorrectas: `401`
- Limite superado: `429` con detalle de bloqueo temporal
- Login correcto tras estado limpio: `200`

## Validacion

- `.\venv\Scripts\python.exe -m pytest -q app/tests/test_auth_api.py`

Casos cubiertos:

- bloqueo tras multiples fallos consecutivos.
- reseteo de contador despues de login valido.

## Riesgos pendientes

- No hay almacenamiento distribuido para conteo multi-instancia (actualmente DB local).
- No se aplica politica diferenciada por rol o por endpoint.


