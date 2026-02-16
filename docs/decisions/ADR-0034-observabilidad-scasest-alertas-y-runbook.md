# ADR-0034: Observabilidad SCASEST con Alertas y Runbook

## Estado

Aprobado

## Contexto

Ya existían métricas SCASEST y auditoría IA vs humano, pero faltaba capa operativa para detectar degradación de calidad sin revisión manual continua.

## Decisión

1. Añadir paneles SCASEST en Grafana:
   - runs totales,
   - under-rate,
   - over-rate,
   - match de escalado.
2. Añadir alertas Prometheus:
   - `ScasestAuditUnderRateHigh` (`under_rate > 10%` por 2m),
   - `ScasestAuditOverRateHigh` (`over_rate > 20%` por 2m).
3. Crear runbook de respuesta:
   - `docs/51_runbook_alertas_scasest.md`.

## Consecuencias

### Positivas

- detección temprana de degradación en calidad SCASEST,
- respuesta operativa estandarizada ante alertas,
- menor dependencia de inspección manual ad-hoc.

### Riesgos / Costes

- umbrales iniciales pueden requerir ajuste según volumen real,
- con baja muestra pueden aparecer alertas poco representativas.

## Validación

- parseo JSON del dashboard actualizado sin errores,
- tests de métricas en verde:
  - `.\venv\Scripts\python.exe -m pytest -q app/tests/test_metrics_endpoint.py`.
