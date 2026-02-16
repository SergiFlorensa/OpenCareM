# Resolucion de Problemas

## Target de Prometheus en DOWN

1. Verifica que el contenedor API esta levantado.
2. Verifica `/metrics` desde host.
3. Verifica logs de Prometheus.
4. Confirma que el target en `ops/prometheus/prometheus.yml` es `api:8000`.

## Grafana sin datos

1. Confirma que el datasource de Prometheus es accesible.
2. Confirma que el rango de consulta incluye trafico reciente.
3. Genera trafico (`/health`, `/api/v1/tasks/`) y refresca.

## Error al arrancar Compose

1. Asegura que el motor de Docker Desktop esta en ejecucion.
2. Ejecuta `docker compose config` para validar sintaxis.
3. Reinicia la pila con `docker compose down` y luego `docker compose up --build`.

