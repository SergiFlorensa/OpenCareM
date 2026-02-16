# ADR-0036: Observabilidad del Scorecard Global (alertas y paneles)

## Estado

Aprobado

## Contexto

Tras incorporar el scorecard global de calidad IA clinica (`TM-058`), faltaba
operativizar su uso en observabilidad diaria:

- deteccion temprana de degradacion de calidad,
- visualizacion simple para seguimiento de guardia.

## Decision

Agregar:

- Alertas Prometheus en `ops/prometheus/alerts.yml`:
  - `CareTaskQualityUnderRateHigh`
  - `CareTaskQualityOverRateHigh`
  - `CareTaskQualityMatchRateLow`
- Paneles Grafana en `ops/grafana/dashboards/task_manager_overview.json`:
  - `Calidad Global Audit Total`
  - `Calidad Global Under Rate %`
  - `Calidad Global Over Rate %`
  - `Calidad Global Match Rate %`
- Runbook operativo:
  - `docs/54_runbook_alertas_calidad_global.md`

## Consecuencias

### Positivas

- deteccion mas rapida de drift IA vs validacion humana,
- menor friccion operativa al unificar lectura de calidad.

### Riesgos / Costes

- umbrales globales pueden requerir ajuste por volumen y estacionalidad,
- posible ruido inicial mientras crece el volumen auditado.

## Validacion

- parseo JSON de dashboard correcto,
- pruebas de metricas:
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py`
