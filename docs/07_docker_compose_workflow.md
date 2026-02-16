# Flujo de Docker Compose

Guia paso a paso para ejecutar el proyecto en contenedores con PostgreSQL.

## 1. Que se levanta

- `db`: PostgreSQL 16
- `api`: FastAPI del proyecto
- `prometheus`: servidor de metricas para scraping de `/metrics`
- `grafana`: visualizacion de metricas y dashboards

El servicio `api` espera a que `db` este saludable y luego ejecuta:

1. `alembic upgrade head`
2. `uvicorn app.main:app ...`

## 2. Arranque

Desde la raiz del repo:

```bash
docker compose up --build
```

## 3. Verificacion

En otra terminal:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/v1/tasks/
curl http://127.0.0.1:9090/-/healthy
```

Esperado:

- `/health` responde `200`.
- `/api/v1/tasks/` responde lista JSON.

## 4. Apagado

```bash
docker compose down
```

Si quieres borrar datos de PostgreSQL:

```bash
docker compose down -v
```

## 5. Comandos utiles de diagnostico

Ver estado de servicios:

```bash
docker compose ps
```

Ver logs:

```bash
docker compose logs -f api
docker compose logs -f db
docker compose logs -f prometheus
docker compose logs -f grafana
```

## 6. Archivos implicados

- `docker-compose.yml`
- `docker/Dockerfile`
- `.dockerignore`
- `.env.docker`
- `ops/prometheus/prometheus.yml`
- `ops/grafana/provisioning/datasources/datasource.yml`
- `ops/grafana/provisioning/dashboards/dashboard.yml`
- `ops/grafana/dashboards/task_manager_overview.json`

## 7. Hardening aplicado

El `Dockerfile` usa:

- Build multi-stage (`builder` + `runtime`).
- Entorno virtual copiado desde stage de build.
- Usuario no root (`appuser`) en runtime.
- Imagen base `python:3.12-slim`.

Objetivo:

- Reducir superficie de runtime.
- Evitar ejecutar la API como root.
- Mantener dependencia de build separada del entorno final.


