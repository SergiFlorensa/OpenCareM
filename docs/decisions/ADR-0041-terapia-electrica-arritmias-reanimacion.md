# ADR-0041: Terapia electrica de arritmias integrada en motor de reanimacion

- Fecha: 2026-02-13
- Estado: aceptada

## Contexto

El motor de reanimacion ya cubria RCP, farmacos y post-ROSC, pero no exponia
un bloque especifico y estructurado para:

- decision cardioversion sincronizada vs desfibrilacion
- energia orientativa por tipo de ritmo
- sedoanalgesia peri-procedimiento
- checklist de seguridad pre-descarga

## Decision

Se extiende `ResuscitationProtocolRecommendation` con:

- `electrical_therapy_plan`
- `sedoanalgesia_plan`
- `pre_shock_safety_checklist`

Y se amplian entradas con:

- `systolic_bp_mm_hg`
- `diastolic_bp_mm_hg`

Para detectar presion de pulso estrecha como senal de bajo gasto en arritmias
con pulso.

## Consecuencias

### Positivas

- Mayor accionabilidad en escenarios de arritmias inestables.
- Menor ambiguedad operativa sobre energia inicial por ritmo.
- Mejor seguridad procedimental con checklist pre-descarga.

### Trade-offs

- Payload de salida mas amplio.
- Necesidad de mantener actualizada la tabla de energia segun protocolos locales.

## Alternativas consideradas

1. Crear endpoint separado solo para cardioversion/desfibrilacion.
   - Rechazada: fragmenta flujo y trazabilidad.
2. Mantener recomendaciones electricas dentro de `primary_actions`.
   - Rechazada: baja estructura para consumidores de frontend/observabilidad.
3. Integrar bloques dedicados en workflow de reanimacion existente.
   - Elegida.
