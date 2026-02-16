# Fundacion de Autenticacion

Base de seguridad para autenticacion preparada en capa `core`.

## Objetivo

Disponer de utilidades reutilizables para:

- Hash y verificacion de contraseÃ±as.
- Emision y validacion de JWT access tokens.

Sin acoplar aun endpoints de login/usuarios.

## Componentes

Archivo: `app/core/security.py`

- `get_password_hash(password)`
- `verify_password(plain_password, hashed_password)`
- `create_access_token(subject, expires_delta=None, additional_claims=None)`
- `decode_access_token(token)`

## Claims JWT usados

- `sub`: identificador principal (usuario/actor).
- `iat`: issued at.
- `exp`: expiration.

## Pruebas

Archivo: `app/tests/test_security_core.py`

Cubre:

- Hash/verify de password.
- Emision/decodificacion de token valido.
- Rechazo de token invalido.
- Rechazo de token sin claim `sub`.



