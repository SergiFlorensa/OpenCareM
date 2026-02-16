# ADR-0042: Soporte bioetico pediatrico en motor medico-legal

- Fecha: 2026-02-13
- Estado: aceptada

## Contexto

El motor medico-legal cubria consentimiento, cadena de custodia y judicializacion,
pero no modelaba de forma explicita el conflicto critico pediatrico cuando:

- hay riesgo vital inminente del menor
- existe rechazo representado de tratamiento potencialmente salvador
- hay desamparo legal o imposibilidad de autorizacion judicial inmediata

Este vacio reducia la capacidad del sistema para guiar trazabilidad y acciones
en un escenario de alta complejidad bioetica y legal.

## Decision

Se extiende `MedicolegalOpsRequest` con campos opcionales para el conflicto:

- `legal_representatives_deceased`
- `parental_religious_refusal_life_saving_treatment`
- `life_threatening_condition`
- `blood_transfusion_indicated`
- `immediate_judicial_authorization_available`

Y se agregan reglas en `MedicolegalOpsService` para:

- elevar riesgo legal a `high` en conflicto pediatrico critico
- emitir alertas de interes superior del menor y deber de proteccion
- exigir documentacion reforzada (proporcionalidad/estado de necesidad)
- recomendar acciones sin demora de soporte vital indicado en riesgo inminente

## Consecuencias

### Positivas

- Mayor claridad operativa en escenarios eticamente extremos.
- Mejor trazabilidad defensiva clinico-legal.
- Compatibilidad hacia atras: nuevos campos son opcionales.

### Trade-offs

- Aumenta el numero de variables en el payload medico-legal.
- Requiere disciplina documental mas estricta por parte del equipo asistencial.

## Alternativas consideradas

1. Mantener manejo ad-hoc en notas libres.
   - Rechazada: baja estandarizacion y menor auditabilidad.
2. Crear endpoint independiente de bioetica.
   - Rechazada: fragmenta flujo operativo y duplicaria reglas.
3. Extender motor medico-legal existente.
   - Elegida.
