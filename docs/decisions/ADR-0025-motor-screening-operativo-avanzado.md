# ADR-0025 - Motor de Screening Operativo Avanzado

## Estado

Aprobado

## Contexto

Tras TM-046, el proyecto dispone de motores operativos por dominio, pero faltaba
un flujo transversal para combinar:

- vulnerabilidad geriatrica,
- cribado precoz orientado por indicadores,
- gestion de alertas con fatiga,
- y eficiencia operativa en transicion de terapias.

## Decision

Implementar un motor unificado de screening avanzado con:

1. endpoint: `POST /api/v1/care-tasks/{id}/screening/recommendation`;
2. servicio dedicado: `AdvancedScreeningService`;
3. workflow trazable: `advanced_screening_support_v1`;
4. metricas de ejecucion y calidad de alertas en Prometheus.

## Consecuencias

### Positivas

- Mayor utilidad operativa en triage real sin introducir caja negra.
- Trazabilidad completa de por que se dispara cada alerta.
- Capacidad de medir ruido operativo (alertas suprimidas).

### Trade-offs

- Reglas iniciales simplificadas que requieren calibracion con datos reales.
- Riesgo de rigidez si no se versionan umbrales por entorno.
- Incremento de complejidad en contratos y pruebas.

## Alternativas consideradas

- Mantener solo motores separados por dominio: descartado por duplicidad de logica.
- Ir directo a modelo ML opaco: descartado por interpretabilidad insuficiente.
- No medir supresion de alertas: descartado por riesgo de fatiga no controlada.
