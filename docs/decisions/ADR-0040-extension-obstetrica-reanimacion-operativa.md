# ADR-0040: Extension obstetrica del soporte operativo de reanimacion

- Fecha: 2026-02-13
- Estado: aceptada

## Contexto

El motor de reanimacion (`resuscitation_protocol_support_v1`) ya cubria ACLS/BLS general, pero faltaban reglas obstetricas criticas para paro en gestante:

- alivio mecanico de compresion aortocava
- ventana operativa 4-5 minutos para histerotomia resucitativa
- activacion explicita de equipo obstetrico multidisciplinar
- sospecha/antidoto de toxicidad por magnesio

Sin esta extension, el soporte operativo quedaba incompleto para uno de los escenarios de mayor riesgo tiempo-dependiente.

## Decision

Se extiende el contrato de entrada de reanimacion con campos obstetricos opcionales:

- `gestational_weeks`
- `uterine_fundus_at_or_above_umbilicus`
- `minutes_since_arrest`
- `access_above_diaphragm_secured`
- `fetal_monitor_connected`
- `magnesium_infusion_active`
- `magnesium_toxicity_suspected`

Y se amplian las recomendaciones con:

- acciones de codigo obstetrico y equipo multidisciplinar
- desplazamiento uterino lateral manual 15-30 grados
- regla 4-5 minutos para histerotomia resucitativa
- checklist reversible ampliado con enfoque A-B-C-D-E-F-G-H obstetrico
- alertas criticas por ventana temporal y acceso vascular no asegurado

## Consecuencias

### Positivas

- Mejor cobertura operativa en reanimacion obstetrica critica.
- Mayor trazabilidad de decisiones en `agent_runs`/`agent_steps` sin cambios de esquema.
- Compatibilidad hacia atras: todos los campos nuevos son opcionales.

### Trade-offs

- Incremento de complejidad del payload del endpoint de reanimacion.
- Mayor necesidad de validacion humana estricta en escenarios obstetricos.

## Alternativas consideradas

1. Crear workflow obstetrico separado
   - Rechazada: duplicaba logica y fragmentaba observabilidad.
2. Mantener motor general sin extension
   - Rechazada: cobertura insuficiente para riesgo materno-fetal.
3. Extender workflow de reanimacion actual con campos opcionales
   - Elegida.
