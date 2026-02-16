# ADR-0005: Grafana en Compose con dashboard base

## Contexto

Con Prometheus ya integrado, faltaba una capa visual para interpretar metricas
de forma rapida durante desarrollo y pruebas operativas.

## Decision

Integrar Grafana en `docker-compose.yml` con provisioning automatico de:

- datasource Prometheus
- dashboard base de API

La configuracion queda versionada en `ops/grafana/`.

## Consecuencias

Beneficios:

- Onboarding mas rapido para observabilidad.
- Dashboards reproducibles entre equipos.
- Base para alertas y SLO en fases siguientes.

Costes:

- Servicio adicional en stack local.
- Credenciales por defecto solo aptas para entorno local.

## Validacion

- `docker compose config`
- `http://127.0.0.1:3000` accesible
- Dashboard `Resumen API Gestor de Tareas` disponible




