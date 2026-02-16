# ADR-0027 - Soporte Operativo de Interpretacion RX Torax

## Estado

Aprobado

## Contexto

El proyecto necesita ampliar su capacidad de soporte clinico-operativo con
una lectura estructurada de radiografia de torax para urgencias, manteniendo:

- interpretabilidad,
- trazabilidad,
- y validacion humana obligatoria.

## Decision

Implementar workflow `chest_xray_support_v1` con:

1. endpoint `POST /api/v1/care-tasks/{id}/chest-xray/interpretation-support`;
2. servicio `ChestXRaySupportService` basado en reglas de patrones/signos;
3. trazabilidad en `agent_runs` y `agent_steps`;
4. metricas de ejecucion y alertas criticas en Prometheus.

## Consecuencias

### Positivas

- Estandariza lectura sistematica y priorizacion de red flags.
- Refuerza seguridad en urgencias con acciones orientativas auditables.
- Mantiene separacion clara entre soporte operativo y diagnostico medico final.

### Trade-offs

- Reglas iniciales simplificadas; requieren calibracion con especialistas.
- Mayor complejidad de contratos API, pruebas y observabilidad.

## Alternativas consideradas

- Prompt libre sin estructura: descartado por baja reproducibilidad.
- Modelo opaco de clasificacion: descartado por falta de interpretabilidad.
