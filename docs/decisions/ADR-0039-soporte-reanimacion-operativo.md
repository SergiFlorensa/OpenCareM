# ADR-0039: Soporte operativo de reanimacion con auditoria y observabilidad

- Fecha: 2026-02-12
- Estado: aceptada

## Contexto

El proyecto ya cubre triaje y multiples motores clinico-operativos, pero faltaba un bloque especifico para escenarios de reanimacion y soporte vital (paro, arritmias inestables, post-ROSC), incluyendo reglas operativas de choque, ventilacion y causas reversibles.

Tambien faltaba incorporar este dominio en el marco de auditoria IA vs humano y en scorecard global de calidad.

## Decision

Se implementa:

1. Motor `resuscitation_protocol_support_v1`:
   - endpoint `POST /care-tasks/{id}/resuscitation/recommendation`
   - salida explicable y validacion humana obligatoria

2. Auditoria de reanimacion:
   - `POST/GET /care-tasks/{id}/resuscitation/audit`
   - `GET /care-tasks/{id}/resuscitation/audit/summary`
   - clasificacion `match/under_resuscitation_risk/over_resuscitation_risk`

3. Observabilidad:
   - metricas `resuscitation_protocol_*` y `resuscitation_audit_*`
   - alertas `ResuscitationAuditUnderRateHigh` y `ResuscitationAuditOverRateHigh`
   - inclusion del dominio `resuscitation` en scorecard global

4. Datos:
   - tabla `care_task_resuscitation_audit_logs`
   - migracion Alembic dedicada

## Consecuencias

### Positivas

- Se cubre un flujo de alto impacto en urgencias con reglas explicables y trazables.
- Se mantiene enfoque seguro: soporte no diagnostico + human-in-the-loop.
- La calidad del nuevo dominio queda medible y comparable con el resto.

### Trade-offs

- Mayor complejidad de contratos y mantenimiento de pruebas.
- Nuevas series metricas/alertas que requieren ajuste operativo continuo.

## Alternativas consideradas

1. Implementar solo recomendacion sin auditoria
   - Rechazada: no permite medir desviacion IA vs humano.
2. Implementar sin metricas ni alertas
   - Rechazada: rompe estandar de observabilidad del proyecto.
3. Implementacion completa con auditoria+metricas+alertas
   - Elegida.
