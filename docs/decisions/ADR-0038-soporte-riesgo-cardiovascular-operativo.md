# ADR-0038: Soporte operativo de riesgo cardiovascular con auditoria y observabilidad

- Fecha: 2026-02-12
- Estado: aceptada

## Contexto

El proyecto ya cubre varios motores operativos (triaje, screening, medico-legal, sepsis, SCASEST), pero faltaba una pieza especifica para riesgo cardiovascular preventivo-operativo (no-HDL/ApoB, estratificacion y plan inicial).

Tambien faltaba incorporar ese dominio en el marco de auditoria IA vs humano y en scorecard global de calidad.

## Decision

Se implementa:

1. Motor `cardio_risk_support_v1`:
   - endpoint `POST /care-tasks/{id}/cardio-risk/recommendation`
   - salida explicable y validacion humana obligatoria

2. Auditoria cardiovascular:
   - `POST/GET /care-tasks/{id}/cardio-risk/audit`
   - `GET /care-tasks/{id}/cardio-risk/audit/summary`
   - clasificacion `match/under_cardio_risk/over_cardio_risk`

3. Observabilidad:
   - metricas `cardio_risk_support_*` y `cardio_risk_audit_*`
   - alertas `CardioRiskAuditUnderRateHigh` y `CardioRiskAuditOverRateHigh`
   - inclusion del dominio `cardio_risk` en scorecard global

4. Datos:
   - tabla `care_task_cardio_risk_audit_logs`
   - migracion Alembic dedicada

## Consecuencias

### Positivas

- Se amplian capacidades clinico-operativas con un dominio cardiovascular de alto impacto real.
- Se mantiene enfoque seguro: soporte no diagnostico + human-in-the-loop.
- La calidad del nuevo dominio queda medible y comparable con el resto.

### Trade-offs

- Mayor complejidad de contratos y mantenimiento de tests.
- Nuevas series metricas y alertas que requieren tuning operativo continuo.

## Alternativas consideradas

1. No auditar el dominio cardiovascular
   - Rechazada: reduce control de calidad y trazabilidad.
2. Implementar solo recomendacion sin observabilidad
   - Rechazada: no alineado con estandar de operacion del proyecto.
3. Implementacion completa con auditoria+metricas+alertas
   - Elegida.
