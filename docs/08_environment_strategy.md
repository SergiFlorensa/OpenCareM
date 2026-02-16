# Estrategia de Entornos

Guia de configuracion por entorno para mantener coherencia entre local, Docker y CI.

## Archivos

- `.env.example`: plantilla base para desarrollo local.
- `.env.docker`: variables para `docker-compose`.
- `.env`: archivo local real (no versionado).

## Flujo recomendado

1. Copiar plantilla local:
   - `cp .env.example .env` (Git Bash)
   - `Copy-Item .env.example .env` (PowerShell)
2. Ajustar valores sensibles en `.env`.
3. Para Docker Compose, usar `.env.docker` como fuente declarada en `docker-compose.yml`.

## Regla de seguridad

- Nunca commitear `.env` real.
- Solo commitear plantillas (`.env.example`, `.env.docker` si no contiene secretos reales).

## Variables clave

- `DATABASE_URL`:
  - local default: SQLite
  - Docker: PostgreSQL en servicio `db`
- `DATABASE_ECHO`:
  - `true` para debug local
  - `false` para Docker/CI
- `SECRET_KEY`:
  - en `development` puede usar default para aprendizaje local
  - fuera de `development` debe ser distinta al default y de 32+ caracteres
- `BACKEND_CORS_ORIGINS`:
  - en no-dev no debe incluir `"*"`
- `SECRET_KEY` y `ALGORITHM`:
  - se usan para firmar y validar JWT de autenticacion

## Validacion rapida

Local:

- `pytest -q`
- `alembic current`

Docker:

- `docker compose up --build`
- `curl http://127.0.0.1:8000/health`


