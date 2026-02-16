# Flujo API de Autenticacion

Flujo minimo de autenticacion disponible en la API.

## Endpoints

- `POST /api/v1/auth/register`
  - Entrada: JSON `username`, `password`
  - Salida: `id`, `username` creado
  - Reglas:
    - username unico
    - password con minimo de seguridad (8+, mayus/minus y numero)

- `POST /api/v1/auth/login`
  - Entrada: `application/x-www-form-urlencoded`
  - Campos: `username`, `password`
  - Salida: `access_token` JWT + `refresh_token` JWT + `token_type`

- `POST /api/v1/auth/refresh`
  - Entrada: JSON `{ "refresh_token": "..." }`
  - Salida: nuevo `access_token` + nuevo `refresh_token` (rotacion)

- `POST /api/v1/auth/logout`
  - Entrada: JSON `{ "refresh_token": "..." }`
  - Efecto: revoca la sesion refresh para bloquear reuso

- `GET /api/v1/auth/me`
  - Requiere header: `Authorization: Bearer <token>`
  - Salida: `username` + `is_superuser`

- `GET /api/v1/auth/admin/users`
  - Requiere header: `Authorization: Bearer <token>`
  - Requiere rol admin (`is_superuser = true`)
  - Salida: lista de usuarios del sistema (`id`, `username`, `is_active`, `is_superuser`)

## Credenciales demo

Esta version autentica contra tabla `users` en base de datos.
Para probar, primero necesitas un usuario persistido.

## Ejemplo rapido

1. Crear usuario (ejemplo SQL directo para pruebas):
   - `INSERT INTO users (username, hashed_password, is_active) VALUES (...)`
2. Login:
   - `curl -X POST http://127.0.0.1:8000/api/v1/auth/login -H "Content-Type: application/x-www-form-urlencoded" -d "username=admin&password=admin12345"`
3. Usar token en `/me`:
   - `curl http://127.0.0.1:8000/api/v1/auth/me -H "Authorization: Bearer <token>"`
4. (Opcional admin) listar usuarios:
   - `curl http://127.0.0.1:8000/api/v1/auth/admin/users -H "Authorization: Bearer <token>"`
5. Rotar sesion con refresh:
   - `curl -X POST http://127.0.0.1:8000/api/v1/auth/refresh -H "Content-Type: application/json" -d "{\"refresh_token\":\"<refresh>\"}"`

## Limite actual

Esta version ya usa usuarios persistentes, RBAC admin basico y refresh token con rotacion.
Todavia falta revocacion global por usuario y gestion completa de cuentas.


