# Flujo de Gestion de Errores

Este documento explica como responde la API cuando algo falla y como diagnosticarlo.

## Objetivo

- Tener un criterio unico para interpretar errores HTTP.
- Acelerar debug en Postman, logs y pruebas automatizadas.

## Estructura actual de error

La API usa el formato por defecto de FastAPI:

- Errores de negocio/control (`HTTPException`): `{ "detail": "..." }`
- Errores de validacion (`422`): `{ "detail": [ ... ] }`

## Catalogo de errores frecuentes

### `400 Bad Request`

Errores de reglas de negocio en registro:

- Nombre de usuario duplicado.
- Contrasena debil.

Ejemplo:

```json
{ "detail": "El nombre de usuario ya existe." }
```

### `401 Unauthorized`

Errores de autenticacion:

- Credenciales de login incorrectas.
- Token ausente o invalido.
- Refresh token revocado/expirado/invalido.

Ejemplo:

```json
{ "detail": "Nombre de usuario o contrasena incorrectos." }
```

### `403 Forbidden`

Token valido pero sin permisos admin.

Ejemplo:

```json
{ "detail": "Se requieren permisos de administrador." }
```

### `404 Not Found`

Recurso no encontrado (por ejemplo, tarea inexistente).

Ejemplo:

```json
{ "detail": "Tarea con ID 999 no encontrada" }
```

### `422 Unprocessable Entity`

Payload o formato invalido (campos faltantes/tipo incorrecto).

Ejemplo resumido:

```json
{
  "detail": [
    { "loc": ["body", "username"], "msg": "Field required" }
  ]
}
```

### `500 Internal Server Error`

Inconsistencia interna inesperada (caso raro, pero contemplado).

## Flujo de diagnostico rapido

1. Revisar status code.
2. Leer `detail` completo en respuesta.
3. Confirmar tipo de body correcto:
   - `/auth/login`: `x-www-form-urlencoded`
   - `/auth/register`, `/auth/refresh`, `/auth/logout`: JSON
4. Verificar token/cabeceras (`Authorization: Bearer ...`).
5. Validar que el recurso exista en DB.

## Referencias de pruebas

- `app/tests/test_auth_api.py`
- `app/tests/test_tasks_api.py`

Estas pruebas ya cubren los errores mas comunes (400/401/403/404/422).

## Riesgos pendientes

- No hay un envelope estandarizado unico para todos los errores.
- No hay catalogo de codigos de error internos (`error_code`) por dominio.


