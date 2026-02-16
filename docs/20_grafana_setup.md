# Configuracion de Grafana

Guia para usar Grafana con Prometheus en este proyecto.

## Para que sirve Grafana aqui

- Visualizar metricas en paneles claros.
- Ver tendencia (no solo foto puntual).
- Detectar problemas rapido (latencia, errores, caidas).

Prometheus guarda metricas; Grafana las visualiza.

## Que se provisiona automaticamente

1. Data source `Prometheus` apuntando a `http://prometheus:9090`.
2. Dashboard base: `Resumen API Gestor de Tareas`.

Archivos:

- `ops/grafana/provisioning/datasources/datasource.yml`
- `ops/grafana/provisioning/dashboards/dashboard.yml`
- `ops/grafana/dashboards/task_manager_overview.json`

## Arranque paso a paso

1. Levantar stack:
   - `docker compose up --build`
2. Abrir Grafana:
   - `http://127.0.0.1:3000`
3. Login inicial:
   - user: `admin`
   - pass: `admin`
4. Ir a Dashboards y abrir:
   - `Resumen API Gestor de Tareas`

## Que paneles veras

1. `HTTP Requests Rate (1m)`:
   - volumen de requests por ruta/metodo/status.
2. `Latency p95 (5m)`:
   - latencia alta tipica del percentil 95.
3. `5xx Error Ratio (5m)`:
   - porcentaje de errores servidor.
4. `Total de Ejecuciones de Agente`:
   - corridas totales persistidas de workflows agente.
5. `Ejecuciones Fallidas de Agente`:
   - corridas fallidas para detectar problemas de confiabilidad.
6. `Tasa de Fallback de Agente %`:
   - porcentaje de corridas donde se uso fallback.
7. `Pasos con Fallback de Agente`:
   - total de pasos que activaron fallback.

## Como practicar

1. Lanza varias requests:
   - `GET /health`
   - `GET /api/v1/tasks/`
   - `POST /api/v1/tasks/`
2. Vuelve al dashboard.
3. Observa como suben requests y cambian las curvas.

## Riesgos pendientes

- Credenciales admin por defecto en local (no usar en entornos reales).
- Aun no hay alertas configuradas.



